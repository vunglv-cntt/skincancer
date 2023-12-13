import streamlit as st
import requests
from datetime import datetime
import base64
import streamlit.components.v1 as components

 

st.title("Skin Cancer Detection")

# getInfo()
pic = st.file_uploader(
    label="Upload a picture",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=False,
    help="Upload a picture of your skin to get a diagnosis",
)
def set_access_token():
    # Kiểm tra xem 'access_token' đã có trong session_state chưa, nếu chưa, khởi tạo nó
    if 'access_token' not in st.session_state:
        st.session_state['access_token'] = None
    # Lấy access token từ query params nếu có
    access_token_param = st.experimental_get_query_params().get("access_token", [None])[0]
    if access_token_param:
        st.session_state['access_token'] = access_token_param
def get_access_token():
    # Sử dụng JavaScript nhúng để lấy access token từ local storage
    token_retrieval_script = """
        <script>
        const accessToken = localStorage.getItem('access_token');
        if (accessToken) {
            // Gửi accessToken trở lại máy chủ Streamlit thông qua postMessage
            window.parent.postMessage({type: 'streamlit:accessToken', accessToken: accessToken}, '*');
        }
        </script>
    """
    components.html(token_retrieval_script, height=0)

# Hàm này sẽ được gọi khi ứng dụng khởi động
get_access_token()
def on_message(message):
    if message['type'] == 'streamlit:accessToken':
        # Lưu trữ access_token vào session_state
        st.session_state['access_token'] = message['accessToken']

# Lắng nghe các message từ client-side
st.experimental_on_script_runner_event(on_message)
def get_user_info():
    # Sử dụng get() để tránh KeyError nếu 'access_token' không tồn tại
    access_token = st.session_state.get('access_token')
    if access_token:
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get('http://localhost:5000/api/get_user_info', headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                return user_info.get('user_name', '')
            else:
                st.warning("Không thể lấy thông tin người dùng.")
                return ''
        except Exception as e:
            st.error(f"Có lỗi xảy ra khi gọi API: {e}")
            return ''
    else:
        st.error("Không tìm thấy access token. Vui lòng đăng nhập lại.")
        return ''
user_name = get_user_info()
if st.button("Predict") and pic is not None:
    st.header("Results")
    
    cols = st.columns([1, 2])
    with cols[0]:
        st.image(pic, caption=pic.name, use_column_width=True)


    with cols[1]:
        with st.spinner("Đang dự đoán..."):
            try:
                # Gửi ảnh đến API AI
                response = requests.post('http://localhost:5000/api/predict', files={'file': pic.read()})


                # Kiểm tra mã trạng thái HTTP
                if response.status_code == 200:
                    result = response.json()
                    st.write(f"**Dự đoán:** `{result['disease']}`")
                    st.write(f"**Độ tin cậy:** `{result['confidence']}`")

                    
                     # Gửi dữ liệu đến API MongoDB
                    data = {
                        'image': base64.b64encode(pic.read()).decode("utf-8"),
                        'disease': result['disease'],
                        'confidence': result['confidence'],
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'username': user_name
                    }
                    requests.post('http://localhost:5000/api/store', json=data)

                else:
                    st.error(f"Lỗi: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {e}")

            finally:
                st.warning(
                    ":warning: Đây không phải là chẩn đoán y khoa. Vui lòng tham khảo ý kiến của bác sĩ cho chẩn đoán chuyên nghiệp."
                )