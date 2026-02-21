import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Agent Insure — Knowledge Assistant", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
        /* AWS dark background */
        .main { background-color: #0d1117; }
        [data-testid="stAppViewContainer"] { background-color: #0d1117; }
        [data-testid="stSidebar"] { background-color: #161b22; }

        /* Answer box — AWS Squid Ink + AWS Orange accent */
        .answer-box {
            background-color: #1b2230;
            border-left: 4px solid #ff9900;
            padding: 1.2rem 1.5rem;
            border-radius: 6px;
            margin-top: 1rem;
            font-size: 1rem;
            line-height: 1.7;
            color: #d4dae3;
        }

        /* Source pills — AWS Orange tint */
        .source-pill {
            display: inline-block;
            background-color: #2a2000;
            color: #ff9900;
            border: 1px solid #ff9900;
            border-radius: 4px;
            padding: 3px 10px;
            margin: 4px 4px 0 0;
            font-size: 0.78rem;
            font-family: monospace;
        }

        /* Section labels */
        .section-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #ff9900;
            margin-top: 1.4rem;
            margin-bottom: 0.4rem;
            font-weight: 600;
        }

        /* Button override — AWS Orange */
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
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ AI Agent Insure")
st.caption("Knowledge Assistant — powered by Amazon Bedrock RAG")

st.divider()

query = st.text_area("Ask a question about AI Agent Insure products or coverage:", height=100, placeholder="e.g. What products does AI Agent Insure offer?")

col1, col2 = st.columns([1, 5])
with col1:
    submit = st.button("Ask", use_container_width=True, type="primary")

if submit:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Querying knowledge base..."):
            try:
                response = requests.post(f"{FASTAPI_URL}/query", json={"query": query}, timeout=30)
                response.raise_for_status()
                data = response.json()

                answer = data.get("generated_response", "")
                s3_locations = data.get("s3_locations", [])

                st.markdown('<div class="section-label">Answer</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

                if s3_locations:
                    st.markdown('<div class="section-label">Sources</div>', unsafe_allow_html=True)
                    pills = ""
                    for uri in s3_locations:
                        filename = uri.split("/")[-1].replace("_", " ").replace(".md", "")
                        pills += f'<span class="source-pill">{filename}</span>'
                    st.markdown(pills, unsafe_allow_html=True)

            except requests.exceptions.Timeout:
                st.error("Request timed out. The FastAPI server or Lambda may be slow — try again.")
            except requests.exceptions.HTTPError as e:
                st.error(f"API error: {e.response.status_code} — {e.response.text}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
