# AWS-FCJ-Project Backend

## 🤖 Giới Thiệu
Backend API kết hợp:
1. **AI Multi-Agent System** - Hệ thống AI agents chuyên biệt
2. **Authentication System** - Xác thực người dùng với Email OTP

## ✨ Tính Năng

### 🔐 Authentication (Simplified)
- ✅ **Register** với Email + Password
- ✅ **Email OTP Verification** (lưu trong MongoDB)
- ✅ **Login** với Email + Password (session-based)
- ✅ **Password Reset** với Email OTP
- ❌ **Không dùng JWT** - Dùng session-based auth
- ❌ **Không dùng TOTP 2FA** - Chỉ Email OTP
- ❌ **Không dùng Redis** - OTP lưu trong MongoDB

### 🤖 AI Agents
- **Orchestrator Agent** - Điều phối câu hỏi
- **Specialized Agents**: Math, Physics, Literature, Quiz, Tutor, Web Search
- **Conversation Memory** - Lưu trong MongoDB
- **Web Search** - Tavily integration

## 🛠️ Tech Stack

**Core:**
- FastAPI + Pydantic
- Python 3.11.3

**Authentication:**
- Session-based (SessionMiddleware)
- Email OTP (MongoDB storage)
- Bcrypt password hashing
- SlowAPI rate limiting

**AI & Database:**
- Pydantic AI + LiteLLM
- MongoDB (users, conversations, OTPs)
- Tavily Search
- Logfire Monitoring

## 📋 Yêu Cầu
- Python 3.11.3
- MongoDB (local hoặc Atlas)
- Gmail account (for OTP emails)
- API Keys: OpenAI/Gemini/Claude

## 🚀 Cài Đặt

### 1. Cài đặt Dependencies
```bash
# Cài uv (nếu chưa có)
pip install uv

# Sync dependencies
uv sync
```

### 2. Thiết Lập MongoDB
```bash
# Local MongoDB
mongod

# Hoặc dùng MongoDB Atlas free tier
```

