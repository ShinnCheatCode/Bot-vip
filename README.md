# Bot key 1 giờ — GitHub Actions + Supabase + Telegram

Bot không đọc / không trả lời tin nhắn hay lệnh.
Mỗi 5 tiếng (05:00, 10:00, 15:00, 20:00 giờ VN) tạo đúng 1 key 1 giờ trên bảng public.keys rồi gửi group -1004446959502.

Không tạo 1d / 3d / 7d / 30d.

## Publishable key không đủ

sb_publishable_... chỉ đọc được bảng keys. INSERT bị RLS chặn.
Cần secret key (sb_secret_... hoặc service_role) trong GitHub Secrets.

## Secrets

TELEGRAM_BOT_TOKEN = token BotFather
SUPABASE_SECRET_KEY = secret / service_role

URL và Chat ID đã gắn trong workflow.

## Telegram

Thêm bot vào group, cho quyền gửi tin. Không bật webhook/polling nên bot im lặng với mọi lệnh.
