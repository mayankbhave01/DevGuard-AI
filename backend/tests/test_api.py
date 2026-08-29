def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_login(client):
    r = client.post("/api/auth/register", json={"name": "Mayank", "email": "m@example.com", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "m@example.com"
    r2 = client.post("/api/auth/login", json={"email": "m@example.com", "password": "password123"})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_scan_detects_findings(client, token):
    code = 'password = "supersecret123"\nprint(password)\neval(input())\n'
    r = client.post("/api/scans", headers=auth(token), json={"title": "Bad sample", "language": "python", "code": code, "use_llm": False})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["issue_count"] >= 2
    assert body["score"] < 100
    assert any(i["rule_id"] == "SEC001" for i in body["issues"])


def test_dashboard(client, token):
    code = "print('hello')"
    client.post("/api/scans", headers=auth(token), json={"title": "Sample", "language": "python", "code": code})
    r = client.get("/api/scans/dashboard", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["total_scans"] == 1


def test_requires_authentication(client):
    r = client.get("/api/scans")
    assert r.status_code == 401


def test_export_markdown(client, token):
    r = client.post("/api/scans", headers=auth(token), json={"title": "Export me", "language": "python", "code": "eval(input())"})
    scan_id = r.json()["id"]
    export = client.get(f"/api/scans/{scan_id}/export/md", headers=auth(token))
    assert export.status_code == 200
    assert "DevGuard AI Report" in export.text


def test_python_command_injection_detection(client, token):
    code = 'import os\nusername = input("Username: ")\nos.system("echo " + username)\n'
    r = client.post(
        "/api/scans",
        headers=auth(token),
        json={"title": "Command injection sample", "language": "python", "code": code, "use_llm": False},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert any(i["rule_id"] == "SEC006" for i in body["issues"])
    finding = next(i for i in body["issues"] if i["rule_id"] == "SEC006")
    assert finding["severity"] == "high"
    assert finding["line"] == 3


def test_export_multiple_formats(client, token):
    r = client.post(
        "/api/scans",
        headers=auth(token),
        json={"title": "Multi export", "language": "python", "code": 'password = "secret123"\nprint(password)'},
    )
    scan_id = r.json()["id"]
    cases = {
        "json": "application/json",
        "md": "text/markdown",
        "txt": "text/plain",
        "csv": "text/csv",
        "html": "text/html",
        "pdf": "application/pdf",
        "zip": "application/zip",
    }
    for fmt, media in cases.items():
        export = client.get(
            f"/api/scans/{scan_id}/export/{fmt}?include_source=false&include_suggestions=true&mode=detailed",
            headers=auth(token),
        )
        assert export.status_code == 200, (fmt, export.text[:200])
        assert export.headers["content-type"].startswith(media)
        assert export.content
    pdf = client.get(f"/api/scans/{scan_id}/export/pdf", headers=auth(token))
    assert pdf.content.startswith(b"%PDF")
    bundle = client.get(f"/api/scans/{scan_id}/export/zip", headers=auth(token))
    assert bundle.content.startswith(b"PK")
