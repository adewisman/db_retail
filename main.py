
import streamlit as st
from passlib.context import CryptContext
import base64
import os
import re
from streamlit_option_menu import option_menu

# Set page configuration at the very top
st.set_page_config(page_title="DB Daya Retail", layout="wide", page_icon="static/logo-icons.jpg", initial_sidebar_state="expanded")

# This will prevent Streamlit from trying to create a sidebar navigation
# if you have a `pages/` directory. We are using our own navigation logic.
st.set_option("client.showSidebarNavigation", False)

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(image_filename):
    """
    Sets a background image for the Streamlit app from the static folder.
    Also adds custom CSS for the login form.
    """
    image_path = os.path.join("static", image_filename)
    if not os.path.exists(image_path):
        st.error(f"Background image not found at {image_path}")
        return

    image_base64 = get_base64_of_bin_file(image_path)
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{image_base64}");
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

def get_page_config():
    """
    Scans the 'pages' directory to build a nested dictionary of available pages.
    The structure is { 'Category': { 'PageName': 'path/to/page.py' } }.
    """
    page_config = {}
    pages_dir = "pages"
    if not os.path.exists(pages_dir):
        return page_config

    for category in sorted(os.listdir(pages_dir)):
        category_path = os.path.join(pages_dir, category)
        if os.path.isdir(category_path):
            page_config[category] = {}
            for page_file in sorted(os.listdir(category_path)):
                if page_file.endswith(".py") and not page_file.startswith("_"):
                    page_name = os.path.splitext(page_file)[0]
                    # Remove leading numbers/underscores, replace underscores with spaces
                    page_name = re.sub(r"^\d+_", "", page_name).replace("_", " ")
                    page_config[category][page_name] = os.path.join(category_path, page_file)
    return page_config

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
            st.image("static/logo.png", width=150)
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

# Initialize session state
if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = False
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "selected_page" not in st.session_state:
    st.session_state.selected_page = None
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Apply the selected theme
st._config.set_option("theme.base", st.session_state.theme)


# If not authenticated, show the login form
if not st.session_state["authentication_status"]:
    set_background("bg-login.jpg")
    #st.title("Dashbord Retail")
    login_form()

    # Hide the main menu and sidebar for the login page
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] { display: none }
            section[data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)
else:
    # --- Dynamic Page Loading ---
    page_config = get_page_config()
    
    if not page_config:
        st.warning("No pages found. Please add pages to the 'pages' directory.")
        st.stop()

    # --- Sidebar Navigation ---
    with st.sidebar:
        st.image("static/logo.png", width=100)
        st.success(f"Logged in as **{st.secrets.get('USERNAME', 'user')}**.")
        st.markdown("---")

        # Custom CSS for menu font sizes
        st.markdown("""
            <style>
                [data-testid="stExpander"] summary {
                    font-size: 18px !important;
                    font-weight: bold !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # Set default category and page if not set
        if st.session_state.selected_category is None:
            st.session_state.selected_category = list(page_config.keys())[0]
        
        # Check if the selected page is valid for the selected category
        if st.session_state.selected_page is None or st.session_state.selected_page not in page_config[st.session_state.selected_category]:
            st.session_state.selected_page = list(page_config[st.session_state.selected_category].keys())[0]

        for category, pages in page_config.items():
            if not pages:
                with st.expander(category, expanded=False):
                    st.info("No pages in this category.")
                continue

            with st.expander(category, expanded=(st.session_state.selected_category == category)):
                # Determine the default index for the option_menu
                if st.session_state.selected_category == category:
                    try:
                        default_index = list(pages.keys()).index(st.session_state.selected_page)
                    except ValueError:
                        default_index = 0
                else:
                    default_index = 0
                
                selected = option_menu(
                    None,
                    options=list(pages.keys()),
                    icons=["file-earmark-text" for _ in pages.keys()],
                    default_index=default_index,
                    key=f"menu_{category}",
                    styles={
                        "nav-link": {"font-size": "14px"}
                    }
                )

                # If the selection has changed, update the state and rerun
                if selected != st.session_state.selected_page or st.session_state.selected_category != category:
                    st.session_state.selected_category = category
                    st.session_state.selected_page = selected
                    st.rerun()

        # Logout and theme selector
        st.markdown("---")
        st.button("Logout", on_click=lambda: st.session_state.update(authentication_status=False), use_container_width=True)
        theme = st.selectbox("Choose a theme", ["light", "dark"], index=0 if st.session_state.theme == "light" else 1)
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()

    # --- Load and Display Page ---
    if st.session_state.selected_category and st.session_state.selected_page:
        page_path = page_config[st.session_state.selected_category][st.session_state.selected_page]
        try:
            with open(page_path, "r") as f:
                exec(f.read(), globals())
        except Exception as e:
            st.error(f"Error loading page: {e}")
    else:
        st.info("Please select a page to continue.")
