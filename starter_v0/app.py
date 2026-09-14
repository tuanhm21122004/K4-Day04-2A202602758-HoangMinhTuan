"""
IT Helpdesk Agent — Streamlit Chat UI (Ultra Modern SaaS Edition)
Reuses run_model_tool_loop from chat.py for strictly consistent agent behavior.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from chat import run_model_tool_loop, trim_history
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict

# ─── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

# ─── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Northstar IT Helpdesk AI Core",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS (High Contrast, Ultra Modern SaaS Glassmorphism) ────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-main: #0a0d14;
    --bg-sidebar: #0f1420;
    --bg-card: rgba(19, 26, 42, 0.75);
    --bg-card-hover: rgba(28, 38, 62, 0.85);
    --bg-glass: rgba(255, 255, 255, 0.03);
    
    --primary: #6366f1;
    --primary-glow: rgba(99, 102, 241, 0.35);
    --accent-purple: #8b5cf6;
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    
    --text-pure: #ffffff;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    --border-glass: rgba(255, 255, 255, 0.08);
    --border-accent: rgba(99, 102, 241, 0.4);
    
    --grad-primary: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    --grad-cyan: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
    --grad-emerald: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
}

/* Global Font & App Canvas */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.stApp {
    background: radial-gradient(circle at 50% 0%, #171f38 0%, #0a0d14 60%, #07090e 100%) !important;
    color: var(--text-primary) !important;
}

.main .block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px !important;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-glass) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
}

section[data-testid="stSidebar"] * {
    color: var(--text-primary);
}

/* Hero Header Banner */
.hero-container {
    background: linear-gradient(180deg, rgba(30, 41, 69, 0.5) 0%, rgba(15, 20, 32, 0.4) 100%);
    border: 1px solid var(--border-glass);
    border-radius: 18px;
    padding: 1.25rem 1.75rem;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.hero-title-wrap {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.hero-icon-box {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: var(--grad-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.75rem;
    box-shadow: 0 0 24px var(--primary-glow);
}

.hero-title {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.hero-badges {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}

.badge-live {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 30px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34d399;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
}

.badge-version {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 30px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #a5b4fc;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}

/* Chat Message Styling & Text Contrast */
.stChatMessage {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 16px !important;
    padding: 1.25rem 1.25rem !important;
    margin-bottom: 1rem !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.2s ease;
}

.stChatMessage:hover {
    border-color: rgba(99, 102, 241, 0.25) !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3) !important;
}

/* Force high contrast text inside chat messages */
.stChatMessage, 
.stChatMessage p, 
.stChatMessage li, 
.stChatMessage span, 
.stChatMessage div {
    color: #f1f5f9 !important;
    font-size: 0.95rem;
    line-height: 1.6;
}

/* User Message Specifics */
.stChatMessage[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: rgba(30, 38, 64, 0.6) !important;
    border-left: 3px solid #6366f1 !important;
}

/* Assistant Message Specifics */
.stChatMessage[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(20, 26, 44, 0.8) !important;
    border-left: 3px solid #10b981 !important;
}

/* Human-friendly Assistant Reply Box */
.assistant-reply-card {
    background: rgba(14, 20, 36, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
    margin: 0.5rem 0;
    color: #f8fafc !important;
    font-size: 1rem !important;
    line-height: 1.65;
}

.assistant-reply-card p {
    color: #f8fafc !important;
    margin: 0 0 0.5rem 0;
}

/* Meta Pills (Intent, Action, Evidence) */
.meta-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 0.75rem;
}

.meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 500;
}

.meta-intent {
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #c7d2fe;
}

.meta-action {
    background: rgba(6, 182, 212, 0.15);
    border: 1px solid rgba(6, 182, 212, 0.3);
    color: #67e8f9;
}

.meta-evidence {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #fcd34d;
}

/* Tool execution container */
.tool-box {
    background: rgba(12, 16, 28, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 0.75rem;
    margin: 0.5rem 0;
}

/* Tool Call & Result Badges */
.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.tool-badge-call {
    background: rgba(99, 102, 241, 0.18);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.35);
}
.tool-badge-result {
    background: rgba(16, 185, 129, 0.18);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.tool-badge-error {
    background: rgba(244, 63, 94, 0.18);
    color: #fda4af;
    border: 1px solid rgba(244, 63, 94, 0.35);
}

/* Status Indicators */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.5rem;
}
.status-pass { 
    background: rgba(16, 185, 129, 0.15); 
    color: #34d399; 
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.status-fail { 
    background: rgba(244, 63, 94, 0.15); 
    color: #fb7185; 
    border: 1px solid rgba(244, 63, 94, 0.3);
}
.status-wait { 
    background: rgba(245, 158, 11, 0.15); 
    color: #fbbf24; 
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Version & Config Cards in Sidebar */
.info-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    backdrop-filter: blur(8px);
}
.info-label {
    font-size: 0.65rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 700;
}
.info-value {
    font-size: 0.82rem;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace !important;
    word-break: break-all;
    margin-top: 2px;
}

/* Quick prompt chips container */
.quick-prompt-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* Streamlit button enhancements */
div.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border-glass) !important;
    background: rgba(255, 255, 255, 0.04) !important;
    color: var(--text-primary) !important;
}
div.stButton > button:hover {
    background: var(--primary) !important;
    color: #ffffff !important;
    border-color: var(--primary) !important;
    box-shadow: 0 4px 14px var(--primary-glow) !important;
    transform: translateY(-1px);
}

/* Code block dark style */
pre, code {
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 8px !important;
}

/* Expander headers */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.02) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Helper functions ───────────────────────────────────────────────────
def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "run"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_transcript(path: Path, transcript: dict[str, Any]) -> None:
    transcript["updated_at"] = now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def render_tool_event(event: dict[str, Any]) -> None:
    """Render a single tool call + result as a styled expander."""
    tool_name = event.get("tool", "unknown")
    args = event.get("args", {})
    result = event.get("result", {})
    has_error = isinstance(result, dict) and result.get("error")

    badge_class = "tool-badge-error" if has_error else "tool-badge-result"
    status_icon = "❌ Lỗi" if has_error else "✅ Thành công"

    with st.expander(f"⚙️ Tool: `{tool_name}` — {status_icon}", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                '<span class="tool-badge tool-badge-call">⚡ INPUT ARGS</span>',
                unsafe_allow_html=True,
            )
            st.code(json.dumps(args, ensure_ascii=False, indent=2), language="json")
        with col2:
            st.markdown(
                f'<span class="tool-badge {badge_class}">📤 OUTPUT RESULT</span>',
                unsafe_allow_html=True,
            )
            result_str = json.dumps(result, ensure_ascii=False, indent=2, default=str)
            if len(result_str) > 2000:
                result_str = result_str[:2000] + "\n...(truncated)"
            st.code(result_str, language="json")


def render_rounds(rounds: list[dict[str, Any]]) -> None:
    """Render all tool rounds for a turn with round badges."""
    for rnd in rounds:
        round_num = rnd.get("round", "?")
        tool_calls = rnd.get("tool_calls", [])
        tool_results = rnd.get("tool_results", [])

        if not tool_calls and not tool_results:
            continue

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:8px 0 4px 0;">'
            f'<span style="background:var(--grad-primary);color:#fff;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:12px;">ROUND {round_num}</span>'
            f'<span style="font-size:0.8rem;color:var(--text-secondary);">{len(tool_calls)} tool execution(s)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for event in tool_results:
            render_tool_event(event)


def render_assistant_content(text: str) -> None:
    """Parse JSON responses cleanly, showing human reply & metadata badges."""
    if not text:
        return

    # Check if text is a JSON payload from the prompt contract
    try:
        data = json.loads(text.strip())
        if isinstance(data, dict):
            reply = data.get("reply") or data.get("message")
            intent = data.get("intent")
            action = data.get("action")
            evidence = data.get("evidence_ids")

            if reply:
                # Meta pills row
                badges = []
                if intent:
                    badges.append(f'<span class="meta-pill meta-intent">🎯 Intent: <b>{intent}</b></span>')
                if action:
                    badges.append(f'<span class="meta-pill meta-action">⚡ Action: <b>{action}</b></span>')
                # Fallback evidence extraction if model forgot to populate it
                if not evidence:
                    found_ev = re.findall(r"\b(?:INC|REQ|CHG|LT|DT)-\d+\b|\bPOL-[A-Z0-9_-]+\b", reply, flags=re.IGNORECASE)
                    if found_ev:
                        evidence = list(dict.fromkeys(found_ev))

                if evidence:
                    ev_str = ", ".join(evidence) if isinstance(evidence, list) else str(evidence)
                    badges.append(f'<span class="meta-pill meta-evidence">📌 Evidence: <b>{ev_str}</b></span>')

                if badges:
                    st.markdown(f'<div class="meta-container">{" ".join(badges)}</div>', unsafe_allow_html=True)

                # Render reply using native markdown for clean bullet points, bolding & spacing
                st.markdown(reply)

                # Collapsible raw JSON inspect
                with st.expander("🔍 Xem chi tiết Raw JSON Response", expanded=False):
                    st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
                return
    except Exception:
        pass

    # Fallback to direct markdown rendering
    st.markdown(text)


# ─── Session state init ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "turn_index" not in st.session_state:
    st.session_state.turn_index = 0
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "transcript_path" not in st.session_state:
    st.session_state.transcript_path = None
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# ─── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#a855f7);display:flex;align-items:center;justify-content:center;font-size:1.2rem;">⚡</div>
        <div>
            <div style="font-size:1.1rem;font-weight:800;color:#fff;letter-spacing:-0.01em;">IT Helpdesk Core</div>
            <div style="font-size:0.75rem;color:#94a3b8;">Northstar Labs AI Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Provider & model config
    provider_name = st.selectbox(
        "AI Provider",
        ["openrouter", "gemini", "openai", "anthropic"],
        index=0,
        help="Chọn nhà cung cấp mô hình LLM",
    )

    default_models = {
        "openrouter": "openai/gpt-4o-mini",
        "gemini": "gemini-3.5-flash",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-20250514",
    }
    model_name = st.text_input(
        "Model Identifier",
        value=default_models.get(provider_name, ""),
        help="Định danh model sử dụng",
    )

    version_label = st.selectbox(
        "Artifact Version",
        ["v0", "v1", "v2", "v3"],
        index=0,
        help="Phiên bản prompt & tool declarations",
    )

    col_hw, col_mr = st.columns(2)
    with col_hw:
        history_window = st.number_input("History Window", min_value=1, max_value=10, value=5)
    with col_mr:
        max_tool_rounds = st.number_input("Max Rounds", min_value=1, max_value=8, value=4)

    st.divider()

    # Load artifacts & show version info
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"

    try:
        artifact_version = build_artifact_version(version_label, system_prompt_path, tools_path)
        st.markdown(f"""
        <div class="info-card">
            <div class="info-label">Artifact Tag</div>
            <div class="info-value">{artifact_version.artifact_version}</div>
        </div>
        <div class="info-card">
            <div class="info-label">Prompt SHA256</div>
            <div class="info-value">{artifact_version.prompt_hash[:16]}...</div>
        </div>
        <div class="info-card">
            <div class="info-label">Tools SHA256</div>
            <div class="info-value">{artifact_version.tools_hash[:16]}...</div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Lỗi tải artifacts: {e}")
        st.stop()

    st.divider()

    # Live Transcript Card & Download
    st.markdown('<div class="info-label" style="margin-bottom:6px;">LIVE TRANSCRIPT SESSION</div>', unsafe_allow_html=True)
    if st.session_state.transcript_path:
        t_name = Path(st.session_state.transcript_path).name
        st.markdown(f"""
        <div class="info-card" style="border-left: 3px solid #10b981;">
            <div style="font-size:0.75rem;color:#34d399;font-weight:700;">● RECORDING ACTIVE</div>
            <div class="info-value" style="font-size:0.75rem;">{t_name}</div>
            <div style="font-size:0.72rem;color:#94a3b8;margin-top:4px;">Turns: <b>{st.session_state.turn_index}</b></div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.transcript:
            transcript_bytes = json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2, default=str).encode("utf-8")
            st.download_button(
                label="📥 Tải Transcript JSON",
                data=transcript_bytes,
                file_name=t_name,
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.caption("Chưa có lượt chat nào trong phiên này.")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    if st.button("🗑️ Reset Cuộc Trò Chuyện", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.turn_index = 0
        st.session_state.transcript = None
        st.session_state.transcript_path = None
        st.session_state.pending_prompt = None
        st.rerun()


# ─── Load resources ─────────────────────────────────────────────────────
@st.cache_resource
def get_provider(name: str):
    return make_provider(name)


@st.cache_data
def get_tools(tools_path_str: str):
    declarations = load_tool_declarations(Path(tools_path_str))
    return declarations, to_openai_tools(declarations)


system_prompt = system_prompt_path.read_text(encoding="utf-8")
tool_declarations, openai_tools = get_tools(str(tools_path))


# ─── Initialize transcript ─────────────────────────────────────────────
def init_transcript() -> None:
    if st.session_state.transcript is not None:
        return
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(version_label),
        safe_slug(provider_name),
        timestamp,
    ])
    path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript_path = str(path)
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model_name,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


# ─── Hero Header ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-container">
    <div class="hero-title-wrap">
        <div class="hero-icon-box">⚡</div>
        <div>
            <h1 class="hero-title">IT Helpdesk Intelligence System</h1>
            <p class="hero-subtitle">Hỗ trợ tự động: Sự cố mạng, VPN, Tài sản thiết bị, Tra cứu Ticket & Chính sách</p>
        </div>
    </div>
    <div class="hero-badges">
        <div class="badge-live">
            <span class="badge-dot"></span>
            AGENT LIVE
        </div>
        <div class="badge-version">
            🛠️ {len(tool_declarations)} Tools Active
        </div>
        <div class="badge-version">
            🏷️ {version_label.upper()}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Quick Starter Chips ────────────────────────────────────────────────
st.markdown('<div class="quick-prompt-title">⚡ GỢI Ý YÊU CẦU NHANH:</div>', unsafe_allow_html=True)
quick_cols = st.columns(5)
quick_samples = [
    ("🌐 Trạng thái VPN", "Kiểm tra trạng thái VPN production"),
    ("🎫 Tra cứu Ticket", "Tra cứu trạng thái của ticket INC-1042"),
    ("💻 Thiết bị NB-5521", "Kiểm tra tình trạng thiết bị NB-5521"),
    ("📜 Chính sách BYOD", "Quy định công ty về chính sách BYOD và thiết bị cá nhân"),
    ("➕ Báo lỗi Outlook", "Tạo ticket báo sự cố Outlook không kết nối email"),
]

for col, (btn_label, prompt_text) in zip(quick_cols, quick_samples):
    if col.button(btn_label, use_container_width=True):
        st.session_state.pending_prompt = prompt_text
        st.rerun()

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# ─── Render chat history ────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f"**{msg['content']}**")
        else:
            if msg.get("rounds"):
                render_rounds(msg["rounds"])
            render_assistant_content(msg["content"])

        if msg.get("status"):
            status_class = {
                "answered": "status-pass",
                "waiting_for_user": "status-wait",
                "max_tool_rounds": "status-fail",
                "provider_error": "status-fail",
            }.get(msg["status"], "")
            st.markdown(
                f'<span class="status-pill {status_class}">Status: {msg["status"]}</span>',
                unsafe_allow_html=True,
            )

# ─── Handle Chat Input (either from chat_input or quick starter chips) ──
user_input = None
if st.session_state.pending_prompt:
    user_input = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
else:
    user_input = st.chat_input("Nhập yêu cầu trợ giúp IT hoặc hỏi về thiết bị, ticket, dịch vụ...")

if user_input:
    init_transcript()

    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(f"**{user_input}**")

    # Build messages
    st.session_state.turn_index += 1
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_input},
    ]

    # Prepare turn record
    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_input,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        try:
            provider = get_provider(provider_name)
            with st.spinner("🤖 Agent đang suy luận và gọi tools..."):
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_name or None,
                    max_tool_rounds=max_tool_rounds,
                )

            turn_record.update(result)
            assistant_text = result.get("assistant_text", "")
            rounds = result.get("rounds", [])
            status = result.get("status", "unknown")

            # Display tool rounds first
            if rounds:
                render_rounds(rounds)

            # Display human-friendly response
            render_assistant_content(assistant_text)

            # Status pill
            status_class = {
                "answered": "status-pass",
                "waiting_for_user": "status-wait",
                "max_tool_rounds": "status-fail",
            }.get(status, "")
            st.markdown(
                f'<span class="status-pill {status_class}">Status: {status}</span>',
                unsafe_allow_html=True,
            )

            # Save to session
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "rounds": rounds,
                "status": status,
            })
            st.session_state.history.append({"role": "user", "content": user_input})
            st.session_state.history.append({"role": "assistant", "content": assistant_text})

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {str(exc)}"
            turn_record.update({
                "status": "provider_error",
                "error": error_msg,
            })
            st.error(f"⚠️ Lỗi Provider: {error_msg}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Error: {error_msg}",
                "status": "provider_error",
            })

    # Save transcript
    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(
        Path(st.session_state.transcript_path),
        st.session_state.transcript,
    )
