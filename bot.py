import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = "https://efhqbzdnrtifqjqlqseb.supabase.co"

SUPABASE_ANON_KEY = "sb_publishable_jnycTCgXRMrluvwJORd_4g_B7ojwi9R"


# ============================================================
# TELEGRAM
# ============================================================

# Token lấy từ GitHub Secrets
BOT_TOKEN = os.getenv("8841904683:AAFDQmAuhcoWv26p_5TC_tQV9zhdaXbNoCk")

# ID nhóm Telegram
GROUP_CHAT_ID = "-1004446959502"


# ============================================================
# TIME
# ============================================================

TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# 07:00 - 12:00 - 17:00 - 22:00
DROP_HOURS = [7, 12, 17, 22]

LABEL = "FeedBack @ShinnThieuu"


# ============================================================
# KIỂM TRA TOKEN
# ============================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN chưa được thiết lập trong GitHub Secrets."
    )


# ============================================================
# TẠO KEY
# ============================================================

def create_keys():

    url = (
        f"{SUPABASE_URL}"
        "/rest/v1/rpc/create_shinn_key"
    )

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "p_role": "Member",
        "p_count": 5,
        "p_hours": 1,
        "p_label": LABEL,
    }

    print("[INFO] Đang kết nối Supabase...")

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    print(
        "[INFO] Supabase HTTP:",
        response.status_code
    )

    if not response.ok:
        print("[ERROR] Supabase response:")
        print(response.text)

    response.raise_for_status()

    data = response.json()

    print("[INFO] Đã nhận dữ liệu từ Supabase.")

    # RPC trả về danh sách key
    if isinstance(data, list):

        if len(data) == 0:
            raise RuntimeError(
                "Supabase không trả về key."
            )

        return "\n".join(
            f"`{str(key)}`"
            for key in data
        )

    # RPC trả về một giá trị
    return f"`{str(data).replace(chr(34), '')}`"


# ============================================================
# GỬI TELEGRAM
# ============================================================

def send_message(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": GROUP_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    print("[INFO] Đang gửi tin nhắn Telegram...")

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    print(
        "[INFO] Telegram HTTP:",
        response.status_code
    )

    if not response.ok:
        print("[ERROR] Telegram response:")
        print(response.text)

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API lỗi: {result}"
        )

    print("[SUCCESS] Đã gửi tin nhắn Telegram.")


# ============================================================
# NỘI DUNG TIN NHẮN
# ============================================================

def build_message(keys):

    return f"""🎁 *SHINN CHEAT TEST KEYS*

{keys}

🇻🇳 *KEY TEST*
• 5 key miễn phí
• Hiệu lực: 1 giờ
• 1 thiết bị / key
• Owner: FeedBack @ShinnThieuu

🇺🇸 *TEST KEYS*
• 5 free keys
• Valid for 1 hour
• 1 device per key
• Owner: FeedBack @ShinnThieuu
"""


# ============================================================
# MAIN
# ============================================================

def main():

    now = datetime.now(TZ)

    print("=" * 55)

    print(
        "[INFO] Giờ Việt Nam:",
        now.strftime("%Y-%m-%d %H:%M:%S")
    )

    print(
        "[INFO] Giờ phát:",
        DROP_HOURS
    )

    print("=" * 55)

    # GitHub Actions truyền biến này khi bấm
    # Run workflow thủ công.
    manual_run = os.getenv("MANUAL_RUN", "false").lower() == "true"

    # Nếu chạy tự động thì chỉ cho phép các giờ quy định.
    # Nếu bấm Run workflow thì cho phép chạy test ngay.
    if not manual_run:

        if now.hour not in DROP_HOURS:
            print("[INFO] Chưa đến giờ phát key.")
            print("[INFO] Kết thúc.")
            return

    else:
        print("[INFO] Đang chạy TEST thủ công.")

    # --------------------------------------------------------
    # TẠO KEY
    # --------------------------------------------------------

    print("[INFO] Đang tạo 5 key...")

    keys = create_keys()

    print("[SUCCESS] Đã tạo key.")

    # --------------------------------------------------------
    # TẠO MESSAGE
    # --------------------------------------------------------

    message = build_message(keys)

    # --------------------------------------------------------
    # GỬI TELEGRAM
    # --------------------------------------------------------

    send_message(message)

    print("=" * 55)
    print("[SUCCESS] HOÀN TẤT")
    print("=" * 55)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()