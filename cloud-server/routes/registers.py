from flask import Blueprint, request, jsonify
from db import get_db
from datetime import datetime, timezone, timedelta
import json
from bson import json_util

# Khởi tạo Blueprint cho register
register_bp = Blueprint("register", __name__)
db = get_db()
register_collection = db["registers"]  # Collection cho Register
parking_collection = db["parkings"]  # Collection cho Parkings
users_collection = db["users"]  # Collection cho Users

# Lấy danh sách đăng ký
@register_bp.route("/", methods=["GET"])
def get_registers():
    registers = list(register_collection.find({}, {"_id": 0}))
    return jsonify(registers), 200

@register_bp.route('/get_register_list', methods=['POST'])
def get_register_list():
    try:
        data = request.get_json()
        parking_id = data.get("parking_id")

        if not parking_id:
            return jsonify({"status": "error", "message": "parking_id is required"}), 400

        # Tìm tất cả các đăng ký theo parking_id
        registers_cursor = register_collection.find(
            {"parking_id": parking_id},
            {
                "_id": 0,
                "user_id": 1,
                "license_plate": 1,
                "register_time": 1,
                "expired": 1,
                "last_update": 1
            }
        )

        registers_list = list(registers_cursor)

        if not registers_list:
            return jsonify({"status": "error", "message": "No registers found for this parking_id"}), 404

        # Convert ObjectId/Date to JSON-serializable
        registers_json = json.loads(json_util.dumps(registers_list))

        return jsonify({
            "status": "success",
            "message": "Registers retrieved successfully",
            "data": registers_json
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# insert register
@register_bp.route('/add_register_parking', methods=['POST'])
def register_parking():
    try:
        data = request.get_json()

        user_id = data.get("user_id")
        parking_id = data.get("parking_id")
        license_plate = data.get("license_plate")

        if not user_id or not parking_id or not license_plate:
            return jsonify({"message": "Missing required fields", "status": "fail"}), 400

        now = datetime.now(timezone.utc)
        expired_time = now + timedelta(days=30)

        # Kiểm tra user_id có tồn tại không
        user_exists = users_collection.find_one({"user_id": user_id})
        if not user_exists:
            return jsonify({"message": "User does not exist", "status": "fail"}), 400

        # Kiểm tra trạng thái bãi đỗ
        parking_doc = parking_collection.find_one({"parking_id": parking_id})
        if not parking_doc:
            return jsonify({
                "message": "Parking lot not found",
                "status": "not_found"
            }), 404

        if parking_doc.get("status") != "active":
            return jsonify({
                "message": "Parking lot is not active",
                "status": "inactive"
            }), 403

        # Tránh trùng license_plate giữa user khác trong cùng parking_id
        same_plate = register_collection.find_one({
            "license_plate": license_plate,
            "parking_id": parking_id,
            "expired": {"$gt": now}
        })

        if same_plate and same_plate["user_id"] != user_id:
            return jsonify({
                "message": "This license plate is already registered by another user",
                "status": "conflict"
            }), 409

        #  Biển số đã đăng ký và còn hiệu lực bởi chính user
        existing = register_collection.find_one({
            "user_id": user_id,
            "parking_id": parking_id,
            "license_plate": license_plate,
            "expired": {"$gt": now}
        })

        if existing:
            return jsonify({
                "message": "License plate already registered and still valid",
                "status": "exists"
            }), 409

        # Tạo bản ghi mới
        register_data = {
            "parking_id": parking_id,
            "user_id": user_id,
            "license_plate": license_plate,
            "register_time": now,
            "expired": expired_time,
            "last_update": now
        }

        register_collection.insert_one(register_data)

        return jsonify({"message": "Registration successful", "status": "success"}), 201

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500
    
# update register

@register_bp.route('/update_register_parking', methods=['PUT'])
def update_register_parking():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        parking_id = data.get("parking_id")
        license_plate = data.get("license_plate")

        if not user_id or not parking_id or not license_plate:
            return jsonify({"message": "Missing required fields", "status": "fail"}), 400

        now = datetime.now(timezone.utc)
        # Kiểm tra user_id có tồn tại không
        user_exists = users_collection.find_one({"user_id": user_id})
        if not user_exists:
            return jsonify({"message": "User does not exist", "status": "fail"}), 400

        # Kiểm tra bãi đỗ tồn tại
        parking_lot = parking_collection.find_one({"parking_id": parking_id})
        if not parking_lot:
            return jsonify({"message": "Parking lot not found", "status": "not_found"}), 404

        # Kiểm tra trạng thái bãi đỗ
        if parking_lot.get("status") != "active":
            return jsonify({"message": "Parking lot is not active", "status": "inactive"}), 403

        # Kiểm tra biển số đã được user này đăng ký chưa
        existing = register_collection.find_one({
            "user_id": user_id,
            "parking_id": parking_id,
            "license_plate": license_plate
        })

        if not existing:
            return jsonify({"message": "No registration found to update", "status": "not_found"}), 404

        # Kiểm tra xem biển số này có đang được user khác dùng và còn hiệu lực không
        conflict = register_collection.find_one({
            "user_id": {"$ne": user_id},
            "parking_id": parking_id,
            "license_plate": license_plate,
            "expired": {"$gt": now}
        })

        if conflict:
            return jsonify({"message": "This license plate is already used by another user", "status": "conflict"}), 409

        # Cập nhật thời gian hết hạn thêm 30 ngày kể từ hiện tại
        updated_fields = {
            "register_time": now,
            "expired": now + timedelta(days=30),
            "last_update": now
        }

        register_collection.update_one(
            {
                "user_id": user_id,
                "parking_id": parking_id,
                "license_plate": license_plate
            },
            {"$set": updated_fields}
        )

        return jsonify({"message": "Update successful", "status": "success"}), 200

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@register_bp.route("/get_registered_vehicles", methods=["POST"])
def get_registered_vehicles():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "Missing 'user_id'"}), 400

    # Lấy tất cả bản ghi đã đăng ký của user
    registrations = list(register_collection.find(
        {"user_id": user_id},
        {"_id": 0, "license_plate": 1, "parking_id": 1}
    ))

    if not registrations:
        return jsonify({"status": "success", "data": []}), 200

    # Tạo set các parking_id để truy vấn 1 lần
    parking_ids = list(set([r["parking_id"] for r in registrations]))

    # Lấy tên bãi xe tương ứng
    parking_map = {
        p["parking_id"]: p["parking_name"]
        for p in parking_collection.find(
            {"parking_id": {"$in": parking_ids}},
            {"_id": 0, "parking_id": 1, "parking_name": 1}
        )
    }

    # Gắn tên bãi xe vào từng bản ghi
    result = []
    for r in registrations:
        result.append({
            "license_plate": r["license_plate"],
            "parking_name": parking_map.get(r["parking_id"], "Unknown")
        })

    return jsonify({"status": "success", "data": result}), 200
