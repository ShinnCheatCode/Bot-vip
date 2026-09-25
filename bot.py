#!/usr/bin/env python3
from __future__ import annotations

import sys
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

SUPABASE_URL = "https://efhqbzdnrtifqjqlqseb.supabase.co"
SUPABASE_API_KEY = "sb_publishable_jnycTCgXRMrluvwJORd_4g_B7ojwi9R"
TELEGRAM_BOT_TOKEN = "8841904683:AAFDQmAuhcoWv26p_5TC_tQV9zhdaXbNoCk"
TELEGRAM_CHAT_ID = "-1004446959502"

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
KEY_TTL_HOURS = 1
KEYS_PER_DROP = 5
KEY_MIN = 1
KEY_MAX = 50
KEY_PATTERN = re.compile(r"^Shinn-Cheat-Test(\\d+)$")
KEY_LABEL = "FeedBack @ShinnThieuu"


def now_vn():
    return datetime.now(tz=VN_TZ)


def now_utc():
    return datetime.now(tz=timezone.utc)


def headers(prefer=None):
    h = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def parse_iso(value):
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_test_keys():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/keys",
        headers=headers(),
        params={
            "select": "id,key,expires_at,created_at",
            "key": "like.Shinn-Cheat-Test*",
            "order": "created_at.desc",
            "limit": "200",
        },
        timeout=30,
    )
    data = r.json()
    if r.status_code >= 300:
        raise RuntimeError(data)
    return data


def pick_next(rows, now):
    used = set()
    for row in rows:
        m = KEY_PATTERN.match(row.get("key") or "")
        if not m:
            continue
        num = int(m.group(1))
        exp = parse_iso(row.get("expires_at"))
        if KEY_MIN <= num <= KEY_MAX and (exp is None or exp > now):
            used.add(num)
    free = [n for n in range(KEY_MIN, KEY_MAX + 1) if n not in used]
    if len(free) < KEYS_PER_DROP:
        raise RuntimeError("Het slot Test1-50. Xoa key het han.")
    return free[:KEYS_PER_DROP]


def create_key(number, expires):
    payload = {
        "key": f"Shinn-Cheat-Test{number}",
        "device_id": None,
        "max_devices": 1,
        "expires_at": expires.isoformat(),
        "activated_at": None,
        "is_used": False,
        "is_vip": False,
        "role": "member",
        "label": KEY_LABEL,
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/keys",
        headers=headers(prefer="return=representation"),
        json=payload,
        timeout=30,
    )
    data = r.json()
    if r.status_code >= 300:
        raise RuntimeError(data)
    return data[0] if isinstance(data, list) else data


def build_message(rows):
    block = "\\n".join(f"{i}. {row['key']}" for i, row in enumerate(rows, 1))
    exp = parse_iso(rows[0].get("expires_at")) if rows else None
    exp_txt = exp.astimezone(VN_TZ).strftime("%H:%M %d/%m/%Y") if exp else "-"
    return (
        "SHINN CHEAT — Free test keys\\n\\n"
        f"{block}\\n\\n"
        "VI\\n"
        "• 5 key / lần • hạn 1 giờ • 1 thiết bị\\n"
        "• Cập nhật mỗi 5 giờ\\n"
        "• Thêm thành viên để nhận key free\\n"
        "• Key dài hạn / tạo key: @ShinnThieuu\\n\\n"
        "EN\\n"
        "• 5 keys per drop • 1 hour • 1 device\\n"
        "• Posted every 5 hours\\n"
        "• Add members to get free keys\\n"
        "• Long-term / create keys: @ShinnThieuu\\n\\n"
        f"Hết hạn: {exp_txt} (VN)"
    )


def send_telegram(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    data = r.json()
    if not r.ok or not data.get("ok"):
        raise RuntimeError(data)
    return data


def run_once():
    now = now_vn()
    print("[info]", now.isoformat())
    if not (5 <= now.hour < 24):
        print("[skip] ngoai 5h-24h")
        return 0
    utc = now_utc()
    expires = utc + timedelta(hours=KEY_TTL_HOURS)
    nums = pick_next(fetch_test_keys(), utc)
    print("[info] tao", nums)
    rows = [create_key(n, expires) for n in nums]
    send_telegram(build_message(rows))
    print("[ok] da gui group")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run_once())
    except Exception as e:
        print("[error]", e, file=sys.stderr)
        sys.exit(1)