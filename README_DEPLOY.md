## 1. Cơ chế hoạt động & Lý do lựa chọn (Architecture & Rationale)

Hệ thống hoạt động theo mô hình **Edge AI + Central Storage**. Đây là lựa chọn tối ưu nhất cho bài toán giám sát từ xa:

### A. Tại sao dùng Edge AI (Xử lý trên máy học sinh)?
*   **Tiết kiệm băng thông (99%):** Nếu gửi video trực tiếp về máy bạn, ngrok sẽ bị lag ngay lập tức và tốn rất nhiều dung lượng. Bằng cách xử lý tại chỗ, máy học sinh chỉ gửi về một file ảnh cực nhẹ khi có vi phạm.
*   **Tính riêng tư:** Video gốc không bao giờ rời khỏi máy học sinh. Chỉ có ảnh bằng chứng vi phạm mới được gửi đi.
*   **Khả năng mở rộng:** Máy PC của bạn không phải xử lý AI, nên nó có thể nhận log từ 100 học sinh cùng lúc mà không bị treo máy.

### B. Vấn đề "404 Not Found" trước đây và cách giải quyết
Trong quá trình phát triển, chúng ta đã gặp lỗi `404 Not Found` hoặc `Unexpected token '<'` khi dùng laptop truy cập qua Ngrok.

*   **Nguyên nhân:** Trước đây chúng ta dùng 2 server riêng biệt (Vite cổng 5173 và FastAPI cổng 8000). Vite dùng một cơ chế gọi là "Proxy" để đẩy dữ liệu sang cổng 8000. Tuy nhiên, khi đi qua đường ống Ngrok, cơ chế Proxy này thường xuyên bị lỗi "kẹt" hoặc không nhận diện được đường dẫn, dẫn đến việc request bị chặn lại tại Vite và trả về trang HTML lỗi.
*   **Giải pháp (Consolidated Serving):** Chúng ta đã dẹp bỏ server Vite khi chạy thực tế. Toàn bộ Frontend được "đóng gói" (build) và đưa trực tiếp vào Backend FastAPI. 
    *   Bây giờ, mọi thứ chạy trên duy nhất **cổng 8000**.
    *   Request từ máy học sinh đi thẳng vào Backend, không qua bất kỳ lớp trung gian nào nữa. Đây là cách làm ổn định nhất cho các ứng dụng dùng Tunnel như Ngrok.

### C. Ngrok và Header đặc biệt
Ngrok thường hiện trang cảnh báo "Abuse Detection" làm gián đoạn việc gửi dữ liệu. Chúng ta đã giải quyết bằng cách:
*   Yêu cầu `ngrok-skip-browser-warning: true` trong mỗi request từ Frontend để "vượt rào" cảnh báo này một cách tự động.

---

## 2. Cách vận hành hệ thống (Step-by-Step)

Để hệ thống hoạt động ổn định nhất, hãy thực hiện theo đúng thứ tự sau trên máy PC của bạn:

### Bước 1: Đóng gói Frontend (Chỉ cần làm 1 lần khi có thay đổi code)
Mở terminal tại thư mục `frontend`:
```bash
npm run build
```
*Lệnh này sẽ tạo ra thư mục `dist` chứa giao diện web đã được tối ưu hóa.*

### Bước 2: Chạy Backend (Máy chủ)
Mở terminal tại thư mục `backend`:
```bash
uv run uvicorn src.main:app --reload
```
*Lúc này server sẽ chạy tại cổng **8000**. Nó sẽ tự động phục vụ cả giao diện web từ thư mục `dist` vừa build.*

### Bước 3: Mở cổng ra Internet (Ngrok)
Mở một terminal mới (tại bất kỳ đâu):
```bash
ngrok http 8000
```
*Bạn sẽ nhận được một đường link có dạng `https://xxx.ngrok-free.dev`. Đây chính là link bạn sẽ gửi cho học sinh.*

---

## 3. Cách chạy thử (Testing)

1.  **Trên máy Laptop/Điện thoại khác:**
    *   Truy cập vào đường link ngrok bạn vừa nhận được ở Bước 3.
    *   Nếu trình duyệt hiện trang cảnh báo "You are about to visit...", hãy nhấn **"Visit Site"**.
    *   Cho phép trình duyệt truy cập Camera.
2.  **Thực hiện hành vi vi phạm:**
    *   **Trường hợp 1:** Bạn quay mặt đi chỗ khác hoặc che camera để mặt biến mất khỏi khung hình.
    *   **Trường hợp 2:** Có thêm một người nữa ghé mặt vào khung hình cùng bạn.
3.  **Kiểm tra kết quả trên máy PC:**
    *   Kiểm tra thư mục `backend/storage/violation_captures/` -> Bạn sẽ thấy ảnh bằng chứng được lưu tại đó với thời gian thực.
    *   Kiểm tra file `backend/storage/violations.json` -> Bạn sẽ thấy nhật ký chi tiết các lần vi phạm.

---

## 4. Các lưu ý quan trọng

*   **Một cổng duy nhất:** Bạn chỉ cần chạy ngrok cho cổng **8000**. Không cần chạy ngrok cho cổng 5173 hay chạy `npm run dev` khi đã build xong.
*   **Xóa Log:** Nếu muốn xóa dữ liệu cũ để test mới, bạn chỉ cần xóa các file trong `storage/violation_captures` và xóa nội dung trong `violations.json`.
*   **Tốc độ mạng:** Ảnh chụp vi phạm đã được nén lại (320x240) nên việc gửi qua ngrok rất nhanh, không làm lag máy học sinh.
