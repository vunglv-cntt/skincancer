import streamlit as st
import requests
from datetime import datetime
import base64
import json
import streamlit.components.v1 as components
from streamlit_local_storage import LocalStorage
st.title("Skin Cancer Detection")
# Tạo một đối tượng LocalStorage
local_storage = LocalStorage()

all_values = local_storage.getAll()
if all_values is not None:
    access_token_value = all_values["access_token"]
else:
    st.warning("Không tìm thấy Access Token trong local storage.")
pic = st.file_uploader(
    label="Upload a picture",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=False,
    help="Upload a picture of your skin to get a diagnosis",
)
# print(access_token_value,"!212")
def get_user_info(access_token_value):
        # print(access_token_value,"____")
        headers = {'Authorization': f'Bearer {access_token_value}'}
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

user_name = get_user_info(access_token_value)
if st.button("Predict") and pic is not None:
    st.header("Results")
    cols = st.columns([1, 2])
    with cols[0]:
        st.image(pic, caption=pic.name, use_column_width=True)
    with cols[1]:
        with st.spinner("Đang dự đoán..."):
            try:
                # Gửi ảnh đến API AI
                pic_data = pic.read()
                response = requests.post('http://localhost:5000/api/predict', files={'file': pic.read()})
                # Kiểm tra mã trạng thái HTTP
                if response.status_code == 200:
                    result = response.json()
                    st.write(f"**Dự đoán:** `{result['disease']}`")
                    st.write(f"**Độ tin cậy:** `{result['confidence']}`")
                    
                     # Gửi dữ liệu đến API MongoDB
                    data = {
                        'image': base64.b64encode(pic_data).decode("utf-8"),
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