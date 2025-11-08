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

---

## 🚀 Giới thiệu

**WorkBehavior Monitor** được phát triển nhằm hỗ trợ doanh nghiệp trong việc:
- Theo dõi hành vi làm việc của nhân viên trong giờ hành chính.
- Phát hiện tình trạng không hoạt động (AFK) hoặc rời khỏi chỗ ngồi.
- Ghi nhận thời gian làm việc thực tế.
- Lưu trữ và hiển thị lịch sử hoạt động theo ngày.

Hệ thống có thể kết hợp với **camera**, **cảm biến khoảng cách**, hoặc **loadcell HX711** để nhận biết hành vi và tư thế làm việc, từ đó tạo báo cáo trực quan qua giao diện web.

---

## ⚙️ Tính năng chính
✅ Giám sát hành vi làm việc theo thời gian thực.  
✅ Phát hiện khi nhân viên rời chỗ hoặc không hoạt động.  
✅ Lưu trữ dữ liệu vào cơ sở dữ liệu SQLite.  
✅ Giao diện web hiển thị thông tin, lịch sử và thống kê.  
✅ Hỗ trợ cảm biến Loadcell (HX711) cho ứng dụng vật lý.  
✅ Dễ dàng mở rộng, sao lưu và khôi phục dữ liệu.  

---

## 🧱 Cấu trúc thư mục
WorkBehavior Monitor/
├─ Backup-2/
├─ Backup-3/
├─ Backup-4/
├─ Backup-5/
├─ HX711 Loadcell/
│ ├─ hx711.py
│ └─ main.py
├─ project/
│ ├─ database.py
│ ├─ distance_utils.py
│ ├─ session_monitor.py
│ ├─ static/
│ │ └─ style.css
│ ├─ templates/
│ │ ├─ history.html
│ │ └─ index.html
│ ├─ test_webcam_index.py
│ └─ webserver.py
└─ README.md

- `project/`: chứa mã nguồn chính của hệ thống web và xử lý dữ liệu.  
- `HX711 Loadcell/`: module xử lý cảm biến đo lực / trọng lượng.  
- `Backup-*`: các bản sao lưu mã nguồn cũ để tham khảo.  
- `static/` và `templates/`: chứa giao diện web (CSS, HTML).  
- `database.py`: quản lý cơ sở dữ liệu SQLite.  
- `webserver.py`: chạy server Flask hiển thị giao diện web.  

---

## 💻 Cài đặt & Thiết lập

### 1. Clone dự án
```bash
git clone https://github.com/NamHaiIT2HUST/WorkBehavior-Monitor.git
cd WorkBehavior-Monitor

### 2. Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate        # Windows
# hoặc
source venv/bin/activate    # Linux/Mac


