
from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from db import get_db

# Khởi tạo Blueprint
coordinate_bp = Blueprint('coordinate', __name__)
db = get_db()
coordinates_collection = db['coordinates']

# Lấy tất cả coordinates
@coordinate_bp.route('/', methods=['GET'])
def get_all_coordinates():
    coordinates = list(coordinates_collection.find({}, {'_id': 0}))
    return jsonify(coordinates), 200
#
# Lấy coordinates theo parking_id
@coordinate_bp.route('/<string:parking_id>', methods=['GET'])
def get_coordinates_by_parking_id(parking_id):
    coordinates = list(coordinates_collection.find({'parking_id': parking_id}, {'_id': 0}))
    if not coordinates:
        return jsonify({'message': 'Coordinates not found'}), 404
    return jsonify(coordinates), 200

# Lấy coordinates theo parking_id và camera_id
@coordinate_bp.route('/<string:parking_id>/<string:camera_id>', methods=['GET'])
def get_coordinates_by_parking_id_and_camera_id(parking_id, camera_id):
    coordinates = list(coordinates_collection.find({'parking_id': parking_id, 'camera_id': camera_id}, {'_id': 0}))
    if not coordinates:
        return jsonify({'message': 'Coordinates not found'}), 404
    return jsonify(coordinates), 200

# Thêm mới coordinates
@coordinate_bp.route('/add', methods=['POST'])
def insert_coordinates():
    data = request.json
    required_fields = ['parking_id', 'camera_id','image_url' 'coordinates_list']
    
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    new_coordinate = {
        'parking_id': data['parking_id'],
        'camera_id': data['camera_id'],
        'image_url': data.get('image_url', ''),
        'coordinates_list': data['coordinates_list']
    }

    coordinates_collection.insert_one(new_coordinate)
    return jsonify({'message': 'Coordinates added successfully'}), 201

# Cập nhật coordinates
@coordinate_bp.route('/update/<string:parking_id>/<string:camera_id>', methods=['PUT'])
def update_coordinates(parking_id, camera_id):
    data = request.json
    print("Received JSON:", data)
    update_data = {}

    if 'image_url' in data:
        update_data['image_url'] = data['image_url']
    if 'coordinates_list' in data:
        update_data['coordinates_list'] = data['coordinates_list']
    if 'coordinates_reid_list' in data:
        update_data['coordinates_reid_list'] = data['coordinates_reid_list']

    if not update_data:
        return jsonify({'message': 'No data provided for update'}), 400

    result = coordinates_collection.update_one(
        {'parking_id': parking_id, 'camera_id': camera_id},
        {'$set': update_data}
    )

    if result.matched_count == 0:
        return jsonify({'message': 'Coordinates not found'}), 404

    return jsonify({'message': 'Coordinates updated successfully'}), 200
