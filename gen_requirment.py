import os
import subprocess

# ---- Đường dẫn project ----
project_path = "./"  # đổi thành đường dẫn tới project của bạn

# ---- Tạo danh sách các thư viện mà project sử dụng ----
print("🔍 Đang quét project để tìm các thư viện thực sự được sử dụng...")
subprocess.run(["pipreqs", project_path, "--force", "--ignore", "venv"], check=True)

# ---- Đọc các thư viện phát hiện được ----
with open(os.path.join(project_path, "requirements.txt")) as f:
    used_libs = [line.strip().split("==")[0] for line in f if line.strip()]

# ---- Lấy toàn bộ thư viện + phiên bản hiện có trong hệ thống ----
output = subprocess.check_output(["pip", "freeze"]).decode()
installed_libs = {}
for line in output.splitlines():
    if "==" in line:
        name, version = line.split("==", 1)
        installed_libs[name.lower()] = version

# ---- Lọc ra các thư viện thực sự dùng ----
final_libs = []
for lib in used_libs:
    ver = installed_libs.get(lib.lower())
    if ver:
        final_libs.append(f"{lib}=={ver}")
    else:
        final_libs.append(lib)

# ---- Ghi vào file requirements.txt ----
with open(os.path.join(project_path, "requirements.txt"), "w") as f:
    f.write("\n".join(sorted(final_libs)))

print("✅ File requirements.txt đã được tạo thành công!")
