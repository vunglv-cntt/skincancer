from PIL import Image
import streamlit as st
import tensorflow as tf
from Hive import logout

# Initialize session state
if 'prediction_done' not in st.session_state:
    st.session_state.prediction_done = False

@st.cache_resource
def load_model():
    model = tf.keras.models.load_model("./model/model.h5")
    return model

st.title("Skin Cancer Detection")
logout_button = st.sidebar.button("Logout")
if logout_button:
    logout()

pic = st.file_uploader(
    label="Upload a picture",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=False,
    help="Upload a picture of your skin to get a diagnosis",
)

if st.button("Predict") and pic is not None:
    st.session_state.prediction_done = True  # Đánh dấu là đã thực hiện dự đoán
    st.header("Results")

    cols = st.columns([1, 2])
    with cols[0]:
        st.session_state.image = pic
        st.image(st.session_state.image, caption=pic.name, use_column_width=True)

    with cols[1]:
        labels = [
            "actinic keratosis",
            "basal cell carcinoma",
            "dermatofibroma",
            "melanoma",
            "nevus",
            "pigmented benign keratosis",
            "seborrheic keratosis",
            "squamous cell carcinoma",
            "vascular lesion",
        ]
        st.session_state.disease = labels
        model = load_model()

        with st.spinner("Predicting..."):
            img = Image.open(pic).convert("RGB")
            img = img.resize((180, 180))
            img = tf.keras.preprocessing.image.img_to_array(img)
            img = tf.expand_dims(img, axis=0)

            prediction = model.predict(img)
            prediction = tf.nn.softmax(prediction)

            st.session_state.score = tf.reduce_max(prediction)
            st.session_state.score = tf.round(st.session_state.score * 100, 2)

            prediction = tf.argmax(prediction, axis=1)
            prediction = prediction.numpy()
            prediction = prediction[0]

            st.session_state.disease = labels[prediction].title()
            st.write(f"**Prediction:** `{st.session_state.disease}`")
            st.write(f"**Confidence:** `{st.session_state.score:.2f}%`")

            st.warning(
                ":warning: This is not a medical diagnosis. Please consult a doctor for a professional diagnosis."
            )

# Display message if prediction is done
if st.session_state.prediction_done:
    message = st.text_area("Message", height=100)
    st.text(message)
