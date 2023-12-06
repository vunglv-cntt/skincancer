from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity
from pymongo import MongoClient
import secrets

secret_key = secrets.token_hex(32)
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
# Kết nối đến MongoDB
client = MongoClient("mongodb+srv://levanvung113:vungle2001@hive-cluser.zw2amvy.mongodb.net/?retryWrites=true&w=majority")
db = client["user_name"]
users_collection = db["hive"]

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

if __name__ == '__main__':
    app.run(debug=True)
