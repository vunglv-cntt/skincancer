from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, unset_jwt_cookies
from pymongo import MongoClient
import secrets
from PIL import Image
import tensorflow as tf
import io

secret_key = secrets.token_hex(32)
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
bcrypt = Bcrypt(app)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_IDENTITY_CLAIM'] = 'sub'
jwt = JWTManager(app)
# Kết nối đến MongoDB
client = MongoClient("mongodb+srv://levanvung113:vungle2001@hive-cluser.zw2amvy.mongodb.net/?retryWrites=true&w=majority")
db = client["user_name"]
users_collection = db["hive"]
predictions_collection = db["predictions"]
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users_collection.find_one({"username": username})

    if user and bcrypt.check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify({"idUser": user['idUser'],"status": " success" ,"user_name" :user['username'], "access_token": access_token, }),200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Kiểm tra xem username đã tồn tại hay chưa
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400

    # Kiểm tra xem email đã tồn tại hay chưa
    existing_email = users_collection.find_one({"email": email})
    if existing_email:
        return jsonify({"error": "Email already exists"}), 400

    # Nếu username và email không tồn tại, tiếp tục đăng ký
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    last_user = users_collection.find_one(sort=[("idUser", -1)])

    if last_user:
        last_id_user = last_user.get("idUser", 0)
    else:
        last_id_user = 0

    new_id_user = last_id_user + 1

    user_data = {
        "idUser": new_id_user,
        "username": username,
        "email": email,
        "password": hashed_password
    }

    users_collection.insert_one(user_data)
    return jsonify({"message": "Successfully registered!"})

@app.route('/api/get_user_info', methods=['GET'])
@jwt_required()
def get_user_info():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"username": current_user}, {"_id": 0, "password": 0})

    if user:
        # Trả về thông tin người dùng bao gồm user_name
        return jsonify({"user_name": user.get("username", "")}), 200
    else:
        return jsonify({"error": "User not found"}), 404
    
def load_model():
    model = tf.keras.models.load_model("../model/model.h5")
    return model
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

@app.route('/api/predict', methods=['POST'])
def predict():
    file = request.files['file']
    img = Image.open(io.BytesIO(file.read())).convert("RGB")
    img = img.resize((180, 180))
    img = tf.keras.preprocessing.image.img_to_array(img)
    img = tf.expand_dims(img, axis=0)

    model = load_model()  # Hàm load_model giống như trong ứng dụng Streamlit của bạn

    prediction = model.predict(img)
    prediction = tf.nn.softmax(prediction)

    score = tf.reduce_max(prediction)
    score = tf.round(score * 100, 2)

    prediction = tf.argmax(prediction, axis=1)
    prediction = prediction.numpy()
    prediction = prediction[0]

    return jsonify({'disease': labels[prediction].title(), 'confidence': f'{score:.2f}%'})
@app.route('/api/store', methods=['POST'])
def store():
    data = request.json

    last_record = predictions_collection.find_one(sort=[("id", -1)])
    if last_record:
        last_id = last_record.get("id", 0)
    else:
        last_id = 0

    new_id = last_id + 1
    data['id'] = new_id

    # Thêm dữ liệu mới vào MongoDB
    predictions_collection.insert_one(data)
    return {'status': 'Data stored successfully'}
# @app.route('/api/logout', methods=['POST'])
# @jwt_required()
# def api_logout():
#     resp = jsonify({"message": "Logout successful"})
#     unset_jwt_cookies(resp)
#     return resp, 200

if __name__ == '__main__':
    app.run(debug=True)
