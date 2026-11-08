"""إشعارات واتساب / SMS للمستفيد عند كل تحديث على الطلب.

المزوّد يُحدَّد من متغير البيئة NOTIFY_PROVIDER:
  - console  (افتراضي): يسجّل الرسالة في سجل الخادم فقط — للتجربة دون اشتراك.
  - twilio   : يتطلب TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM (ويدعم واتساب بالبادئة whatsapp:)
  - unifonic : يتطلب UNIFONIC_APP_SID, UNIFONIC_SENDER
"""
import base64
import json
import os
import urllib.parse
import urllib.request


def normalize_sa_phone(phone: str) -> str:
    """يحوّل 05xxxxxxxx أو 5xxxxxxxx إلى 9665xxxxxxxx."""
    p = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if p.startswith("00966"):
        p = p[2:]
    if p.startswith("05"):
        p = "966" + p[1:]
    elif p.startswith("5") and len(p) == 9:
        p = "966" + p
    return p


def build_message(req_no: str, status: str, note: str = "", track_url: str = "") -> str:
    msg = f"منصة بناء وتأثيث\nتحديث على طلبك رقم {req_no}\nالحالة: {status}"
    if note:
        msg += f"\nملاحظة: {note}"
    if track_url:
        msg += f"\nللمتابعة: {track_url}"
    return msg


def send(phone: str, message: str, channel: str = "whatsapp") -> tuple[bool, str]:
    """يرسل الرسالة ويعيد (نجاح؟, تفاصيل). فشل الإشعار لا يوقف تحديث الطلب."""
    provider = os.environ.get("NOTIFY_PROVIDER", "console").lower()
    to = normalize_sa_phone(phone)
    if not to:
        return False, "لا يوجد رقم جوال"
    try:
        if provider == "twilio":
            return _twilio(to, message, channel)
        if provider == "unifonic":
            return _unifonic(to, message)
        print(f"[NOTIFY:{channel}] -> {to}\n{message}\n", flush=True)
        return True, "console"
    except Exception as e:
        return False, f"خطأ: {e}"


def _twilio(to, message, channel):
    sid, token = os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"]
    sender = os.environ["TWILIO_FROM"]
    prefix = "whatsapp:" if channel == "whatsapp" else ""
    data = urllib.parse.urlencode({"To": f"{prefix}+{to}", "From": f"{prefix}{sender}", "Body": message}).encode()
    req = urllib.request.Request(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data=data)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode())
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status < 300, json.loads(r.read()).get("sid", "")


def _unifonic(to, message):
    data = urllib.parse.urlencode({
        "AppSid": os.environ["UNIFONIC_APP_SID"], "SenderID": os.environ["UNIFONIC_SENDER"],
        "Recipient": to, "Body": message,
    }).encode()
    req = urllib.request.Request("https://el.cloud.unifonic.com/rest/SMS/messages", data=data)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status < 300, r.read().decode()[:200]
