## 1. Cơ chế hoạt động & Lý do lựa chọn (Architecture & Rationale)

Hệ thống hoạt động theo mô hình **Edge AI + Central Storage**. Đây là lựa chọn tối ưu nhất cho bài toán giám sát từ xa:

### A. Tại sao dùng Edge AI (Xử lý trên máy học sinh)?
*   **Tiết kiệm băng thông (99%):** Nếu gửi video trực tiếp về máy bạn, ngrok sẽ bị lag ngay lập tức và tốn rất nhiều dung lượng. Bằng cách xử lý tại chỗ, máy học sinh chỉ gửi về một file ảnh cực nhẹ khi có vi phạm.
*   **Tính riêng tư:** Video gốc không bao giờ rời khỏi máy học sinh. Chỉ có ảnh bằng chứng vi phạm mới được gửi đi.
*   **Khả năng mở rộng:** Máy PC của bạn không phải xử lý AI, nên nó có thể nhận log từ 100 học sinh cùng lúc mà không bị treo máy.

### B. Cơ chế Proxy và Phát triển nhanh (Fast Development)
Để thuận tiện nhất khi đang phát triển (code đến đâu web đổi đến đó), chúng ta sử dụng cơ chế **Vite Proxy**:
*   **Vite (Cổng 5173):** Chạy giao diện web, tự động nhận diện thay đổi code (HMR).
*   **FastAPI (Cổng 8000):** Chạy xử lý logic backend, nhận log và lưu trữ dữ liệu.
*   **Proxy:** Mọi yêu cầu từ web gửi đến `/camera` hoặc `/api` sẽ được Vite tự động chuyển sang Backend (8000) một cách trong suốt.

---

## 2. Cách vận hành hệ thống (Step-by-Step)

Để hệ thống hoạt động ổn định và dễ sửa code nhất, hãy thực hiện theo đúng thứ tự sau:

### Bước 1: Chạy Frontend (Giao diện)
Mở terminal tại thư mục `frontend`:
```bash
npm run dev
```
*Lúc này giao diện web sẽ sẵn sàng tại cổng **5173**.*

### Bước 2: Chạy Backend (Máy chủ)
Mở terminal tại thư mục `backend`:
```bash
uv run uvicorn src.main:app --reload
```
*Backend sẽ chạy tại cổng **8000**. Mọi giao tiếp giữa Frontend và Backend đã được cấu hình tự động qua Proxy.*

### Bước 3: Mở cổng ra Internet (Ngrok)
Mở một terminal mới (tại thư mục gốc dự án):
```bash
ngrok http 5173
```
*Bạn sẽ nhận được một đường link có dạng `https://xxx.ngrok-free.dev`. Bạn chỉ cần gửi link này cho học sinh. Khi học sinh truy cập, Ngrok sẽ vào cổng 5173, và từ 5173 nó sẽ tự "nối" sang backend cổng 8000 cho bạn.*

---

## 3. Cách chạy thử (Testing)

1.  **Trên máy Laptop/Điện thoại khác:**
    *   Truy cập vào đường link ngrok bạn vừa nhận được ở Bước 3.
    *   Nếu trình duyệt hiện trang cảnh báo "You are about to visit...", hãy nhấn **"Visit Site"**.
    *   Cho phép trình duyệt truy cập Camera. (Đảm bảo camera đang hoạt động bình thường).
2.  **Thực hiện hành vi vi phạm:**
    *   **Trường hợp 1:** Bạn quay mặt đi chỗ khác hoặc che camera để mặt biến mất khỏi khung hình.
    *   **Trường hợp 2:** Có thêm một người nữa ghé mặt vào khung hình cùng bạn.
3.  **Kiểm tra kết quả trên máy PC:**
    *   Kiểm tra thư mục `backend/storage/violation_captures/` -> Bạn sẽ thấy ảnh bằng chứng được lưu tại đó với thời gian thực.
    *   Kiểm tra file `backend/storage/violations.json` -> Bạn sẽ thấy nhật ký chi tiết các lần vi phạm.

---

## 4. Các lưu ý quan trọng

*   **Chỉ ngrok cổng 5173:** Bạn chỉ cần chạy ngrok cho cổng của Frontend (5173). Không cần chạy cho 8000 vì Vite đã làm nhiệm vụ trung gian rồi.
*   **Hot Reload:** Bạn có thể vừa sửa code Frontend vừa xem kết quả ngay lập tức trên link Ngrok mà không cần chạy lại lệnh nào.*   **Xóa Log:** Nếu muốn xóa dữ liệu cũ để test mới, bạn chỉ cần xóa các file trong `storage/violation_captures` và xóa nội dung trong `violations.json`.
### 5. Cách chạy thử mô hình Backend (Tùy chọn)
Nếu bạn muốn kiểm tra khả năng nhận diện trực tiếp từ phía Backend (không qua AI của học sinh), bạn có thể truy cập:
- `http://localhost:8000/tests/websocket_test.html` (chạy local)
- Hoặc mở trực tiếp file `backend/tests/websocket_test.html` trong trình duyệt.
*Lưu ý: Bạn cần cấu hình FastAPI để phục vụ thư mục tests nếu muốn mở qua URL.*
