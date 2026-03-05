# 🚀 AWS Integration Guide — AWS-FCJ-Project

## Tổng quan 3 dịch vụ bắt buộc

> 📌 **Email / OTP**: Tạm thời bỏ qua — dự kiến sẽ không dùng OTP trong tương lai.

| # | Dịch vụ | Thay thế cho | Trạng thái |
|---|---|---|---|
| 1 | **Amazon S3** | Local `uploads/` folder | 🔴 Cần làm ngay |
| 2 | **Amazon ElastiCache (Redis)** | `redis://localhost:6379` | 🔴 Cần làm ngay |
| 3 | **MongoDB Atlas** | — | ✅ Đã có sẵn |
| ~~4~~ | ~~Amazon SES (Email)~~ | ~~Gmail SMTP~~ | ⏸️ Tạm bỏ qua |

---

## 🟥 Bước 0 — Cài đặt prerequisites

```bash
# Cài AWS CLI
# Windows: https://awscli.amazonaws.com/AWSCLIV2.msi

# Cấu hình credentials
aws configure
# AWS Access Key ID: <key của IAM user>
# AWS Secret Access Key: <secret>
# Default region: ap-southeast-1
# Default output format: json
```

---

## 🔴 #1 — Amazon S3 (File Uploads)

**Vì sao bắt buộc:** Thư mục `uploads/` hiện chỉ lưu local trên EC2 → **mất hết khi restart container**.

### A. Cách 1 — Dùng Terraform (Khuyến nghị)

Terraform đã được cập nhật sẵn, chỉ cần chạy:

```bash
cd .github/terraform

# Tạo file vars (copy từ example)
cp terraform.tfvars.example terraform.tfvars
# Điền giá trị thực vào terraform.tfvars

terraform init
terraform plan
terraform apply
```

Sau khi apply xong, lấy credentials:
```bash
terraform output backend_aws_access_key_id
terraform output backend_aws_secret_access_key
```

### B. Cách 2 — Tạo thủ công trên AWS Console

1. **AWS Console → S3 → Create bucket**
   - Bucket name: `aws-fcj-project-uploads`
   - Region: `ap-southeast-1`
   - Block all public access: ✅

2. **IAM → Policies → Create policy**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
       "Resource": [
         "arn:aws:s3:::aws-fcj-project-uploads",
         "arn:aws:s3:::aws-fcj-project-uploads/*"
       ]
     }]
   }
   ```

3. **IAM → Users → Create user** → tên: `aws-fcj-backend`
   → Gắn policy → **Create access key** → lưu lại

### C. Thêm vào `.env`

```env
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=aws-fcj-project-uploads
```

### D. Sử dụng S3 trong code

Module S3 đã được tạo tại `backend/src/aws/s3_service.py`:

```python
from src.aws.s3_service import upload_file, get_presigned_url, delete_file

# Upload file
s3_key = upload_file(file_bytes, "document.pdf", content_type="application/pdf")

# Tạo link download (tự hết hạn sau 1 giờ)
url = get_presigned_url(s3_key, expires_in=3600)

# Xóa file
delete_file(s3_key)
```

---

## 🔴 #2 — Amazon ElastiCache Redis (OTP / Session Cache)

**Vì sao bắt buộc:** `.env` đang có `REDIS_URL=redis://localhost:6379` → **localhost không tồn tại trên EC2 production**.

> ⚠️ **Lưu ý VPC:** ElastiCache chỉ truy cập được từ **cùng VPC với EC2**.
> Khi tạo, nhớ chọn đúng VPC.

### A. Tạo ElastiCache Cluster

1. **AWS Console → ElastiCache → Create cluster**
2. Chọn **Redis OSS (Serverless)** hoặc **Redis OSS Cluster**
3. Điền:
   - Cluster name: `aws-fcj-redis`
   - Node type: `cache.t3.micro` (~$12/tháng)
   - Number of replicas: `0` (dev) / `1` (prod)
   - **VPC: chọn cùng VPC với EC2** ← Quan trọng!
   - Subnet group: tạo mới hoặc dùng mặc định
4. **Create** → Chờ ~5 phút
5. Sau khi tạo xong: copy **Primary endpoint**
   - Ví dụ: `aws-fcj-redis.abc123.cache.amazonaws.com:6379`

### B. Mở Security Group

EC2 cần được phép kết nối tới Redis:

1. **EC2 → Security Groups** → chọn SG của EC2
2. **Inbound rules → Edit** → Add rule:
   - Type: `Custom TCP`
   - Port: `6379`
   - Source: Security Group của ElastiCache (hoặc CIDR của VPC)

### C. Cập nhật `.env`

```env
# Bỏ localhost:
# REDIS_URL=redis://localhost:6379

# Thêm ElastiCache endpoint:
REDIS_URL=redis://aws-fcj-redis.abc123.cache.amazonaws.com:6379
```

Code `otp_storage.py` đã được cập nhật để dùng Redis thay MongoDB, không cần sửa thêm gì.

---

## ✅ #3 — MongoDB Atlas (Đã có, không cần làm gì)

```env
MONGO_URI=mongodb+srv://minfuz391_db_user:admin@cluster0.ugggr32.mongodb.net/aws-fcj-project
```

✅ **Không cần thay đổi gì!** Atlas là managed service hoạt động tốt với AWS EC2.

---

## ⏸️ Email / SES — Tạm bỏ qua

Email và OTP **tạm thời giữ nguyên** (Gmail SMTP), vì:
- Dự kiến sẽ bỏ OTP trong tương lai
- Không cần đầu tư SES lúc này

Code `email_service.py` vẫn hoạt động với Gmail như bình thường.

---

## 🔑 GitHub Secrets cần thêm

Vào **GitHub repo → Settings → Secrets → Actions → New secret**:

| Secret Name | Giá trị | Dùng cho |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | IAM Access Key | S3 uploads |
| `AWS_SECRET_ACCESS_KEY` | IAM Secret Key | S3 uploads |
| `S3_BUCKET_NAME` | `aws-fcj-project-uploads` | S3 uploads |
| `REDIS_URL` | ElastiCache endpoint | OTP / cache |

> Thêm các secrets này vào `BACKEND_ENV_FILE` (secret tổng) được dùng trong `deploy-ec2.yml`.

---

## 📋 Checklist tích hợp

- [ ] Chạy `terraform apply` (hoặc tạo thủ công trên Console)
- [ ] Tạo S3 bucket `aws-fcj-project-uploads`
- [ ] Tạo IAM user với S3 policy → lấy Access Key
- [ ] Tạo ElastiCache Redis cluster **cùng VPC với EC2**
- [ ] Mở Security Group port 6379 cho EC2
- [ ] Cập nhật `.env` với `AWS_*`, `S3_BUCKET_NAME`, `REDIS_URL`
- [ ] Thêm secrets vào GitHub Actions
- [ ] Deploy lại backend (`workflow_dispatch` trên GitHub Actions)
- [ ] Kiểm tra `/health` endpoint sau deploy
