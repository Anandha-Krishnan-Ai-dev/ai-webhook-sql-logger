import sqlite3
from pathlib import Path


class AITelemetryDB:
    """Manages SQL database operations for AI agents and webhook logs."""

    def __init__(self, db_path: str = "telemetry.db", schema_path: str = "schema.sql"):
        self.db_path = db_path
        self.schema_path = schema_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Executes the external .sql schema file to set up tables and views."""
        schema_sql = Path(self.schema_path).read_text(encoding="utf-8")
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema_sql)

    def seed_sample_data(self) -> None:
        """Populates the database with realistic AI & webhook telemetry data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Prevent duplicate seeding
            cursor.execute("SELECT COUNT(*) FROM ai_agents")
            if cursor.fetchone()[0] > 0:
                return

            # 1. Insert AI Agents
            agents = [
                ("AutoFlow Lead Qualifier", "WhatsApp", "gpt-4o-mini"),
                ("SQL Query Assistant", "Web_API", "claude-3-5-sonnet"),
                ("Order Status Webhook Bot", "Custom_Webhook", "gemini-1.5-flash"),
            ]
            cursor.executemany(
                "INSERT INTO ai_agents (agent_name, platform, model_name) VALUES (?, ?, ?)",
                agents,
            )

            # 2. Insert Chat Sessions
            sessions = [
                (1, "+91-9876543210", "resolved"),
                (1, "+91-9123456780", "active"),
                (2, "user_dev_101", "resolved"),
                (3, "webhook_order_882", "escalated"),
            ]
            cursor.executemany(
                "INSERT INTO chat_sessions (agent_id, external_user_id, session_status) VALUES (?, ?, ?)",
                sessions,
            )

            # 3. Insert Webhook & Token Execution Logs
            # (session_id, prompt_tokens, completion_tokens, latency_ms, http_status, cost_usd)
            logs = [
                (1, 320, 140, 410, 200, 0.000153),
                (1, 450, 210, 520, 200, 0.000219),
                (2, 290, 95, 380, 200, 0.000125),
                (3, 1200, 650, 1450, 200, 0.013350),
                (3, 980, 420, 1120, 200, 0.009240),
                (4, 150, 0, 3100, 504, 0.000015),  # Simulated webhook timeout
                (4, 150, 85, 290, 200, 0.000088),  # Retry succeeded
            ]
            cursor.executemany(
                """INSERT INTO execution_logs 
                   (session_id, prompt_tokens, completion_tokens, latency_ms, http_status, cost_usd) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                logs,
            )
            conn.commit()

    def print_analytics_report(self) -> None:
        """Runs analytical SQL queries and formats the output in the terminal."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            print("\n📊 === AI AGENT PERFORMANCE & COST REPORT (SQL VIEW) ===")
            cursor.execute("SELECT * FROM v_agent_performance ORDER BY total_cost_usd DESC")
            for row in cursor.fetchall():
                print(
                    f"• {row['agent_name']} ({row['platform']} | {row['model_name']})\n"
                    f"  Requests: {row['total_requests']} | Tokens: {row['total_tokens_used']} | "
                    f"Avg Latency: {row['avg_latency_ms']}ms | Success: {row['success_rate_pct']}% | "
                    f"Cost: ${row['total_cost_usd']:.4f}\n"
                )

            print("⚠️ === HIGH-LATENCY OR FAILED WEBHOOK CALLS (>1000ms or HTTP != 200) ===")
            cursor.execute("""
                SELECT a.agent_name, s.external_user_id, l.latency_ms, l.http_status, l.logged_at
                FROM execution_logs l
                JOIN chat_sessions s ON l.session_id = s.session_id
                JOIN ai_agents a ON s.agent_id = a.agent_id
                WHERE l.latency_ms > 1000 OR l.http_status != 200
                ORDER BY l.latency_ms DESC
            """)
            for row in cursor.fetchall():
                print(
                    f"• [{row['http_status']}] {row['agent_name']} -> User: {row['external_user_id']} "
                    f"({row['latency_ms']}ms)"
                )


if __name__ == "__main__":
    db = AITelemetryDB()
    db.seed_sample_data()
    db.print_analytics_report()