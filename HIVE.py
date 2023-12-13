import streamlit as st
import streamlit.components.v1 as components
from pymongo.mongo_client import MongoClient
from streamlit_extras.switch_page_button import switch_page
from streamlit.source_util import _on_pages_changed, get_pages
from pathlib import Path
import json
import requests
# from streamlit.server.server import Server

DEFAULT_PAGE = "HIVE.py"
SECOND_PAGE_NAME = "About"

API_BASE_URL = "http://localhost:5000/api"

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
    # Remove all but the login page
    for key, val in list(current_pages.items()):
        if val["page_name"] != DEFAULT_PAGE.replace(".py", ""):
            del current_pages[key]
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
# Callback to handle successful login
def set_access_token_in_local_storage(access_token):
    components.html(
        f"""
        <script>
        localStorage.setItem('access_token', '{access_token}');
        </script>
        """,
        height=0,
        width=0
    )   
 
# Login form
def login():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        response = requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:    
            data = response.json()  
            access_token = data.get("access_token")
            st.session_state['access_token'] = access_token
            set_access_token_in_local_storage(access_token)
            show_all_pages()  # Gọi tất cả các trang
            hide_page(DEFAULT_PAGE.replace(".py", ""))  # Ẩn trang đầu tiên
            switch_page(SECOND_PAGE_NAME)  # Chuyển đến trang thứ hai 
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

def clear_access_token_from_local_storage():
    # Tạo mã JavaScript để xóa access_token khỏi localStorage
    js_code = """
    <script>
    localStorage.removeItem('access_token');
    window.location.reload();  // Tùy chọn: reload trang sau khi logout
    </script>
    """
    # Gửi mã JavaScript này đến trình duyệt thông qua Streamlit Component
    components.html(js_code, height=0, width=0)

def logout():
    clear_access_token_from_local_storage()  # Xóa access token khỏi localStorage
    clear_all_but_first_page()  # Hiển thị chỉ trang đăng nhập
 
# Run the Streamlit app
def main():
    # Hiển thị biểu mẫu đăng nhập hoặc đăng ký nếu chưa đăng nhập
        form_choice = st.selectbox("Select an option:", ("Login", "Sign Up"))
        if form_choice == "Login":
            login()
        elif form_choice == "Sign Up":
            signup()
# Execute the main app
if __name__ == '__main__':
    main()
