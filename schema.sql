-- schema.sql: Normalized Relational Schema for AI & Webhook Telemetry

PRAGMA foreign_keys = ON;

-- 1. Clients / Bots Table
CREATE TABLE IF NOT EXISTS ai_agents (
    agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('WhatsApp', 'Telegram', 'Web_API', 'Custom_Webhook')),
    model_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Conversation Sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    external_user_id VARCHAR(100) NOT NULL,
    session_status VARCHAR(20) DEFAULT 'active' CHECK (session_status IN ('active', 'resolved', 'escalated')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES ai_agents(agent_id) ON DELETE CASCADE
);

-- 3. Webhook & LLM Execution Logs (Fact Table)
CREATE TABLE IF NOT EXISTS execution_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    prompt_tokens INTEGER NOT NULL CHECK (prompt_tokens >= 0),
    completion_tokens INTEGER NOT NULL CHECK (completion_tokens >= 0),
    latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
    http_status INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- 4. Analytical View: Agent Performance & Cost Summary
CREATE VIEW IF NOT EXISTS v_agent_performance AS
SELECT 
    a.agent_name,
    a.platform,
    a.model_name,
    COUNT(l.log_id) AS total_requests,
    SUM(l.prompt_tokens + l.completion_tokens) AS total_tokens_used,
    ROUND(AVG(l.latency_ms), 2) AS avg_latency_ms,
    ROUND(SUM(l.cost_usd), 4) AS total_cost_usd,
    ROUND(SUM(CASE WHEN l.http_status = 200 THEN 1 ELSE 0 END) * 100.0 / COUNT(l.log_id), 1) AS success_rate_pct
FROM ai_agents a
JOIN chat_sessions s ON a.agent_id = s.agent_id
JOIN execution_logs l ON s.session_id = l.session_id
GROUP BY a.agent_id, a.agent_name, a.platform, a.model_name;