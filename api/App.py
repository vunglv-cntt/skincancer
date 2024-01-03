import datetime
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token,get_jwt_identity, jwt_required, unset_jwt_cookies
from pymongo import MongoClient
from bson import ObjectId
from PIL import Image
import tensorflow as tf
import io
from flask_cors import CORS
from datetime import timedelta
from dotenv import load_dotenv
import os
from utils import load_model
from werkzeug.utils import secure_filename
import boto3


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'D:/CODE/SKIN/skincancer/UPLOAD_FOLDER'
CORS(app)

# r2session = boto3.Session(region_name='us-east-1')
# # bucket_name="r2admin1234"
# s3client = r2session.client('s3')
# s3client.create_bucket(Bucket="vung-skin-cancer")

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_IDENTITY_CLAIM'] = 'sub'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)


app.config['S3_BUCKET'] = os.getenv('S3_BUCKET_NAME')
app.config['S3_KEY'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['S3_SECRET'] = os.getenv('AWS_SECRET_ACCESS_KEY')
app.config['S3_REGION'] = os.getenv('AWS_REGION')

s3client = boto3.client(
    's3',
    aws_access_key_id=app.config['S3_KEY'],
    aws_secret_access_key=app.config['S3_SECRET'],
    region_name=app.config['S3_REGION']
)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

client = MongoClient(os.getenv('MONGO_URI'))
db = client["skin_cancer"]
users_collection = db["User"]
predictions_collection = db["Predict"]
post_collection = db["Post"]

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = users_collection.find_one({"username": username})

    if user and bcrypt.check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        return jsonify({"idUser": user['idUser'],"status": " success" ,"user_name" :user['username'], "access_token": access_token,"refresh_token": refresh_token }),200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/api/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({'access_token': new_token})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400

    existing_email = users_collection.find_one({"email": email})
    if existing_email:
        return jsonify({"error": "Email already exists"}), 400

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
        return jsonify({"user_name": user.get("username", ""), "idUser": user.get("idUser", "")}), 200
    else:
        return jsonify({"error": "User not found"}), 404
    
labels = [
    "actinic keratosis",
    "basal cell carcinoma",
    "dermatofibroma",
    "error",
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

@app.route('/api/get_predictions_by_user_id', methods=['GET'])
@jwt_required()
def get_predictions_by_user_id():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"username": current_user}, {"_id": 0, "password": 0})

    if user:
        user_id = user.get("idUser")

        # Thêm tham số phân trang với giá trị mặc định
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        skip = (page - 1) * page_size

        # Lấy tổng số bản ghi để tính tổng số trang
        total_records = predictions_collection.count_documents({"userId": str(user_id)})
        total_pages = (total_records + page_size - 1) // page_size

        # Truy vấn dữ liệu được phân trang từ MongoDB
        predictions = predictions_collection.find(
            {"userId": str(user_id)}, {"_id": 0}
        ).sort("time", -1).skip(skip).limit(page_size)
        predictions_list = list(predictions)

        # Trả về dữ liệu cùng thông tin phân trang
        return jsonify({
            "data": predictions_list,
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size
        }), 200
    else:
        return jsonify({"error": "User not found"}), 404
    
@app.route('/api/delete_prediction/<int:prediction_id>', methods=['DELETE'])
@jwt_required()
def delete_prediction(prediction_id):
    current_user = get_jwt_identity()
    user = users_collection.find_one({"username": current_user})

    if user:
        # Tìm bản ghi dự đoán theo id
        prediction = predictions_collection.find_one({"id": prediction_id})
        if prediction and str(prediction.get("userId")) == str(user.get("idUser")):
            # Xóa bản ghi nếu người dùng có quyền
            predictions_collection.delete_one({"id": prediction_id})
            return jsonify({"message": "Prediction with id {} deleted successfully".format(prediction_id)}), 200
        else:
            # Nếu bản ghi không tồn tại hoặc người dùng không có quyền
            return jsonify({"error": "Prediction not found or access denied"}), 404
    else:
        # Nếu thông tin người dùng không tồn tại trong DB
        return jsonify({"error": "User not found"}), 404
    
