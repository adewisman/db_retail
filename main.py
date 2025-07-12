
import streamlit as st
from passlib.context import CryptContext
import base64
import os
from streamlit_option_menu import option_menu

# Set page configuration at the very top
st.set_page_config(page_title="Login", layout="wide", initial_sidebar_state="expanded")

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

# Initialize session state if not already done
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False
if "selected_option" not in st.session_state:
    st.session_state.selected_option = "Sales Overview"
if "theme" not in st.session_state:
    st.session_state.theme = "light"

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
    # If authenticated, show the main app with vertical tab navigation in the sidebar
    # This requires installing a new dependency: pip install streamlit-option-menu
    with st.sidebar:
        st.image("static/logo.png", width=100)
        st.success(f"Logged in as **{st.secrets.get('USERNAME', 'user')}**.")

        options = ["Penjualan By Tipe Motor", "Inventory", "Customer Analytics"]
        try:
            # Set the default index to the last selected option
            default_idx = options.index(st.session_state.selected_option)
        except ValueError:
            default_idx = 0

        selected = option_menu(
            menu_title="Main Menu",  # required
            options=options,
            icons=["graph-up-arrow", "box-seam", "people"],  # optional
            menu_icon="cast",  # optional
            default_index=default_idx,
        )
        # Persist the selection in session state
        st.session_state.selected_option = selected

        st.button(
            "Logout",
            on_click=lambda: st.session_state.update(authentication_status=False),
            use_container_width=True,
        )

        # Add theme selector
        theme = st.selectbox("Choose a theme", ["light", "dark"], index=0 if st.session_state.theme == "light" else 1)
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()

    # Apply the selected theme
    st._config.set_option("theme.base", st.session_state.theme)


    # Display content based on selection
    if selected == "Penjualan By Tipe Motor":
        #st.title(f"Viewing: {selected}")
        #st.info("This is where the main sales overview dashboard would be displayed.")
        # Embed the content of 1_Profile_Penjualan_By_Tipe_Motor.py here
        exec(open("pages/1_Profile_Penjualan_By_Tipe_Motor.py").read())

    elif selected == "Inventory":
        st.title(f"Viewing: {selected}")
        st.info("This is where you would manage product inventory.")
        # Add your inventory management components here
        st.table({"Item": ["Laptops", "Monitors", "Keyboards"], "Stock": [50, 75, 200]})

    elif selected == "Customer Analytics":
        st.title(f"Viewing: {selected}")
        st.info("This is where customer analytics and reports would be shown.")
        # Add your customer analytics components here
        st.bar_chart({"data": [10, 20, 5, 15]})
