from flask import Blueprint, request, jsonify
from db import get_db
from datetime import datetime, timezone

parking_slot_bp = Blueprint("parking_slot", __name__)

db = get_db()
parking_slots_collection = db["parking_slots"]
parking_collection = db["parkings"]

# get by parking_id
@parking_slot_bp.route("/get_parking_slots", methods=["POST"])
def get_parking_slots():
    data = request.get_json()
    parking_id = data.get("parking_id")

    if not parking_id:
        return jsonify({"error": "Missing parking_id"}), 400

    slot = parking_slots_collection.find_one({"parking_id": parking_id}, {"_id": 0})
    if not slot:
        return jsonify({"error": "Parking slots not found"}), 404

    return jsonify({"status": "success", "data": slot}), 200

# insert parking slots
@parking_slot_bp.route("/insert_parking_slots", methods=["POST"])
def insert_parking_slots():
    data = request.get_json()

    required_fields = ["parking_id", "available_list", "occupied_list"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Kiểm tra parking_id tồn tại trong collection parkings
    if not parking_collection.find_one({"parking_id": data["parking_id"]}):
        return jsonify({"error": f"Parking ID '{data['parking_id']}' does not exist"}), 400

    # Kiểm tra trùng lặp
    exists = parking_slots_collection.find_one({"parking_id": data["parking_id"]})
    if exists:
        return jsonify({"error": "Parking slots for this parking_id already exist"}), 400

    data["last_update"] = datetime.now(timezone.utc)

    parking_slots_collection.insert_one(data)
    return jsonify({"message": "Parking slots inserted successfully"}), 201

# update parking slots
@parking_slot_bp.route("/update_parking_slots", methods=["POST"])
def update_parking_slots():
    data = request.get_json()
    parking_id = data.get("parking_id")

    if not parking_id:
        return jsonify({"error": "Missing parking_id"}), 400

    update_fields = {}
    if "available_list" in data:
        update_fields["available_list"] = data["available_list"]
    if "occupied_list" in data:
        update_fields["occupied_list"] = data["occupied_list"]
    if "occupied_license_list" in data:
        update_fields["occupied_license_list"] = data["occupied_license_list"]

    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400
    
    # kiểm tra xem parking_id có tồn tại trong collection 'parkings'
    if not parking_collection.find_one({"parking_id": parking_id}):
        return jsonify({"error": f"Parking ID '{parking_id}' does not exist"}), 400
    
    # kiem tra parking_id có tồn tại trong collection 'parking_slots'
    if not parking_slots_collection.find_one({"parking_id": parking_id}):
        return jsonify({"error": f"Parking ID '{parking_id}' does not exist"}), 400

    from datetime import datetime
    update_fields["last_update"] = datetime.now(timezone.utc)


    result = parking_slots_collection.update_one(
        {"parking_id": parking_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Parking slots not found"}), 404

    return jsonify({"message": "Parking slots updated successfully"}), 200

