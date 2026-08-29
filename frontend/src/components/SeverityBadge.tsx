export default function SeverityBadge({ severity }: { severity: string }) {
  return <span className={`badge sev-${severity.toLowerCase()}`}>{severity}</span>
}