@app.route('/api/get_prediction/<int:prediction_id>', methods=['GET'])
@jwt_required()
def get_prediction(prediction_id):
    current_user = get_jwt_identity()
    user = users_collection.find_one({"username": current_user})

    if user:
        # Truy vấn bản ghi dự đoán theo id
        prediction = predictions_collection.find_one({"id": prediction_id}, {"_id": 0})
        if prediction:
            # Kiểm tra người dùng có quyền xem bản ghi này không
            if str(prediction.get("userId")) == str(user.get("idUser")):
                return jsonify({"data":prediction}), 200
            else:
                # Truy cập bị từ chối nếu người dùng không có quyền
                return jsonify({"error": "Access denied"}), 403
        else:
            # Bản ghi không tồn tại
            return jsonify({"error": "Prediction not found"}), 404
    else:
        # Người dùng không tìm thấy trong cơ sở dữ liệu
        return jsonify({"error": "User not found"}), 404
    
@app.route('/api/search/predictions', methods=['GET'])
@jwt_required()
def get_predictions_by_disease():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"username": current_user})
    
    if user:
        # Lấy tham số truy vấn 'disease'
        disease_name = request.args.get('disease', type=str)
        # Lấy tham số phân trang 'page' và 'limit', đặt giá trị mặc định nếu không được cung cấp
        current_page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        # Tính toán chỉ số bắt đầu cho các bản ghi của trang hiện tại
        skip = (current_page - 1) * limit

        if disease_name:
            # Tính tổng số bản ghi
            total = predictions_collection.count_documents({"disease": disease_name})
            # Tìm và lấy các bản ghi với giới hạn và bỏ qua
            predictions = predictions_collection.find({"disease": disease_name}, {"_id": 0}).sort("time", -1).skip(skip).limit(limit)
            predictions_list = list(predictions)
            
            if predictions_list:
                # Tính tổng số trang
                total_pages = (total + limit - 1) // limit
                return jsonify({
                    "total_records": total,
                    "total_pages": total_pages,
                    "current_page": current_page,
                    "limit": limit,
                    "predictions": predictions_list
                }), 200
            else:
                return jsonify({"message": "No predictions found for the given disease"}), 404
        else:
            return jsonify({"error": "Disease parameter is required"}), 400
    else:
        return jsonify({"error": "User not found"}), 404
    

    
@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    current_user = get_jwt_identity()
    title = request.form.get('title')
    content = request.form.get('content')
    image = request.files.get('image')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    image_url = None
    if image:
        # Secure and generate filename
        filename = secure_filename(image.filename)
        # Generate the file path
        file_path = f"images/{filename}"

        # Upload the image to S3
        s3client.upload_fileobj(
            image,
            app.config['S3_BUCKET'],
            file_path,
            ExtraArgs={'ACL': 'public-read'}
        )

        image_url = f"https://{app.config['S3_BUCKET']}.s3.amazonaws.com/{file_path}"

    # Get the last_post_id and increment it
    last_post_id_doc = db["last_post_id"].find_one()
    if last_post_id_doc is None:
        last_post_id = 1
        db["last_post_id"].insert_one({"_id": "last_post_id", "value": last_post_id})
    else:
        last_post_id = last_post_id_doc["value"] + 1
        db["last_post_id"].update_one({"_id": "last_post_id"}, {"$set": {"value": last_post_id}})

    new_post = {
        "post_id": last_post_id,
        "title": title,
        "content": content,
        "image_url": image_url,
        "author": current_user,
        "comments": [],
        "reactions": [],
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }
    post_id = post_collection.insert_one(new_post).inserted_id

    # Convert ObjectId to string
    new_post['_id'] = str(post_id)

    return jsonify({"message": "Post created", "post": new_post}), 201

