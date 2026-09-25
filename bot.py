#!/usr/bin/env python3
"""
Bot GitHub Actions: mỗi lần tạo 5 key 1 giờ (Shinn-Cheat-Test1..Test50)
rồi gửi vào group. Không polling, không trả lời lệnh / tin nhắn.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
ACTIVE_START_HOUR = 5
ACTIVE_END_HOUR = 24
KEY_TTL_HOURS = 1
KEYS_PER_DROP = 5
KEY_MIN = 1
KEY_MAX = 50
KEY_PATTERN = re.compile(r"^Shinn-Cheat-Test(\d+)$")

SUPABASE_URL = os.getenv(
    "SUPABASE_URL", "https://efhqbzdnrtifqjqlqseb.supabase.co"
).rstrip("/")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004446959502")
TELEGRAM_API = "https://api.telegram.org/bot{8841904683:AAFDQmAuhcoWv26p_5TC_tQV9zhdaXbNoCk}/sendMessage"

KEY_LABEL = "FeedBack @ShinnThieuu"
KEY_ROLE = "member"


def now_vn() -> datetime:
    return datetime.now(tz=VN_TZ)


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def is_active_hours(dt: datetime | None = None) -> bool:
    dt = dt or now_vn()
    return ACTIVE_START_HOUR <= dt.hour < ACTIVE_END_HOUR


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(
            f"Thiếu {name}. Publishable key không INSERT được (RLS). "
            "Cần SUPABASE_SECRET_KEY + TELEGRAM_BOT_TOKEN."
        )
    return value


def sb_headers(secret: str) -> dict:
    return {
        "apikey": secret,
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
    }


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_test_keys(secret: str) -> list[dict]:
    url = f"{SUPABASE_URL}/rest/v1/keys"
    params = {
        "select": "id,key,expires_at,is_used,label,created_at",
        "key": "like.Shinn-Cheat-Test*",
        "order": "created_at.desc",
        "limit": "200",
    }
    resp = requests.get(url, headers=sb_headers(secret), params=params, timeout=30)
    data = _json(resp)
    if resp.status_code >= 300:
        raise RuntimeError(f"Đọc keys thất bại ({resp.status_code}): {data}")
    if not isinstance(data, list):
        raise RuntimeError(f"Đọc keys lạ: {data}")
    return data


def test_number(key: str) -> int | None:
    match = KEY_PATTERN.match(key or "")
    if not match:
        return None
    return int(match.group(1))


def active_numbers(rows: list[dict], now: datetime) -> set[int]:
    """Số Test đang còn hạn — không tái sử dụng trong ngày nếu chưa xoá."""
    used: set[int] = set()
    for row in rows:
        num = test_number(row.get("key", ""))
        if num is None or num < KEY_MIN or num > KEY_MAX:
            continue
        expires = parse_iso(row.get("expires_at"))
        if expires is None or expires > now:
            used.add(num)
    return used


def pick_next_numbers(used: set[int], count: int) -> list[int]:
    free = [n for n in range(KEY_MIN, KEY_MAX + 1) if n not in used]
    if len(free) < count:
        raise RuntimeError(
            f"Hết slot Test{KEY_MIN}-{KEY_MAX} còn hạn "
            f"(còn {len(free)}, cần {count}). Xoá key hết hạn rồi chạy lại."
        )
    return free[:count]


def create_key(secret: str, number: int, expires: datetime) -> dict:
    payload = {
        "key": f"Shinn-Cheat-Test{number}",
        "device_id": None,
        "max_devices": 1,
        "expires_at": expires.isoformat(),
        "activated_at": None,
        "is_used": False,
        "is_vip": False,
        "role": KEY_ROLE,
        "label": KEY_LABEL,
    }
    url = f"{SUPABASE_URL}/rest/v1/keys"
    headers = {**sb_headers(secret), "Prefer": "return=representation"}
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    data = _json(resp)
    if resp.status_code >= 300:
        raise RuntimeError(f"Tạo Test{number} thất bại ({resp.status_code}): {data}")
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict) and data.get("key"):
        return data
    raise RuntimeError(f"Tạo Test{number} không trả hàng: {data}")


def build_message(rows: list[dict]) -> str:
    lines = [f"{i}. {row['key']}" for i, row in enumerate(rows, start=1)]
    key_block = "\n".join(lines)
    expires = parse_iso(rows[0].get("expires_at")) if rows else None
    expires_txt = (
        expires.astimezone(VN_TZ).strftime("%H:%M %d/%m/%Y") if expires else "-"
    )
    return (
        "SHINN CHEAT — Free test keys\n"
        "\n"
        f"{key_block}\n"
        "\n"
        "VI\n"
        f"• {KEYS_PER_DROP} key / lần • hạn 1 giờ • 1 thiết bị\n"
        "• Cập nhật mỗi 5 giờ\n"
        "• Thêm thành viên để nhận key free\n"
        "• Key dài hạn / tạo key: @ShinnThieuu\n"
        "\n"
        "EN\n"
        f"• {KEYS_PER_DROP} keys per drop • 1 hour • 1 device\n"
        "• Posted every 5 hours\n"
        "• Add members to get free keys\n"
        "• Long-term / create keys: @ShinnThieuu\n"
        "\n"
        f"Hết hạn: {expires_txt} (VN)"
    )


def send_telegram(token: str, text: str) -> dict:
    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
        "disable_notification": False,
    }
    resp = requests.post(url, json=payload, timeout=30)
    data = _json(resp)
    if not resp.ok or not data.get("ok"):
        raise RuntimeError(f"Gửi Telegram thất bại ({resp.status_code}): {data}")
    return data


def _json(resp: requests.Response):
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text[:400]}


def run_once(dry_run: bool = False) -> int:
    now_local = now_vn()
    print(f"[info] Giờ VN: {now_local.isoformat()}")
    if not is_active_hours(now_local):
        print("[skip] Ngoài khung 05:00–24:00 VN.")
        return 0

    utc = now_utc()
    expires = utc + timedelta(hours=KEY_TTL_HOURS)

    if dry_run:
        nums = list(range(KEY_MIN, KEY_MIN + KEYS_PER_DROP))
        rows = [
            {
                "key": f"Shinn-Cheat-Test{n}",
                "expires_at": expires.isoformat(),
            }
            for n in nums
        ]
        print("[dry-run] Không ghi server, không gửi Telegram.\n")
        print(build_message(rows))
        return 0

    secret = require_env("SUPABASE_SECRET_KEY")
    existing = fetch_test_keys(secret)
    used = active_numbers(existing, utc)
    numbers = pick_next_numbers(used, KEYS_PER_DROP)
    print(f"[info] Slot còn hạn: {sorted(used)}")
    print(f"[info] Sẽ tạo: {numbers}")

    created: list[dict] = []
    for num in numbers:
        row = create_key(secret, num, expires)
        created.append(row)
        print(f"[ok] {row.get('key')} hết hạn {row.get('expires_at')}")

    token = require_env("TELEGRAM_BOT_TOKEN")
    result = send_telegram(token, build_message(created))
    mid = result.get("result", {}).get("message_id")
    print(f"[ok] Đã gửi group {TELEGRAM_CHAT_ID} message_id={mid}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        sys.exit(run_once(dry_run=args.dry_run))
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
