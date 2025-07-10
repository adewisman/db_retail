
import streamlit as st
from passlib.context import CryptContext

def main():
    """
    A simple script to hash a password and print it to the console.
    This should be run once locally to generate the hash for your secrets file.
    """
    st.title("Password Hasher")

    st.warning(
        "This tool is for generating a password hash for your secrets file. "
        "Do not run this in a public or untrusted environment."
    )

    password = st.text_input("Enter the password to hash:", type="password")

    if st.button("Generate Hash"):
        if password:
            try:
                # It's crucial that the CryptContext settings here match the ones
                # used in your main application for verification.
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                hashed_password = pwd_context.hash(password)
                st.success("Password hashed successfully!")
                st.code(hashed_password, language="")
                st.info("Copy this hash and paste it into your .streamlit/secrets.toml file as the PASSWORD_HASH value.")
            except Exception as e:
                st.error(f"An error occurred during hashing: {e}")
        else:
            st.error("Please enter a password.")

if __name__ == "__main__":
    main()
