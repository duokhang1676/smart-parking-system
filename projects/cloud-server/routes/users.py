from flask import Blueprint, request, jsonify
from db import get_db
from werkzeug.security import check_password_hash,generate_password_hash

# Khởi tạo Blueprint cho user
user_bp = Blueprint("user", __name__)
db = get_db()
users_collection = db["users"]  # Collection cho User
register_collection = db["registers"]
parking_collection = db["parkings"]

# Lấy danh sách tất cả người dùng
@user_bp.route("/", methods=["GET"])
def get_users():
    users = list(users_collection.find({}, {"_id": 0}))
    return jsonify(users), 200

# Tạo người dùng mới
@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.json

    # Kiểm tra các trường cần thiết
    if not all(key in data for key in ("user_id", "user_name", "password")):
        return jsonify({"error": "Missing fields"}), 400

    # Kiểm tra nếu user_id đã tồn tại
    if users_collection.find_one({"user_id": data["user_id"]}):
        return jsonify({"error": "User already exists"}), 400

    # Mã hóa mật khẩu trước khi lưu
    data["password"] = generate_password_hash(data["password"])

    users_collection.insert_one(data)
    return jsonify({"message": "User created successfully"}), 201


# Cập nhật thông tin người dùng
@user_bp.route("/update_user", methods=["POST"])
def update_user():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing 'user_id'"}), 400

    # Loại bỏ user_id khỏi phần dữ liệu cần cập nhật
    update_data = {k: v for k, v in data.items() if k != "user_id"}

    if not update_data:
        return jsonify({"error": "No fields to update"}), 400

    # Mã hóa mật khẩu nếu có trường password
    if "password" in update_data:
        update_data["password"] = generate_password_hash(update_data["password"])

    result = users_collection.update_one({"user_id": user_id}, {"$set": update_data})

    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User updated successfully"}), 200

# Xóa người dùng
@user_bp.route("/delete_user", methods=["POST"])
def delete_user():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing 'user_id'"}), 400

    result = users_collection.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User deleted successfully"}), 200


# API đăng nhập với mật khẩu mã hóa
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    phone = data.get("user_id")
    password = data.get("password")

    if not phone or not password:
        return jsonify({"message": "Phone and password are required", "status": "wrong"}), 400

    # Kiểm tra người dùng trong cơ sở dữ liệu
    user = users_collection.find_one({"user_id": phone})
    if not user:
        return jsonify({"message": "User does not exist", "status": "not exist"}), 404

    # So sánh mật khẩu với hash lưu trong cơ sở dữ liệu
    if check_password_hash(user["password"], password):
        # Đăng nhập thành công
        return jsonify({"message": user["user_id"], "status": "success"}), 200
    else:
        # Sai mật khẩu
        return jsonify({"message": "Invalid password", "status": "wrong password"}), 401

# @user_bp.route("/login", methods=["POST"])
# def login():
#     data = request.get_json()
#     phone = data.get("phone")
#     password = data.get("password")

#     # Kiểm tra người dùng trong cơ sở dữ liệu
#     user = users_collection.find_one({"phone": phone, "password": password})
#     if user:
#         return jsonify({"message": "Login successful", "status": "success"}), 200
#     return jsonify({"message": "Invalid username or password", "status": "fail"}), 401
# API Đăng Ký
@user_bp.route('/signin', methods=['POST'])
def register_user():
    data = request.get_json()
    user_id = data.get("user_id")
    name = data.get("name")
    password = data.get("password")

    if not user_id or not name or not password:
        return jsonify({"message": "Missing required fields", "status": "fail"}), 400

    # Kiểm tra xem user_id đã tồn tại chưa
    if users_collection.find_one({"user_id": user_id}):
        return jsonify({"message": "User already exists", "status": "exists"}), 409

    # Mã hóa mật khẩu
    hashed_password = generate_password_hash(password)

    # Thêm người dùng vào cơ sở dữ liệu
    users_collection.insert_one({
        "user_id": user_id,
        "name": name,
        "password": hashed_password
    })

    return jsonify({"message": "User registered successfully", "status": "success"}), 201
# lấy danh sách bãi xe đã đăng kí theo user_id
@user_bp.route('/registered-parkings', methods=['POST'])
def get_registered_parkings():
    try:
        print("Payload from Unity:", request.data)
        # Lấy thông tin user_id từ request body
        user_id = request.json.get('user_id')
        
        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        # Truy vấn các bãi xe đã đăng ký từ collection 'register' cho user_id
        registered_documents = register_collection.find({"user_id": user_id})
        
        # Dùng set để lưu thông tin các bãi xe đã đăng ký từ parking collection
        registered_parking_ids = set()
        for doc in registered_documents:
            # Dùng parking_id trong 'register' để tìm thông tin bãi xe tương ứng
            parking_id = doc.get("parking_id")
            if parking_id:
                # Ánh xạ `parking_id` sang `_id` trong collection parking
                parking_doc = parking_collection.find_one({"parking_id": parking_id})
                if parking_doc:
                    registered_parking_ids.add(
                        f"{parking_doc.get('address')}, {parking_doc.get('parking_name')}"
                    )

        return jsonify({
            "registered_parkings": list(registered_parking_ids),
            "status": "success"
        }), 200

    except Exception as e:
        print("Error occurred:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
@user_bp.route('/getUserInfo', methods=['POST'])
def handle_request():
    data = request.json
    action = data.get("action", None)
    user_id = data.get("user_id", None)

    if not action or not user_id:
        return jsonify({"message": "Missing 'action' or 'user_id' in request"}), 400

    if action == "get_user_info":
        # Lấy thông tin user
        user = users_collection.find_one({"user_id": user_id}, {"_id": 0})
        if user:
            return jsonify({"status": "success", "data": user}), 200
        else:
            return jsonify({"status": "error", "message": "User not found"}), 404

    elif action == "get_registers":
        # Lấy danh sách đăng ký
        registers = register_collection.find_one({"user_id": user_id}, {"_id": 0})
        if registers:
            return jsonify({"status": "success", "data": registers}), 200
        else:
            return jsonify({"status": "error", "message": "No registers found"}), 404

    elif action == "get_parking_info":
        # Lấy thông tin bãi giữ xe
        parking_id = data.get("parking_id", None)
        if not parking_id:
            return jsonify({"message": "Missing 'parking_id' in request"}), 400

        parking = parking_collection.find_one({"_id": parking_id}, {"_id": 0})
        if parking:
            return jsonify({"status": "success", "data": parking}), 200
        else:
            return jsonify({"status": "error", "message": "Parking not found"}), 404

    else:
        return jsonify({"message": "Invalid action"}), 400