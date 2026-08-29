export type User = { id: number; name: string; email: string }
export type AuthResponse = { access_token: string; token_type: string; user: User }
export type Issue = {
  id: number; rule_id: string; category: string; severity: string; title: string;
  description: string; suggestion: string; line: number | null; snippet: string | null
}
export type Scan = {
  id: number; title: string; language: string; score: number; issue_count: number;
  critical_count: number; high_count: number; medium_count: number; low_count: number;
  created_at: string; code?: string; llm_summary?: string | null; issues?: Issue[]
}
export type DashboardStats = {
  total_scans: number; average_score: number; total_issues: number;
  severity_counts: Record<string, number>; category_counts: Record<string, number>;
  language_counts: Record<string, number>; recent_scans: Scan[]
}
