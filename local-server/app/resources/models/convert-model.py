from ultralytics import YOLO

# Load a YOLO11n PyTorch model
model = YOLO("car-yolo11n-416.pt")

# Export the model to TensorRT
model.export(format="engine")  # creates 'yolo11n.engine'

# Load the exported TensorRT model
trt_model = YOLO("car-yolo11n-416.engine")

# Run inference
# results = trt_model("https://ultralytics.com/images/bus.jpg")