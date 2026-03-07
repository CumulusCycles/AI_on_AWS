"""
AI Agent Insure — Bedrock Agent chat application.

Calls the Bedrock Agent runtime directly via boto3. No backend server required.
"""
import os
import json
import uuid
import boto3
from botocore.exceptions import ClientError
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AGENT_ID = os.environ["AGENT_ID"]
AGENT_ALIAS_ID = os.environ["AGENT_ALIAS_ID"]

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Agent Insure — Agent Assistant",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #0d1117; }
    [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    [data-testid="stSidebar"] { background-color: #161b22; }

    .msg-user {
        background-color: #1f2937;
        border-left: 4px solid #ff9900;
        padding: 0.9rem 1.2rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        color: #d4dae3;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .msg-assistant {
        background-color: #1b2230;
        border-left: 4px solid #3b82f6;
        padding: 0.9rem 1.2rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        color: #d4dae3;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .msg-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .label-user { color: #ff9900; }
    .label-assistant { color: #3b82f6; }

    .trace-step {
        background-color: #0f1923;
        border-left: 3px solid #22c55e;
        padding: 0.5rem 0.9rem;
        border-radius: 4px;
        margin: 0.3rem 0;
        font-size: 0.78rem;
        font-family: monospace;
        color: #86efac;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .section-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #ff9900;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
        font-weight: 600;
    }
    .stButton > button[kind="primary"] {
        background-color: #ff9900;
        color: #0d1117;
        border: none;
        font-weight: 700;
        border-radius: 4px;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #e88a00;
        color: #0d1117;
    }
    .session-pill {
        display: inline-block;
        background-color: #1f2937;
        color: #9ca3af;
        border: 1px solid #374151;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.72rem;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "history" not in st.session_state:
    st.session_state.history = []


# ---------------------------------------------------------------------------
# Bedrock Agent helpers
# ---------------------------------------------------------------------------

def _parse_trace_event(event: dict) -> list[str]:
    """Extract human-readable trace strings from a single Bedrock event."""
    messages = []
    trace = event.get("trace", {}).get("trace", {})
    orch = trace.get("orchestrationTrace", {})

    rationale = orch.get("rationale", {}).get("text", "")
    if rationale:
        messages.append(rationale)

    inv_input = orch.get("invocationInput", {})

    action_inv = inv_input.get("actionGroupInvocationInput", {})
    if action_inv:
        fn = action_inv.get("function", "")
        params = action_inv.get("parameters", [])
        param_str = ", ".join(f"{p['name']}={p['value']}" for p in params)
        messages.append(f"Calling `{fn}({param_str})`")

    kb_inv = inv_input.get("knowledgeBaseLookupInput", {})
    if kb_inv:
        messages.append(f'Searching knowledge base: "{kb_inv.get("text", "")}"')

    obs = orch.get("observation", {})
    action_result = obs.get("actionGroupInvocationOutput", {}).get("text", "")
    if action_result:
        try:
            result_preview = json.dumps(json.loads(action_result), indent=2)
        except (json.JSONDecodeError, TypeError):
            result_preview = action_result
        messages.append(f"Tool result:\n{result_preview}")

    return messages


def invoke_agent(message: str, session_id: str):
    """
    Call invoke_agent and yield (type, content) tuples:
      ("trace", str)   — agent reasoning step
      ("chunk", str)   — incremental response text
      ("error", str)   — error message
    """
    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=message,
            enableTrace=True,
        )
        for event in response["completion"]:
            if "trace" in event:
                for msg in _parse_trace_event(event):
                    yield ("trace", msg)
            elif "chunk" in event:
                chunk_bytes = event["chunk"].get("bytes", b"")
                if chunk_bytes:
                    yield ("chunk", chunk_bytes.decode("utf-8"))
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        yield ("error", f"AWS error ({code}): {msg}")
    except Exception as e:
        yield ("error", str(e))


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🤖 AI Agent Insure")
    st.caption("Bedrock Agent — Claims & Policy Assistant")
    st.divider()

    st.markdown("### Session")
    if st.session_state.session_id:
        st.markdown(
            f'<span class="session-pill">{st.session_state.session_id[:16]}…</span>',
            unsafe_allow_html=True,
        )
        if st.button("New conversation", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No active session — send a message to start one.")

    st.divider()

    show_trace = st.toggle("Show agent trace", value=True)

    st.divider()

    st.markdown("### Try asking…")
    examples = [
        "What policies does AI Agent Insure offer?",
        "Look up policy POL-001",
        "List all policies",
        "What's the coverage limit on POL-003?",
        "I need to file a claim under POL-002 — our AI model crashed and caused $80,000 in losses",
        "Check the status of claim CLM-ABC123",
        "What does Agentic AI Liability Insurance cover?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex[:20]}"):
            st.session_state["send_prefill"] = ex  # send this message on next run
            st.rerun()


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("🤖 AI Agent Insure")
st.caption("Powered by Amazon Bedrock Agents · Claude 3.5 Sonnet")
st.divider()

# --- Conversation history ---
chat_col, trace_col = st.columns([3, 2]) if show_trace else (st.container(), None)

with chat_col:
    for turn in st.session_state.history:
        if turn["role"] == "user":
            st.markdown(
                f'<div class="msg-label label-user">You</div>'
                f'<div class="msg-user">{turn["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="msg-label label-assistant">Aria (Agent)</div>'
                f'<div class="msg-assistant">{turn["content"]}</div>',
                unsafe_allow_html=True,
            )

if show_trace and trace_col is not None:
    with trace_col:
        st.markdown('<div class="section-label">Agent Trace</div>', unsafe_allow_html=True)
        last_traces = []
        for turn in reversed(st.session_state.history):
            if turn["role"] == "assistant" and turn.get("traces"):
                last_traces = turn["traces"]
                break
        if last_traces:
            for step in last_traces:
                st.markdown(f'<div class="trace-step">{step}</div>', unsafe_allow_html=True)
        else:
            st.caption("Agent reasoning steps will appear here during a response.")

# --- Input ---
st.divider()

# If user clicked an example, treat it as "Send" with that message (don't require clicking Send)
message_to_send = st.session_state.pop("send_prefill", None)
user_input = st.text_area(
    "Message",
    value="",
    height=90,
    placeholder="Ask about policies, file a claim, check claim status…",
    label_visibility="collapsed",
)

col_send, col_clear = st.columns([1, 5])
with col_send:
    send = st.button("Send", type="primary", use_container_width=True)
with col_clear:
    if st.button("Clear chat", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.history = []
        st.rerun()

# Use example text as message if an example was clicked; otherwise use typed input + Send
if message_to_send:
    user_message = message_to_send.strip()
else:
    user_message = user_input.strip() if send else ""

# ---------------------------------------------------------------------------
# Handle send — call Bedrock directly, update trace live
# ---------------------------------------------------------------------------
if user_message:
    if not st.session_state.session_id:
        st.session_state.session_id = str(uuid.uuid4())

    st.session_state.history.append({
        "role": "user",
        "content": user_message,
        "traces": [],
    })

    traces_collected: list[str] = []
    response_text = ""

    with st.spinner("Aria is thinking…"):
        # Live trace panel — updates as events arrive
        if show_trace and trace_col is not None:
            with trace_col:
                st.markdown('<div class="section-label">Agent Trace</div>', unsafe_allow_html=True)
                trace_placeholder = st.empty()

        for event_type, content in invoke_agent(user_message, st.session_state.session_id):
            if event_type == "trace":
                traces_collected.append(content)
                if show_trace and trace_col is not None:
                    trace_html = "".join(
                        f'<div class="trace-step">{step}</div>'
                        for step in traces_collected
                    )
                    trace_placeholder.markdown(trace_html, unsafe_allow_html=True)
            elif event_type == "chunk":
                response_text += content
            elif event_type == "error":
                st.error(content)
                st.stop()

    st.session_state.history.append({
        "role": "assistant",
        "content": response_text,
        "traces": traces_collected,
    })

    st.rerun()
