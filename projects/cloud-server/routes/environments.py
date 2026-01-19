from flask import Blueprint, request, jsonify
from db import get_db

# Khởi tạo Blueprint cho parking
environment_bp = Blueprint("environment", __name__)
db = get_db()
environment_collection = db["environments"]
parking_collection = db["parkings"]

# get all environment
@environment_bp.route("/", methods=["GET"])
def get_environments():
    """
    Lấy danh sách tất cả các môi trường.
    """
    environments = list(environment_collection.find({}, {"_id": 0}))
    return jsonify(environments), 200

# get environment by parking_id
@environment_bp.route("/get_environment", methods=["POST"])
def get_environment_by_parking_id():
    data = request.json
    parking_id = data.get("parking_id")

    if not parking_id:
        return jsonify({"status": "error", "message": "Missing 'parking_id'"}), 400

    env = environment_collection.find_one({"parking_id": parking_id}, {"_id": 0})
    
    if env:
        return jsonify({"status": "success", "data": env}), 200
    else:
        return jsonify({"status": "error", "message": "Environment data not found"}), 404

    
# insert environment
@environment_bp.route("/", methods=["POST"])
def insert_environment():
    data = request.json
    parking_id = data.get("parking_id")

    # Kiểm tra các trường bắt buộc
    required_fields = ["parking_id", "temperature", "humidity", "light"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Kiểm tra bãi đỗ tồn tại
    parking_lot = parking_collection.find_one({"parking_id": parking_id})
    if not parking_lot:
        return jsonify({"message": "Parking lot not found", "status": "not_found"}), 404

    # Thêm dữ liệu vào MongoDB
    result = environment_collection.insert_one({
        "parking_id": data["parking_id"],
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "light": data["light"]
    })

    return jsonify({
        "message": "Environment data inserted successfully",
        "inserted_id": str(result.inserted_id)
    }), 201

# update environment
@environment_bp.route("/update_environment", methods=["POST"])
def update_environment():
    data = request.json
    parking_id = data.get("parking_id")

    if not parking_id:
        return jsonify({"error": "Missing 'parking_id'"}), 400

    # Kiểm tra các trường cần thiết
    update_fields = ["temperature", "humidity", "light"]
    valid_data = {key: value for key, value in data.items() if key in update_fields}

    if not valid_data:
        return jsonify({"error": "No valid fields to update"}), 400

    result = environment_collection.update_one(
        {"parking_id": parking_id},
        {"$set": valid_data}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Parking environment data not found"}), 404

    return jsonify({"message": "Environment data updated successfully"}), 200
