# import streamlit as st
# from pymongo import MongoClient
# from PIL import Image
# import io
# from streamlit_extras.switch_page_button import switch_page
# from dotenv import load_dotenv
# import os


# load_dotenv()

# uri = os.getenv("API_KEY")
# # Connect to MongoDB
# client = MongoClient(uri)
# db = client["Donate_app"]
# users_collection = db["donations"]

# # Define a function to create a donor template
# def donor_template(data):
#     template = """
#     *Name:* {}
#     *Item:* {}
#     *Distance from Current Location:* {} km
#     *Contact:* {}
#     """.format(data["name"], data["item"], data["location"], data["contact"])
    
#     return template

# # Title and distance filter
# st.title("Donors Gallery")

# def main():
#     # Set the page layout to center the buttons
#     with open('style.css') as f:
#             st.markdown('<style>(f.read())</style>', unsafe_allow_html=True)

#     # Add the donate button
#     if st.button("Donate an Item", key="donate_button"):
#         # Add your donate button logic here
#         switch_page("Donate an item")

#     # Add some space between the buttons
#     st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)

#     # Add the receive button
#     if st.button("Receive an Item", key="receive_button"):
#         # Add your receive button logic here
#         switch_page("Search an item")

#     # Close the container div
#     st.markdown('</div>', unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()


# # for data in donors_within_distance:
# #     st.write("Donor Details:")
# #     donor_info = donor_template(data)
# #     st.markdown(donor_info)
    
# #     st.write("Donor Images:")
# #     for photo_data in data["photos"]:
# #         st.image(Image.open(io.BytesIO(photo_data)), use_column_width=True)
    
# #     st.write("-" * 50)  # Add a separator line between entries
import requests
import streamlit as st
from streamlit_lottie import st_lottie


def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


st.set_page_config(
    page_title="Skin Cancer",
    page_icon="♋",
    layout="wide",
    initial_sidebar_state="expanded",
)

lottie_health = load_lottieurl(
    "https://assets2.lottiefiles.com/packages/lf20_5njp3vgg.json"
)
lottie_welcome = load_lottieurl(
    "https://assets1.lottiefiles.com/packages/lf20_puciaact.json"
)
lottie_healthy = load_lottieurl(
    "https://assets10.lottiefiles.com/packages/lf20_x1gjdldd.json"
)

st.title("Welcome to team Diagnose!")
st_lottie(lottie_welcome, height=300, key="welcome")
# st.header("Melanoma detection at your skin images.")


with st.container():
    st.write("---")
    left_column, right_column = st.columns(2)
    with left_column:
        st.write("##")
        st.write(
            """
            Melanoma is a type of cancer that can be deadly if not detected early. It accounts for 75% of skin cancer deaths. A solution which can evaluate images and alert the dermatologists about the presence of melanoma has the potential to
            reduce a lot of manual effort needed in diagnosis.

            Our application detects the following diseases:
            * Actinic keratosis,
            * Basal cell carcinoma,
            * Dermatofibroma,
            * Melanoma,
            * Nevus,
            * Pigmented benign keratosis,
            * Seborrheic keratosis,
            * Squamous cell carcinoma,
            * Vascular lesion.
            """
        )
        st.write("##")
        st.write(
            "[Learn More >](https://www.researchgate.net/publication/356093241_Characteristics_of_publicly_available_skin_cancer_image_datasets_a_systematic_review)"
        )
    with right_column:
        st_lottie(lottie_health, height=500, key="check")

with st.container():
    st.write("---")
    cols = st.columns(2)
    with cols[0]:
        st.header("How it works?")
        """
        Our application utilizes machine learning to predict what skin disease you may have, from just your skin images!
        We then recommend you specialized doctors based on your type of disease, if our model predicts you're healthy we'll suggest you a general doctor.
        ##
        [Learn More >](https://youtu.be/sFIXmJn3vGk)
        """
    with cols[1]:
        st_lottie(lottie_healthy, height=300, key="healthy")
