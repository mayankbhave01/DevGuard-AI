from __future__ import annotations
import ast
import re
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class Finding:
    rule_id: str
    category: str
    severity: str
    title: str
    description: str
    suggestion: str
    line: int | None = None
    snippet: str | None = None

    def to_dict(self):
        return asdict(self)


SEVERITY_PENALTY = {
    "critical": 24,
    "high": 14,
    "medium": 7,
    "low": 3,
    "info": 1,
}


def _line_for_match(code: str, start: int) -> int:
    return code.count("\n", 0, start) + 1


def _snippet(code: str, line: int | None) -> str | None:
    if not line:
        return None
    lines = code.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()[:240]
    return None


def _regex_findings(code: str, language: str) -> list[Finding]:
    rules: list[tuple[str, str, str, str, str, str, str]] = [
        ("SEC001", "security", "critical", r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]", "Hard-coded credential", "A credential-like value appears to be embedded in source code.", "Move secrets to environment variables or a managed secret store."),
        ("SEC002", "security", "high", r"(?i)\b(md5|sha1)\s*\(", "Weak cryptographic hash", "MD5/SHA-1 is unsuitable for security-sensitive hashing.", "Use SHA-256+ for integrity or Argon2/bcrypt/scrypt for passwords."),
        ("SEC003", "security", "high", r"(?i)(SELECT|INSERT|UPDATE|DELETE).*(\+|format\(|f['\"])", "Potential SQL injection", "SQL appears to be constructed using string interpolation or concatenation.", "Use parameterized queries or an ORM query builder."),
        ("SEC004", "security", "high", r"\beval\s*\(", "Dynamic eval usage", "eval() can execute attacker-controlled input and makes code hard to audit.", "Replace eval() with explicit parsing or a safe whitelist-based dispatcher."),
        ("SEC005", "security", "high", r"(?i)shell\s*=\s*True", "Shell command execution", "Executing subprocesses through a shell increases command-injection risk.", "Avoid shell=True and pass command arguments as a list."),
        ("QUAL001", "maintainability", "low", r"(?m)^\s*(print\(|console\.log\()", "Debug logging left in code", "Debug output can leak data and clutter production logs.", "Use a structured logger with appropriate log levels."),
        ("QUAL002", "maintainability", "low", r"(?i)\b(TODO|FIXME|HACK)\b", "Unresolved maintenance marker", "The code contains a TODO/FIXME/HACK marker.", "Resolve it or create a tracked issue with clear ownership."),
        ("BUG001", "bug-risk", "medium", r"(?m)^\s*except\s*:\s*$", "Bare except block", "A bare except catches system-exiting exceptions and hides root causes.", "Catch specific exception types and log the failure context."),
        ("PERF001", "performance", "low", r"(?m)for\s+\w+\s+in\s+range\([^\n]+\):\s*\n\s+.*\.append\(", "Possible append-loop hotspot", "A loop builds a collection incrementally and may be replaceable with a clearer comprehension/vectorized operation.", "Consider a list comprehension, generator, or vectorized operation where appropriate."),
    ]

    if language.lower() in {"javascript", "typescript", "js", "ts"}:
        rules += [
            ("WEB001", "security", "high", r"\.innerHTML\s*=", "Unsafe innerHTML assignment", "Direct innerHTML assignment can enable DOM XSS.", "Prefer textContent or sanitize trusted HTML before rendering."),
            ("WEB002", "security", "high", r"\bchild_process\.(exec|execSync)\s*\(", "Shell execution in Node.js", "child_process exec invokes a shell and can expose command injection.", "Prefer spawn/execFile with fixed argument arrays."),
        ]

    findings: list[Finding] = []
    for rule_id, category, severity, pattern, title, description, suggestion in rules:
        for match in re.finditer(pattern, code):
            line = _line_for_match(code, match.start())
            findings.append(Finding(rule_id, category, severity, title, description, suggestion, line, _snippet(code, line)))
    return findings


