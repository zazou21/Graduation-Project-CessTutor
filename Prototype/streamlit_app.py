'''
This is the main Streamlit application for CessTutor. It handles user
authentication, chat interface, and integrates with Firebase for backend services.
'''
import streamlit as st
from firebase_init import (
    init_firebase, create_user, login_user, create_user_profile,
    get_user_profile, save_conversation, get_user_conversations,
    get_conversation, update_conversation, delete_conversation
)
from datetime import datetime

# Page config
st.set_page_config(
    page_title="CessTutor - AI Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Minimal styling
st.markdown("""
<style>
    /* Message containers */
    .user-message {
        display: flex;
        justify-content: flex-end;
        margin: 12px 0;
    }
    
    .user-message-content {
        background-color: #d0d0d0;
        color: #000;
        padding: 12px 16px;
        border-radius: 12px;
        max-width: 70%;
        word-wrap: break-word;
    }
    
    .bot-message {
        display: flex;
        justify-content: flex-start;
        margin: 12px 0;
    }
    
    .bot-message-content {
        background-color: #f0f0f0;
        color: #000;
        padding: 12px 16px;
        border-radius: 12px;
        max-width: 70%;
        word-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
db = init_firebase()

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False


def login_page():
    """Display login/register page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("")
        st.markdown("")
        st.markdown("# 💬 CessTutor")
        st.markdown("*Your AI Learning Assistant*")
        st.markdown("---")
        
        # Toggle between login and register
        auth_mode = st.radio("", ["Login", "Register"], horizontal=True)
        
        st.markdown("###")
        
        if auth_mode == "Login":
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password", placeholder="••••••")
                st.markdown("")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        result = login_user(email, password)
                        if result["success"]:
                            user_profile = get_user_profile(result["uid"])
                            if user_profile["success"]:
                                st.session_state.user_id = result["uid"]
                                st.session_state.user_email = email
                                st.session_state.user_name = user_profile["data"]["username"]
                                st.success("Login successful!")
                                st.rerun()
                        else:
                            st.error(result["message"])
        
        else:  # Register
            with st.form("register_form"):
                display_name = st.text_input("Display Name", placeholder="Your name")
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password", placeholder="••••••")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••")
                st.markdown("")
                submit = st.form_submit_button("Create Account", use_container_width=True)
                
                if submit:
                    if not display_name or not email or not password or not confirm_password:
                        st.error("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        # Create user in Firebase Auth
                        auth_result = create_user(email, password)
                        if auth_result["success"]:
                            # Create user profile in Firestore
                            profile_result = create_user_profile(auth_result["uid"], email, display_name)
                            if profile_result["success"]:
                                # Automatically log in the user
                                st.session_state.user_id = auth_result["uid"]
                                st.session_state.user_email = email
                                st.session_state.user_name = display_name
                                st.success("Account created successfully!")
                                st.rerun()
                            else:
                                st.error(f"Profile creation failed: {profile_result['message']}")
                        else:
                            st.error(auth_result["message"])


def chat_page():
    """Display main chat interface"""
    
    # Sidebar with conversations
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.markdown("---")
        
        # New Chat button
        if st.button("+ New Chat", use_container_width=True):
            st.session_state.current_conversation = None
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("###")
        st.markdown("**Previous Chats**")
        st.markdown("")
        
        # Get user conversations
        conv_result = get_user_conversations(st.session_state.user_id)
        if conv_result["success"]:
            if conv_result["data"] and len(conv_result["data"]) > 0:
                for conv in conv_result["data"]:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(conv["title"], use_container_width=True, key=f"conv_{conv['conv_id']}"):
                            st.session_state.current_conversation = conv["conv_id"]
                            st.session_state.messages = conv["messages"]
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{conv['conv_id']}"):
                            delete_conversation(conv["conv_id"])
                            st.rerun()
            else:
                st.markdown("*No previous chats yet*")
        else:
            st.markdown(f"*Error loading chats*")
        
        st.markdown("---")
        st.markdown("")
        
        # Upload button
        if st.button("➕ Upload File", use_container_width=True):
            st.session_state.show_uploader = not st.session_state.get("show_uploader", False)
        
        st.markdown("")
        
        # Logout button
        if st.button("Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.session_state.current_conversation = None
            st.session_state.messages = []
            st.rerun()
    
    # Main chat area
    st.markdown("# 💬 CessTutor")
    st.markdown("---")
    
    # Display messages with scrolling
    if st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="user-message"><div class="user-message-content">{msg["content"]}</div></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="bot-message"><div class="bot-message-content">{msg["content"]}</div></div>',
                    unsafe_allow_html=True
                )
    else:
        st.markdown("<p style='text-align: center; color: #888; margin-top: 80px; font-size: 16px;'>Start a conversation...</p>", unsafe_allow_html=True)
    
    # Spacer to push input to bottom
    st.markdown("")
    st.markdown("")
    
    # Show file uploader if toggled in sidebar
    if st.session_state.get("show_uploader", False):
        uploaded_file = st.file_uploader(
            "Upload file",
            type=["pdf", "txt", "doc", "docx"],
            label_visibility="collapsed",
            key="file_upload"
        )
        if uploaded_file:
            st.success(f"📄 {uploaded_file.name} uploaded")
    else:
        uploaded_file = None
    
    # Chat input (Enter key to send)
    user_input = st.chat_input("Type your message...")
    
    # Handle message send (Enter key automatically submits with chat_input)
    if user_input:
        # Add user message to session
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # TODO: Add RAG + LLM response here
        # For now, just add a placeholder response
        bot_response = "This is a placeholder response. RAG integration coming soon!"
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        # Save or update conversation
        if st.session_state.current_conversation:
            # Update existing conversation
            update_conversation(st.session_state.current_conversation, st.session_state.messages)
        else:
            # Create new conversation
            conv_title = user_input[:50] + "..." if len(user_input) > 50 else user_input
            save_result = save_conversation(st.session_state.user_id, conv_title, st.session_state.messages)
            if save_result["success"]:
                st.session_state.current_conversation = save_result["conv_id"]
        
        st.rerun()


# Main app logic
if st.session_state.user_id:
    chat_page()
else:
    login_page()