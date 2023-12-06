import streamlit as st

import bcrypt
from pymongo.mongo_client import MongoClient
from streamlit_extras.switch_page_button import switch_page
from streamlit.source_util import _on_pages_changed, get_pages
from pathlib import Path
import json
import requests


DEFAULT_PAGE = "Hive.py"
SECOND_PAGE_NAME = "About"
is_logged_in = False
API_BASE_URL = "http://localhost:5000/api"
ACCESS_TOKEN_KEY = "access_token"
# all pages request
def get_all_pages():
    default_pages = get_pages(DEFAULT_PAGE)
    pages_path = Path("pages.json")

    if pages_path.exists():
        saved_default_pages = json.loads(pages_path.read_text())
        current_pages = get_pages(DEFAULT_PAGE)
        current_pages.update(saved_default_pages)
        _on_pages_changed.send()
    else:
        saved_default_pages = default_pages.copy()
        pages_path.write_text(json.dumps(default_pages, indent=5))

    return saved_default_pages

# clear all page but not login page
def clear_all_but_first_page():
    current_pages = get_pages(DEFAULT_PAGE)
    if len(current_pages.keys()) == 1:
        return

    get_all_pages()

    # Remove all but the first page
    key, val = list(current_pages.items())[0]
    current_pages.clear()
    current_pages[key] = val

    _on_pages_changed.send()

# show all pages
def show_all_pages():
    current_pages = get_pages(DEFAULT_PAGE)

    saved_pages = get_all_pages()

    # Replace all the missing pages
    for key in saved_pages:
        if key not in current_pages:
            current_pages[key] = saved_pages[key]

    _on_pages_changed.send()

# Hide default page
def hide_page(name: str):
    current_pages = get_pages(DEFAULT_PAGE)
    for key, val in current_pages.items():
        if val["page_name"] == name:
            del current_pages[key]
            _on_pages_changed.send()
            break

# calling only default(login) page
clear_all_but_first_page()

st.image('HIVE.png', use_column_width=True)
st.title("Welcome to Hive")

uri = "mongodb+srv://levanvung113:vungle2001@hive-cluser.zw2amvy.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["user_name"]
users_collection = db["hive"]

# Callback to handle successful login
def handle_successful_login(username):
    show_all_pages()  # call all pages
    hide_page(DEFAULT_PAGE.replace(".py", ""))  # hide first page
    switch_page(SECOND_PAGE_NAME)  # switch to second page
    
# Login form
def login():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        response = requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})

        if response.status_code == 200:
            data = response.json()
            handle_successful_login(username)
            print(data)
        else:
            st.error("Invalid username or password")
            clear_all_but_first_page()





# Sign-up form
def signup():
    st.header("Sign Up")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up"):
        response = requests.post(f"{API_BASE_URL}/signup", json={"username": username, "email": email, "password": password})

        if response.status_code == 200:
            st.success(response.json()["message"])
        elif response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get("error", "Đã xảy ra lỗi không xác định.")
            st.error(f"Lỗi đăng ký: {error_message}")
        else:
            st.error("Registration failed. Please try again.")

# Run the Streamlit app
def main():
    # Display the login or sign-up form based on user selection
    form_choice = st.selectbox("Select an option:", ("Login", "Sign Up"))
   
    if form_choice == "Login":
        login()
    elif form_choice == "Sign Up":
        signup()


# Execute the main app
if __name__ == '__main__':
    main()
