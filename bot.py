import os
import html
import requests


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = "https://efhqbzdnrtifqjqlqseb.supabase.co"

SUPABASE_ANON_KEY = (
    "sb_publishable_jnycTCgXRMrluvwJORd_4g_B7ojwi9R"
)


# ============================================================
# TELEGRAM
# ============================================================

# Lấy BOT TOKEN từ GitHub Secrets
BOT_TOKEN = os.getenv("8841904683:AAFDQmAuhcoWv26p_5TC_tQV9zhdaXbNoCk")

# ID nhóm Telegram
GROUP_CHAT_ID = "-1004446959502"


# ============================================================
# CONFIG
# ============================================================

LABEL = "FeedBack @ShinnThieuu"


# ============================================================
# KIỂM TRA CONFIG
# ============================================================

def check_config():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN chưa được thiết lập trong GitHub Secrets."
        )

    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL chưa được thiết lập."
        )

    if not SUPABASE_ANON_KEY:
        raise RuntimeError(
            "SUPABASE_ANON_KEY chưa được thiết lập."
        )

    if not GROUP_CHAT_ID:
        raise RuntimeError(
            "GROUP_CHAT_ID chưa được thiết lập."
        )


# ============================================================
# TẠO KEY TỪ SUPABASE
# ============================================================

def create_keys():

    url = (
        f"{SUPABASE_URL}/rest/v1/rpc/create_shinn_key"
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
        f"[INFO] Supabase HTTP: {response.status_code}"
    )

    if not response.ok:
        print("[ERROR] Supabase response:")
        print(response.text)

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Supabase trả về dữ liệu không phải JSON."
        ) from exc

    print("[INFO] Đã nhận dữ liệu từ Supabase.")

    # --------------------------------------------------------
    # Trường hợp RPC trả về danh sách
    # --------------------------------------------------------

    if isinstance(data, list):

        if not data:
            raise RuntimeError(
                "Supabase không trả về key nào."
            )

        formatted_keys = []

        for item in data:

            # Nếu item là object/dict
            if isinstance(item, dict):

                # Hỗ trợ một số dạng phổ biến
                key = (
                    item.get("key")
                    or item.get("license")
                    or item.get("code")
                    or item.get("value")
                )

                if key is None:
                    key = str(item)

            else:
                key = str(item)

            # Escape HTML để key không phá message Telegram
            key = html.escape(str(key))

            formatted_keys.append(
                f"<code>{key}</code>"
            )

        return "\n".join(formatted_keys)

    # --------------------------------------------------------
    # Trường hợp RPC trả về object/string
    # --------------------------------------------------------

    if isinstance(data, dict):

        key = (
            data.get("key")
            or data.get("license")
            or data.get("code")
            or data.get("value")
        )

        if key is not None:
            key = html.escape(str(key))
            return f"<code>{key}</code>"

    if isinstance(data, str):

        key = html.escape(data)

        if not key.strip():
            raise RuntimeError(
                "Supabase trả về key rỗng."
            )

        return f"<code>{key}</code>"

    # --------------------------------------------------------
    # Không nhận diện được dữ liệu
    # --------------------------------------------------------

    raise RuntimeError(
        f"Định dạng dữ liệu Supabase không được hỗ trợ: "
        f"{type(data).__name__}"
    )


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
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    print("[INFO] Đang gửi tin nhắn Telegram...")

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    print(
        f"[INFO] Telegram HTTP: {response.status_code}"
    )

    if not response.ok:
        print("[ERROR] Telegram response:")
        print(response.text)

    response.raise_for_status()

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Telegram trả về dữ liệu không phải JSON."
        ) from exc

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API lỗi: {result}"
        )

    print("[SUCCESS] Đã gửi tin nhắn Telegram.")


# ============================================================
# NỘI DUNG TIN NHẮN
# ============================================================

def build_message(keys):

    return f"""🎁 <b>SHINN CHEAT TEST KEYS</b>

{keys}

🇻🇳 <b>KEY TEST</b>
• 5 key miễn phí
• Hiệu lực: 1 giờ
• 1 thiết bị / key
• Owner: FeedBack @ShinnThieuu

🇺🇸 <b>TEST KEYS</b>
• 5 free keys
• Valid for 1 hour
• 1 device per key
• Owner: FeedBack @ShinnThieuu
"""


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("[INFO] SHINN TEST KEY BOT")
    print("[INFO] Bắt đầu chạy...")
    print("=" * 60)

    # Kiểm tra cấu hình
    check_config()

    # --------------------------------------------------------
    # TẠO 5 KEY
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

    # --------------------------------------------------------
    # HOÀN TẤT
    # --------------------------------------------------------

    print("=" * 60)
    print("[SUCCESS] HOÀN TẤT")
    print("=" * 60)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()