@app.route('/api/editPost', methods=['PUT'])
@jwt_required()
def update_post():
    post_id = request.args.get('post_id', type = int)
    if post_id is None:
        return jsonify({"error": "Missing post_id parameter"}), 400
    current_user = get_jwt_identity()
    title = request.form.get('title')
    content = request.form.get('content')
    image = request.files.get('image')

    post = post_collection.find_one({"post_id": post_id, "author": current_user})

    if not post:
        return jsonify({"error": "Post not found"}), 404

    update_data = {}

    if title:
        update_data['title'] = title
    if content:
        update_data['content'] = content
    if image:
        filename = secure_filename(image.filename)
        file_path = f"images/{filename}"
        s3client.upload_fileobj(
            image,
            app.config['S3_BUCKET'],
            file_path,
            ExtraArgs={'ACL': 'public-read'}
        )
        image_url = f"https://{app.config['S3_BUCKET']}.s3.amazonaws.com/{file_path}"
        update_data['image_url'] = image_url

    update_data['updated_at'] = datetime.datetime.utcnow()

    post_collection.update_one({"post_id": post_id, "author": current_user}, {"$set": update_data})

    return jsonify({"message": "Post updated"}), 200

@app.route('/api/deletePost', methods=['DELETE'])
@jwt_required()
def delete_post():
    post_id = request.args.get('post_id', type = int)
    if post_id is None:
        return jsonify({"error": "Missing post_id parameter"}), 400
    current_user = get_jwt_identity()

    post = post_collection.find_one({"post_id": post_id, "author": current_user})

    if not post:
        return jsonify({"error": "Post not found"}), 404

    post_collection.delete_one({"post_id": post_id, "author": current_user})

    return jsonify({"message": "Post deleted"}), 200

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    current_user = get_jwt_identity()
    text = request.form.get('text')

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    # Get the last_comment_id and increment it
    last_comment_id_doc = db["last_comment_id"].find_one()
    if last_comment_id_doc is None:
        last_comment_id = 1
        db["last_comment_id"].insert_one({"_id": "last_comment_id", "value": last_comment_id})
    else:
        last_comment_id = last_comment_id_doc["value"] + 1
        db["last_comment_id"].update_one({"_id": "last_comment_id"}, {"$set": {"value": last_comment_id}})

    comment = {
        "comment_id": last_comment_id,
        "user": current_user,
        "text": text,
        "replies": []
    }

    post_collection.update_one({"post_id": post_id}, {"$push": {"comments": comment}})

    return jsonify({"message": "Comment added"}), 201

@app.route('/api/posts/<int:post_id>/reactions', methods=['POST'])
@jwt_required()
def add_reaction(post_id):
    current_user = get_jwt_identity()
    type = request.form.get('type')

    if not type or type not in ['like', 'unlike']:
        return jsonify({'error': 'Valid type (like or unlike) is required'}), 400

    reaction = post_collection.find_one({"post_id": post_id, "reactions.user": current_user})

    if reaction:
        post_collection.update_one({"post_id": post_id, "reactions.user": current_user}, {"$set": {"reactions.$.type": type}})
    else:
        new_reaction = {
            "user": current_user,
            "type": type
        }
        post_collection.update_one({"post_id": post_id}, {"$push": {"reactions": new_reaction}})

    return jsonify({"message": "Reaction added or updated"}), 201

@app.route('/api/posts/<int:post_id>/comments/<int:comment_id>/replies', methods=['POST'])
@jwt_required()
def add_reply(post_id, comment_id):
    current_user = get_jwt_identity()
    text = request.form.get('text')

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    # Get the last_reply_id and increment it
    last_reply_id_doc = db["last_reply_id"].find_one()
    if last_reply_id_doc is None:
        last_reply_id = 1
        db["last_reply_id"].insert_one({"_id": "last_reply_id", "value": last_reply_id})
    else:
        last_reply_id = last_reply_id_doc["value"] + 1
        db["last_reply_id"].update_one({"_id": "last_reply_id"}, {"$set": {"value": last_reply_id}})

    reply = {
        "reply_id": last_reply_id,
        "user": current_user,
        "text": text
    }

    post_collection.update_one({"post_id": post_id, "comments.comment_id": comment_id}, {"$push": {"comments.$.replies": reply}})

    return jsonify({"message": "Reply added"}), 201
if __name__ == '__main__':
    app.run(debug=True)