class PythonVisitor(ast.NodeVisitor):
    def __init__(self, code: str):
        self.code = code
        self.findings: list[Finding] = []

    def add(self, rule_id, category, severity, title, description, suggestion, node):
        line = getattr(node, "lineno", None)
        self.findings.append(Finding(rule_id, category, severity, title, description, suggestion, line, _snippet(self.code, line)))

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if len(node.args.args) > 7:
            self.add("QUAL003", "maintainability", "medium", "Function has many parameters", "This function has more than seven positional parameters, increasing coupling and call-site complexity.", "Group related parameters into a typed object/dataclass or split the responsibility.", node)
        if len(node.body) > 45:
            self.add("QUAL004", "maintainability", "medium", "Large function", "This function contains many statements and is likely doing more than one job.", "Extract cohesive helper functions and keep each function focused on one responsibility.", node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_Compare(self, node: ast.Compare):
        if any(isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and comparator.value not in {None, True, False}:
                    self.add("BUG002", "bug-risk", "medium", "Identity comparison with literal", "Using 'is'/'is not' with a non-singleton literal can behave unexpectedly.", "Use == or != for value comparison.", node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            parent_is_with = False
            # AST has no parent pointers; this is a heuristic signal only.
            if not parent_is_with:
                self.add("QUAL005", "maintainability", "low", "File handle lifecycle", "A file is opened directly; verify it is always closed on every path.", "Prefer 'with open(...) as f:' to guarantee cleanup.", node)

        # Python command-execution sinks. These are high-risk when arguments are
        # assembled dynamically (for example: os.system("echo " + username)).
        if isinstance(node.func, ast.Attribute):
            owner = node.func.value.id if isinstance(node.func.value, ast.Name) else None
            name = node.func.attr

            if owner == "os" and name in {"system", "popen"}:
                self.add(
                    "SEC006", "security", "high", "Potential command injection",
                    f"{owner}.{name} executes a shell command and can become injectable when input reaches the command string.",
                    "Avoid shell command strings. Prefer a safe library API or subprocess.run([...], shell=False) with a fixed argument list and validated input.",
                    node,
                )

            if owner == "subprocess" and name in {"run", "Popen", "call", "check_call", "check_output"}:
                shell_true = any(
                    kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                    for kw in node.keywords
                )
                if shell_true:
                    self.add(
                        "SEC007", "security", "high", "Shell-enabled subprocess",
                        "subprocess is invoked with shell=True, increasing command-injection risk.",
                        "Use shell=False and pass the executable plus arguments as a list. Validate any user-controlled values.",
                        node,
                    )

        self.generic_visit(node)


def analyze_code(code: str, language: str) -> dict:
    findings = _regex_findings(code, language)

    if language.lower() in {"python", "py"}:
        try:
            tree = ast.parse(code)
            visitor = PythonVisitor(code)
            visitor.visit(tree)
            findings.extend(visitor.findings)
        except SyntaxError as exc:
            findings.append(Finding(
                "BUG000", "bug-risk", "critical", "Python syntax error",
                exc.msg, "Fix the syntax error before running or deploying this code.",
                exc.lineno, _snippet(code, exc.lineno)
            ))

    # De-duplicate same rule/line/title.
    unique: dict[tuple, Finding] = {}
    for finding in findings:
        unique[(finding.rule_id, finding.line, finding.title)] = finding
    findings = list(unique.values())

    counts = {sev: 0 for sev in ["critical", "high", "medium", "low", "info"]}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1

    penalty = sum(SEVERITY_PENALTY.get(f.severity, 0) for f in findings)
    score = max(0.0, round(100 - penalty, 1))

    return {
        "score": score,
        "findings": [f.to_dict() for f in sorted(findings, key=lambda x: (-(SEVERITY_PENALTY.get(x.severity, 0)), x.line or 10**9))],
        "counts": counts,
    }
