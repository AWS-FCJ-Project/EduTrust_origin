
#### 3.2. Chạy Redis Container
# Pull Redis image
docker pull redis:latest

# Chạy Redis container
docker run -d \
  --name aws-fcj-redis \
  -p 6379:6379 \
  redis:latest

# Kiểm tra Redis đang chạy
docker ps




### **Bước 5: Tạo Google App Password** 📧
Google App Password cần thiết để gửi email OTP qua Gmail SMTP.
#### 5.1. Bật 2-Step Verification
1. Truy cập [Google Account Security](https://myaccount.google.com/security)
2. Tìm phần **"2-Step Verification"**
3. Click **"Get started"** và làm theo hướng dẫn
4. Hoàn thành việc bật 2-Step Verification

#### 5.2. Tạo App Password
1. Sau khi bật 2-Step Verification, quay lại [Security](https://myaccount.google.com/security)
2. Tìm phần **"App passwords"** (ở mục 2-Step Verification)
3. Click vào **"App passwords"**
4. Chọn:
   - **Select app**: Mail
   - **Select device**: Other (Custom name)
   - Nhập tên: `AWS FCJ Backend`
5. Click **"Generate"**
6. Copy password 16 ký tự (dạng: `xxxx xxxx xxxx xxxx`)
7. Lưu password này vào `.env`

**Lưu ý**: App password chỉ hiện 1 lần, hãy copy ngay!



#### 9.2. Start Backend Server
uv run uvicorn src.main:app --reload --port 8000





✅ **Thành công!**

### **1. Đăng ký tài khoản**


curl -X 'POST' \
  'http://localhost:8000/register' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "your_password"
}'


**Response:**
```json
{
  "message": "User registered. Please verify email."
}
```

→ Kiểm tra email để lấy OTP (6 số)

### **2. Xác thực email**

```bash
curl -X 'POST' \
  'http://localhost:8000/verify-email' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "otp": "123456"
}'
```

**Response:**
```json
{
  "message": "Email verified",
  "totp_uri": "otpauth://totp/...",
  "totp_secret": "JBSWY3DPEHPK3PXP"
}
```

→ Quét `totp_uri` bằng Google Authenticator hoặc Authy

### **3. Đăng nhập**

```bash
curl -X 'POST' \
  'http://localhost:8000/login' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "your_password"
}'
```

**Response:**
```json
{
  "message": "Credentials valid. Please enter 2FA code."
}
```

### **4. Xác thực 2FA**

Mở Google Authenticator, lấy mã 6 số:

```bash
curl -X 'POST' \
  'http://localhost:8000/verify-2fa' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "totp_code": "123456"
}'


**Response:**
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}


