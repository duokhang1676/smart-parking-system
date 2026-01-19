from flask import Flask
from routes.users import user_bp
from routes.parking import parking_bp
from routes.registers import register_bp
from routes.customers import customer_bp
from routes.histories import history_bp
from routes.environments import environment_bp
from routes.coordinates import coordinate_bp
from routes.parking_slots import parking_slot_bp
from routes.parked_vehicles import parked_vehicle_bp

# Tạo ứng dụng Flask
app = Flask(__name__)

# Đăng ký các Blueprint
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(parking_bp, url_prefix="/api/parking")
app.register_blueprint(register_bp, url_prefix="/api/registers")
app.register_blueprint(customer_bp, url_prefix="/api/customers")
app.register_blueprint(history_bp, url_prefix="/api/histories")
app.register_blueprint(environment_bp, url_prefix="/api/environments")
app.register_blueprint(coordinate_bp, url_prefix="/api/coordinates")
app.register_blueprint(parking_slot_bp, url_prefix="/api/parking_slots")
app.register_blueprint(parked_vehicle_bp, url_prefix="/api/parked_vehicles")

@app.route("/")
def index():
    """
    Route kiểm tra server.
    """
    return "Parking Management API is running!", 200

# Điểm khởi chạy server
if __name__ == "__main__":
    app.run(debug=True)
