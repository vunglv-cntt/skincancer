import streamlit as st
import requests
from Hive import logout
from datetime import datetime

st.title("Skin Cancer Detection")

# logout_button = st.sidebar.button("Logout")
# if logout_button:
#     logout()

pic = st.file_uploader(
    label="Upload a picture",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=False,
    help="Upload a picture of your skin to get a diagnosis",
)

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
                        'image': pic.name,
                        'disease': result['disease'],
                        'confidence': result['confidence'],
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'userid': 'userid'  
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