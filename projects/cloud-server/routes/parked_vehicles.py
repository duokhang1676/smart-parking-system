from flask import Blueprint, request, jsonify
from db import get_db
import re

parked_vehicle_bp = Blueprint("parked_vehicle", __name__)
db = get_db()
parked_vehicle_collection = db["parked_vehicles"]
parking_collection = db["parking"]

# get parked vehicles by parking_id
@parked_vehicle_bp.route('/get_parked_vehicles', methods=['POST'])
def get_parked_vehicles():
    data = request.get_json()
    parking_id = data.get('parking_id')

    if not parking_id:
        return jsonify({'error': 'parking_id is required'}), 400

    try:
        parked_vehicles = parked_vehicle_collection.find_one({'parking_id': parking_id}, {'list': 1, '_id': 0})

        if not parked_vehicles:
            return jsonify({'error': 'Parking ID not found'}), 404

        return jsonify({'parked_vehicles': parked_vehicles.get('list', [])}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# add vehicle to list
@parked_vehicle_bp.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    data = request.get_json()
    parking_id = data.get('parking_id')
    vehicle = data.get('vehicle')

    if not parking_id or not vehicle:
        return jsonify({'error': 'parking_id and vehicle data are required'}), 400

    try:
        result = parked_vehicle_collection.update_one(
            {'parking_id': parking_id},
            {'$push': {'list': vehicle}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Parking ID not found'}), 404

        return jsonify({'message': 'Vehicle added successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# remove vehicle from list
@parked_vehicle_bp.route('/remove_vehicle', methods=['DELETE'])
def remove_vehicle():
    data = request.get_json()
    parking_id = data.get('parking_id')
    user_id = data.get('user_id')
    license_plate = data.get('license_plate')

    if not parking_id or not user_id or not license_plate:
        return jsonify({'error': 'parking_id, user_id, and license_plate are required'}), 400

    try:
        result = parked_vehicle_collection.update_one(
            {'parking_id': parking_id},
            {'$pull': {'list': {'user_id': user_id, 'license_plate': license_plate}}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Parking ID not found'}), 404

        return jsonify({'message': 'Vehicle removed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# update slot_name and num_slot
@parked_vehicle_bp.route('/update_vehicle', methods=['PUT'])
def update_vehicle():
    data = request.get_json()
    parking_id = data.get('parking_id')
    user_id = data.get('user_id')
    license_plate = data.get('license_plate')
    slot_name = data.get('slot_name')
    num_slot = data.get('num_slot')

    if not parking_id or not user_id or not license_plate:
        return jsonify({'error': 'parking_id, user_id, and license_plate are required'}), 400

    try:
        result = parked_vehicle_collection.update_one(
            {
                'parking_id': parking_id,
                'list.user_id': user_id,
                'list.license_plate': license_plate
            },
            {
                '$set': {
                    'list.$.slot_name': slot_name,
                    'list.$.num_slot': num_slot
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Vehicle not found'}), 404

        return jsonify({'message': 'Vehicle updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# update entire list
@parked_vehicle_bp.route('/update_vehicle_list', methods=['PUT'])
def update_vehicle_list():
    data = request.get_json()
    parking_id = data.get('parking_id')
    new_list = data.get('list')

    if parking_id is None or new_list is None:
        return jsonify({'error': 'parking_id and list are required'}), 400

    try:
        result = parked_vehicle_collection.update_one(
            {'parking_id': parking_id},
            {'$set': {'list': new_list}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Parking ID not found'}), 404

        return jsonify({'message': 'List updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# @parked_vehicle_bp.route("/get_user_parked_vehicle", methods=["POST"])
# def get_user_parked_vehicle():
#     data = request.json
#     user_id = data.get("user_id")
#     parking_id = data.get("parking_id")

#     if not user_id or not parking_id:
#         return jsonify({
#             "status": "error",
#             "message": "Missing 'user_id' or 'parking_id'"
#         }), 400

#     # Tìm xe đang đỗ của user trong đúng bãi này
#     parked_doc = parked_vehicle_collection.find_one(
#         {"parking_id": parking_id, "list.user_id": user_id},
#         {"_id": 0, "list.$": 1}
#     )

#     if not parked_doc or "list" not in parked_doc or len(parked_doc["list"]) == 0:
#         # Không tìm thấy xe của user trong bãi
#         return jsonify({
#             "status": "not_found",
#             "message": "No parked vehicle found for this user in the selected parking lot",
#             "data": None
#         }), 200

#     vehicle_info = parked_doc["list"][0]

#     result = {
#         "license_plate": vehicle_info.get("license_plate"),
#         "slot_name": vehicle_info.get("slot_name"),
#         "time_in": vehicle_info.get("time_in"),
#         "parking_id": parking_id,
#         "num_slot": vehicle_info.get("num_slot")
#     }

#     return jsonify({"status": "success", "data": result}), 200
@parked_vehicle_bp.route("/get_user_parked_vehicle", methods=["POST"])
def get_user_parked_vehicle():
    data = request.json
    user_id = data.get("user_id")
    parking_id = data.get("parking_id")

    # Kiểm tra đầu vào
    if not user_id or not parking_id:
        return jsonify({
            "status": "error",
            "message": "Missing 'user_id' or 'parking_id'"
        }), 400

    # Tìm document bãi đỗ xe tương ứng
    parked_doc = parked_vehicle_collection.find_one(
        {"parking_id": parking_id},
        {"_id": 0, "list": 1}
    )

    # Kiểm tra bãi có tồn tại không
    if not parked_doc or "list" not in parked_doc:
        return jsonify({
            "status": "error",
            "message": "Parking lot not found or no vehicles found",
            "data": None
        }), 404

    # Lọc ra tất cả các xe thuộc về user_id
    user_vehicles = [v for v in parked_doc["list"] if v.get("user_id") == user_id]

    # Nếu không có xe nào của user trong bãi
    if not user_vehicles:
        return jsonify({
            "status": "not_found",
            "message": "No parked vehicles found for this user in the selected parking lot",
            "data": []
        }), 200

    # Trả danh sách xe của user
    result = []
    for v in user_vehicles:
        result.append({
            "license_plate": v.get("license_plate"),
            "slot_name": v.get("slot_name"),
            "time_in": v.get("time_in"),
            "parking_id": parking_id,
            "num_slot": v.get("num_slot")
        })

    return jsonify({
        "status": "success",
        "count": len(result),
        "data": result
    }), 200

