import cv2
import yaml

# ==== Cấu hình ====
video_path = 0  # 🔸 thay đường dẫn video tại đây
output_yml = "app/resources/coordinates/reid-data/0.yml"

# ==== Biến toàn cục ====
points = []  # Danh sách chứa dict {id, x, y}
current_char = 'A'
counter = 0
image_copy = None


def mouse_callback(event, x, y, flags, param):
    global counter, image_copy
    if event == cv2.EVENT_LBUTTONDOWN:
        # Tạo ID mới
        point_id = f"{current_char}{counter}"
        counter += 1

        # Lưu điểm
        points.append({"id": point_id, "x": x, "y": y})

        # Hiển thị điểm lên ảnh
        cv2.circle(image_copy, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(image_copy, point_id, (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("Frame", image_copy)


def save_points_to_yml():
    """Lưu danh sách points ra file YAML"""
    with open(output_yml, 'w') as f:
        yaml.dump(points, f, sort_keys=False)
    print(f"✅ Đã lưu {len(points)} điểm vào {output_yml}")


def main():
    global image_copy, points, current_char, counter

    cap = cv2.VideoCapture(video_path)
    # Đi đến frame thứ 6 (chỉ số bắt đầu từ 0 => index 5)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 5)
    ret, frame = cap.read()
    frame = cv2.resize(frame, (640, 640))
    cap.release()

    if not ret:
        print("❌ Không đọc được video.")
        return

    image_copy = frame.copy()
    cv2.imshow("Frame", image_copy)
    cv2.setMouseCallback("Frame", mouse_callback)

    print("🖱️ Click để đánh dấu điểm.")
    print("➡️ Phím B, C, D... để đổi nhóm ID.")
    print("↩️ BACKSPACE để xóa điểm cuối cùng.")
    print("⎋ ESC để xóa tất cả điểm.")
    print("💾 ENTER để lưu ra file .yml.")
    print("❎ Q để thoát.")

    while True:
        key = cv2.waitKey(0) & 0xFF

        # Thoát
        if key == ord('q'):
            print("👋 Thoát chương trình.")
            break

        # Đổi ký tự ID
        elif 65 <= key <= 90 or 97 <= key <= 122:  # A-Z hoặc a-z
            current_char = chr(key).upper()
            counter = 0
            print(f"🔤 Đổi sang nhóm ID: {current_char}")

        # Xóa điểm cuối
        elif key == 8:  # Backspace
            if points:
                counter -= 1
                removed = points.pop()
                print(f"❌ Xóa điểm {removed['id']}")
                image_copy = frame.copy()
                for p in points:
                    cv2.circle(image_copy, (p['x'], p['y']), 5, (0, 0, 255), -1)
                    cv2.putText(image_copy, p['id'], (p['x'] + 10, p['y'] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow("Frame", image_copy)
            else:
                print("⚠️ Không có điểm nào để xóa.")

        # Xóa tất cả
        elif key == 27:  # ESC
            points.clear()
            counter = 0
            image_copy = frame.copy()
            cv2.imshow("Frame", image_copy)
            print("🧹 Đã xóa tất cả điểm.")

        # Lưu file
        elif key == 13:  # Enter
            save_points_to_yml()
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
