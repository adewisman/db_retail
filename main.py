
import streamlit as st
from passlib.context import CryptContext

# Set page configuration at the very top
st.set_page_config(page_title="Login", layout="centered")

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
    """Displays the login form."""
    st.title("Retail Daya App")
    st.write("Please log in to continue.")

    with st.form("login_form"):
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        submitted = st.form_submit_button("Login")

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
    login_form()
else:
    # If authenticated, show the main app content
    st.title("Welcome to the Retail Daya App!")
    st.success(f"You are logged in as **{st.secrets.get('USERNAME', 'user')}**.")
    st.info("Select a profile from the sidebar to view the analytics.")

    if st.button("Logout"):
        st.session_state["authentication_status"] = False
        st.rerun()
