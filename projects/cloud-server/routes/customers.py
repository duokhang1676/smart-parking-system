from flask import Blueprint, request, jsonify
from db import get_db
from bson.objectid import ObjectId

# Khởi tạo Blueprint
customer_bp = Blueprint("customer", __name__)
db = get_db()
customers_collection = db["customers"]  # Collection MongoDB

# Lấy danh sách tất cả khách hàng
@customer_bp.route("/", methods=["GET"])
def get_all_customers():
    customers = list(customers_collection.find({}, {"_id": 0}))
    return jsonify(customers), 200

# Lấy thông tin khách hàng theo user_id
@customer_bp.route("/<user_id>", methods=["GET"])
def get_customer(user_id):
    customer = customers_collection.find_one({"user_id": user_id}, {"_id": 0})
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer), 200

# Tạo mới một khách hàng
@customer_bp.route("/", methods=["POST"])
def create_customer():
    data = request.json
    # Kiểm tra các trường bắt buộc
    if not all(key in data for key in ("user_id", "license", "register_time", "expired")):
        return jsonify({"error": "Missing required fields"}), 400

    # Kiểm tra nếu user_id đã tồn tại
    if customers_collection.find_one({"user_id": data["user_id"]}):
        return jsonify({"error": "Customer already exists"}), 400

    customers_collection.insert_one(data)
    return jsonify({"message": "Customer created successfully"}), 201

# Cập nhật thông tin khách hàng
@customer_bp.route("/<user_id>", methods=["PUT"])
def update_customer(user_id):
    data = request.json
    result = customers_collection.update_one({"user_id": user_id}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify({"message": "Customer updated successfully"}), 200

# Xóa một khách hàng
@customer_bp.route("/<user_id>", methods=["DELETE"])
def delete_customer(user_id):
    result = customers_collection.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify({"message": "Customer deleted successfully"}), 200
