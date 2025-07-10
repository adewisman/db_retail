
import streamlit as st
from passlib.context import CryptContext
import base64
import os

# Set page configuration at the very top
st.set_page_config(page_title="Login", layout="wide")

def set_bg_from_local(image_file):
    """
    Sets a local image as the background of the Streamlit app.
    Also adds custom CSS for the login form.
    """
    if not os.path.exists(image_file):
        st.error(f"Background image not found at {image_file}")
        return
    with open(image_file, "rb") as f:
        data = f.read()
    encoded_string = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
        }}
        div[data-testid="stForm"] {{
            background-color: rgba(255, 255, 255, 0.8);
            padding: 2rem;
            border-radius: 0.5rem;
        }}
        h1 {{
            color: white;
            text-shadow: 2px 2px 4px #000000;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
# Initialize CryptContext
# This must match the settings in hash_password.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def check_credentials():
    """
    Checks if the entered username and password match the secrets.
    Returns True if authenticated, False otherwise.
    """
    try:
        stored_username = st.secrets["USERNAME"]
        stored_password_hash = st.secrets["PASSWORD_HASH"]
    except KeyError:
        st.error("Username or password hash not found in secrets. Please set them.")
        return False

    # Check if the username from the session state matches the stored username
    if st.session_state["username"] != stored_username:
        return False

    # Verify the password from the session state against the stored hash
    return pwd_context.verify(st.session_state["password"], stored_password_hash)

def login_form():
    """Displays the login form on the right side of the page."""
    _, col2 = st.columns([2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### Login")
            username = st.text_input(
                "Username",
                key="username",
                placeholder="Username",
                label_visibility="collapsed",
            )
            password = st.text_input(
                "Password",
                type="password",
                key="password",
                placeholder="Password",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if check_credentials():
                    st.session_state["authentication_status"] = True
                    st.rerun()  # Rerun the script to reflect the login state
                else:
                    st.session_state["authentication_status"] = False
                    st.error("Incorrect username or password.")

# --- Main Application Logic ---

# Initialize session state if not already done
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False

# If not authenticated, show the login form
if not st.session_state["authentication_status"]:
    set_bg_from_local(os.path.join(".streamlit", "bg-login.jpg"))
    st.title("Retail Daya App")
    login_form()
else:
    # If authenticated, show the main app content
    st.title("Welcome to the Retail Daya App!")
    st.success(f"You are logged in as **{st.secrets.get('USERNAME', 'user')}**.")
    st.info("Select a profile from the sidebar to view the analytics.")

    if st.button("Logout"):
        st.session_state["authentication_status"] = False
        st.rerun()
