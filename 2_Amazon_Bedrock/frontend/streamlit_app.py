"""
Streamlit frontend for AWS Bedrock chat application
"""
import streamlit as st
import requests
import os
import json
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
CHAT_STREAM_ENDPOINT = f"{API_BASE_URL}/chat/stream"

# Page configuration
st.set_page_config(
    page_title="AWS Bedrock Chat",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None


def get_backend_config():
    """
    Fetch default configuration from backend API
    This is a hard dependency - frontend requires backend to be available
    """
    try:
        response = requests.get(f"{API_BASE_URL}/config", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Cannot connect to backend API at {API_BASE_URL}. Please ensure the backend server is running.")
        st.stop()
        raise


# Fetch backend configuration on initial load - hard dependency
if "backend_config" not in st.session_state:
    st.session_state.backend_config = get_backend_config()


def send_message_to_api(user_message: str, use_streaming: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Send user message to FastAPI backend and return assistant response
    Args:
        user_message: The user's message
        use_streaming: If True, use the streaming endpoint
    Returns: (response_message, error_message)
    If successful, error_message will be None
    If error, response_message will be None
    """
    # Build messages list with conversation history
    messages = []
    for msg in st.session_state.messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # Prepare request - use values from session state (set from sliders)
    request_data = {
        "messages": messages,
        "temperature": st.session_state.get("temperature"),
        "max_tokens": st.session_state.get("max_tokens")
    }
    
    # Select endpoint based on streaming preference
    endpoint = CHAT_STREAM_ENDPOINT if use_streaming else CHAT_ENDPOINT
    
    try:
        if use_streaming:
            # Handle streaming response
            response = requests.post(endpoint, json=request_data, stream=True, timeout=60)
            response.raise_for_status()
            
            # Parse Server-Sent Events (SSE) stream
            full_message = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        try:
                            data = json.loads(data_str)
                            if data.get('type') == 'delta':
                                # Accumulate text deltas
                                full_message += data.get('text', '')
                            elif data.get('type') == 'error':
                                return None, data.get('error', 'Unknown streaming error')
                            elif data.get('type') == 'complete':
                                # Stream complete, return full message
                                return data.get('message', full_message), None
                        except json.JSONDecodeError:
                            continue
            
            # If we get here, return what we have
            return full_message if full_message else None, None
        else:
            # Handle non-streaming response
            response = requests.post(endpoint, json=request_data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["message"], None
    except requests.exceptions.HTTPError as e:
        # Server returned an error status code
        error_detail = None
        try:
            error_response = response.json()
            error_detail = error_response.get("detail", str(e))
        except (ValueError, AttributeError):
            error_detail = f"HTTP {response.status_code}: {response.text}" if hasattr(response, 'status_code') else str(e)
        return None, error_detail
    except requests.exceptions.ConnectionError:
        return None, f"❌ Cannot connect to backend API at {API_BASE_URL}. Please ensure the backend server is running."
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out. The server took too long to respond."
    except requests.exceptions.RequestException as e:
        return None, f"❌ Error connecting to API: {str(e)}"
    except Exception as e:
        return None, f"❌ Unexpected error: {str(e)}"


def main():
    """Main Streamlit application"""
    
    # Title and header
    st.title("🤖 AWS Bedrock Chat Application")
    st.markdown("Chat with AWS Bedrock models powered by Claude")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model settings - values and limits from backend config
        config = st.session_state.backend_config
        
        # Initialize session state values from backend config if not already set
        if "temperature" not in st.session_state:
            st.session_state.temperature = config["default_temperature"]
        if "max_tokens" not in st.session_state:
            st.session_state.max_tokens = config["default_max_tokens"]
        if "use_streaming" not in st.session_state:
            st.session_state.use_streaming = False
        
        st.subheader("Model Settings")
        
        # Display model ID from backend .env
        if "model_id" in config:
            st.info(f"**Model:** {config['model_id']}")
        
        temperature = st.slider(
            "Temperature",
            min_value=config["temperature_min"],
            max_value=config["temperature_max"],
            value=st.session_state.temperature,
            step=0.01,
            format="%.2f",
            help="Controls randomness in responses. Lower = more focused, Higher = more creative"
        )
        st.session_state.temperature = temperature
        
        # Checkbox to limit max tokens to 1000 (render first to get current state)
        limit_max_tokens = st.checkbox(
            "Limit Max Tokens to 1000",
            value=st.session_state.get("limit_max_tokens", False),
            help="When enabled, limits the max tokens slider to a maximum of 1000"
        )
        st.session_state.limit_max_tokens = limit_max_tokens
        
        # Determine max value for slider based on checkbox
        max_tokens_slider_max = 1000 if limit_max_tokens else config["max_tokens_max"]
        
        # If checkbox is enabled and current value exceeds 1000, reset to 1000
        if limit_max_tokens and st.session_state.max_tokens > 1000:
            st.session_state.max_tokens = 1000
        
        # Calculate appropriate step size for max_tokens based on range
        max_tokens_range = max_tokens_slider_max - config["max_tokens_min"]
        if max_tokens_range > 10000:
            step_size = 500
        elif max_tokens_range > 1000:
            step_size = 100
        else:
            step_size = 10
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=config["max_tokens_min"],
            max_value=max_tokens_slider_max,
            value=st.session_state.max_tokens,
            step=step_size,
            help=f"Maximum number of tokens in the response (range: {config['max_tokens_min']:,} - {max_tokens_slider_max:,})"
        )
        st.session_state.max_tokens = max_tokens
        
        # Streaming option
        use_streaming = st.checkbox(
            "Enable Streaming",
            value=st.session_state.get("use_streaming", False),
            help="Use streaming endpoint for real-time response (if implemented)"
        )
        st.session_state.use_streaming = use_streaming
        
        st.divider()
        
        # API settings
        st.subheader("API Settings")
        api_url = st.text_input(
            "API URL",
            value=API_BASE_URL,
            help="Base URL for the FastAPI backend"
        )
        
        # Test connection button
        if st.button("Test API Connection"):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ API connection successful!")
                else:
                    st.error(f"❌ API returned status code: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to API: {str(e)}")
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]
            is_error = message.get("is_error", False)
            
            with st.chat_message(role):
                if is_error:
                    st.error(content)
                else:
                    st.markdown(content)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                assistant_response, error_message = send_message_to_api(
                    user_input, 
                    use_streaming=st.session_state.get("use_streaming", False)
                )
                
                if error_message:
                    # Display error message and add to conversation history
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "is_error": True
                    })
                elif assistant_response:
                    st.markdown(assistant_response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "is_error": False
                    })
                else:
                    error_msg = "❌ Failed to get response from the API"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "is_error": True
                    })
        
        # Rerun to update the display
        st.rerun()


if __name__ == "__main__":
    main()