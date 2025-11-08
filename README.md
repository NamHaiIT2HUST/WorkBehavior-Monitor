# 🧠 WorkBehavior Monitor

**WorkBehavior Monitor** là hệ thống giám sát và phân tích hành vi làm việc của nhân viên văn phòng, giúp doanh nghiệp theo dõi hiệu suất, cải thiện năng suất và tối ưu môi trường làm việc.

---

## 📖 Mục lục
- [Giới thiệu](#giới-thiệu)
- [Tính năng chính](#tính-năng-chính)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cài đặt & Thiết lập](#cài-đặt--thiết-lập)
- [Cách sử dụng](#cách-sử-dụng)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Đóng góp & Phát triển](#đóng-góp--phát-triển)
- [Giấy phép](#giấy-phép)
- [Tác giả](#tác-giả)

---

## 🚀 Giới thiệu

**WorkBehavior Monitor** được phát triển nhằm hỗ trợ doanh nghiệp trong việc:
- Theo dõi hành vi làm việc của nhân viên trong giờ hành chính.
- Phát hiện tình trạng không hoạt động (AFK) hoặc rời khỏi chỗ ngồi.
- Ghi nhận thời gian làm việc thực tế và lịch sử hoạt động.
- Trực quan hóa dữ liệu qua giao diện web.

Hệ thống có thể kết hợp với **camera**, **cảm biến khoảng cách**, hoặc **loadcell HX711** để nhận biết hành vi và tư thế làm việc, từ đó tạo báo cáo chi tiết cho người quản lý.

---

## ⚙️ Tính năng chính

✅ Giám sát hành vi làm việc theo thời gian thực.  
✅ Phát hiện khi nhân viên rời chỗ hoặc không hoạt động.  
✅ Lưu trữ dữ liệu vào cơ sở dữ liệu SQLite.  
✅ Giao diện web hiển thị thông tin, lịch sử và thống kê.  
✅ Hỗ trợ cảm biến Loadcell (HX711) cho ứng dụng thực tế.  
✅ Dễ dàng mở rộng, sao lưu và khôi phục dữ liệu.  

---

## 🧱 Cấu trúc thư mục

| Thư mục / Tệp | Mô tả |
|----------------|--------|
| `project/` | Thư mục chứa toàn bộ mã nguồn chính |
| ├── `database.py` | Xử lý cơ sở dữ liệu SQLite |
| ├── `distance_utils.py` | Hàm tính toán khoảng cách, chuyển động |
| ├── `session_monitor.py` | Theo dõi thời gian làm việc |
| ├── `static/` | Chứa tài nguyên tĩnh (CSS, JS, ảnh) |
| ├── `templates/` | Các file HTML giao diện người dùng |
| ├── `test_webcam_index.py` | Kiểm tra kết nối webcam |
| └── `webserver.py` | Chạy ứng dụng Flask Web |
| `HX711 Loadcell/` | Module cảm biến HX711 để giám sát tư thế |
| `Backup-2/ ... Backup-5/` | Các bản sao lưu mã nguồn |
| `README.md` | Tài liệu hướng dẫn |

- `project/`: chứa mã nguồn chính của hệ thống web và xử lý dữ liệu.  
- `HX711 Loadcell/`: module cảm biến đo lực / tư thế làm việc.  
- `Backup-*`: các bản sao lưu mã nguồn cũ.  
- `static/` và `templates/`: chứa tài nguyên giao diện web.  
- `database.py`: xử lý kết nối cơ sở dữ liệu SQLite.  
- `webserver.py`: chạy ứng dụng web (Flask server).  

---

## 💻 Cài đặt & Thiết lập

### 1. Clone dự án

git clone https://github.com/NamHaiIT2HUST/WorkBehavior-Monitor.git
cd WorkBehavior-Monitor


### 2. Tạo môi trường ảo (tùy chọn, khuyến khích)

Sao chép mã
python -m venv venv
venv\Scripts\activate  # Nếu dùng Window
hoặc
source venv/bin/activate    # Nếu dùng Linux/Mac


### 3. Cài đặt thư viện cần thiết

Nếu có file requirements.txt:
Sao chép mã
pip install -r requirements.txt

Hoặc cài đặt thủ công:
Sao chép mã
pip install flask opencv-python numpy


### 4. Chạy hệ thống

Sao chép mã
python project/webserver.py
Mở trình duyệt và truy cập địa chỉ:
http://127.0.0.1:5000



## 🧩 Cách sử dụng
Chạy server Flask bằng webserver.py.

Kết nối camera hoặc cảm biến Loadcell nếu có.

Theo dõi hành vi làm việc, thời gian hoạt động và biểu đồ trên giao diện web.

Dữ liệu sẽ tự động lưu trong file work_monitor.db hoặc work_sessions.db.

Vào trang History để xem lịch sử làm việc chi tiết.

## 🧰 Công nghệ sử dụng
Thành phần	Mô tả
Python	Ngôn ngữ lập trình chính
Flask	Framework web nhẹ và dễ triển khai
OpenCV	Phát hiện chuyển động, khuôn mặt, khoảng cách
SQLite	Lưu trữ dữ liệu cục bộ
HTML / CSS	Xây dựng giao diện web
HX711 Loadcell	Cảm biến vật lý giám sát tư thế và trọng lượng

## 🤝 Đóng góp & Phát triển
Mọi ý tưởng, đóng góp hoặc báo lỗi đều được chào đón!

Cách tham gia:
Fork dự án về tài khoản của bạn.
Tạo branch mới cho tính năng hoặc bản sửa lỗi.
Commit & Push thay đổi.
Tạo Pull Request để nhóm phát triển xem xét.

## 📜 Giấy phép
Dự án được phát hành dưới giấy phép MIT License.
Bạn có thể sử dụng, chỉnh sửa và phân phối cho mục đích học tập, nghiên cứu hoặc thương mại.

## 👨‍💻 Tác giả
Nguyễn Đào Nam Hải

🎓 Đại học Bách Khoa Hà Nội (HUST)

📧 Liên hệ: GitHub - NamHaiIT2HUST