### 3. Thiết Lập Google App Password
1. Truy cập [Google Account Security](https://myaccount.google.com/security)
2. Bật **2-Step Verification**
3. Tạo **App Password** cho Mail
4. Copy password 16 ký tự

### 4. Cấu Hình Environment
```bash
cp .env.example .env
# Edit .env với thông tin của bạn
```

Chỉnh sửa `.env`:
```env
# LLM
OPENAI_API_KEY=your_key
AGENTS_CONFIG_PATH=config/agents.yaml
LLMS_CONFIG_PATH=config/llms.yaml

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=proctoring_db

# Email OTP
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password

# Session Secret
SECRET_KEY=your-super-secret-key-change-this
```

### 5. Chạy Server
```bash
uv run uvicorn src.main:app --reload --port 8000
```

Server: http://localhost:8000  
Docs: http://localhost:8000/docs

## 📡 API Endpoints

### Authentication

#### 1. Register
```bash
POST /register
{
  "email": "user@example.com",
  "password": "your_password"
}
# Response: "User registered. Please verify email."
# Check email for 6-digit OTP
```

#### 2. Verify Email
```bash
POST /verify-email
{
  "email": "user@example.com",
  "otp": "123456"
}
# Response: "Email verified successfully. You can now login."
```

#### 3. Login
```bash
POST /login
{
  "email": "user@example.com",
  "password": "your_password"
}
# Response: "Login successful"
# Creates session cookie automatically
```

#### 4. Logout
```bash
POST /logout
# Response: "Logged out successfully"
```

#### 5. Forgot Password
```bash
POST /forgot-password
{
  "email": "user@example.com"
}
# Send OTP to email
```

#### 6. Reset Password
```bash
POST /reset-password
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "new_secure_password"
}
```

#### 7. Protected Route (Example)
```bash
GET /protected
# Requires active session
# Response: { "message": "You have access", "user_email": "..." }
```

### AI Agent

```bash
POST /unified-agent/ask
{
  "question": "Giải phương trình x^2 + 5x + 6 = 0",
  "conversation_id": "user123"
}
```

## 🏗️ Cấu Trúc Project

```
backend/
├── config/
│   ├── agents.yaml
│   └── llms.yaml
├── src/
│   ├── auth/
│   │   ├── auth_utils.py         # Password hashing, OTP generation
│   │   ├── email_service.py      # Email sending
│   │   ├── otp_storage.py        # MongoDB OTP storage
│   │   ├── session_handler.py    # Session management
│   │   └── dependencies.py
│   ├── routers/
│   │   ├── auth/
│   │   │   ├── register.py       # Register + verify
│   │   │   ├── login.py          # Login + logout
│   │   │   ├── password.py       # Password reset
│   │   │   └── protected.py      # Protected routes
│   │   └── unified_agent_routes.py
│   ├── models/
│   │   └── auth_models.py
│   ├── schemas/
│   │   └── auth_schemas.py
│   ├── crew/                      # AI agents
│   ├── memory/                    # Conversation storage
│   ├── search_services/           # Web search
│   ├── app_config.py
│   ├── database.py
│   └── main.py
├── .env.example
├── pyproject.toml
└── README.md
```

## 🔒 Security Features

✅ **Password Hashing** - Bcrypt  
✅ **Email OTP** - 6 digits, 5 min expiry  
✅ **Session-based Auth** - Secure cookies  
✅ **Rate Limiting** - SlowAPI  
✅ **CORS** - Configurable  
❌ **No Redis dependency**  
❌ **No JWT complexity**  
❌ **No TOTP 2FA** (simplified)

## 🧪 Testing

### Test Authentication Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 2. Check email for OTP, then verify
curl -X POST http://localhost:8000/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp":"123456"}'

# 3. Login (creates session)
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c cookies.txt

# 4. Access protected route
curl -X GET http://localhost:8000/protected -b cookies.txt

# 5. Logout
curl -X POST http://localhost:8000/logout -b cookies.txt
```

## 📊 Comparison: Before vs After

| Feature | Old (JWT+Redis+TOTP) | New (Session+MongoDB) |
|---------|----------------------|------------------------|
| **Auth Method** | JWT Tokens | Session Cookies |
| **2FA** | TOTP (Google Auth) | Email OTP only |
| **OTP Storage** | Redis | MongoDB |
| **Dependencies** | redis, pyotp, python-jose | Just passlib, slowapi |
| **Complexity** | High | Low |
| **Setup** | MongoDB + Redis + Email | MongoDB + Email |

## 🎯 Lợi Ích Của Session-based Auth

✅ **Đơn giản hơn** - Không cần JWT secret, refresh tokens  
✅ **Tự động hóa** - Browser handle cookies  
✅ **Bảo mật** - HttpOnly, Secure, SameSite cookies  
✅ **Dễ logout** - Clear session instantly  
✅ **Ít dependencies** - Không cần redis, pyotp, python-jose  

## 🔧 Troubleshooting

### Email OTP không gửi được
- Kiểm tra EMAIL_SENDER và EMAIL_PASSWORD trong `.env`
- Đảm bảo dùng Google App Password (16 ký tự)
- Kiểm tra 2-Step Verification đã bật

### Session không work
- Kiểm tra SECRET_KEY trong `.env`
- Browser phải cho phép cookies
- CORS settings phải đúng

### MongoDB connection error
- Kiểm tra MongoDB đang chạy: `mongosh`
- Check MONGO_URI trong `.env`

## 🌐 Deploy

### AWS EC2
```bash
# Setup như local + gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app
```

### Heroku/Render
- Dùng MongoDB Atlas
- Set environment variables
- Procfile: `web: uvicorn src.main:app --host 0.0.0.0 --port $PORT`

## 📝 License
MIT
