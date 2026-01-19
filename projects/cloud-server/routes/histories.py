import pymongo
from flask import Blueprint, request, jsonify
from db import get_db
from bson.objectid import ObjectId
from datetime import datetime, timedelta

# Khởi tạo Blueprint
history_bp = Blueprint("history", __name__)
db = get_db()
histories_collection = db["histories"]  # Collection MongoDB
parking_collection = db["parkings"]

@history_bp.route("/", methods=["POST"])
def add_history():
    try:
        # Lấy dữ liệu từ request body
        data = request.get_json()

        # Kiểm tra các trường bắt buộc
        required_fields = ["user_id", "parking_id", "license_plate", "time_in", "time_out", "parking_time", "total_price"]
        if not all(key in data for key in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Kiểm tra user_id tồn tại
        if not db["users"].find_one({"user_id": data["user_id"]}):
            return jsonify({"error": f"user_id {data['user_id']} does not exist"}), 400

        # Kiểm tra parking_id tồn tại
        parking = db["parkings"].find_one({"parking_id": data["parking_id"]})
        if not parking:
            return jsonify({"error": f"parking_id {data['parking_id']} does not exist"}), 400

        # Kiểm tra định dạng thời gian
        try:
            time_in = datetime.fromisoformat(data["time_in"])
            time_out = datetime.fromisoformat(data["time_out"])
            if time_out < time_in:
                return jsonify({"error": "time_out must be greater than time_in"}), 400
        except ValueError:
            return jsonify({"error": "Invalid ISO format for time_in or time_out"}), 400

        # Tạo đối tượng History
        history = {
            "user_id": data["user_id"],
            "parking_id": data["parking_id"],
            "license_plate": data["license_plate"],
            "time_in": time_in,
            "time_out": time_out,
            "parking_time": float(data["parking_time"]),
            "total_price": float(data["total_price"])
        }

        # Thêm vào MongoDB
        result = histories_collection.insert_one(history)

        return jsonify({"message": "History added successfully", "id": str(result.inserted_id)}), 201

    except pymongo.errors.PyMongoError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

    
@history_bp.route('/get_parking_histories', methods=['POST'])
def get_parking_histories():
    try:
        # Lấy dữ liệu từ request
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        # Tìm tất cả lịch sử của user_id
        histories = list(histories_collection.find({"user_id": user_id}))
        if not histories:
            return jsonify({"status": "error", "message": "No histories found for this user"}), 404

        # Lấy thông tin bãi đỗ xe và chuẩn bị dữ liệu trả về
        response_data = []
        for history in histories:
            parking = parking_collection.find_one({"parking_id": history["parking_id"]})
            if parking:
                response_data.append({
                    "parking_name": parking.get("parking_name", "Unknown"),
                    "license_plate": history.get("license_plate", ""),
                    "parking_time": history.get("parking_time", 0),
                    "total_price": history.get("total_price", 0),
                    "time_in": history["time_in"].isoformat() if isinstance(history["time_in"], datetime) else history["time_in"],
                    "time_out": history["time_out"].isoformat() if isinstance(history["time_out"], datetime) else history["time_out"]
                })

        return jsonify({
            "status": "success",
            "message": "Parking histories retrieved successfully",
            "data": response_data
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@history_bp.route('/by_parking_date', methods=['GET'])
def get_histories_by_parking_and_date():
    try:
        parking_id = request.args.get('parking_id')
        date_str = request.args.get('date')
        day = request.args.get('day')
        month = request.args.get('month')
        year = request.args.get('year')

        if not parking_id:
            return jsonify({"status": "error", "message": "parking_id is required"}), 400

        # Parse date either from `date` (YYYY-MM-DD) or from day/month/year
        if date_str:
            try:
                parsed = datetime.fromisoformat(date_str)
                date_obj = datetime(parsed.year, parsed.month, parsed.day)
            except ValueError:
                return jsonify({"status": "error", "message": "date must be in YYYY-MM-DD format"}), 400
        elif day and month and year:
            try:
                date_obj = datetime(int(year), int(month), int(day))
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid day/month/year"}), 400
        else:
            return jsonify({"status": "error", "message": "Provide `date` (YYYY-MM-DD) or `day`, `month`, `year`"}), 400

        start = date_obj
        end = start + timedelta(days=1)

        # Find histories that overlap with the date interval [start, end)
        query = {
            "parking_id": parking_id,
            "time_in": {"$lt": end},
            "time_out": {"$gte": start}
        }

        histories = list(histories_collection.find(query))

        # Build response
        response_data = []
        for history in histories:
            parking = parking_collection.find_one({"parking_id": history["parking_id"]})
            response_data.append({
                "parking_name": parking.get("parking_name", "Unknown") if parking else "Unknown",
                "license_plate": history.get("license_plate", ""),
                "parking_time": history.get("parking_time", 0),
                "total_price": history.get("total_price", 0),
                "time_in": history["time_in"].isoformat() if isinstance(history["time_in"], datetime) else history.get("time_in"),
                "time_out": history["time_out"].isoformat() if isinstance(history["time_out"], datetime) else history.get("time_out")
            })

        return jsonify({"status": "success", "data": response_data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
