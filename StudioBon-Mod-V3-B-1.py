# ba_meta require api 9
# StudioBon Mod V2-F-CHANNEL
# Compatibility build: BombSquad 1.7.62 (API 9) and newer API 9 builds.
# This is an unpacked version to avoid errors caused by copying quoted/compressed code.

import re
import time
import threading
import socket
import weakref
import babase
import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib import party

teck = babase.apptimer
gsw = bui.get_special_widget
push = bui.screenmessage
Plugin = babase.Plugin
bw = bui.buttonwidget

def _widget_exists(widget):
    """چک امنِ زنده‌بودنِ یه ویجت.
    توی بعضی نسخه‌های بازی (مثل همینی که الان داری) bui.exists اصلاً وجود
    نداره و صدا زدنش AttributeError می‌ده. برای همین اول خودِ bui.exists رو
    امتحان می‌کنیم، بعد babase.exists، و اگه هیچ‌کدوم در دسترس نبود به‌جای
    کرش کردن، True برمی‌گردونیم و اجازه می‌دیم تلاشِ واقعیِ کار با ویجت
    (که همه‌جا توی try/except پیچیده شده) خودش خطای ReferenceError رو
    بگیره و رد کنه."""
    if widget is None:
        return False
    try:
        return bui.exists(widget)
    except AttributeError:
        pass
    except Exception:
        return False
    try:
        return babase.exists(widget)
    except AttributeError:
        pass
    except Exception:
        return False
    return True


# ---------------------------------------------------------------------------
# دکمه‌ی PING (دکمه‌ی اول)
X_OFFSET = -350
Y_FROM_TOP = 363
BTN_SIZE = 34
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# دکمه‌ی IP:PORT (دکمه‌ی دوم)
IP_X_OFFSET = -290
IP_Y_FROM_TOP = 363
IP_BTN_SIZE = 34
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# دکمه‌ی Fix (جایگزین کامل دکمه‌ی ساعت)
FIX_X_OFFSET = -230
FIX_Y_FROM_TOP = 363
FIX_BTN_SIZE = 34
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# دکمه‌ی ماشین‌حساب (دکمه‌ی چهارم)
# همین سه عدد رو عوض کن تا جای دکمه‌ی باز کردن ماشین‌حساب رو جابه‌جا کنی:
CALC_X_OFFSET = -170     # ### مکان: فاصله‌ی افقی از لبه‌ی راست پنجره ###
CALC_Y_FROM_TOP = 363    # ### مکان: فاصله‌ی عمودی از لبه‌ی بالای پنجره ###
CALC_BTN_SIZE = 34       # ### اندازه: اندازه‌ی دکمه (مربعی) ###

# ---------------------------------------------------------------------------
# دکمه‌ی پنجم: Bon
BON_X_OFFSET = -110
BON_Y_FROM_TOP = 363
BON_BTN_SIZE = 34
# دکمه‌ی Bon (ششم)
MLON_X_OFFSET = -50
MLON_Y_FROM_TOP = 363
MLON_BTN_SIZE = 34
# ---------------------------------------------------------------------------

# تنظیمات خودِ پنل ماشین‌حساب (چیزی که وسط صفحه باز میشه) - اینا رنگ آیکون نیستن،
# اینا داخل خود پنل ماشین‌حسابن، برای همینم توی تنظیمات درون‌بازی قرار نگرفتن.
CALC_PANEL_WIDTH = 900
CALC_PANEL_HEIGHT = 700
# فاصله‌ی افقی پنل از حالت دقیقاً وسط صفحه: عدد مثبت = به سمت راست، منفی = به سمت چپ
CALC_PANEL_X_OFFSET = 0
CALC_PANEL_COLOR = (1.0, 0.78, 0.08)
CALC_KEY_COLOR = (0.015, 0.015, 0.02)       # رنگ دکمه‌های عدد/عملگر داخل پنل
CALC_EQUALS_COLOR = (0.015, 0.015, 0.02)    # رنگ دکمه‌ی "=" قبل از تایید
CALC_EQUALS_ARMED_COLOR = (0.06, 0.06, 0.08)  # رنگ دکمه‌ی "=" وقتی منتظر تاییدِ دومه
CALC_CLOSE_COLOR = (0.015, 0.015, 0.02)
CALC_DISPLAY_COLOR = (0.15, 0.85, 0.90)
CALC_CONFIRM_TIMEOUT = 2.5  # ثانیه - اگه تا این مدت دوباره "=" رو نزنی، حالت تایید کنسل میشه
# ---------------------------------------------------------------------------

# راهنمای سریع جابه‌جایی دکمه‌ها:
# - همه از لبه‌ی راست پنجره اندازه‌گیری میشن (..._X_OFFSET).
# - همه از لبه‌ی بالای پنجره اندازه‌گیری میشن (..._Y_FROM_TOP).
# - اگه خواستی کنار هم (افقی) باشن، Y همه رو یکی کن و X هرکدوم رو ۴۰-۵۰ واحد فرق بذار.
# - برای رنگ آیکون‌ها (پس‌زمینه/نوشته) دیگه لازم نیست این فایل رو باز کنی؛
#   از تنظیمات درون‌بازیِ خودِ مود (بخش «تنظیمات» کنار مود توی لیست افزونه‌ها) تغییرشون بده.

# ---------------------------------------------------------------------------
# 🏷️ TAG-NEW-BUTTON (خودت، برای خودت):
#   هر وقت یه دکمه‌ی جدید به پنجره‌ی پارتی اضافه کردی (مثل Ping/IP/Time/Calc)،
#   بدون اینکه کاربر بگه، همینجا هم یه کلید جدید به _DEFAULT_COLORS و _LABELS اضافه کن
#   و توی _patched_party_init هم رنگش رو از _colors[...] بخون و رفرنسش رو توی
#   _live_buttons بذار (دقیقاً مثل ۴ تای فعلی). پنل تنظیمات رنگ خودش اسکرول‌پذیره و
#   بخش جدید رو خودکار ردیف می‌کنه، فقط کافیه اسم کلید رو به _SECTION_ORDER هم اضافه کنی.
# ---------------------------------------------------------------------------

# رنگ پیش‌فرض آیکون‌ها (فقط اولین باری که مود اجرا میشه استفاده میشه؛
# بعدش هرچی از تنظیمات درون‌بازی ست کنی همون ذخیره و استفاده میشه)
_DEFAULT_COLORS = {
    "ping":  {"bg": (0.0, 0.0, 0.0), "text": (1.0, 0.9, 0.0)},   # زرد
    "ip":    {"bg": (0.0, 0.0, 0.0), "text": (0.2, 1.0, 0.2)},   # سبز
    "calc":  {"bg": (0.0, 0.0, 0.0), "text": (1.0, 1.0, 1.0)},   # سفید
    "bon":   {"bg": (0.0, 0.0, 0.0), "text": (1.0, 1.0, 1.0)},   # سفید
    "mlon":  {"bg": (0.0, 0.0, 0.0), "text": (0.2, 1.0, 0.2)},   # سبز
    "fix":   {"bg": (0.0, 0.0, 0.0), "text": (0.55, 0.85, 1.0)},   # آبی روشن
    "radar": {"bg": (0.0, 0.0, 0.0), "text": (0.2, 0.95, 0.7)},
}

# نام‌هایی که روی دکمه‌ها نوشته میشه (برای پیش‌نمایش توی پنجره‌ی تنظیمات هم استفاده میشه)
# آیکون‌های سبک و کوتاه؛ در نسخه‌های BombSquad که ایموجی را روی دکمه‌ها
# درست نمایش ندهند، متن کوتاهِ قابل‌خواندن همچنان عملکرد را حفظ می‌کند.
_LABELS = {
    "ping": "📶",
    "ip": "👥️",
    "calc": "🧮",
    "bon": "⌛",
    "mlon": "Bon",
    "fix": "💳",
    "radar": "Radar",
}

_CONFIG_KEY = "StudioBon Icon Colors"


def _load_colors():
    """رنگ‌های ذخیره‌شده رو از کانفیگ بازی می‌خونه؛ اگه چیزی ذخیره نشده بود، پیش‌فرض می‌ذاره."""
    saved = {}
    try:
        raw = babase.app.config.get(_CONFIG_KEY)
        if isinstance(raw, dict):
            saved = raw
    except Exception:
        saved = {}

    colors = {}
    for key, default in _DEFAULT_COLORS.items():
        entry = saved.get(key) if isinstance(saved.get(key), dict) else {}
        try:
            bg = tuple(entry.get("bg", default["bg"]))
            if len(bg) != 3:
                bg = default["bg"]
        except Exception:
            bg = default["bg"]
        try:
            text = tuple(entry.get("text", default["text"]))
            if len(text) != 3:
                text = default["text"]
        except Exception:
            text = default["text"]
        colors[key] = {"bg": bg, "text": text}
    return colors


_colors = _load_colors()

# رفرنسِ زنده‌ی دکمه‌های واقعیِ پنجره‌ی پارتی (آخرین باری که پنجره باز شده)
# تا وقتی از تنظیمات رنگ عوض می‌کنی، بدون نیاز به بستن/بازکردن پنجره، فوری اعمال بشه.
_live_buttons = {"ping": None, "ip": None, "calc": None, "bon": None, "mlon": None, "fix": None, "radar": None}


def _save_colors():
    try:
        babase.app.config[_CONFIG_KEY] = {
            key: {"bg": list(val["bg"]), "text": list(val["text"])}
            for key, val in _colors.items()
        }
        babase.app.config.commit()
    except Exception as e:
        try:
            push(f"StudioBon: خطا در ذخیره‌ی تنظیمات: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass


def _apply_color(key, which, color):
    """رنگ یه آیکون رو عوض می‌کنه، ذخیره می‌کنه و اگه پنجره‌ی پارتی بازه، فوری روش اعمال می‌کنه."""
    _colors[key][which] = color
    _save_colors()
    widget = _live_buttons.get(key)
    if widget is not None and _widget_exists(widget):
        try:
            if which == "bg":
                bw(edit=widget, color=color)
            else:
                bw(edit=widget, textcolor=color)
        except Exception:
            pass
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 📐 جا / اندازه / شکل آیکون‌ها (پنل تنظیماتِ جدید)
_DEFAULT_LAYOUT = {
    "ping":  {"x": X_OFFSET, "y": Y_FROM_TOP, "size": BTN_SIZE, "shape": "square"},
    "ip":    {"x": IP_X_OFFSET, "y": IP_Y_FROM_TOP, "size": IP_BTN_SIZE, "shape": "square"},
    "calc":  {"x": CALC_X_OFFSET, "y": CALC_Y_FROM_TOP, "size": CALC_BTN_SIZE, "shape": "square"},
    "bon":   {"x": BON_X_OFFSET, "y": BON_Y_FROM_TOP, "size": BON_BTN_SIZE, "shape": "square"},
    "mlon":  {"x": MLON_X_OFFSET, "y": MLON_Y_FROM_TOP, "size": MLON_BTN_SIZE, "shape": "square"},
    "fix":   {"x": FIX_X_OFFSET, "y": FIX_Y_FROM_TOP, "size": FIX_BTN_SIZE, "shape": "square"},
    "radar": {"x": -410, "y": 363, "size": 34, "shape": "square"},
}

# محدوده‌ی مجاز تغییرات، فقط برای اینکه دکمه‌ها از صفحه بیرون نزنن
_LAYOUT_LIMITS = {
    "x": (-500, 0),
    "y": (20, 600),
    "size": (18, 70),
}
_LAYOUT_STEP = {"x": 10, "y": 10, "size": 4}
_SHAPES = ["square", "rectangle"]
_SHAPE_LABELS = {"square": "🔲 مربع", "rectangle": "▭ مستطیل"}

_CONFIG_KEY_LAYOUT = "StudioBon Icon Layout"


def _load_layout():
    saved = {}
    try:
        raw = babase.app.config.get(_CONFIG_KEY_LAYOUT)
        if isinstance(raw, dict):
            saved = raw
    except Exception:
        saved = {}

    layout = {}
    for key, default in _DEFAULT_LAYOUT.items():
        entry = saved.get(key) if isinstance(saved.get(key), dict) else {}
        try:
            x = int(entry.get("x", default["x"]))
        except Exception:
            x = default["x"]
        try:
            y = int(entry.get("y", default["y"]))
        except Exception:
            y = default["y"]
        try:
            size = int(entry.get("size", default["size"]))
        except Exception:
            size = default["size"]
        shape = entry.get("shape", default["shape"])
        if shape not in _SHAPES:
            shape = default["shape"]
        layout[key] = {"x": x, "y": y, "size": size, "shape": shape}
    return layout


_layout = _load_layout()

# رفرنسِ زنده‌ی پنجره‌ی پارتیِ فعلی، تا بشه دکمه‌ها رو بدون بستن/بازکردنِ پنجره
# بازسازی کرد وقتی جا/اندازه/شکلشون از تنظیمات عوض میشه.
# ### نکته‌ی مهم: به خودِ آبجکتِ پنجره‌ی پارتی (self) هرگز رفرنسِ مستقیم/قوی نگه
# ### نمی‌داریم، چون خودِ اون کلاس یه تایمرِ داخلیِ weak-reference داره که باید
# ### با بسته‌شدنِ پنجره خودکار از کار بیفته؛ رفرنسِ قوی جلوی اینو می‌گیره و باعث
# ### میشه بعد از بستنِ پنجره، تایمرش هر فریم روی ویجت‌های حذف‌شده کار کنه و
# ### ارور بده (و همین باعث میشد بارِ دوم پنجره‌ی پارتی درست باز نشه). برای همین
# ### فقط یه weakref بهش نگه می‌داریم.
_live_party_window_ref = None
_live_party_root = None
_live_party_dims = (0, 0)


def _get_live_party_window():
    if _live_party_window_ref is None:
        return None
    return _live_party_window_ref()


def _save_layout():
    try:
        babase.app.config[_CONFIG_KEY_LAYOUT] = {
            key: {"x": val["x"], "y": val["y"], "size": val["size"], "shape": val["shape"]}
            for key, val in _layout.items()
        }
        babase.app.config.commit()
    except Exception as e:
        try:
            push(f"StudioBon: خطا در ذخیره‌ی جا/اندازه: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass


def _clamp(value, field):
    lo, hi = _LAYOUT_LIMITS[field]
    return max(lo, min(hi, value))


def _shape_button_type(shape):
    # ### این نسخه از بازی فقط از button_type="square" پشتیبانی می‌کنه؛ "circle"
    # ### کرش می‌کرد («Invalid button type: 'circle'») برای همین حذف شد. این تابع
    # ### رو نگه داشتیم تا اگه یه‌روز بازی شکل‌های بیشتری پشتیبانی کرد، فقط همینجا
    # ### اضافه بشه، بدون نیاز به تغییر جای دیگه‌ای از کد.
    return "square"


def _shape_size(base_size, shape):
    if shape == "rectangle":
        return (int(base_size * 1.6), base_size)
    return (base_size, base_size)


def _create_icon_button(key):
    """دکمه‌ی یه آیکون رو با جا/اندازه/شکل/رنگِ فعلی، توی پنجره‌ی پارتیِ زنده می‌سازه."""
    if _live_party_root is None or not _widget_exists(_live_party_root):
        return None
    cfg = _layout[key]
    size = _shape_size(cfg["size"], cfg["shape"])
    px, py = _live_party_dims
    try:
        btn = bw(
            parent=_live_party_root,
            position=(px + cfg["x"], py - cfg["y"]),
            size=size,
            button_type=_shape_button_type(cfg["shape"]),
            label=_LABELS[key],
            text_scale=0.9 if key == "calc" else 1.1,
            color=_colors[key]["bg"],
            textcolor=_colors[key]["text"],
            autoselect=True,
            on_activate_call=_BUTTON_CALLBACKS[key],
        )
    except Exception:
        return None
    _live_buttons[key] = btn
    return btn


def _refresh_icon_button(key, shape_changed):
    """بعد از تغییر جا/اندازه/شکل از تنظیمات، دکمه‌ی واقعیِ توی پنجره‌ی پارتی رو آپدیت می‌کنه."""
    widget = _live_buttons.get(key)
    cfg = _layout[key]
    if widget is None or not _widget_exists(widget):
        return
    if shape_changed:
        # ### button_type بعد از ساختِ ویجت قابل تغییر نیست، پس دکمه‌ی قدیمی رو حذف و
        # ### یکی جدید با شکل تازه می‌سازیم. اگه این نسخه از بازی اجازه‌ی حذفِ زنده‌ی
        # ### ویجت رو نده، دکمه‌ی قدیمی همون‌جا می‌مونه (فقط جا/اندازه‌ش آپدیت میشه) و
        # ### شکلِ جدید بعد از بستن/بازکردنِ پنجره‌ی پارتی اعمال میشه.
        deleted = False
        try:
            bui.widget(edit=widget, delete=True)
            deleted = True
        except Exception:
            deleted = False
        if deleted:
            _create_icon_button(key)
            return
    try:
        size = _shape_size(cfg["size"], cfg["shape"])
        px, py = _live_party_dims
        bw(edit=widget, position=(px + cfg["x"], py - cfg["y"]), size=size)
    except Exception:
        pass


def _apply_layout(key, **updates):
    for field in ("x", "y", "size"):
        if field in updates:
            _layout[key][field] = _clamp(int(updates[field]), field)
    shape_changed = False
    if "shape" in updates and updates["shape"] in _SHAPES:
        shape_changed = _layout[key]["shape"] != updates["shape"]
        _layout[key]["shape"] = updates["shape"]
    _save_layout()
    _refresh_icon_button(key, shape_changed)
# ---------------------------------------------------------------------------

_server_ip = "127.0.0.1"
_server_port = 43210
current_ping = 0.0

_orig_connect_to_party = bs.connect_to_party
_orig_disconnect_from_host = bs.disconnect_from_host


def _new_connect_to_party(address, port=43210, print_progress=False):
    global _server_ip, _server_port, _game_session_started_at
    _server_ip = address
    _server_port = port
    result = _orig_connect_to_party(address, port, print_progress)
    _game_session_started_at = time.time()
    try:
        _sb_schedule_welcome()
        _sb_reset_radar_stats()
        _sb_enemy_announced_this_session.clear()
        teck(2.0, _sb_check_enemy_roster)
    except Exception:
        pass
    return result


def _new_disconnect_from_host():
    global _server_ip, _server_port, _game_session_started_at
    try:
        _sb_cancel_welcome()
    except Exception:
        pass
    _server_ip = "127.0.0.1"
    _server_port = 43210
    _game_session_started_at = None
    return _orig_disconnect_from_host()


bs.connect_to_party = _new_connect_to_party
bs.disconnect_from_host = _new_disconnect_from_host


class _PingThread(threading.Thread):
    """پینگ واقعی رو با یه پکت کوچیک UDP اندازه می‌گیره."""

    def __init__(self):
        super().__init__(daemon=True)
        self.running = True

    def run(self):
        global current_ping
        while self.running:
            try:
                if _server_ip != "127.0.0.1" and _server_port != 43210:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(1)
                    start = time.time()
                    sock.sendto(b"\x0b", (_server_ip, _server_port))
                    try:
                        data, _addr = sock.recvfrom(10)
                        current_ping = (
                            round((time.time() - start) * 1000.0)
                            if data == b"\x0c"
                            else 999
                        )
                    except socket.timeout:
                        current_ping = 999
                    except Exception:
                        current_ping = 0
                    finally:
                        sock.close()
                else:
                    current_ping = 0
            except Exception:
                current_ping = 0
            time.sleep(1)

    def stop(self):
        self.running = False


_ping_thread = _PingThread()
_ping_thread.start()


def _on_ping_press():
    try:
        ping = int(current_ping)
        # LRM اطراف عدد/واحد برای جلوگیری از جابه‌جایی عدد انگلیسی داخل متن فارسی.
        n = "\u200e%d\u200ems" % ping
        if ping > 39:
            bs.chatmessage("❌️ Pingam Rid ! : %s" % n)
        else:
            bs.chatmessage("📶 My Ping Now : %s" % n)
    except Exception as e:
        try:
            push(f"StudioBon error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass


def _on_ip_press():
    try:
        bs.chatmessage("f i")
    except Exception as e:
        try:
            push(f"StudioBon error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# تبدیل تاریخ میلادی به شمسی (الگوریتم استاندارد، بدون نیاز به کتابخونه‌ی جدا)
_J_MONTH_NAMES = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

# روزهای هفته به انگلیسی (بر اساس time.localtime().tm_wday : دوشنبه=0 ... یکشنبه=6)
_WEEKDAY_EN = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]



# ---------------------------------------------------------------------------
# مود ماشین‌حساب حرفه‌ای
_OP_MAP = {"÷": "/", "×": "*", "−": "-"}
_calc_window = None  # رفرنس زنده نگه‌داشتن پنجره، وگرنه پایتون حذفش می‌کنه



# ---------------------------------------------------------------------------
# 💳 AutoBuy: watch newly received chat messages and answer each code once.
# Polling is retained from the previously working implementation; a code cooldown
# prevents echoed "b sNNNN" messages or repeated callbacks from sending duplicates.
_autobuy_enabled = False
_autobuy_seen_messages = {}
_autobuy_poll_running = False
_autobuy_recent_codes = {}
_AUTOBUY_CODE_RE = re.compile(r'(?<![A-Za-z0-9])s(\d{2,4})(?!\d)', re.I)


def _autobuy_snapshot():
    try:
        getter = getattr(bs, "get_chat_messages", None)
        vals = getter() if callable(getter) else []
        return [str(x) for x in (vals or [])]
    except Exception:
        return []


def _autobuy_toggle():
    global _autobuy_enabled, _autobuy_seen_messages, _autobuy_poll_running, _autobuy_recent_codes
    _autobuy_enabled = not _autobuy_enabled
    if _autobuy_enabled:
        _autobuy_seen_messages = {}
        _autobuy_recent_codes = {}
        for _msg in _autobuy_snapshot():
            _autobuy_seen_messages[_msg] = _autobuy_seen_messages.get(_msg, 0) + 1
        try:
            push("AutoBuy ON 💸", color=(0.2, 1.0, 0.35))
        except Exception:
            pass
        if not _autobuy_poll_running:
            _autobuy_poll_running = True
            teck(0.1, _autobuy_poll)
    else:
        try:
            push("AutoBuy OFF 📤", color=(1.0, 0.65, 0.2))
        except Exception:
            pass


def _autobuy_process_message(msg):
    if not _autobuy_enabled or _sb_v3_danger_enabled:
        return
    try:
        match = _AUTOBUY_CODE_RE.search(str(msg))
        if not match:
            return
        code = "s" + match.group(1)
        now = time.monotonic()
        previous = _autobuy_recent_codes.get(code, 0.0)
        if now - previous < 3.0:
            return
        _autobuy_recent_codes[code] = now
        for old_code, stamp in list(_autobuy_recent_codes.items()):
            if now - stamp > 15.0:
                _autobuy_recent_codes.pop(old_code, None)
        bs.chatmessage("b " + code)
    except Exception:
        pass


def _autobuy_handle_incoming(msg):
    # Kept as a hook fallback; polling and hook share the same deduplication.
    _autobuy_process_message(msg)


def _autobuy_poll():
    global _autobuy_poll_running, _autobuy_seen_messages
    if not _autobuy_enabled:
        _autobuy_poll_running = False
        return
    try:
        messages = _autobuy_snapshot()
        current_counts = {}
        for msg in messages:
            current_counts[msg] = current_counts.get(msg, 0) + 1
            if current_counts[msg] <= _autobuy_seen_messages.get(msg, 0):
                continue
            _autobuy_process_message(msg)
        _autobuy_seen_messages = current_counts
    except Exception:
        pass
    teck(0.1, _autobuy_poll)

# ---------------------------------------------------------------------------
# StudioBon V3-A payment panels. The existing normal AutoBuy implementation is
# preserved; the 💳 button now opens a control panel instead of toggling it.
_sb_v3_danger_enabled = False
_sb_v3_secure_enabled = False
_sb_v3_items = {}
_sb_v3_config_key = "StudioBon V3-A Item Limits"
_sb_v3_main_window = None
_sb_v3_settings_window = None
_sb_v3_item_name_widget = None
_sb_v3_item_price_widget = None
_sb_v3_danger_seen = {}

try:
    _saved_v3_items = babase.app.config.get(_sb_v3_config_key, {})
    if isinstance(_saved_v3_items, dict):
        _sb_v3_items = {str(k): float(v) for k, v in _saved_v3_items.items() if str(k).strip() and float(v) > 0}
except Exception:
    _sb_v3_items = {}


def _sb_v3_close(win):
    try:
        if win is not None and _widget_exists(win):
            bui.containerwidget(edit=win, transition="out_scale")
    except Exception:
        pass


def _sb_v3_open_main():
    global _sb_v3_main_window
    try:
        w = bui.containerwidget(size=(520, 570), scale=0.85, stack_offset=(0, 0),
                                color=(0.20, 0.78, 0.30), transition="in_scale")
        _sb_v3_main_window = w
        bui.textwidget(parent=w, text="💶سرویس آسان پرداخت بانک استودیوبون💳",
                       position=(260, 525), size=(480, 32), h_align="center",
                       color=(1, 1, 1), scale=1.0)
        # Normal AutoBuy toggle: same underlying handler/behavior as the original.
        bui.buttonwidget(parent=w, position=(45, 465), size=(430, 42),
                         label="روشن/خاموش کردن آسان خرید عادی", color=(1.0, 0.92, 0.25),
                         textcolor=(0, 0, 0), on_activate_call=_autobuy_toggle)
        bui.buttonwidget(parent=w, position=(45, 405), size=(430, 42),
                         label="خرید در لحظه بدون نیاز به ارسال عدد ۱", color=(1.0, 0.92, 0.25),
                         textcolor=(0, 0, 0), on_activate_call=_sb_v3_open_warning)
        bui.buttonwidget(parent=w, position=(45, 345), size=(430, 42),
                         label="تنظیم قیمت خرید/خرید سریع امن", color=(0.12, 0.45, 0.95),
                         textcolor=(1, 1, 1), on_activate_call=_sb_v3_open_settings)
        bui.buttonwidget(parent=w, position=(45, 285), size=(430, 38), label="غیرفعال کردن خرید خودکار خطرناک",
                         color=(1.0, 0.82, 0.15), textcolor=(1, 0, 0), on_activate_call=_sb_v3_disable_danger)
        bui.textwidget(parent=w, text="وضعیت خرید عادی: " + ("روشن" if _autobuy_enabled else "خاموش"),
                       position=(260, 235), size=(460, 25), h_align="center", color=(1,1,1), scale=0.75)
        bui.buttonwidget(parent=w, position=(170, 35), size=(180, 38), label="بستن",
                         color=(0.15, 0.45, 0.2), textcolor=(1,1,1),
                         on_activate_call=lambda: _sb_v3_close(w))
    except Exception as exc:
        try: push("StudioBon payment panel error: " + str(exc), color=(1,0.2,0.2))
        except Exception: pass


def _sb_v3_open_warning():
    try:
        w = bui.containerwidget(size=(540, 650), scale=0.82, color=(0.78, 0.06, 0.08), transition="in_scale")
        bui.textwidget(parent=w, text="⚠️ هشدار ⚠️", position=(270, 610), size=(490, 36),
                       h_align="center", color=(1,1,1), scale=1.2)
        scroll = bui.scrollwidget(parent=w, position=(25, 105), size=(490, 475), color=(0.62,0.02,0.04))
        content = bui.containerwidget(parent=scroll, size=(470, 800), background=False)
        warning = ("با فعال کردن این دکمه هر کد بعدی که\n"
                   "ارسال بشود به طور خودکار و بدون\n"
                   "اجازه از شما خریداری میشود پس\n"
                   "اطمینان حاصل فرمایید که به جز شما\n"
                   "و شخص فروشنده قابل اعتمادتان\n"
                   "فرد دیگری داخل سرورحضور نداشته باشد\n"
                   "تا از کلاهبرداری جلوگیری شود\n\n"
                   "مسئولیت استفاده از این قابلیت بر عهده\n"
                   "خودتان است پس نهایت احتیاط را به خرج\n"
                   "دهید\n\n"
                   "ارسال کد اشتباه یا قیمت اشتباه در چت بازی\n"
                   "باعث میشود ایتم اشتباه با قیمت اشتباه خریداری\n"
                   "شود. پس این قابلیت را همیشه خاموش نگهدارید\n"
                   "مگر در مواقع ضروری برای خرید خیلی سریع\n\n"
                   ">>>>>>>>>>>>>>>>")
        bui.textwidget(parent=content, text=warning, position=(20, 25), size=(430, 740),
                       h_align="center", v_align="top", color=(1,1,1), scale=0.78)
        bui.buttonwidget(parent=w, position=(25, 35), size=(305, 45),
                         label="مطلب رو خوندم/فعال کردن❗️", color=(0.12,0.85,0.20),
                         textcolor=(1,0,0), on_activate_call=lambda: _sb_v3_enable_danger(w))
        bui.buttonwidget(parent=w, position=(345, 35), size=(170, 45), label="غیرفعال کردن",
                         color=(0.95,0.78,0.12), textcolor=(1,0,0),
                         on_activate_call=lambda: (_sb_v3_disable_danger(), _sb_v3_close(w)))
    except Exception as exc:
        try: push("Warning panel error: " + str(exc), color=(1,0.2,0.2))
        except Exception: pass


def _sb_v3_enable_danger(win):
    global _sb_v3_danger_enabled, _sb_v3_danger_seen
    _sb_v3_danger_enabled = True
    _sb_v3_danger_seen = {}
    _sb_v3_close(win)
    try: push("قابلیت خرید خودکار خطرناک فعال شد!", color=(1,0.1,0.1))
    except Exception: pass


def _sb_v3_disable_danger():
    global _sb_v3_danger_enabled
    _sb_v3_danger_enabled = False
    try: push("خرید خودکار خطرناک غیر فعال شد✅️", color=(0.1,1,0.25))
    except Exception: pass


def _sb_v3_open_settings():
    global _sb_v3_settings_window
    try:
        w = bui.containerwidget(size=(570, 590), scale=0.82, color=(0.60,0.60,0.62), transition="in_scale")
        _sb_v3_settings_window = w
        bui.textwidget(parent=w, text="آسان پرداخت ویژه و امن", position=(285, 550), size=(520, 35),
                       h_align="center", color=(0.05,0.75,0.18), scale=1.1)
        bui.buttonwidget(parent=w, position=(30, 495), size=(245, 38), label="فعال کردن خرید امن",
                         color=(0.08, 0.72, 0.20), textcolor=(1, 1, 1),
                         on_activate_call=lambda: _sb_v3_enable_secure())
        bui.buttonwidget(parent=w, position=(295, 495), size=(245, 38), label="غیر فعال کردن",
                         color=(0.82, 0.08, 0.10), textcolor=(1, 1, 1),
                         on_activate_call=lambda: _sb_v3_disable_secure())
        scroll = bui.scrollwidget(parent=w, position=(25, 105), size=(520, 365), color=(0.78,0.78,0.80))
        height = max(350, len(_sb_v3_items) * 52 + 20)
        content = bui.containerwidget(parent=scroll, size=(500, height), background=False)
        if not _sb_v3_items:
            bui.textwidget(parent=content, text="هنوز مشخصات خریدی ثبت نشده", position=(250, height-65),
                           size=(460, 30), h_align="center", color=(0.18,0.18,0.18), scale=0.8)
        else:
            y = height - 48
            for item, price in list(_sb_v3_items.items()):
                bui.textwidget(parent=content, text=str(item) + " — حداکثر قیمت: " + str(price),
                               position=(15,y), size=(350,30), color=(0.08,0.08,0.08), scale=0.75)
                bui.buttonwidget(parent=content, position=(390,y-5), size=(90,32), label="حذف",
                                 color=(0.85,0.15,0.15), textcolor=(1,1,1),
                                 on_activate_call=lambda item=item, win=w: _sb_v3_delete_item(item, win))
                y -= 52
        bui.buttonwidget(parent=w, position=(35, 45), size=(300, 42), label="اضافه کردن مشخصات خرید",
                         color=(0.12,0.7,0.25), textcolor=(1,1,1),
                         on_activate_call=lambda: _sb_v3_open_add_item(w))
        bui.buttonwidget(parent=w, position=(370, 45), size=(150, 42), label="بستن",
                         color=(0.35,0.35,0.35), textcolor=(1,1,1), on_activate_call=lambda: _sb_v3_close(w))
    except Exception as exc:
        try: push("Settings panel error: " + str(exc), color=(1,0.2,0.2))
        except Exception: pass


def _sb_v3_open_add_item(parent_window=None):
    global _sb_v3_item_name_widget, _sb_v3_item_price_widget
    try:
        w = bui.containerwidget(size=(470, 330), scale=0.9, color=(0.36,0.36,0.38), transition="in_scale")
        bui.textwidget(parent=w, text="افزودن مشخصات خرید", position=(235, 285), size=(420,30),
                       h_align="center", color=(1,1,1), scale=1.0)
        bui.textwidget(parent=w, text="اسم آیتم", position=(40, 230), color=(1,1,1), scale=0.85)
        _sb_v3_item_name_widget = bui.textwidget(parent=w, text="", position=(40,195), size=(390,28),
                                                editable=True, color=(1,1,1), max_chars=40)
        bui.textwidget(parent=w, text="حداکثر قیمت ایتم", position=(40, 155), color=(1,1,1), scale=0.85)
        _sb_v3_item_price_widget = bui.textwidget(parent=w, text="", position=(40,120), size=(390,28),
                                                 editable=True, color=(1,1,1), max_chars=10)
        bui.buttonwidget(parent=w, position=(45,45), size=(160,38), label="ذخیره",
                         color=(0.12,0.75,0.22), textcolor=(1,1,1),
                         on_activate_call=lambda: _sb_v3_save_item(w, parent_window))
        bui.buttonwidget(parent=w, position=(245,45), size=(160,38), label="لغو",
                         color=(0.8,0.15,0.15), textcolor=(1,1,1), on_activate_call=lambda: _sb_v3_close(w))
    except Exception as exc:
        try: push("Add item panel error: " + str(exc), color=(1,0.2,0.2))
        except Exception: pass


def _sb_v3_save_item(win, parent_window=None):
    global _sb_v3_items
    try:
        item = str(bui.textwidget(query=_sb_v3_item_name_widget)).strip()
        price = float(str(bui.textwidget(query=_sb_v3_item_price_widget)).replace(",", "").strip())
        if not item or price <= 0:
            raise ValueError("اسم آیتم و قیمت مثبت وارد کن")
        _sb_v3_items[item] = price
        cfg = babase.app.config
        cfg[_sb_v3_config_key] = dict(_sb_v3_items)
        cfg.commit()
        _sb_v3_close(win)
        if parent_window is not None: _sb_v3_close(parent_window)
        push("مشخصات خرید ذخیره شد ✅", color=(0.2,1,0.3))
        _sb_v3_open_settings()
    except Exception as exc:
        try: push("اطلاعات نامعتبر است: " + str(exc), color=(1,0.2,0.2))
        except Exception: pass


def _sb_v3_delete_item(item, win):
    global _sb_v3_items
    _sb_v3_items.pop(item, None)
    try:
        cfg = babase.app.config
        cfg[_sb_v3_config_key] = dict(_sb_v3_items)
        cfg.commit()
    except Exception: pass
    _sb_v3_close(win)
    _sb_v3_open_settings()


def _sb_v3_process_danger_message(msg):
    """Danger mode: purchase only a newly seen sale code, then send one confirmation 1 second later."""
    if not _sb_v3_danger_enabled:
        return
    try:
        raw = str(msg)
        # Do not react to our own buy/confirmation commands.
        if re.search(r'\bb\s*s\d{2,4}\b', raw, re.I) or raw.strip() == '1':
            return
        match = _AUTOBUY_CODE_RE.search(raw)
        if not match:
            return
        code = "s" + match.group(1)
        now = time.monotonic()
        if now - _sb_v3_danger_seen.get(code, 0) < 15.0:
            return
        _sb_v3_danger_seen[code] = now
        bs.chatmessage("b " + code)
        teck(1.0, lambda: bs.chatmessage("1") if _sb_v3_danger_enabled else None)
    except Exception:
        pass


def _sb_v3_secure_notice(message, color):
    try:
        push(message, color=color, transient=True)
    except Exception:
        try: push(message, color=color)
        except Exception:
            try: print(message)
            except Exception: pass


def _sb_v3_enable_secure():
    global _sb_v3_secure_enabled
    _sb_v3_secure_enabled = True
    _sb_v3_secure_notice("خرید امن فعال شد", (0.15, 1.0, 0.25))


def _sb_v3_disable_secure():
    global _sb_v3_secure_enabled
    _sb_v3_secure_enabled = False
    _sb_v3_secure_notice("خرید امن غیرفعال شد", (1.0, 0.2, 0.2))


def _sb_v3_process_secure_message(msg):
    """Only buy configured items within their saved price limit when secure mode is enabled."""
    if not _sb_v3_secure_enabled:
        return
    try:
        raw = str(msg)
        match = _AUTOBUY_CODE_RE.search(raw)
        if not match:
            return
        # Only proceed when a configured item name and an explicit numeric price
        # are present in the same incoming line; this avoids guessing from code-only messages.
        lower = raw.casefold()
        for item, limit in list(_sb_v3_items.items()):
            if item.casefold() not in lower:
                continue
            number_groups = re.findall(r'(?<!\d)(\d{1,7})(?!\d)', raw)
            code_number = match.group(1)
            number_groups = [n for n in number_groups if n != code_number]
            if not number_groups:
                continue
            price = float(number_groups[-1])
            code = "s" + match.group(1)
            if price <= limit:
                bs.chatmessage("b " + code)
                teck(0.4, lambda: bs.chatmessage("1"))
            return
    except Exception:
        pass


def _on_fix_press():
    _sb_v3_open_main()


# ---------------------------------------------------------------------------
class _CalcWindow:
    def __init__(self, party_window):
        self._expr = ""
        self._problem = ""  # صورت مسئله (قبل از محاسبه)، برای فرستادن همراه جواب
        self._confirm_armed = False

        w = CALC_PANEL_WIDTH
        h = CALC_PANEL_HEIGHT
        self._width = w
        self._height = h

        # ### نکته‌ی مهم: پنل به لایه‌ی overlay_stack وصله که کل صفحه رو می‌گیره،
        # ### نه فقط پنجره‌ی پارتی. قبلاً وسط‌چین‌کردن بر اساس عرض/ارتفاعِ خودِ
        # ### party_window حساب می‌شد که غلط بود (اون پنجره خودش کوچیک‌تر و جابه‌جاست)،
        # ### برای همین هر مقداری به آفست می‌دادیم، درست وسطِ کل صفحه نمی‌نشست.
        # ### حالا اندازه‌ی واقعیِ کل صفحه (همون چیزی که overlay_stack توشه) رو
        # ### می‌گیریم و پنل رو نسبت به مرکز واقعیِ صفحه وسط‌چین می‌کنیم.
        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            # ### fallback برای اگه اسم تابع فرق داشت / در دسترس نبود
            sw, sh = party_window._width, party_window._height
        pos_x = (sw - w) / 2 + CALC_PANEL_X_OFFSET
        pos_y = (sh - h) / 2

        # ### به‌جای وصل‌کردن به پنجره‌ی پارتی (که رو همون لایه‌ی چته و همیشه
        # ### پشتش رد میشه)، پنل رو به لایه‌ی مخصوص «overlay_stack» وصل می‌کنیم؛
        # ### این لایه همیشه بالاتر از همه‌چیز (از جمله چت) قرار می‌گیره و خودش
        # ### به‌طور طبیعی کاملاً کدره، پس دیگه نیازی به هیچ لایه‌ی اضافه‌ای نیست
        # ### و ظاهر خمیریِ پیش‌فرض پنل هم دقیقاً مثل قبل دست‌نخورده می‌مونه.
        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"),
            position=(pos_x, pos_y),
            size=(w, h),
            transition="in_scale",
            scale=1.0,
            color=CALC_PANEL_COLOR,
        )
        self._root_widget = self.root_widget

        margin = 16

        # عنوان
        bui.textwidget(
            parent=self._root_widget,
            position=(0, h - 32),
            size=(w, 24),
            text="🧮  STUDIOBON CALCULATOR",
            h_align="center",
            v_align="center",
            scale=1.1,
            color=(0.02, 0.02, 0.02),
        )

        # دکمه‌ی بستن
        bw(
            parent=self._root_widget,
            position=(w - margin - 66, h - 54),
            size=(66, 66),
            button_type="square",
            label="✕",
            text_scale=1.55,
            color=CALC_CLOSE_COLOR,
            textcolor=(1.0, 0.85, 0.08),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._close),
        )

        # نمایشگر بزرگ با کادر فیروزه‌ای/آبی
        self._display_margin = margin + 22
        self._display_box = bui.containerwidget(
            parent=self._root_widget,
            position=(self._display_margin, h - 112),
            size=(w - 2 * self._display_margin, 74),
            background=True,
            color=CALC_DISPLAY_COLOR)
        self._display = bui.textwidget(
            parent=self._display_box,
            position=(0, 6),
            size=(w - 2 * self._display_margin, 62),
            text="0",
            h_align="center",
            v_align="center",
            scale=2.4,
            color=(0.02, 0.02, 0.02),
        )

        # صفحه‌کلید (دکمه‌ها بزرگ‌تر شدن و فاصله‌ی بیشتری از هم گرفتن)
        rows = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "−"],
            ["❌", "0", ".", "+"],
        ]
        btn_w, btn_h, gap = 150, 78, 18
        grid_left = (w - (4 * btn_w + 3 * gap)) / 2
        grid_top = h - 245

        for r, row in enumerate(rows):
            for c, label in enumerate(row):
                x = grid_left + c * (btn_w + gap)
                y = grid_top - r * (btn_h + gap)
                bw(
                    parent=self._root_widget,
                    position=(x, y),
                    size=(btn_w, btn_h),
                    button_type="square",
                    label=label,
                    text_scale=1.35,
                    color=CALC_KEY_COLOR,
                    textcolor=(1.0, 0.85, 0.08),
                    autoselect=True,
                    on_activate_call=bui.WeakCall(self._append, label),
                )

        # دکمه‌ی "=" (همون دکمه‌ی تایید - باید دوبار زده بشه تا بفرسته تو چت)
        last_row_bottom = grid_top - (len(rows) - 1) * (btn_h + gap)
        equals_y = last_row_bottom - gap - 52
        self._equals_btn = bw(
            parent=self._root_widget,
            position=(grid_left, equals_y),
            size=(4 * btn_w + 3 * gap, 64),
            button_type="square",
            label="=",
            text_scale=1.45,
            color=CALC_EQUALS_COLOR,
            textcolor=(1.0, 0.85, 0.08),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._on_equals_press),
        )

    # -- منطق دکمه‌ها --

    def _append(self, ch):
        if self._confirm_armed:
            # اگه وسط حالت "منتظر تایید دوم" بودیم و کاربر دوباره تایپ کرد، لغوش کن
            self._reset_confirm_state()
        if ch == "❌":
            self._expr = self._expr[:-1]
        else:
            self._expr += _OP_MAP.get(ch, ch)
        self._update_display()

    def _update_display(self):
        text = self._expr if self._expr else "0"
        # Keep the font size fixed; if the expression gets too long, keep its
        # right-most part visible instead of shrinking the digits.
        max_chars = 10
        shown = text if len(text) <= max_chars else "…" + text[-(max_chars - 1):]
        try:
            bui.textwidget(edit=self._display, text=shown, scale=2.4)
        except Exception:
            pass

    def _show_error(self, msg):
        try:
            bui.textwidget(edit=self._display, text=msg)
        except Exception:
            pass
        self._expr = ""

    def _calculate(self):
        expr = self._expr.strip()
        if not expr:
            return False
        if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
            self._show_error("عبارت نامعتبره")
            return False
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            self._problem = expr  # صورت مسئله رو نگه می‌داریم
            self._expr = str(result)
            self._update_display()
            return True
        except ZeroDivisionError:
            self._show_error("تقسیم بر صفر!")
            return False
        except Exception:
            self._show_error("خطا در محاسبه")
            return False

    def _on_equals_press(self):
        if not self._confirm_armed:
            # بار اول: فقط محاسبه کن و منتظر تاییدِ دوم بمون
            if self._calculate():
                self._confirm_armed = True
                try:
                    bw(edit=self._equals_btn, label="ارسال برای نمایش💠", color=CALC_EQUALS_ARMED_COLOR, textcolor=(1.0, 0.85, 0.08))
                except Exception:
                    pass
                teck(CALC_CONFIRM_TIMEOUT, bui.WeakCall(self._confirm_timeout))
        else:
            # بار دوم: بفرست تو چت
            self._send_to_chat()
            self._reset_confirm_state()

    def _confirm_timeout(self):
        if _widget_exists(self._root_widget):
            self._reset_confirm_state()

    def _reset_confirm_state(self):
        self._confirm_armed = False
        try:
            bw(edit=self._equals_btn, label="=", color=CALC_EQUALS_COLOR, textcolor=(1.0, 0.85, 0.08))
        except Exception:
            pass

    def _send_to_chat(self):
        try:
            problem = self._problem if self._problem else self._expr
            bs.chatmessage(f"🧮 {problem} = {self._expr}")
        except Exception as e:
            try:
                push(f"CalcMod error: {e}", color=(1, 0.3, 0.3))
            except Exception:
                pass

    def _close(self):
        try:
            bui.containerwidget(edit=self._root_widget, transition="out_scale")
        except Exception:
            pass
        global _calc_window
        _calc_window = None


def _on_calc_press(party_window):
    global _calc_window
    try:
        if _calc_window is not None and _widget_exists(_calc_window.root_widget):
            return  # از قبل بازه، دوباره باز نکن
        _calc_window = _CalcWindow(party_window)
    except Exception as e:
        try:
            push(f"CalcMod error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# پنجره‌ی «تنظیمات ۱: رنگ آیکون‌ها» (از هاب تنظیمات باز میشه، پایین‌تر توضیح داده شده)
# اینجا هرچی تغییر بدی هم فوری روی دکمه‌های پنجره‌ی پارتی (اگه بازه) اعمال میشه،
# هم توی کانفیگ بازی ذخیره میشه، پس بعد از بستن/باز کردنِ بازی هم می‌مونه.
# صفحه اسکرول‌پذیره، پس هر چندتا دکمه/رنگ بعداً اضافه بشه، جا براش هست و لازم نیست
# اندازه‌ی پنل عوض بشه.

# پالت رنگ‌های آماده برای انتخاب پس‌زمینه/نوشته
_PALETTE = [
    (0.0, 0.0, 0.0),   # مشکی
    (1.0, 1.0, 1.0),   # سفید
    (0.5, 0.5, 0.5),   # خاکستری
    (1.0, 0.2, 0.2),   # قرمز
    (1.0, 0.55, 0.1),  # نارنجی
    (1.0, 0.85, 0.1),  # زرد
    (0.3, 0.85, 0.3),  # سبز
    (0.2, 0.85, 0.85),  # فیروزه‌ای
    (0.3, 0.5, 1.0),   # آبی
    (0.7, 0.3, 1.0),   # بنفش
]

SETTINGS_PANEL_WIDTH = 840
SETTINGS_PANEL_HEIGHT = 690
SETTINGS_PANEL_COLOR = (0.12, 0.12, 0.17)

# ### اندازه‌ی دکمه‌های رنگ: اگه بازم بهم‌چسبیده به نظر رسید، همین دوتا رو بزرگ‌تر کن
SWATCH_SIZE = 32
SWATCH_GAP = 12

_SECTION_ORDER = ["ping", "ip", "calc", "bon", "mlon", "fix", "radar"]
_color_window = None  # رفرنس زنده نگه‌داشتن پنجره


class _ColorSettingsWindow:
    def __init__(self):
        w = SETTINGS_PANEL_WIDTH
        h = SETTINGS_PANEL_HEIGHT
        self._width = w
        self._height = h
        self._previews = {}

        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = w, h
        pos_x = (sw - w) / 2
        pos_y = (sh - h) / 2

        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"),
            position=(pos_x, pos_y),
            size=(w, h),
            transition="in_scale",
            scale=1.0,
            color=SETTINGS_PANEL_COLOR,
        )
        self._root_widget = self.root_widget

        # عنوان
        bui.textwidget(
            parent=self._root_widget,
            position=(0, h - 34),
            size=(w, 24),
            text="🎨 تنظیمات ۱ - رنگ آیکون‌ها",
            h_align="center",
            v_align="center",
            scale=1.1,
            color=(1, 1, 1),
        )

        # دکمه‌ی بستن (بالا-راست)
        bw(
            parent=self._root_widget,
            position=(w - 18 - 52, h - 64),
            size=(52, 52),
            button_type="square",
            label="✕",
            text_scale=1.25,
            color=CALC_CLOSE_COLOR,
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._close),
        )

        # --- ناحیه‌ی اسکرول‌پذیر: هرچقدر بخش (دکمه) بیشتر بشه، همینجا بالا/پایین میشه ---
        margin = 20
        bottom_bar_h = 56
        scroll_y = bottom_bar_h
        scroll_h = h - 60 - bottom_bar_h
        scroll_w = w - 2 * margin

        sec_h = 140
        content_h = max(scroll_h, 20 + len(_SECTION_ORDER) * sec_h)

        try:
            self._scroll = bui.scrollwidget(
                parent=self._root_widget,
                position=(margin, scroll_y),
                size=(scroll_w, scroll_h),
                highlight=False,
                capture_arrows=True,
            )
            self._content = bui.containerwidget(
                parent=self._scroll,
                size=(scroll_w, content_h),
                background=False,
            )
        except Exception:
            # ### fallback خیلی نادر: اگه اسکرول‌ویجت در دسترس نبود، مستقیم روی پنل بساز
            self._scroll = None
            self._content = self._root_widget

        sec_top = content_h - 20
        for key in _SECTION_ORDER:
            self._build_section(key, 10, sec_top)
            sec_top -= sec_h

        # دکمه‌های پایین (بیرون از ناحیه‌ی اسکرول، همیشه دیده میشن): بازنشانی همه + بستن
        bw(
            parent=self._root_widget,
            position=(margin, 14),
            size=(160, 34),
            button_type="square",
            label="بازنشانی همه",
            text_scale=0.8,
            color=(0.35, 0.35, 0.4),
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._reset_all),
        )
        bw(
            parent=self._root_widget,
            position=(w - margin - 160, 14),
            size=(160, 34),
            button_type="square",
            label="بستن",
            text_scale=0.85,
            color=(0.2, 0.45, 0.25),
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._close),
        )

    def _build_section(self, key, x, top):
        c = _colors[key]
        label = _LABELS[key]

        bui.textwidget(
            parent=self._content,
            position=(x, top),
            size=(70, 22),
            text=label,
            h_align="left",
            v_align="center",
            scale=1.0,
            color=(1, 1, 1),
        )

        # پیش‌نمایش زنده‌ی دکمه (همیشه رنگ فعلیِ ذخیره‌شده رو نشون می‌ده)
        preview = bw(
            parent=self._content,
            position=(x + 60, top - 4),
            size=(54, 28),
            button_type="square",
            label=label,
            text_scale=0.8,
            color=c["bg"],
            textcolor=c["text"],
            autoselect=True,
            on_activate_call=lambda: None,
        )
        self._previews[key] = preview

        self._add_swatch_row(x, top - 44, "زمینه", key, "bg")
        self._add_swatch_row(x, top - 44 - (SWATCH_SIZE + 16), "متن", key, "text")

    def _add_swatch_row(self, x, y, row_label, key, which):
        bui.textwidget(
            parent=self._content,
            position=(x, y + SWATCH_SIZE / 2 - 8),
            size=(52, 18),
            text=row_label,
            h_align="left",
            v_align="center",
            scale=0.75,
            color=(0.8, 0.8, 0.85),
        )
        sx = x + 56
        for color in _PALETTE:
            bw(
                parent=self._content,
                position=(sx, y),
                size=(SWATCH_SIZE, SWATCH_SIZE),
                button_type="square",
                label="",
                color=color,
                autoselect=True,
                on_activate_call=bui.WeakCall(self._pick, key, which, color),
            )
            sx += SWATCH_SIZE + SWATCH_GAP

    def _pick(self, key, which, color):
        _apply_color(key, which, color)
        preview = self._previews.get(key)
        if preview is not None and _widget_exists(preview):
            try:
                if which == "bg":
                    bw(edit=preview, color=color)
                else:
                    bw(edit=preview, textcolor=color)
            except Exception:
                pass

    def _reset_all(self):
        for key, default in _DEFAULT_COLORS.items():
            _apply_color(key, "bg", default["bg"])
            _apply_color(key, "text", default["text"])
            preview = self._previews.get(key)
            if preview is not None and _widget_exists(preview):
                try:
                    bw(edit=preview, color=default["bg"], textcolor=default["text"])
                except Exception:
                    pass

    def _close(self):
        try:
            bui.containerwidget(edit=self._root_widget, transition="out_scale")
        except Exception:
            pass
        global _color_window
        _color_window = None


def _open_color_settings():
    global _color_window
    try:
        if _color_window is not None and _widget_exists(_color_window.root_widget):
            return  # از قبل بازه
        _color_window = _ColorSettingsWindow()
    except Exception as e:
        try:
            push(f"StudioBon settings error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# پنجره‌ی «تنظیمات ۲: جا / اندازه / شکل آیکون‌ها»
# دقیقاً مثل پنل رنگ‌ها اسکرول‌پذیره؛ هر بخش، موقعیت X/Y، اندازه و شکل (مربع/مستطیل)
# یه آیکون رو نشون می‌ده. جا/اندازه فوری روی پنجره‌ی بازِ پارتی اعمال میشن، شکل هم تا
# جایی که بازی اجازه بده فوریه، وگرنه بعد از بازکردنِ دوباره‌ی پنجره‌ی پارتی.

LAYOUT_PANEL_WIDTH = SETTINGS_PANEL_WIDTH
LAYOUT_PANEL_HEIGHT = SETTINGS_PANEL_HEIGHT
LAYOUT_PANEL_COLOR = SETTINGS_PANEL_COLOR

_layout_window = None  # رفرنس زنده نگه‌داشتن پنجره


class _LayoutSettingsWindow:
    def __init__(self):
        w = LAYOUT_PANEL_WIDTH
        h = LAYOUT_PANEL_HEIGHT
        self._width = w
        self._height = h
        self._previews = {}
        self._preview_pos = {}
        self._value_labels = {}
        self._shape_buttons = {}

        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = w, h
        pos_x = (sw - w) / 2
        pos_y = (sh - h) / 2

        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"),
            position=(pos_x, pos_y),
            size=(w, h),
            transition="in_scale",
            scale=1.0,
            color=LAYOUT_PANEL_COLOR,
        )
        self._root_widget = self.root_widget

        bui.textwidget(
            parent=self._root_widget,
            position=(0, h - 34),
            size=(w, 24),
            text="📐 تنظیمات ۲ - جا / اندازه / شکل آیکون‌ها",
            h_align="center",
            v_align="center",
            scale=1.1,
            color=(1, 1, 1),
        )

        bw(
            parent=self._root_widget,
            position=(w - 18 - 52, h - 64),
            size=(52, 52),
            button_type="square",
            label="✕",
            text_scale=1.25,
            color=CALC_CLOSE_COLOR,
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._close),
        )

        margin = 20
        bottom_bar_h = 56
        scroll_y = bottom_bar_h
        scroll_h = h - 60 - bottom_bar_h
        scroll_w = w - 2 * margin

        self._row_w = scroll_w - 20
        sec_h = 205
        content_h = max(scroll_h, 20 + len(_SECTION_ORDER) * sec_h)

        try:
            self._scroll = bui.scrollwidget(
                parent=self._root_widget,
                position=(margin, scroll_y),
                size=(scroll_w, scroll_h),
                highlight=False,
                capture_arrows=True,
            )
            self._content = bui.containerwidget(
                parent=self._scroll,
                size=(scroll_w, content_h),
                background=False,
            )
        except Exception:
            self._scroll = None
            self._content = self._root_widget

        sec_top = content_h - 20
        for key in _SECTION_ORDER:
            self._build_section(key, 10, sec_top)
            sec_top -= sec_h

        bw(
            parent=self._root_widget,
            position=(margin, 14),
            size=(160, 34),
            button_type="square",
            label="بازنشانی همه",
            text_scale=0.8,
            color=(0.35, 0.35, 0.4),
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._reset_all),
        )
        bw(
            parent=self._root_widget,
            position=(w - margin - 160, 14),
            size=(160, 34),
            button_type="square",
            label="بستن",
            text_scale=0.85,
            color=(0.2, 0.45, 0.25),
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._close),
        )

    def _build_section(self, key, x, top):
        cfg = _layout[key]
        label = _LABELS[key]
        row_w = self._row_w

        bui.textwidget(
            parent=self._content,
            position=(x, top),
            size=(70, 22),
            text=label,
            h_align="left",
            v_align="center",
            scale=1.0,
            color=(1, 1, 1),
        )

        preview_pos = (x + 60, top - 4)
        self._preview_pos[key] = preview_pos
        preview = bw(
            parent=self._content,
            position=preview_pos,
            size=(44, 44),
            button_type=_shape_button_type(cfg["shape"]),
            label=label,
            text_scale=0.7,
            color=_colors[key]["bg"],
            textcolor=_colors[key]["text"],
            autoselect=True,
            on_activate_call=lambda: None,
        )
        self._previews[key] = preview

        row1_y = top - 56
        self._build_stepper(key, "x", "X", x, row1_y, row_w / 2 - 10)
        self._build_stepper(key, "y", "Y", x + row_w / 2 + 10, row1_y, row_w / 2 - 10)

        row2_y = row1_y - 42
        self._build_stepper(key, "size", "اندازه", x, row2_y, row_w)

        row3_y = row2_y - 48
        self._build_shape_row(key, x, row3_y, row_w)

    def _build_stepper(self, key, field, label, x, y, width):
        cfg = _layout[key]
        btn_size = 26
        minus_x = x + width - (btn_size * 2 + 6)
        plus_x = x + width - btn_size
        text_w = max(40, width - 2 * btn_size - 14)

        value_widget = bui.textwidget(
            parent=self._content,
            position=(x, y + 4),
            size=(text_w, 18),
            text=f"{label}: {cfg[field]}",
            h_align="left",
            v_align="center",
            scale=0.8,
            color=(0.85, 0.85, 0.9),
        )
        self._value_labels[f"{key}_{field}"] = value_widget

        bw(
            parent=self._content,
            position=(minus_x, y),
            size=(btn_size, btn_size),
            button_type="square",
            label="-",
            text_scale=1.0,
            color=(0.3, 0.3, 0.38),
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._step, key, field, -1, label),
        )
        bw(
            parent=self._content,
            position=(plus_x, y),
            size=(btn_size, btn_size),
            button_type="square",
            label="+",
            text_scale=1.0,
            color=(0.3, 0.3, 0.38),
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._step, key, field, 1, label),
        )

    def _build_shape_row(self, key, x, y, width):
        btn_w = (width - 2 * 10) / 3
        bx = x
        self._shape_buttons[key] = {}
        for shape in _SHAPES:
            selected = _layout[key]["shape"] == shape
            btn = bw(
                parent=self._content,
                position=(bx, y),
                size=(btn_w, 30),
                button_type="square",
                label=_SHAPE_LABELS[shape],
                text_scale=0.75,
                color=(0.25, 0.55, 0.3) if selected else (0.25, 0.25, 0.32),
                textcolor=(1, 1, 1),
                autoselect=True,
                on_activate_call=bui.WeakCall(self._pick_shape, key, shape),
            )
            self._shape_buttons[key][shape] = btn
            bx += btn_w + 10

    # -- منطق دکمه‌ها --

    def _step(self, key, field, direction, label):
        step = _LAYOUT_STEP[field]
        current = _layout[key][field]
        _apply_layout(key, **{field: current + direction * step})
        new_val = _layout[key][field]
        widget = self._value_labels.get(f"{key}_{field}")
        if widget is not None and _widget_exists(widget):
            try:
                bui.textwidget(edit=widget, text=f"{label}: {new_val}")
            except Exception:
                pass

    def _pick_shape(self, key, shape):
        _apply_layout(key, shape=shape)
        for s, btn in self._shape_buttons.get(key, {}).items():
            if _widget_exists(btn):
                try:
                    bw(edit=btn, color=(0.25, 0.55, 0.3) if s == shape else (0.25, 0.25, 0.32))
                except Exception:
                    pass
        self._rebuild_preview(key)

    def _rebuild_preview(self, key):
        old = self._previews.get(key)
        pos = self._preview_pos.get(key)
        if old is None or pos is None or not _widget_exists(old):
            return
        cfg = _layout[key]
        try:
            bui.widget(edit=old, delete=True)
        except Exception:
            return  # نتونستیم حذفش کنیم؛ پیش‌نمایش با همون شکل قبلی می‌مونه
        try:
            new_preview = bw(
                parent=self._content,
                position=pos,
                size=(44, 44),
                button_type=_shape_button_type(cfg["shape"]),
                label=_LABELS[key],
                text_scale=0.7,
                color=_colors[key]["bg"],
                textcolor=_colors[key]["text"],
                autoselect=True,
                on_activate_call=lambda: None,
            )
            self._previews[key] = new_preview
        except Exception:
            pass

    def _reset_all(self):
        field_labels = {"x": "X", "y": "Y", "size": "اندازه"}
        for key, default in _DEFAULT_LAYOUT.items():
            _apply_layout(
                key,
                x=default["x"],
                y=default["y"],
                size=default["size"],
                shape=default["shape"],
            )
            for field, flabel in field_labels.items():
                widget = self._value_labels.get(f"{key}_{field}")
                if widget is not None and _widget_exists(widget):
                    try:
                        bui.textwidget(edit=widget, text=f"{flabel}: {default[field]}")
                    except Exception:
                        pass
            for s, btn in self._shape_buttons.get(key, {}).items():
                if _widget_exists(btn):
                    try:
                        bw(edit=btn, color=(0.25, 0.55, 0.3) if s == default["shape"] else (0.25, 0.25, 0.32))
                    except Exception:
                        pass
            self._rebuild_preview(key)

    def _close(self):
        try:
            bui.containerwidget(edit=self._root_widget, transition="out_scale")
        except Exception:
            pass
        global _layout_window
        _layout_window = None


def _open_layout_settings():
    global _layout_window
    try:
        if _layout_window is not None and _widget_exists(_layout_window.root_widget):
            return  # از قبل بازه
        _layout_window = _LayoutSettingsWindow()
    except Exception as e:
        try:
            push(f"StudioBon settings error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# هاب تنظیمات: چیزی که با زدن دکمه‌ی «تنظیمات» کنار مود توی لیست افزونه‌ها باز میشه.
# هر پنل جدا (مثل همین رنگ آیکون‌ها) یه ردیفِ شماره‌دار توی این هاب می‌گیره.
#
# 🏷️ TAG-NEW-SETTINGS-PANEL (خودت، برای خودت):
#   هر وقت کاربر یه پنل تنظیماتِ کاملاً جدا و جدید خواست (نه فقط رنگ)، بدون اینکه
#   بهت بگه شماره‌ش چنده، فقط یه تابع «_open_...» مثل _open_color_settings بساز و
#   یه ردیف جدید به لیست _SETTINGS_MODULES زیر اضافه کن؛ شماره‌گذاری (۱، ۲، ۳...) و
#   دکمه‌ش توی هاب خودکار درست میشه، لازم نیست جای دیگه‌ای دست بزنی.
_SETTINGS_MODULES = [
    {"title": "رنگ دکمه ها", "icon": "🎨", "open": _open_color_settings},
    {"title": "مکان/سایز/شکل دکمه ها", "icon": "📐", "open": _open_layout_settings},
]

HUB_PANEL_WIDTH = 840
HUB_PANEL_HEIGHT = 600
HUB_PANEL_COLOR = (0.12, 0.12, 0.17)

_hub_window = None


class _SettingsHubWindow:
    def __init__(self):
        w = HUB_PANEL_WIDTH
        h = max(HUB_PANEL_HEIGHT, 110 + len(_SETTINGS_MODULES) * 56)
        self._width = w
        self._height = h

        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = w, h
        pos_x = (sw - w) / 2
        pos_y = (sh - h) / 2

        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"),
            position=(pos_x, pos_y),
            size=(w, h),
            transition="in_scale",
            scale=1.0,
            color=HUB_PANEL_COLOR,
        )
        self._root_widget = self.root_widget

        bui.textwidget(
            parent=self._root_widget,
            position=(0, h - 34),
            size=(w, 24),
            text="⚙️ BonMod",
            h_align="center",
            v_align="center",
            scale=1.1,
            color=(1, 1, 1),
        )

        bw(
            parent=self._root_widget,
            position=(w - 16 - 26, h - 40),
            size=(26, 26),
            button_type="square",
            label="✕",
            text_scale=0.8,
            color=CALC_CLOSE_COLOR,
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._close),
        )

        margin = 20
        row_top = h - 74
        row_h = 56
        for i, module in enumerate(_SETTINGS_MODULES, start=1):
            self._build_row(i, module, margin, row_top)
            row_top -= row_h

    def _build_row(self, number, module, margin, top):
        icon = module.get("icon", "🔧")
        label = f"{number}. {icon}  {module['title']}"
        bw(
            parent=self._root_widget,
            position=(margin, top - 40),
            size=(self._width - 2 * margin, 40),
            button_type="square",
            label=label,
            text_scale=0.95,
            color=(0.2, 0.2, 0.28),
            textcolor=(1, 1, 1),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._open_module, module),
        )

    def _open_module(self, module):
        self._close()
        module["open"]()

    def _close(self):
        try:
            bui.containerwidget(edit=self._root_widget, transition="out_scale")
        except Exception:
            pass
        global _hub_window
        _hub_window = None


def _open_settings_hub():
    global _hub_window
    try:
        if _hub_window is not None and _widget_exists(_hub_window.root_widget):
            return  # از قبل بازه
        _hub_window = _SettingsHubWindow()
    except Exception as e:
        try:
            push(f"StudioBon settings error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Game Timer: زمان از لحظه‌ی ورود به سرور شروع می‌شود.
_game_session_started_at = None


def _format_game_timer():
    if _game_session_started_at is None:
        return 0, 0
    elapsed = max(0, int(time.time() - _game_session_started_at))
    return elapsed // 60, elapsed % 60


def _on_timer_press():
    try:
        minutes, seconds = _format_game_timer()
        bs.chatmessage("Game Timer ⏲️ : %dmin/%ds" % (minutes, seconds))
    except Exception as e:
        try:
            push(f"StudioBon error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# پنجره‌ی کوچک Bon
_mlon_window = None


class _BonWindow:
    def __new__(cls):
        # V2 window implementation.
        return _BonV2Window()

def _on_mlon_press():
    global _mlon_window
    try:
        if _mlon_window is not None and _widget_exists(_mlon_window.root_widget):
            return
        _mlon_window = _BonWindow()
    except Exception as e:
        try:
            push(f"StudioBon error: {e}", color=(1, 0.3, 0.3))
        except Exception:
            pass


# کال‌بکِ هر دکمه.

# ---------------------------------------------------------------------------
# Bon V2 - extra tools
# ---------------------------------------------------------------------------
_net_mode = False
_spam_mode = False
_spam_token = 0
_spam_text = ""

# A compact offline Finglish dictionary. This is intentionally a transliteration
# helper (not a translation service); unknown words are left mostly intact.
_FINGLISH_WORDS = {
    "salam":"سلام","slm":"سلام","man":"من","to":"تو","toro":"تو رو","ro":"رو",
    "dostet":"دوستت","dost":"دوست","nadaram":"ندارم","daram":"دارم","dare":"داره",
    "dooset":"دوست","doostet":"دوستت","dooset":"دوست","kheili":"خیلی","kheilii":"خیلی",
    "khob":"خوب","khoobi":"خوبی","chetori":"چطوری","chetoori":"چطوری",
    "chi":"چی","chera":"چرا","che":"چه","ino":"اینو","in":"این","oon":"اون",
    "oono":"اونو","yek":"یک","ye":"یه","manam":"منم","toam":"تو هم",
    "ham":"هم","hamishe":"همیشه","alan":"الان","emrooz":"امروز","farda":"فردا",
    "diruz":"دیروز","bia":"بیا","boro":"برو","biyar":"بیار","berim":"بریم",
    "mikham":"میخوام","mikhay":"میخوای","mikone":"میکنه","mikonam":"میکنم",
    "nakon":"نکن","naro":"نرو","naro":"نرو","beshin":"بشین","besh":"باش",
    "bashe":"باشه","ok":"اوکی","merci":"مرسی","mamnoon":"ممنون","lotfan":"لطفا",
    "bebakhshid":"ببخشید","bebakhsh":"ببخش","khodafez":"خداحافظ","dorood":"درود",
    "eshgh":"عشق","eshghe":"عشقه","ali":"عالی","kheili":"خیلی","bad":"بد",
    "lag":"لگ","ping":"پینگ","bazi":"بازی","game":"گیم","server":"سرور",
    "chat":"چت","bro":"داداش","dadash":"داداش","agha":"آقا","baba":"بابا",
    "chon":"چون","chonke":"چونکه","vali":"ولی","ama":"اما","agar":"اگر",
    "age":"اگه","ke":"که","va":"و","ya":"یا","ba":"با","baraye":"برای",
    "az":"از","be":"به","ta":"تا","dar":"در","ro":"رو","ye":"یه","hamin":"همین",
    "hanooz":"هنوز","vaghti":"وقتی","vaghean":"واقعا","vaghean":"واقعاً",
    "doroste":"درسته","dorost":"درست","khodam":"خودم","khodet":"خودت",
    "khodemun":"خودمون","mige":"میگه","migam":"میگم","goft":"گفت","go":"گو",
    "begoo":"بگو","begu":"بگو","bebin":"ببین","didam":"دیدم","midoni":"میدونی",
    "midunam":"میدونم","nemidunam":"نمیدونم","nemishe":"نمیشه","mishe":"میشه",
    "mitooni":"میتونی","mitoni":"میتونی","mitunam":"میتونم","mitonam":"میتونم",
    "hasti":"هستی","hastam":"هستم","nist":"نیست","nisti":"نیستی",
    "cheshmat":"چشمت","cheshm":"چشم","khande":"خنده","bekhand":"بخند",
    "moshkel":"مشکل","dorostesh":"درستش","komak":"کمک","yeki":"یکی",
    "hame":"همه","hamechi":"همه‌چی","har":"هر","bar":"بار","sob":"صبح",
    "shab":"شب","rooz":"روز","saat":"ساعت","esme":"اسم","esm":"اسم",
    "jafarii":"جعفری","jafari":"جعفری",
}

# Expanded Finglish phrase/word map for common Persian chat writing.
_FINGLISH_EXTRA = {
    "bi sharaf":"بی شرف", "b sharaf":"بی شرف", "bisharaf":"بی شرف",
    "ostad":"استاد", "oostaad":"استاد", "chetori":"چطوری",
    "halet chetore":"حالت چطوره", "haletchetore":"حالت چطوره",
    "halet chetore?":"حالت چطوره؟", "khubi":"خوبی", "khobi":"خوبی",
    "khobam":"خوبم", "khoshgele":"خوشگله", "khoshgel":"خوشگل",
    "che khabar":"چه خبر", "chekhabar":"چه خبر", "khosh omadi":"خوش اومدی",
    "khosh amadid":"خوش آمدید", "merci dadash":"مرسی داداش",
    "dastet dard nakone":"دستت درد نکنه", "dastet dard nakone":"دستت درد نکنه",
    "boro baba":"برو بابا", "bia inja":"بیا اینجا", "kojaei":"کجایی",
    "kojayi":"کجایی", "chi kar mikoni":"چی کار میکنی",
    "chi kar mikoni?":"چی کار میکنی؟", "chi migi":"چی میگی",
    "chi migi?":"چی میگی؟", "nemidunam":"نمیدونم", "nemidoni":"نمیدونی",
    "midoni":"میدونی", "midunam":"میدونم", "dige":"دیگه",
    "vaghean":"واقعاً", "vaghti":"وقتی", "asheghatam":"عاشقتم",
    "dooset daram":"دوستت دارم", "dostet daram":"دوستت دارم",
    "dooset nadaram":"دوستت ندارم", "dostet nadaram":"دوستت ندارم",
    "bezan":"بزن", "nazanin":"نازنین", "khafan":"خفن", "عالی":"عالی",
}
_FINGLISH_WORDS.update(_FINGLISH_EXTRA)
# Expanded high-priority vocabulary adapted from the reference Self mod.
# Exact words/phrases win before phonetic fallback to avoid letter-by-letter noise.
_FINGLISH_WORDS.update({
    "khoda":"خدا", "jahan":"جهان", "donya":"دنیا", "zendegi":"زندگی",
    "rooz":"روز", "mah":"ماه", "sal":"سال", "keshvar":"کشور", "shahr":"شهر",
    "khane":"خانه", "otagh":"اتاق", "madar":"مادر", "pedar":"پدر",
    "baradar":"برادر", "khahar":"خواهر", "doshman":"دشمن", "raees":"رئیس",
    "karmand":"کارمند", "ziba":"زیبا", "zesht":"زشت", "bozorg":"بزرگ",
    "koochak":"کوچک", "boland":"بلند", "kootaah":"کوتاه", "sari":"سریع",
    "kond":"کند", "geran":"گران", "arzan":"ارزان", "chegone":"چگونه",
    "koja":"کجا", "ki":"کی", "khodahafez":"خداحافظ", "bebakhshid":"ببخشید",
    "khahesh":"خواهش", "ishan":"ایشان", "anha":"آنها", "shoma":"شما",
    "hast":"هست", "ast":"است", "bud":"بود", "shod":"شد", "kard":"کرد",
    "goft":"گفت", "dad":"داد", "khord":"خورد", "amad":"آمد", "raft":"رفت",
    "did":"دید", "shenid":"شنید", "ghabl":"قبل", "bad az":"بعد از",
    "emkan":"امکان", "dorost":"درست", "mamulan":"معمولاً", "albate":"البته",
    "fekr":"فکر", "midoonam":"میدونم", "nemidoonam":"نمیدونم",
    "mikhaham":"میخوام", "mikham":"میخوام", "mitavanam":"میتونم",
    "mishe":"میشه", "nemishe":"نمیشه", "bayad":"باید", "nabood":"نبود",
    "hame":"همه", "hamechi":"همه‌چی", "hich":"هیچ", "chizi":"چیزی",
    "chera":"چرا", "chon":"چون", "chonke":"چونکه", "agar":"اگر", "age":"اگه",
    "vali":"ولی", "ama":"اما", "baraye":"برای", "vaghean":"واقعاً",
    "khoshgel":"خوشگل", "khoshgele":"خوشگله", "khafan":"خفن",
    "halet chetore":"حالت چطوره", "che khabar":"چه خبر",
    "salam chetori":"سلام چطوری", "dooset daram":"دوستت دارم",
    "dostet daram":"دوستت دارم", "merci dadash":"مرسی داداش",
    "dastet dard nakone":"دستت درد نکنه", "bia inja":"بیا اینجا",
    "chi kar mikoni":"چی کار میکنی", "chi migi":"چی میگی",
})

def _finglish_word(word):
    lw = word.lower()
    if lw in _FINGLISH_WORDS:
        return _FINGLISH_WORDS[lw]
    # Conservative phonetic fallback for common Latin phonemes.
    # It is not a full NLP translator; known words above take priority.
    if not re.search(r"[a-zA-Z]", word):
        return word
    x = lw
    reps = [
        ("kh","خ"),("gh","غ"),("sh","ش"),("ch","چ"),("zh","ژ"),
        ("aa","ا"),("ee","ی"),("oo","و"),("ou","و"),
    ]
    for a,b in reps:
        x = x.replace(a,b)
    chars = {
        "a":"ا","b":"ب","c":"ک","d":"د","e":"ه","f":"ف","g":"گ",
        "h":"ه","i":"ی","j":"ج","k":"ک","l":"ل","m":"م","n":"ن",
        "o":"و","p":"پ","q":"ق","r":"ر","s":"س","t":"ت","u":"و",
        "v":"و","w":"و","x":"کس","y":"ی","z":"ز"
    }
    # Keep common multi-letter sound patterns ahead of single-letter conversion.
    return "".join(chars.get(ch,ch) for ch in x)

def _finglish_convert_text(msg):
    if not _finglish_mode or not isinstance(msg, str):
        return msg
    # Preserve the sender prefix (usually "Name: ").
    prefix = ""
    body = msg
    if ":" in msg:
        prefix, body = msg.split(":", 1)
        prefix += ":"
    if not re.search(r"[A-Za-z]", body):
        return msg
    # Common multi-word phrases first.
    phrase_map = {
        "man dostet nadaram": "من دوستت ندارم",
        "man doostet nadaram": "من دوستت ندارم",
        "salam chetori": "سلام چطوری",
        "salam chetori": "سلام چطوری",
        "kheili khob": "خیلی خوب",
        "merci kheyli": "مرسی خیلی",
    }
    norm = re.sub(r"\s+", " ", body.strip()).lower()
    # Longest phrases first; this prevents pieces like "halet"/"chetore"
    # from being transliterated separately when the full phrase is known.
    all_phrases = dict(phrase_map)
    all_phrases.update(_FINGLISH_EXTRA)
    all_phrases.update({k: v for k, v in _FINGLISH_WORDS.items() if " " in k})
    for phrase in sorted(all_phrases, key=len, reverse=True):
        if norm == phrase:
            return prefix + " 💬 " + all_phrases[phrase]
    parts = re.split(r"(\s+|[,.!?؛،:;()\[\]{}]+)", body)
    out = []
    for part in parts:
        if not part:
            continue
        if re.fullmatch(r"\s+|[,.!?؛،:;()\[\]{}]+", part):
            out.append(part)
        else:
            out.append(_finglish_word(part))
    return prefix + " 💬 " + "".join(out)

def _show_toggle(text):
    try:
        push(text, color=(0.2, 1.0, 0.2), transient=True)
    except Exception:
        push(text, color=(0.2, 1.0, 0.2))

def _on_net_toggle():
    global _net_mode
    _net_mode = not _net_mode
    # Best-effort local/network hinting only. BombSquad's engine networking
    # remains untouched; Python cannot guarantee lower server latency.
    try:
        if _net_mode:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
                if hasattr(socket, "IPPROTO_IP") and hasattr(socket, "IP_TOS"):
                    s.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)
            finally:
                s.close()
    except Exception:
        pass
    _show_toggle("UntiLag ON♻️" if _net_mode else "UntiLag OFF🚫")

def _spam_step(token, index):
    global _spam_mode
    if not _spam_mode or token != _spam_token or index >= 1000:
        return
    msg = _spam_text + ("-" if index % 2 == 1 else "")
    try:
        bs.chatmessage(msg)
    except Exception:
        pass
    if index + 1 < 1000:
        teck(2.0, lambda: _spam_step(token, index + 1))

def _on_spam_toggle():
    global _spam_mode, _spam_token, _spam_text
    if _spam_mode:
        _spam_mode = False
        _spam_token += 1
        _show_toggle("spam off")
        return
    text = ""
    try:
        if _spam_window is not None and _widget_exists(_spam_window.root_widget):
            queried = bui.textwidget(query=_spam_window.input_widget)
            if queried is not None:
                text = str(queried).strip()
    except Exception as exc:
        print(f"StudioBon spam input read error: {exc}")
    if not text:
        _show_toggle("spam off")
        return
    _spam_text = text
    _spam_mode = True
    _spam_token += 1
    token = _spam_token
    _show_toggle("spam on")
    teck(0.01, lambda: _spam_step(token, 0))

def _open_spam_window():
    global _spam_window
    try:
        if _spam_window is not None and _widget_exists(_spam_window.root_widget):
            return
        _spam_window = _SpamWindow()
    except Exception as e:
        push(f"StudioBon error: {e}", color=(1, 0.3, 0.3))

def _on_finglish_toggle():
    global _finglish_mode
    _finglish_mode = not _finglish_mode
    _show_toggle("Finglish on" if _finglish_mode else "Finglish off")

class _SpamWindow:
    def __init__(self):
        self._width = 560
        self._height = 340
        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = self._width, self._height
        x = max(20, (sw - self._width) * 0.5)
        y = max(20, (sh - self._height) * 0.5)
        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"), position=(x,y), size=(self._width,self._height),
            transition="in_scale", scale=1.0, color=(0.10,0.06,0.10))
        bui.textwidget(parent=self.root_widget, position=(0,270), size=(self._width,40),
                       text="spam massage", h_align="center", v_align="center",
                       scale=1.3, color=(1.0,0.55,0.8))
        self.input_widget = bui.textwidget(parent=self.root_widget, position=(35,105),
                       size=(self._width-70,130), editable=True, text="",
                       maxwidth=self._width-90, v_align="top", h_align="left",
                       color=(1,1,1), flatness=1.0, shadow=0.3)
        bw(parent=self.root_widget, position=(150,45), size=(260,50),
           button_type="square", label="on/off", text_scale=1.0,
           color=(0.15,0.45,1.0), textcolor=(1,1,1),
           autoselect=True, on_activate_call=_on_spam_toggle)
        bw(parent=self.root_widget, position=(self._width-55,self._height-45),
           size=(30,30), button_type="square", label="✕", text_scale=0.8,
           color=(0.45,0.12,0.12), textcolor=(1,1,1),
           on_activate_call=bui.WeakCall(self._close))
    def _close(self):
        global _spam_window
        try: bui.containerwidget(edit=self.root_widget, transition="out_scale")
        except Exception: pass
        _spam_window = None


# ---------------------------------------------------------------------------
# Character Party: same timer/token pattern as Party🪩, with the requested sequence.
_character_party_mode = False
_character_party_token = 0
_CHARACTER_PARTY_SEQUENCE = ["Bon", "Nin", "Spa", "Ber", "Tao", "Fro", "Pix", "Kro", "Zoe", "San", "B90"]
_CHARACTER_PARTY_DELAY = 1.5


def _character_party_step(token, index=0):
    if not _character_party_mode or token != _character_party_token:
        return
    try:
        bs.chatmessage(_CHARACTER_PARTY_SEQUENCE[index])
    except Exception as exc:
        try: print("StudioBon Character Party send error: " + str(exc))
        except Exception: pass
    next_index = (index + 1) % len(_CHARACTER_PARTY_SEQUENCE)
    teck(_CHARACTER_PARTY_DELAY, lambda: _character_party_step(token, next_index))


def _on_character_party_toggle():
    global _character_party_mode, _character_party_token
    _character_party_mode = not _character_party_mode
    _character_party_token += 1
    if _character_party_mode:
        try: push("Character Party Start🎭", color=(1.0, 1.0, 1.0), transient=True)
        except Exception: push("Character Party Start🎭", color=(1.0, 1.0, 1.0))
        _character_party_step(_character_party_token, 0)
    else:
        try: push("Character Party Ended🪬", color=(0.2, 0.45, 1.0), transient=True)
        except Exception: push("Character Party Ended🪬", color=(0.2, 0.45, 1.0))


# ---------------------------------------------------------------------------
# Party🪩 - repeating requested sequence
_party_mode = False
_party_token = 0
_party_cycle_started = 0.0

_PARTY_SEQUENCE = [
    "Cel a",
    "t 1 0 2",
    "t 0 0 0",
    "t 3 3 3",
    "Cel a",
    "t 22 0 0",
    "t 1 4 9",
    "Cel a",
    "t 2 9 0 0",
    "t 1 9 0 0",
    "Cel a",
    "t 1 9 4 9",
    "t 1 0 0 1",
]

_PARTY_DELAY = 2.5
_PARTY_CM_INTERVAL = 120.0
_PARTY_MIN_SEND_INTERVAL = 2.0
_party_send_queue = []
_party_send_busy = False
_party_last_send_time = 0.0


def _party_send_pump():
    global _party_send_busy, _party_last_send_time
    if not _party_send_queue:
        _party_send_busy = False
        return
    text = _party_send_queue.pop(0)
    try:
        bs.chatmessage(text)
    except Exception:
        pass
    _party_last_send_time = time.monotonic()
    if _party_send_queue:
        teck(_PARTY_MIN_SEND_INTERVAL, _party_send_pump)
    else:
        _party_send_busy = False


def _party_send(text):
    global _party_send_busy
    try:
        _party_send_queue.append(str(text))
        if not _party_send_busy:
            _party_send_busy = True
            elapsed = time.monotonic() - _party_last_send_time
            wait = max(0.0, _PARTY_MIN_SEND_INTERVAL - elapsed)
            teck(wait, _party_send_pump)
    except Exception:
        pass

def _party_cm_cycle(token):
    if not _party_mode or token != _party_token:
        return
    _party_send("cm")
    teck(_PARTY_DELAY, lambda: _party_send_flya(token))
    teck(_PARTY_CM_INTERVAL, lambda: _party_cm_cycle(token))

def _party_send_flya(token):
    if not _party_mode or token != _party_token:
        return
    _party_send("fly a")

def _party_sequence_step(token, index):
    if not _party_mode or token != _party_token:
        return
    if index >= len(_PARTY_SEQUENCE):
        # Restart immediately after the last command; only the cm/fly cycle
        # is governed by the separate 2-minute timer above.
        teck(0.0, lambda: _party_sequence_step(token, 0))
        return
    _party_send(_PARTY_SEQUENCE[index])
    teck(_PARTY_DELAY, lambda: _party_sequence_step(token, index + 1))

def _party_cycle(token):
    if not _party_mode or token != _party_token:
        return
    _party_cm_cycle(token)
    _party_sequence_step(token, 0)

def _on_party_toggle():
    global _party_mode, _party_token
    _party_mode = not _party_mode
    _party_token += 1
    if _party_mode:
        _show_toggle("Party Started🎉🥳")
        _party_cycle(_party_token)
    else:
        _show_toggle("Party Ended🥲")

def _party_label_widget(parent, x, y):
    # Separate letters so each can be independently colored.
    letters = [("P",(0.25,1.0,0.35)),("a",(1.0,0.85,0.1)),
               ("r",(1.0,0.2,0.2)),("t",(0.3,0.65,1.0)),
               ("y",(0.75,0.35,1.0)),("🪩",(1.0,0.7,0.2))]
    curx = x
    for ch,col in letters:
        bui.textwidget(parent=parent, position=(curx,y), size=(34,50),
                       text=ch, h_align="center", v_align="center",
                       scale=1.0, color=col)
        curx += 34

_channel_window = None


def _open_studiobon_channel():
    global _channel_window
    try:
        if _channel_window is not None and _widget_exists(_channel_window.root_widget):
            return
        _channel_window = _StudioBonChannelWindow()
    except Exception as exc:
        try:
            push(f"StudioBon channel error: {exc}", color=(1, 0.3, 0.3))
        except Exception:
            pass


def _join_studiobon_channel():
    url = "https://t.me/StudioBon"
    for owner in (babase, bui):
        try:
            opener = getattr(owner, "open_url", None)
            if callable(opener):
                opener(url)
                return
        except Exception:
            pass
    try:
        push("Telegram: https://t.me/StudioBon", color=(0.2, 0.8, 1.0))
    except Exception:
        pass


class _StudioBonChannelWindow:
    def __init__(self):
        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = 900, 700
        self._width = min(620, max(340, int(sw - 40)))
        self._height = min(500, max(360, int(sh - 40)))
        x = max(20, (sw - self._width) * 0.5)
        y = max(20, (sh - self._height) * 0.5)
        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"), position=(x, y),
            size=(self._width, self._height), transition="in_scale",
            scale=1.0, color=(0.02, 0.10, 0.42))
        bui.textwidget(parent=self.root_widget, position=(20, self._height-58),
                       size=(self._width-90, 40), text="StudioBon Channel",
                       h_align="center", v_align="center", scale=1.15,
                       color=(0.45, 0.9, 1.0))
        bw(parent=self.root_widget, position=(self._width-58, self._height-58),
           size=(38, 38), button_type="square", label="✕", text_scale=0.9,
           color=(0.45, 0.12, 0.12), textcolor=(1, 1, 1),
           on_activate_call=bui.WeakCall(self._close))
        bw(parent=self.root_widget, position=(25, self._height-125),
           size=(self._width-50, 48), button_type="square",
           label="Join channel", text_scale=1.0, color=(0.0, 0.55, 0.95),
           textcolor=(1, 1, 1), autoselect=True,
           on_activate_call=_join_studiobon_channel)
        margin = 22
        scroll_y = 22
        scroll_h = self._height - 170
        scroll_w = self._width - 2 * margin
        content_h = max(scroll_h * 2, 720)
        try:
            scroll = bui.scrollwidget(
                parent=self.root_widget, position=(margin, scroll_y),
                size=(scroll_w, scroll_h), highlight=False,
                capture_arrows=True)
            content = bui.containerwidget(
                parent=scroll, size=(scroll_w, content_h), background=False)
        except Exception:
            content = self.root_widget
            content_h = self._height - 190
        lines = [
            ("چنل ما در تلگرام : StudioBon@", (0.75, 0.95, 1.0), 1.0),
            ("برای اطلاع از آخرین آپدیت های این مود در چنل ما عضو باشید❤️💛", (1.0, 1.0, 1.0), 0.9),
            ("نسخه این مود : ورژن ۲", (0.9, 0.95, 1.0), 0.9),
            ("متناسب با نسخه جدید بمب اسکواد API 9", (0.9, 0.95, 1.0), 0.9),
            ("آیدی سازنده در تلگرام : IR_TV2@", (1.0, 0.9, 0.5), 0.9),
            ("اسم خاص سازنده : Bon", (1.0, 0.9, 0.5), 0.9),
            ("در صورت بروز هر گونه اشکال یا در صورت تمایل به ثبت پیشنهادات و انتقادات به آیدی ذکر شده مراجعه فرمایید😇", (1.0, 1.0, 1.0), 0.85),
        ]
        y_pos = content_h - 28
        for text, color, scale in lines:
            bui.textwidget(parent=content, position=(12, y_pos-58),
                           size=(scroll_w-24, 54), text=text,
                           h_align="center", v_align="center",
                           maxwidth=scroll_w-35, scale=scale, color=color)
            y_pos -= 82

    def _close(self):
        global _channel_window
        try:
            bui.containerwidget(edit=self.root_widget, transition="out_scale")
        except Exception:
            try:
                bui.widget(edit=self.root_widget, delete=True)
            except Exception:
                pass
        _channel_window = None


class _BonV2Window:
    def __init__(self):
        target_w, target_h = 1080, 760
        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = target_w, target_h
        # Keep every control inside the virtual screen.
        self._width = min(target_w, max(420, int(sw - 40)))
        self._height = min(target_h, max(500, int(sh - 40)))
        x = max(20, (sw - self._width) * 0.5)
        y = max(20, (sh - self._height) * 0.5)
        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"), position=(x,y),
            size=(self._width,self._height), transition="in_scale",
            scale=1.0, color=(0.05,0.10,0.07))
        bui.textwidget(parent=self.root_widget, position=(0,self._height-190),
                       size=(self._width,150), text="☠", h_align="center",
                       v_align="center", scale=6.0, color=(0.92,0.92,0.92))
        bui.textwidget(parent=self.root_widget, position=(0,self._height-255),
                       size=(self._width,55), text="Bon Menu", h_align="center",
                       v_align="center", scale=1.65, color=(0.95,0.80,0.12), shadow=1.0, flatness=0.0)
        # Dark decorative frame/3D-style title accents.
        bui.textwidget(parent=self.root_widget, position=(35, self._height-270),
                       size=(180,35), text="🕸", h_align="left", v_align="center",
                       scale=1.2, color=(0.55,0.55,0.55))
        bui.textwidget(parent=self.root_widget, position=(self._width-215, self._height-270),
                       size=(180,35), text="🦇", h_align="right", v_align="center",
                       scale=1.2, color=(0.55,0.55,0.55))
        # Balanced 3-column grid: all existing and new tools remain inside the panel.
        gap = 14
        cols = 3
        bwid = int((self._width - 4 * gap) / cols)
        bh = 48
        row_gap = 9
        top_y = min(420, self._height - 308)
        labels = [
            ("Net", (0.15, 1.0, 0.35), _on_net_toggle),
            ("Spam", (1.0, 0.25, 0.65), _open_spam_window),
            ("Finglish", (0.75, 0.55, 1.0), _on_finglish_toggle),
            ("Party🪩", (0.8, 0.8, 0.8), _on_party_toggle),
            ("Smart Target", (0.2, 0.95, 0.85), _open_smart_target),
            ("Live Ping", (0.25, 0.95, 1.0), _open_live_ping),
            ("Channel", (0.05, 0.82, 0.88), _open_studiobon_channel),
            ("Party🎭", (1.0, 0.12, 0.12), _on_character_party_toggle),
            ("Welcome", (1.0, 0.75, 0.2), _open_welcome_settings),
            ("📁File Manager", (1.0, 0.84, 0.12), _open_file_manager),
        ]
        for idx, (label, text_col, callback) in enumerate(labels):
            row = idx // cols
            col_idx = idx % cols
            bx = gap + col_idx * (bwid + gap)
            this_y = top_y - row * (bh + row_gap)
            button_bg = (0.025, 0.055, 0.085)
            if label == "Channel":
                button_bg = (0.02, 0.32, 0.38)
            bw(parent=self.root_widget, position=(bx, this_y), size=(bwid, bh),
               button_type="square", label=label, text_scale=0.67,
               color=button_bg, textcolor=text_col, autoselect=True,
               on_activate_call=callback)
            if label.startswith("Party"):
                _party_label_widget(self.root_widget, bx + 8, this_y + 8)
        bw(parent=self.root_widget, position=(self._width-70,self._height-60),
           size=(45,45), button_type="square", label="✕", text_scale=1.0,
           color=(0.45,0.12,0.12), textcolor=(1,1,1), autoselect=True,
           on_activate_call=bui.WeakCall(self._close))
    def _close(self):
        global _mlon_window
        try: bui.containerwidget(edit=self.root_widget, transition="out_scale")
        except Exception:
            try: bui.widget(edit=self.root_widget, delete=True)
            except Exception: pass
        _mlon_window = None

_finglish_mode = False
_spam_window = None
_spam_mode = False
_net_mode = False

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# StudioBon V2 feature pack: Smart Target, Live Ping Monitor, Auto Chat,
# Radar statistics and configurable auto-welcome. All additions are defensive
# and do not replace the original core controls.
# ---------------------------------------------------------------------------

import collections as _sb_collections
import os as _sb_os

_SB_ACCENT = (0.08, 0.78, 0.82)
_SB_PANEL_BG = (0.025, 0.055, 0.095)
_SB_PANEL_INNER = (0.035, 0.085, 0.13)
_SB_TEXT = (0.86, 0.95, 1.0)
_SB_CONFIG_WELCOME = "StudioBon Welcome Settings"
_SB_CONFIG_AUTOCHAT = "StudioBon Auto Chat Rules"
_sb_selected_target = None
_sb_ping_cache = {}
_sb_server_local_ping = None
_sb_ping_history = []
_sb_kills_by_name = {}
_sb_deaths_by_name = {}
_sb_local_kills = 0
_sb_death_seen = {}
_sb_last_incoming = {}
_sb_autochat_last_rule = {}
_sb_autochat_recent_outgoing = {}
_sb_autochat_fields = {}
_sb_autochat_rule_buttons = {}
_sb_welcome_field = None
_sb_welcome_toggle_widget = None
_sb_welcome_enabled = True
_sb_welcome_message = "سلام به همگی! ❤️"
_sb_autochat_enabled = False
_sb_autochat_rules = []


def _sb_config_get(key, default=None):
    try:
        value = babase.app.config.get(key, default)
        return value if value is not None else default
    except Exception:
        return default


def _sb_config_set(key, value):
    try:
        babase.app.config[key] = value
        babase.app.config.commit()
        return True
    except Exception:
        return False


def _sb_roster():
    """Return actual player rows; omit server/host pseudo-entries with no players."""
    try:
        raw = bs.get_game_roster() or []
    except Exception:
        raw = []
    result = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        players = [p for p in (entry.get("players") or []) if isinstance(p, dict)]
        # Some servers expose a host/server pseudo-row without actual players.
        if not players:
            continue
        cid = entry.get("client_id", entry.get("clientID", entry.get("clientid", -1)))
        try:
            cid = int(cid)
        except Exception:
            cid = -1
        names = []
        for player in players:
            name = (player.get("name_full") or player.get("nameFull") or
                    player.get("name") or player.get("name_full_raw"))
            if name:
                names.append(str(name))
        name = names[0] if names else "Player"
        result.append({"client_id": cid, "name": name, "names": names,
                       "account_id": entry.get("account_id", entry.get("accountID")),
                       "raw": entry})
    return result


def _sb_player_name(player):
    if player is None:
        return "Unknown"
    for full in (True, False):
        try:
            fn = getattr(player, "getname", None)
            if callable(fn):
                try:
                    name = fn(full=full)
                except TypeError:
                    name = fn()
                if name:
                    return str(name)
        except Exception:
            pass
    for attr in ("name", "name_full", "nameFull"):
        try:
            value = getattr(player, attr, None)
            if value:
                return str(value)
        except Exception:
            pass
    try:
        sessionplayer = getattr(player, "sessionplayer", None)
        fn = getattr(sessionplayer, "getname", None)
        if callable(fn):
            value = fn()
            if value:
                return str(value)
    except Exception:
        pass
    return "Unknown"


def _sb_direct_player_ping(client_id):
    """Use a direct ping API only if the running client actually exposes one."""
    if client_id is None or client_id < 0:
        return None
    candidates = [bs, babase]
    for obj in (getattr(bs, "_ba", None), getattr(babase, "_ba", None)):
        if obj is not None:
            candidates.append(obj)
    for obj in candidates:
        try:
            fn = getattr(obj, "get_client_ping", None)
            if callable(fn):
                value = fn(client_id)
                if isinstance(value, (int, float)) and 0 <= value < 10000:
                    _sb_ping_cache[client_id] = int(value)
                    return int(value)
        except Exception:
            continue
    return _sb_ping_cache.get(client_id)


def _sb_ping_label(client_id):
    value = _sb_direct_player_ping(client_id)
    return "%d ms" % value if value is not None else "— / server ping"


def _sb_request_player_ping(client_id):
    try:
        if client_id is None or int(client_id) < 0:
            push("Player ID is not available", color=(1.0, 0.5, 0.3))
            return
        # BSLife-like servers may implement /ping <client_id>; this request is
        # deliberately explicit because a client cannot read another client's
        # private network latency unless the server exposes it.
        _party_send("/ping %d" % int(client_id))
        push("Ping request sent to server", color=(0.25, 0.9, 1.0))
    except Exception:
        pass


def _sb_parse_server_ping_message(msg):
    """Cache ping values if a server replies with a recognizable name + ms."""
    global _sb_server_local_ping
    try:
        text = str(msg)
        # Some BSLife-like servers reply to /ping with the local client's latency.
        if (re.search(r"(?i)(your|my|self|local)\s+ping", text) or
                re.search(r"(?i)^\s*ping\s*[:=]", text)) and not re.search(r"(?i)ping\s+(of|for)\b", text):
            local_match = re.search(r"(?i)ping[^0-9]{0,20}(\d{1,4})\s*ms\b", text)
            if local_match:
                _sb_server_local_ping = int(local_match.group(1))
        patterns = [
            re.compile(r"(?i)([^:\n]{1,40})\s*[:\-]\s*(\d{1,4})\s*ms\b"),
            re.compile(r"(?i)ping\s+(?:of|for)\s+(.{1,40}?)\s*[:\-]?\s*(\d{1,4})\s*ms\b"),
            re.compile(r"(?i)(\d{1,4})\s*ms\s*(?:ping)?\s*(?:for|of)\s+(.{1,40})$")
        ]
        for idx, pattern in enumerate(patterns):
            match = pattern.search(text)
            if not match:
                continue
            if idx == 2:
                ping, name = match.group(1), match.group(2)
            else:
                name, ping = match.group(1), match.group(2)
            name = name.strip().strip("[]() ")
            value = int(ping)
            for person in _sb_roster():
                if person["name"].strip().lower() == name.lower() or any(n.strip().lower() == name.lower() for n in person["names"]):
                    if person["client_id"] >= 0:
                        _sb_ping_cache[person["client_id"]] = value
            break
    except Exception:
        pass


class _SBPanel:
    def __init__(self, title, accent=_SB_ACCENT, width=980, height=680):
        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = width, height
        self._width = min(width, max(420, int(sw - 30)))
        self._height = min(height, max(440, int(sh - 30)))
        x = max(10, (sw - self._width) * 0.5)
        y = max(10, (sh - self._height) * 0.5)
        self._closed = False
        self.root_widget = bui.containerwidget(
            parent=gsw("overlay_stack"), position=(x, y),
            size=(self._width, self._height), transition="in_scale",
            scale=1.0, color=_SB_PANEL_BG)
        bui.textwidget(parent=self.root_widget,
                       position=(18, self._height - 62),
                       size=(self._width - 90, 42), text=title,
                       h_align="left", v_align="center", scale=1.15,
                       color=accent, shadow=1.0, flatness=0.2)
        bui.textwidget(parent=self.root_widget,
                       position=(18, self._height - 88),
                       size=(self._width - 36, 20),
                       text="STUDIOBON  //  API 9  •  LIVE TOOLS",
                       h_align="left", v_align="center", scale=0.55,
                       color=(0.35, 0.68, 0.82))
        bw(parent=self.root_widget,
           position=(self._width - 58, self._height - 66), size=(38, 38),
           button_type="square", label="✕", text_scale=0.9,
           color=(0.35, 0.07, 0.12), textcolor=(1, 1, 1),
           on_activate_call=bui.WeakCall(self.close))

    def make_scroll(self, content_height):
        margin = 18
        sy = 54
        sh = self._height - 160
        sw = self._width - 2 * margin
        scroll = bui.scrollwidget(parent=self.root_widget,
                                  position=(margin, sy), size=(sw, sh),
                                  highlight=False, capture_arrows=True)
        content = bui.containerwidget(parent=scroll,
                                      size=(sw, max(sh, int(content_height))),
                                      background=False)
        return content, sw, max(sh, int(content_height))

    def close(self):
        self._closed = True
        try:
            bui.containerwidget(edit=self.root_widget, transition="out_scale")
        except Exception:
            try:
                bui.widget(edit=self.root_widget, delete=True)
            except Exception:
                pass


_smart_target_window = None


def _open_smart_target():
    global _smart_target_window
    try:
        if _smart_target_window is not None:
            _smart_target_window.close()
        _smart_target_window = _SmartTargetWindow()
    except Exception as exc:
        try: push("Smart Target error: %s" % exc, color=(1, 0.3, 0.3))
        except Exception: pass


class _SmartTargetWindow(_SBPanel):
    def __init__(self):
        super().__init__("◉ SMART TARGET", accent=(0.75, 0.35, 1.0))
        # The panel is intentionally marked as under construction.
        bui.textwidget(parent=self.root_widget,
            position=(22, self._height * 0.48),
            size=(self._width - 44, 54),
            text="⚠️کارگران مشغول کارند⚠️",
            h_align="center", v_align="center", scale=1.05,
            color=(1.0, 0.86, 0.08), shadow=1.0, flatness=0.2)
        bw(parent=self.root_widget, position=(18, 12), size=(self._width - 36, 34),
           button_type="square", label="REFRESH", text_scale=0.75,
           color=(0.25, 0.08, 0.38), textcolor=(1, 1, 1),
           on_activate_call=self._refresh_notice)
        try:
            push("⚠️این قابلیت در حال ساخت می باشد و در آپدیت بعدی قابل استفاده میشود",
                 color=(0.72, 0.28, 1.0), transient=True)
        except Exception:
            try: push("⚠️این قابلیت در حال ساخت می باشد و در آپدیت بعدی قابل استفاده میشود", color=(0.72, 0.28, 1.0))
            except Exception: pass

    def _refresh_notice(self):
        try:
            push("Smart Target در آپدیت بعدی قابل استفاده میشود", color=(0.72, 0.28, 1.0), transient=True)
        except Exception:
            pass


def _sb_select_target(person):
    global _sb_selected_target
    _sb_selected_target = dict(person)
    try:
        push("Target selected: %s" % person.get("name", "Player"), color=(0.2, 1, 0.8))
    except Exception:
        pass


_live_ping_window = None


def _sb_current_ping_value():
    # This is the live value from the existing local probe. Server-reported
    # /ping values are shown separately as a last measurement, not resampled.
    try:
        value = int(current_ping)
        if 0 < value < 999:
            return value
    except Exception:
        pass
    return None


def _sb_request_local_ping():
    # This command is server-dependent; on servers that implement /ping it
    # lets the monitor use the server's own latency measurement as a fallback.
    try:
        _party_send("/ping")
        push("Asked server for local ping (if supported)", color=(0.25, 0.9, 1.0))
    except Exception:
        pass


def _sb_send_live_ping_to_chat():
    value = _sb_current_ping_value()
    if value is None:
        push("پینگ زنده فعلاً در دسترس نیست", color=(1.0, 0.55, 0.2), transient=True)
        return
    _party_send("🟢Live Ping : %dms" % value)
    try: push("پینگ زنده در چت فرستاده شد", color=(0.2, 1.0, 0.45), transient=True)
    except Exception: pass


def _sb_send_max_ping_to_chat():
    vals = [v for _, v in _sb_ping_history]
    if not vals:
        push("هنوز پینگ معتبری برای MAX ثبت نشده", color=(1.0, 0.55, 0.2), transient=True)
        return
    value = max(vals)
    _party_send("🔴My Max Ping Recently : %dms !!" % value)
    try: push("بالاترین پینگ ثبت شده به چت فرستاده شد", color=(1.0, 0.25, 0.25), transient=True)
    except Exception: pass


def _open_live_ping():
    global _live_ping_window
    try:
        if _live_ping_window is not None:
            _live_ping_window.close()
        _live_ping_window = _LivePingWindow()
    except Exception as exc:
        try: push("Live Ping error: %s" % exc, color=(1, 0.3, 0.3))
        except Exception: pass


class _LivePingWindow(_SBPanel):
    def __init__(self):
        super().__init__("⌁ LIVE PING MONITOR", accent=(0.25, 0.95, 1.0), height=620)
        self._readout = bui.textwidget(parent=self.root_widget,
            position=(28, self._height - 180), size=(self._width - 56, 78),
            text="Measuring connection…", h_align="center", v_align="center",
            scale=1.1, color=(0.25, 1.0, 0.75))
        self._stats = bui.textwidget(parent=self.root_widget,
            position=(28, self._height - 225), size=(self._width - 56, 32),
            text="MIN —   AVG —   MAX —", h_align="center", v_align="center",
            scale=0.8, color=(0.45, 0.8, 1.0))
        self._history_widget = bui.textwidget(parent=self.root_widget,
            position=(28, self._height - 275), size=(self._width - 56, 32),
            text="Last 60 valid samples", h_align="center", v_align="center",
            scale=0.65, color=(0.6, 0.75, 0.85))
        gap = 10
        half = (self._width - 48 - gap) // 2
        bw(parent=self.root_widget, position=(24, 20), size=(half, 42),
           button_type="square", label="🟢Send Live Ping on Chat", text_scale=0.57,
           color=(0.02, 0.38, 0.18), textcolor=(1, 1, 1),
           on_activate_call=_sb_send_live_ping_to_chat)
        bw(parent=self.root_widget, position=(24 + half + gap, 20), size=(half, 42),
           button_type="square", label="🔴Send Max Ping on Chat", text_scale=0.57,
           color=(0.48, 0.035, 0.08), textcolor=(1, 1, 1),
           on_activate_call=_sb_send_max_ping_to_chat)
        self._tick()

    def _tick(self):
        if self._closed:
            return
        value = _sb_current_ping_value()
        if value is not None:
            _sb_ping_history.append((time.monotonic(), value))
            del _sb_ping_history[:-60]
            text = "LOCAL PING\n%d ms" % value
            color = (0.2, 1.0, 0.45) if value < 60 else ((1.0, 0.72, 0.12) if value < 130 else (1.0, 0.25, 0.3))
        elif isinstance(_sb_server_local_ping, int) and 0 <= _sb_server_local_ping < 10000:
            text = "LAST SERVER PING\n%d ms  •  press /ping to refresh" % _sb_server_local_ping
            color = (0.25, 0.85, 1.0)
        else:
            text = "LOCAL PING\nNO RESPONSE / UNAVAILABLE"
            color = (1.0, 0.65, 0.18)
        try:
            bui.textwidget(edit=self._readout, text=text, color=color)
            vals = [v for _, v in _sb_ping_history]
            if vals:
                avg = sum(vals) / float(len(vals))
                bui.textwidget(edit=self._stats,
                    text="MIN %d ms    AVG %.1f ms    MAX %d ms" % (min(vals), avg, max(vals)))
                bars = "▁▂▃▄▅▆▇█"
                graph = " ".join(bars[min(7, int(v / max(1, max(vals)) * 7))] for v in vals[-24:])
                bui.textwidget(edit=self._history_widget, text="HISTORY  " + graph)
            else:
                bui.textwidget(edit=self._stats, text="MIN —    AVG —    MAX —")
                bui.textwidget(edit=self._history_widget, text="No valid ping samples yet")
        except Exception:
            pass
        # Other players' pings are server-provided where supported; do not fake them.
        try:
            if not getattr(self, "_remote_label", None):
                self._remote_label = bui.textwidget(parent=self.root_widget,
                    position=(25, 85), size=(self._width - 50, 110),
                    text="OTHER PLAYERS\nUse Smart Target → PING CHECK. Remote latency requires server support.",
                    h_align="left", v_align="center", scale=0.68, color=(0.55, 0.85, 0.95))
            remote = []
            for person in _sb_roster()[:5]:
                p = _sb_direct_player_ping(person["client_id"])
                if p is None:
                    p = _sb_ping_cache.get(person["client_id"])
                remote.append("%s: %s" % (person["name"], "%d ms" % p if p is not None else "—"))
            bui.textwidget(edit=self._remote_label, text="OTHER PLAYERS\n" + ("  •  ".join(remote) if remote else "No roster data"))
        except Exception:
            pass
        teck(1.0, self._tick)


# Auto Chat rebuilt from the response-rule workflow in the reference mod.
# Only the Add/response functionality is included; unrelated menus are omitted.
def _sb_load_autochat():
    global _sb_autochat_enabled, _sb_autochat_rules
    raw = _sb_config_get(_SB_CONFIG_AUTOCHAT, {})
    if not isinstance(raw, dict):
        raw = {}
    _sb_autochat_enabled = bool(raw.get("enabled", False))
    rules = raw.get("rules", [])
    cleaned = []
    for idx in range(5):
        item = rules[idx] if isinstance(rules, list) and idx < len(rules) and isinstance(rules[idx], dict) else {}
        cleaned.append({
            "trigger": str(item.get("trigger", ""))[:120],
            "reply": str(item.get("reply", ""))[:160],
            "enabled": bool(item.get("enabled", False)),
            "mode": "contains" if item.get("mode") == "contains" else "exact",
            "delay": max(0.0, min(60.0, float(item.get("delay", 0.0) or 0.0))),
        })
    _sb_autochat_rules = cleaned


def _sb_save_autochat():
    _sb_config_set(_SB_CONFIG_AUTOCHAT, {"enabled": _sb_autochat_enabled, "rules": _sb_autochat_rules})


_sb_load_autochat()


def _sb_expand_autochat_reply(reply, sender=""):
    """Expand the useful response tokens supported by the reference Add feature."""
    from datetime import datetime
    import random
    now = datetime.now()
    try:
        account = babase.app.plus.get_v1_account_display_string() or "Player"
    except Exception:
        account = "Player"
    try:
        info = bs.get_connection_to_host_info_2() or {}
        server_ip = str(info.get("address", info.get("host", "")))
        server_port = str(info.get("port", ""))
        server = (server_ip + (":" + server_port if server_port else "")) if server_ip else "Unknown"
    except Exception:
        server = "Unknown"
    text = str(reply)
    replacements = {
        "%t": now.strftime("%H:%M:%S"),
        "%d": now.strftime("%Y-%m-%d"),
        "%s": sender or "Unknown",
        "%m": account,
        "%ip": server,
        "%j": random.choice(["پدر: درس خوندی؟ گفتم: دارم تلاش می‌کنم!", "کار امروز را به فردا ننداز!", "خنده بر هر درد بی‌درمان دواست."]),
        "%z": random.choice(["وقت طلاست.", "با یک گل بهار نمی‌شود.", "پایان شب سیه سپید است."]),
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    return text[:160].strip()


def _sb_auto_chat_handle_incoming(msg):
    """Process each newly received chat line once, using the saved response rules."""
    if not _sb_autochat_enabled:
        return
    try:
        raw = str(msg).strip()
        if not raw:
            return
        sender, body = "", raw
        for pattern in (r'^\[([^\]]{1,64})\]\s*(.*)$', r'^<([^>]{1,64})>\s*(.*)$',
                        r'^([^:\n]{1,64}):\s*(.*)$', r'^([^\n]{1,48})\s+>\s*(.*)$'):
            match = re.match(pattern, raw)
            if match:
                sender, body = match.group(1).strip(), match.group(2).strip()
                break
        if not body:
            return
        now = time.monotonic()
        normalized_body = body.casefold()
        normalized_sender = sender.casefold() or "<unknown-sender>"
        event_key = (normalized_sender, normalized_body)
        # PartyWindow can deliver the same event through two hooks. Short dedupe
        # window prevents double sends without blocking a later new message.
        previous = _sb_last_incoming.get(event_key, 0.0)
        if now - previous < 1.25:
            return
        _sb_last_incoming[event_key] = now
        for old, stamp in list(_sb_last_incoming.items()):
            if now - stamp > 12.0:
                _sb_last_incoming.pop(old, None)
        # Ignore our own outgoing reply echoed back into chat history.
        if now - _sb_autochat_recent_outgoing.get(normalized_body, 0.0) < 3.0:
            return
        for idx, rule in enumerate(_sb_autochat_rules):
            trigger = str(rule.get("trigger", "")).strip()
            reply = str(rule.get("reply", "")).strip()
            if not rule.get("enabled") or not trigger or not reply:
                continue
            trigger_norm = trigger.casefold()
            matched = (trigger_norm in normalized_body if rule.get("mode") == "contains"
                       else normalized_body == trigger_norm)
            if not matched:
                continue
            rule_key = (idx, normalized_sender, normalized_body)
            if now - _sb_autochat_last_rule.get(rule_key, 0.0) < 2.0:
                return
            _sb_autochat_last_rule[rule_key] = now
            response = _sb_expand_autochat_reply(reply, sender)
            if not response:
                return
            _sb_autochat_recent_outgoing[response.casefold()] = time.monotonic()
            delay = max(0.0, min(60.0, float(rule.get("delay", 0.0) or 0.0)))
            teck(delay, lambda response=response: _party_send(response))
            break
    except Exception as exc:
        try:
            print("StudioBon Auto Chat error:", repr(exc))
        except Exception:
            pass


_auto_chat_window = None


def _open_auto_chat():
    global _auto_chat_window
    try:
        if _auto_chat_window is not None:
            _auto_chat_window.close()
        _auto_chat_window = _AutoChatWindow()
    except Exception as exc:
        try: push("Auto Chat error: %s" % exc, color=(1, 0.3, 0.3))
        except Exception: pass


class _AutoChatWindow(_SBPanel):
    def __init__(self):
        super().__init__("⌘ AUTO CHAT", accent=(0.72, 0.32, 1.0), height=700)
        try: bui.containerwidget(edit=self.root_widget, color=(0.20, 0.015, 0.36))
        except Exception: pass
        self._enable_button = bw(parent=self.root_widget,
            position=(22, self._height - 128), size=(170, 38),
            button_type="square", label="AUTO CHAT: " + ("ON" if _sb_autochat_enabled else "OFF"),
            text_scale=0.7, color=(0.05, 0.35, 0.22) if _sb_autochat_enabled else (0.3, 0.08, 0.15),
            textcolor=(1, 1, 1), on_activate_call=self._toggle_master)
        bw(parent=self.root_widget, position=(self._width - 205, self._height - 128),
           size=(180, 38), button_type="square", label="SAVE RESPONSES",
           text_scale=0.68, color=(0.34, 0.12, 0.55), textcolor=(1, 1, 1), on_activate_call=self._save)
        margin, viewport_y = 18, 46
        viewport_h = max(220, self._height - 225)
        sw = self._width - 2 * margin
        scroll = bui.scrollwidget(parent=self.root_widget, position=(margin, viewport_y),
            size=(sw, viewport_h), highlight=False, capture_arrows=True)
        ch = max(viewport_h, 5 * 144 + 20)
        content = bui.containerwidget(parent=scroll, size=(sw, ch), background=False)
        self._rule_widgets = []
        for idx, rule in enumerate(_sb_autochat_rules):
            y = ch - 138 - idx * 144
            bui.textwidget(parent=content, position=(8, y + 105), size=(sw - 16, 20),
                text="RESPONSE %02d" % (idx + 1), h_align="left", v_align="center",
                scale=0.65, color=(0.82, 0.55, 1.0))
            trigger = bui.textwidget(parent=content, position=(92, y + 75),
                size=(sw - 104, 27), text=rule["trigger"], editable=True,
                max_chars=120, color=(1, 1, 1), h_align="left", v_align="center", scale=0.7)
            reply = bui.textwidget(parent=content, position=(92, y + 42),
                size=(sw - 104, 27), text=rule["reply"], editable=True,
                max_chars=160, color=(1, 1, 1), h_align="left", v_align="center", scale=0.7)
            bui.textwidget(parent=content, position=(8, y + 72), size=(76, 27),
                text="TRIGGER", h_align="center", v_align="center", scale=0.52, color=(0.95, 0.8, 1.0))
            bui.textwidget(parent=content, position=(8, y + 39), size=(76, 27),
                text="REPLY", h_align="center", v_align="center", scale=0.58, color=(0.95, 0.8, 1.0))
            enabled_btn = bw(parent=content, position=(8, y + 4), size=(68, 29),
                button_type="square", label="ON" if rule["enabled"] else "OFF", text_scale=0.58,
                color=(0.04, 0.35, 0.2) if rule["enabled"] else (0.3, 0.08, 0.13),
                textcolor=(1, 1, 1), on_activate_call=lambda i=idx: self._toggle_rule(i))
            mode_btn = bw(parent=content, position=(82, y + 4), size=(82, 29),
                button_type="square", label="PART" if rule["mode"] == "contains" else "EXACT",
                text_scale=0.52, color=(0.30, 0.16, 0.48), textcolor=(1, 1, 1),
                on_activate_call=lambda i=idx: self._toggle_mode(i))
            delay = bui.textwidget(parent=content, position=(sw - 115, y + 5), size=(42, 27),
                text=str(rule.get("delay", 0.0)), editable=True, max_chars=5,
                color=(1, 1, 1), h_align="center", v_align="center", scale=0.62)
            bui.textwidget(parent=content, position=(sw - 70, y + 5), size=(62, 27),
                text="SEC delay", h_align="left", v_align="center", scale=0.48, color=(0.9, 0.78, 1.0))
            self._rule_widgets.append({"trigger": trigger, "reply": reply, "delay": delay,
                                       "mode": mode_btn, "enabled": enabled_btn})
        bui.textwidget(parent=self.root_widget, position=(22, 12), size=(self._width - 44, 28),
            text="Use %s sender, %m you, %t time, %d date, %ip server | Save after edits",
            h_align="left", v_align="center", scale=0.55, color=(0.75, 0.62, 1.0))

    def _toggle_master(self):
        global _sb_autochat_enabled
        _sb_autochat_enabled = not _sb_autochat_enabled
        self._save()
        try:
            bui.buttonwidget(edit=self._enable_button,
                label="AUTO CHAT: " + ("ON" if _sb_autochat_enabled else "OFF"),
                color=(0.05, 0.35, 0.22) if _sb_autochat_enabled else (0.3, 0.08, 0.15))
        except Exception: pass
        try: push("Auto Chat روشن شد" if _sb_autochat_enabled else "Auto Chat خاموش شد", color=(0.78, 0.4, 1.0), transient=True)
        except Exception: pass

    def _toggle_rule(self, idx):
        _sb_autochat_rules[idx]["enabled"] = not _sb_autochat_rules[idx]["enabled"]
        try:
            btn = self._rule_widgets[idx]["enabled"]
            bui.buttonwidget(edit=btn, label="ON" if _sb_autochat_rules[idx]["enabled"] else "OFF",
                color=(0.04, 0.35, 0.2) if _sb_autochat_rules[idx]["enabled"] else (0.3, 0.08, 0.13))
        except Exception: pass
        self._save()

    def _toggle_mode(self, idx):
        rule = _sb_autochat_rules[idx]
        rule["mode"] = "exact" if rule.get("mode") == "contains" else "contains"
        try:
            bui.buttonwidget(edit=self._rule_widgets[idx]["mode"],
                label="EXACT" if rule["mode"] == "exact" else "PART")
        except Exception: pass
        self._save()

    def _save(self):
        global _sb_autochat_rules
        try:
            for idx, widgets in enumerate(self._rule_widgets):
                rule = _sb_autochat_rules[idx]
                rule["trigger"] = str(bui.textwidget(query=widgets["trigger"]))[:120].strip()
                rule["reply"] = str(bui.textwidget(query=widgets["reply"]))[:160].strip()
                try: rule["delay"] = max(0.0, min(60.0, float(bui.textwidget(query=widgets["delay"]) or 0)))
                except Exception: rule["delay"] = 0.0
        except Exception: pass
        _sb_save_autochat()
        try: push("Auto Chat responses saved ✓", color=(0.8, 0.55, 1.0), transient=True)
        except Exception:
            try: push("Auto Chat responses saved ✓", color=(0.8, 0.55, 1.0))
            except Exception: pass


# Kill/death tracking is best-effort: it only records actual DieMessage events
# observed by the local client; servers may not expose all remote actor events.
def _sb_is_local_player(player):
    if player is None:
        return False
    for attr in ("is_local_player", "is_local"):
        try:
            value = getattr(player, attr, None)
            if callable(value):
                value = value()
            if isinstance(value, bool):
                return value
        except Exception:
            pass
    try:
        sessionplayer = getattr(player, "sessionplayer", None)
        device = getattr(sessionplayer, "inputdevice", None)
        for attr in ("is_local", "is_local_device"):
            value = getattr(device, attr, None)
            if callable(value): value = value()
            if isinstance(value, bool): return value
    except Exception:
        pass
    return False


def _sb_record_death(actor, msg):
    global _sb_local_kills
    try:
        now = time.monotonic()
        key = id(actor)
        if now - _sb_death_seen.get(key, 0.0) < 1.0:
            return
        _sb_death_seen[key] = now
        for old_key, stamp in list(_sb_death_seen.items()):
            if now - stamp > 20:
                _sb_death_seen.pop(old_key, None)
        victim = _sb_player_name(getattr(actor, "player", None))
        if victim != "Unknown":
            _sb_deaths_by_name[victim] = _sb_deaths_by_name.get(victim, 0) + 1
        killer = getattr(msg, "killerplayer", None)
        if killer is not None:
            killer_name = _sb_player_name(killer)
            if killer_name != "Unknown":
                _sb_kills_by_name[killer_name] = _sb_kills_by_name.get(killer_name, 0) + 1
            if _sb_is_local_player(killer):
                _sb_local_kills += 1
    except Exception:
        pass


try:
    import bascenev1lib.actor.playerspaz as _sb_playerspaz_module
    _sb_original_spaz_handlemessage = _sb_playerspaz_module.PlayerSpaz.handlemessage
    if not getattr(_sb_original_spaz_handlemessage, "_studiobon_tracker", False):
        def _sb_tracked_spaz_handlemessage(self, msg):
            try:
                if msg.__class__.__name__ == "DieMessage" or isinstance(msg, getattr(bs, "DieMessage", ())):
                    _sb_record_death(self, msg)
            except Exception:
                pass
            return _sb_original_spaz_handlemessage(self, msg)
        _sb_tracked_spaz_handlemessage._studiobon_tracker = True
        _sb_playerspaz_module.PlayerSpaz.handlemessage = _sb_tracked_spaz_handlemessage
except Exception:
    _sb_playerspaz_module = None


_SB_CONFIG_ENEMIES = "StudioBon Radar Enemies"
_SB_CONFIG_ENEMY_CASES = "StudioBon Radar Enemy Case Notes"
_sb_enemy_case_notes = {}
try:
    _raw_enemy_cases = _sb_config_get(_SB_CONFIG_ENEMY_CASES, {})
    if isinstance(_raw_enemy_cases, dict):
        _sb_enemy_case_notes = {str(k): str(v)[:3000] for k, v in _raw_enemy_cases.items()}
except Exception:
    _sb_enemy_case_notes = {}


def _sb_save_enemy_cases():
    _sb_config_set(_SB_CONFIG_ENEMY_CASES, dict(_sb_enemy_case_notes))


def _sb_open_enemy_case(ident):
    try:
        _EnemyCaseWindow(ident)
    except Exception as exc:
        try: push("خطا در پرونده: " + str(exc)[:90], color=(1, 0.25, 0.25))
        except Exception: pass


class _EnemyCaseWindow:
    def __init__(self, ident):
        self.ident = str(ident)
        sw, sh = bui.get_virtual_screen_size()
        self.width, self.height = min(540, int(sw - 30)), min(560, int(sh - 30))
        x, y = (sw - self.width) / 2, (sh - self.height) / 2
        self.root = bui.containerwidget(parent=gsw("overlay_stack"), position=(x, y),
            size=(self.width, self.height), transition="in_scale", color=(0.015, 0.06, 0.28))
        bui.textwidget(parent=self.root, position=(12, self.height-55), size=(self.width-24, 38),
            text="🚔یگان دادگستری🚨", h_align="center", v_align="center", color=(1,1,1), scale=1.0)
        bui.textwidget(parent=self.root, position=(20, self.height-95), size=(self.width-40, 25),
            text="پرونده: " + self.ident[:45], h_align="left", color=(1,1,1), scale=0.65)
        sy, shh = 92, self.height - 205
        scroll = bui.scrollwidget(parent=self.root, position=(18, sy), size=(self.width-36, shh),
            highlight=False, capture_arrows=True, color=(0.025, 0.09, 0.34))
        content_h = max(720, shh + 120)
        content = bui.containerwidget(parent=scroll, size=(self.width-54, content_h), background=False)
        self.field = bui.textwidget(parent=content, position=(8, content_h-15), size=(self.width-54, content_h-25),
            text=_sb_enemy_case_notes.get(self.ident, ""), editable=True, max_chars=3000,
            h_align="left", v_align="top", color=(1,1,1), scale=0.8)
        bui.buttonwidget(parent=self.root, position=(18, 28), size=(300, 42),
            label="ذخیره پرونده مجرم📋", color=(1.0, 0.78, 0.08), textcolor=(0.05,0.05,0.05),
            on_activate_call=self._save)
        bui.buttonwidget(parent=self.root, position=(self.width-115, 28), size=(95, 42),
            label="بستن", color=(0.45,0.12,0.12), textcolor=(1,1,1), on_activate_call=self._close)

    def _save(self):
        try:
            _sb_enemy_case_notes[self.ident] = str(bui.textwidget(query=self.field))[:3000]
            _sb_save_enemy_cases()
            babase.app.config.commit()
            push("پرونده مجرم ذخیره شد📋", color=(0.25,1,0.35), transient=True)
        except Exception as exc:
            try: push("ذخیره نشد: " + str(exc)[:80], color=(1,0.25,0.25))
            except Exception: pass

    def _close(self):
        try: bui.containerwidget(edit=self.root, transition="out_scale")
        except Exception: pass

_sb_enemies = []
_sb_enemy_announced_this_session = set()


def _sb_load_enemies():
    global _sb_enemies
    raw = _sb_config_get(_SB_CONFIG_ENEMIES, [])
    cleaned = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                ident = str(item.get("id", "")).strip()[:100]
                label = str(item.get("name", "Player")).strip()[:60]
                if ident and not any(x.get("id", "").casefold() == ident.casefold() for x in cleaned):
                    cleaned.append({"id": ident, "name": label or "Player"})
    _sb_enemies = cleaned


def _sb_save_enemies():
    _sb_config_set(_SB_CONFIG_ENEMIES, _sb_enemies)


def _sb_person_device_id(person):
    """Read V2/device/account display identity from nested server roster data."""
    if not isinstance(person, dict):
        return None
    raw = person.get("raw", person)
    wanted = (
        "account_display_string", "account_display_name", "account_name",
        "device_name", "device_display_string", "device_display_name",
        "v2_name", "v2name", "v2_alias", "device_alias", "device",
        "device_id", "deviceid", "display_string", "account_id_string", "account_id", "accountid",
    )
    values = []
    def walk(obj, depth=0):
        if depth > 6:
            return
        if isinstance(obj, dict):
            for key in wanted:
                for actual_key, value in obj.items():
                    if str(actual_key).casefold() == key.casefold() and value is not None:
                        values.append((key, value))
            for value in obj.values():
                if isinstance(value, (dict, list, tuple)):
                    walk(value, depth + 1)
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                if isinstance(value, (dict, list, tuple)):
                    walk(value, depth + 1)
    walk(raw)
    for key in wanted:
        value = person.get(key)
        if value is not None:
            values.append((key, value))
    visible_name = str(person.get("name", "")).strip().casefold()
    for key, value in values:
        try:
            ident = str(value).strip()
        except Exception:
            continue
        if not ident or ident.casefold() in ("none", "unknown", "player", "server"):
            continue
        if ident.casefold() == visible_name:
            continue
        # Short numeric roster IDs (e.g. 137) are not Device/V2 identities.
        if ident.isdigit() and len(ident) < 6:
            continue
        if re.search(r"(?i)(android|pc)\d{3,}|^[0-9a-f]{12,}$|^pb-[a-z0-9-]{6,}$", ident):
            return ident
        # Alias-like strings such as Ostokhon are accepted only from a device/account field.
        if key.casefold() not in ("account_id", "accountid") and len(ident) >= 4 and re.search(r"[A-Za-z]", ident):
            return ident
    return None


def _sb_person_stable_id(person):
    """Identity used by the enemy list: the server-provided device/V2 identity."""
    return _sb_person_device_id(person)


def _sb_add_enemy(person):
    try:
        ident = _sb_person_stable_id(person)
        if not ident:
            push("Device/V2 این بازیکن از اطلاعات سرور پیدا نشد؛ چیزی ذخیره نشد.", color=(1, 0.25, 0.25))
            return
        if any(str(item.get("id", "")).casefold() == ident.casefold() for item in _sb_enemies):
            push("این Device/V2 از قبل در لیست دشمنان است", color=(1, 0.4, 0.25))
            return
        player_name = str(person.get("name", "Player"))[:60] if isinstance(person, dict) else "Player"
        _sb_enemies.append({"id": ident, "name": player_name})
        _sb_save_enemies()
        push("این شخص (%s) متخلف به لیست دشمنان اضافه شد☢️" % ident, color=(1, 0.18, 0.18))
        try:
            _party_send("🚫(%s) Added to ENEMYIES !" % ident)
        except Exception:
            pass
        _open_studiobon_radar()
    except Exception as exc:
        try: push("Radar add error: %s" % str(exc)[:100], color=(1, 0.2, 0.2))
        except Exception: pass


def _sb_remove_enemy(ident):
    global _sb_enemies
    _sb_enemies = [item for item in _sb_enemies if item.get("id", "").casefold() != str(ident).casefold()]
    _sb_save_enemies()
    _open_enemy_list()


_enemy_list_window = None

def _open_enemy_list():
    global _enemy_list_window
    try:
        if _enemy_list_window is not None:
            _enemy_list_window.close()
        _enemy_list_window = _EnemyListWindow()
    except Exception as exc:
        try: push("Enemy list error: %s" % exc, color=(1, 0.3, 0.3))
        except Exception: pass


def _sb_check_enemy_roster():
    try:
        if _server_ip != "127.0.0.1":
            known = {item["id"].casefold(): item for item in _sb_enemies}
            for person in _sb_roster():
                ident = _sb_person_stable_id(person)
                if not ident or ident.casefold() not in known:
                    continue
                key = ident.casefold()
                if key not in _sb_enemy_announced_this_session:
                    _sb_enemy_announced_this_session.add(key)
                    _party_send("📡 StudioBon Radar | (%s) is ENEMY" % ident)
    except Exception:
        pass
    try:
        if _server_ip != "127.0.0.1":
            teck(2.0, _sb_check_enemy_roster)
    except Exception: pass


_sb_load_enemies()


class _EnemyListWindow(_SBPanel):
    def __init__(self):
        super().__init__("Enemies list🚫", accent=(1.0, 0.3, 0.3), height=820)
        try: bui.containerwidget(edit=self.root_widget, color=(0.30, 0.015, 0.035))
        except Exception: pass
        margin = 18
        viewport_y = 48
        viewport_h = max(180, self._height - 205)
        sw = self._width - 2 * margin
        scroll = bui.scrollwidget(parent=self.root_widget, position=(margin, viewport_y),
            size=(sw, viewport_h), highlight=False, capture_arrows=True)
        ch = max(viewport_h, len(_sb_enemies) * 66 + 20)
        content = bui.containerwidget(parent=scroll, size=(sw, ch), background=False)
        bui.textwidget(parent=self.root_widget,
            position=(20, self._height - 128), size=(self._width - 180, 30),
            text="تعداد دشمنان من : %s" % str(len(_sb_enemies)).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")),
            h_align="left", v_align="center", scale=0.72,
            color=(1.0, 0.84, 0.84))
        bw(parent=self.root_widget, position=(self._width - 145, self._height - 128), size=(125, 30),
           button_type="square", label="↻ REFRESH", text_scale=0.55,
           color=(0.5, 0.04, 0.08), textcolor=(1, 1, 1), on_activate_call=_open_enemy_list)
        if not _sb_enemies:
            bui.textwidget(parent=content, position=(12, ch - 70), size=(sw - 24, 50),
                text="No saved enemy IDs yet.", h_align="center", v_align="center", scale=0.8,
                color=(1, 0.85, 0.85))
        for idx, item in enumerate(_sb_enemies):
            y = ch - 78 - idx * 66
            bui.textwidget(parent=content, position=(10, y + 12), size=(sw - 90, 42),
                text="%02d. %s\n%s" % (idx + 1, item.get("name", "Player"), item["id"]),
                h_align="left", v_align="center", scale=0.62, color=(1, 0.88, 0.88))
            bw(parent=content, position=(sw - 140, y + 15), size=(58, 38),
                button_type="square", label="📝", text_scale=0.7,
                color=(0.03, 0.18, 0.48), textcolor=(1, 1, 1),
                on_activate_call=lambda ident=item["id"]: _sb_open_enemy_case(ident))
            bw(parent=content, position=(sw - 72, y + 15), size=(60, 38),
                button_type="square", label="🗑", text_scale=0.7,
                color=(0.55, 0.03, 0.08), textcolor=(1, 1, 1),
                on_activate_call=lambda ident=item["id"]: _sb_remove_enemy(ident))


_radar_window = None


def _open_studiobon_radar():
    global _radar_window
    try:
        if _radar_window is not None:
            _radar_window.close()
        _radar_window = _StudioBonRadarWindow()
    except Exception as exc:
        try: push("Radar error: %s" % exc, color=(1, 0.3, 0.3))
        except Exception: pass


class _StudioBonRadarWindow(_SBPanel):
    """Radar uses the same roster fields as the reference PlayerInfo manager."""
    def __init__(self):
        super().__init__("▣ STUDIOBON RADAR / PLAYER MANAGER",
                         accent=(0.35, 0.72, 1.0), height=720)
        try: bui.containerwidget(edit=self.root_widget, color=(0.015, 0.045, 0.28))
        except Exception: pass
        # Keep the existing enemy-list button.
        bw(parent=self.root_widget, position=(20, self._height - 112), size=(70, 38),
            button_type="square", label="🚫", text_scale=0.85,
            color=(0.55, 0.03, 0.08), textcolor=(1, 1, 1),
            on_activate_call=_open_enemy_list)
        try:
            roster = _sb_roster()
        except Exception:
            roster = []
        bui.textwidget(parent=self.root_widget, position=(102, self._height - 112),
            size=(self._width - 124, 36), text="ONLINE PLAYERS  •  %d" % len(roster),
            h_align="left", v_align="center", scale=0.78, color=(0.65, 0.85, 1.0))
        margin = 18
        viewport_y = 54
        viewport_h = max(180, self._height - 178)
        inner_w = self._width - 2 * margin
        scroll = bui.scrollwidget(parent=self.root_widget, position=(margin, viewport_y),
            size=(inner_w, viewport_h), highlight=False, capture_arrows=True)
        content_h = max(viewport_h, len(roster) * 76 + 48)
        content = bui.containerwidget(parent=scroll, size=(inner_w, content_h), background=False)
        known = {item["id"].casefold() for item in _sb_enemies}
        headers = (("PLAYER NAME", 12), ("CLIENT ID", 270), ("DEVICE / V2", 390))
        for title, x in headers:
            bui.textwidget(parent=content, position=(x, content_h - 28), size=(160, 22),
                text=title, h_align="left", v_align="center", scale=0.58,
                color=(0.6, 0.9, 1.0))
        for idx, person in enumerate(roster):
            y = content_h - 78 - idx * 76
            name = str(person.get("name", "Player"))
            cid = str(person.get("client_id", -1))
            ident = _sb_person_stable_id(person)
            is_enemy = bool(ident and ident.casefold() in known)
            bg = (0.24, 0.06, 0.10) if is_enemy else ((0.06, 0.12, 0.22) if idx % 2 == 0 else (0.035, 0.085, 0.17))
            bw(parent=content, position=(5, y), size=(inner_w - 10, 62),
                button_type="square", label="", color=bg, enable_sound=False)
            bui.textwidget(parent=content, position=(12, y + 16), size=(240, 36),
                text=name[:36], h_align="left", v_align="center", scale=0.7,
                color=(1, 0.38, 0.38) if is_enemy else (1, 1, 1))
            bui.textwidget(parent=content, position=(270, y + 16), size=(100, 36),
                text=cid, h_align="left", v_align="center", scale=0.65,
                color=(0.8, 0.85, 1.0))
            bui.textwidget(parent=content, position=(390, y + 16), size=(inner_w - 610, 36),
                text=ident or "Not exposed by roster", h_align="left", v_align="center",
                scale=0.62, color=(1, 0.38, 0.38) if is_enemy else (0.6, 1.0, 0.68))
            # Preserve the existing add-to-enemy action; no PlayerInfo management
            # controls such as Kick All are imported into this panel.
            bw(parent=content, position=(inner_w - 205, y + 13), size=(190, 36),
                button_type="square",
                label="IN ENEMY LIST" if is_enemy else "Add to ENEMY'S list",
                text_scale=0.54, color=(0.34, 0.025, 0.06) if is_enemy else (0.62, 0.025, 0.06),
                textcolor=(1, 1, 1), on_activate_call=lambda p=person: _sb_add_enemy(p))
        if not roster:
            bui.textwidget(parent=content, position=(10, content_h - 90), size=(inner_w - 20, 60),
                text="No players found. Open while connected to a server.",
                h_align="center", v_align="center", scale=0.8, color=_SB_TEXT)
        bw(parent=self.root_widget, position=(20, 12), size=(self._width - 40, 34),
            button_type="square", label="REFRESH RADAR", text_scale=0.7,
            color=(0.025, 0.16, 0.48), textcolor=(1, 1, 1),
            on_activate_call=_open_studiobon_radar)


def _sb_reset_radar_stats():
    global _sb_local_kills
    _sb_local_kills = 0
    _sb_kills_by_name.clear()
    _sb_deaths_by_name.clear()
    _sb_death_seen.clear()


# Welcome message is configurable and saved across restarts.
def _sb_load_welcome():
    global _sb_welcome_enabled, _sb_welcome_message
    raw = _sb_config_get(_SB_CONFIG_WELCOME, {})
    if not isinstance(raw, dict): raw = {}
    _sb_welcome_enabled = bool(raw.get("enabled", True))
    _sb_welcome_message = str(raw.get("message", "سلام به همگی! ❤️"))[:180]


def _sb_save_welcome():
    _sb_config_set(_SB_CONFIG_WELCOME, {"enabled": _sb_welcome_enabled, "message": _sb_welcome_message})


_sb_load_welcome()
_sb_welcome_connect_token = 0


def _sb_welcome_after_connect(token):
    if token != _sb_welcome_connect_token or not _sb_welcome_enabled:
        return
    if not _sb_welcome_message.strip():
        return
    try:
        if _server_ip == "127.0.0.1":
            return
        _party_send(_sb_welcome_message.strip())
    except Exception:
        pass


def _sb_schedule_welcome():
    global _sb_welcome_connect_token
    _sb_welcome_connect_token += 1
    token = _sb_welcome_connect_token
    try:
        teck(2.0, lambda t=token: _sb_welcome_after_connect(t))
    except Exception:
        pass


def _sb_cancel_welcome():
    global _sb_welcome_connect_token
    _sb_welcome_connect_token += 1


_welcome_window = None


def _open_welcome_settings():
    global _welcome_window
    try:
        if _welcome_window is not None:
            _welcome_window.close()
        _welcome_window = _WelcomeSettingsWindow()
    except Exception as exc:
        try: push("Welcome settings error: %s" % exc, color=(1, 0.3, 0.3))
        except Exception: pass




# BSLife Ranking Reset: refreshable online schedule panel.
_BSLIFE_RESET_URL = "https://bslife.ir/index.php?post=RankingReset"
_bslife_reset_window = None


def _bslife_parse_reset_page(page):
    """Parse BSLife reset schedule from HTML tables or text fallbacks."""
    try:
        from html import unescape as _html_unescape
        # Extract rows and cells, preserving the source table's actual order.
        table_rows = re.findall(r"(?is)<tr\b[^>]*>(.*?)</tr>", page)
        result = []
        for row in table_rows:
            raw_cells = re.findall(r"(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>", row)
            if len(raw_cells) < 2:
                continue
            cells = []
            for raw in raw_cells:
                raw = re.sub(r"(?is)<br\s*/?>", " ", raw)
                raw = re.sub(r"(?is)<[^>]+>", " ", raw)
                raw = _html_unescape(raw)
                raw = re.sub(r"\s+", " ", raw).strip()
                cells.append(raw)
            joined = " ".join(cells)
            if any(x in joined for x in ("نام سرور", "زمان ریست", "تاریخ")):
                continue
            # Server names in this schedule are usually Latin and contain a
            # mode/number; the date is ISO-formatted and the remaining-time
            # column contains Persian words such as امروز/روز دیگر.
            date = next((c for c in cells if re.search(r"\b20\d{2}-\d{2}-\d{2}\b", c)), "")
            remaining = next((c for c in cells if any(w in c for w in ("امروز", "فردا", "روز دیگر", "ساعت"))), "")
            server_candidates = [c for c in cells if c not in (date, remaining) and
                                 c and not re.fullmatch(r"[\d\s:/-]+", c)]
            server = server_candidates[0] if server_candidates else ""
            if server and (remaining or date):
                result.append((server, remaining or date, date))
        if result:
            # Preserve website order; avoid duplicate header/rows.
            seen, unique = set(), []
            for item in result:
                key = tuple(x.casefold() for x in item)
                if key not in seen:
                    seen.add(key); unique.append(item)
            return unique

        # Fallback for a text/markdown rendering of the page.
        text = _html_unescape(re.sub(r"(?is)<[^>]+>", "\n", page))
        text = re.sub(r"[ \t]+", " ", text)
        lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines()]
        lines = [x for x in lines if x]
        for i, line in enumerate(lines):
            if line.startswith("|"):
                continue
            date_match = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", line)
            if not date_match:
                continue
            date = date_match.group(0)
            nearby = " ".join(lines[max(0, i-2):min(len(lines), i+3)])
            rem_match = re.search(r"(امروز(?:\s+ساعت\s+\d{1,2}:\d{2})?|فردا(?:\s+ساعت\s+\d{1,2}:\d{2})?|\d+\s+روز\s+دیگر(?:\s+ساعت\s+\d{1,2}:\d{2})?)", nearby)
            server = ""
            for candidate in lines[max(0, i-2):min(len(lines), i+3)]:
                if re.search(r"\b(?:FOOTBALL|VOLLEYBALL|FFA|DUEL|SMASH|LIFE|UFC|BOMB)\b", candidate, re.I):
                    server = candidate
                    break
            if server:
                result.append((server, rem_match.group(1) if rem_match else date, date))
        if result:
            return result

        # Last fallback: Markdown pipe table.
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line.startswith("|") or line.count("|") < 3:
                continue
            cells = [re.sub(r"\s+", " ", _html_unescape(c)).strip()
                     for c in line.strip("|").split("|")]
            joined = " ".join(cells)
            if any(x in joined for x in ("نام سرور", "زمان ریست", "تاریخ", "---")):
                continue
            date = next((c for c in cells if re.search(r"\b20\d{2}-\d{2}-\d{2}\b", c)), "")
            remaining = next((c for c in cells if any(w in c for w in ("امروز", "فردا", "روز دیگر", "ساعت"))), "")
            server = next((c for c in cells if c and c not in (date, remaining) and not re.fullmatch(r"[\d\s:/-]+", c)), "")
            if server and (remaining or date):
                result.append((server, remaining or date, date))
        return result
    except Exception:
        return []


def _open_bslife_reset():
    global _bslife_reset_window
    try:
        if _bslife_reset_window is not None:
            _bslife_reset_window.close()
        _bslife_reset_window = _BSLifeResetWindow()
        _bslife_reset_window.refresh()
    except Exception as exc:
        try: push("BSLife Reset error: %s" % str(exc)[:100], color=(1, 0.3, 0.3))
        except Exception: pass


class _BSLifeResetWindow(_SBPanel):
    def __init__(self):
        super().__init__("BSLIFE • RANKING RESET", accent=(0.78, 0.65, 1.0), height=820)
        try: bui.containerwidget(edit=self.root_widget, color=(0.13, 0.045, 0.30))
        except Exception: pass
        bw(parent=self.root_widget, position=(20, self._height - 130),
           size=(self._width - 40, 40), button_type="square", label="↻ REFRESH",
           text_scale=0.78, color=(0.30, 0.16, 0.62), textcolor=(1, 1, 1),
           on_activate_call=self.refresh)
        self._status = bui.textwidget(parent=self.root_widget,
            position=(20, self._height - 165), size=(self._width - 40, 24),
            text="Press REFRESH to load server reset schedule", h_align="left",
            v_align="center", scale=0.62, color=(0.85, 0.8, 1.0))
        self._scroll_y = 50
        self._scroll_h = max(180, self._height - 230)
        self._scroll_w = self._width - 36
        self._scroll = bui.scrollwidget(parent=self.root_widget,
            position=(18, self._scroll_y), size=(self._scroll_w, self._scroll_h),
            highlight=False, capture_arrows=True)
        self._content = bui.containerwidget(parent=self._scroll,
            size=(self._scroll_w, self._scroll_h), background=False)
        self._request_token = 0

    def refresh(self):
        import urllib.request as _urllib_request
        self._request_token += 1
        token = self._request_token
        try:
            bui.textwidget(edit=self._status, text="Loading latest schedule...")
        except Exception:
            pass
        def worker():
            try:
                page = ""
                errors = []
                urls = (
                    _BSLIFE_RESET_URL,
                    _BSLIFE_RESET_URL + "&_sb_refresh=" + str(int(time.time())),
                    "http://bslife.ir/index.php?post=RankingReset",
                )
                for target_url in urls:
                    try:
                        req = _urllib_request.Request(
                            target_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
                                "Cache-Control": "no-cache",
                            },
                        )
                        with _urllib_request.urlopen(req, timeout=10) as response:
                            raw = response.read()
                            charset_match = re.search(
                                rb"charset\s*=\s*['\"]?([\w-]+)", raw[:4096], re.I
                            )
                            charset = charset_match.group(1).decode("ascii", "ignore") if charset_match else "utf-8"
                            try:
                                page = raw.decode(charset, "replace")
                            except Exception:
                                page = raw.decode("utf-8", "replace")
                        if _bslife_parse_reset_page(page):
                            break
                        errors.append("page loaded but schedule format not recognized")
                    except Exception as exc:
                        errors.append(str(exc)[:80])
                rows = _bslife_parse_reset_page(page) if page else []
                error = None if rows else ("; ".join(errors[-2:]) or "No reset rows found")
            except Exception as exc:
                rows, error = [], str(exc)[:140]
            def show():
                if self._closed or token != self._request_token:
                    return
                try:
                    for child in self._content.get_children():
                        child.delete()
                except Exception:
                    pass
                if error:
                    bui.textwidget(parent=self._content, position=(12, self._scroll_h - 60),
                        size=(self._scroll_w - 24, 45), text="Could not load schedule: " + error,
                        h_align="left", v_align="center", scale=0.65, color=(1, 0.7, 0.7))
                    try: bui.textwidget(edit=self._status, text="Refresh failed • check connection")
                    except Exception: pass
                    return
                row_h = 44
                content_h = max(self._scroll_h, len(rows) * row_h + 20)
                try: bui.containerwidget(edit=self._content, size=(self._scroll_w, content_h))
                except Exception: pass
                for idx, (server, remaining, date) in enumerate(rows):
                    y = content_h - 44 - idx * row_h
                    row_color = (0.19, 0.09, 0.34) if idx % 2 == 0 else (0.15, 0.065, 0.28)
                    bw(parent=self._content, position=(6, y - 2), size=(self._scroll_w - 12, 39),
                       button_type="square", label="", color=row_color, enable_sound=False)
                    bui.textwidget(parent=self._content, position=(14, y + 3),
                        size=(self._scroll_w * 0.47, 29), text=server,
                        h_align="left", v_align="center", scale=0.62, color=(1, 1, 1))
                    bui.textwidget(parent=self._content, position=(self._scroll_w * 0.52, y + 3),
                        size=(self._scroll_w * 0.25, 29), text=remaining,
                        h_align="center", v_align="center", scale=0.62, color=(0.9, 0.8, 1.0))
                    bui.textwidget(parent=self._content, position=(self._scroll_w * 0.78, y + 3),
                        size=(self._scroll_w * 0.20, 29), text=date,
                        h_align="right", v_align="center", scale=0.5, color=(0.72, 0.86, 1.0))
                try: bui.textwidget(edit=self._status, text="Loaded %d servers • live from bslife.ir" % len(rows))
                except Exception: pass
            try:
                teck(0.0, show)
            except Exception:
                show()
        thread = threading.Thread(target=worker, name="StudioBonBSLifeRefresh", daemon=True)
        thread.start()



# Redesigned Mod File Manager. Uses the actual user mods directory and
# keeps the reference manager's refresh/delete/confirm functionality.
_file_manager_window = None


def _open_file_manager():
    global _file_manager_window
    try:
        if _file_manager_window is not None:
            _file_manager_window.close()
        _file_manager_window = _StudioBonFileManagerWindow()
    except Exception as exc:
        try:
            push("File Manager error: %s" % str(exc)[:100], color=(1, 0.3, 0.3))
        except Exception:
            pass


class _StudioBonFileManagerWindow(_SBPanel):
    def __init__(self):
        super().__init__("📁 FILE MANAGER", accent=(1.0, 0.84, 0.12),
                         width=760, height=560)
        try:
            bui.containerwidget(edit=self.root_widget, color=(0.025, 0.055, 0.17))
        except Exception:
            pass
        try:
            env = babase.env()
            self.mod_path = str(env.get("python_directory_user") or "")
        except Exception:
            self.mod_path = ""
        if not self.mod_path:
            self.mod_path = _sb_os.path.dirname(_sb_os.path.abspath(__file__))
        bui.textwidget(parent=self.root_widget,
            position=(18, self._height - 125), size=(self._width - 36, 24),
            text="INSTALLED MOD FILES  •  Tap a row's trash icon to remove a file",
            h_align="left", v_align="center", scale=0.58,
            color=(0.72, 0.86, 1.0))
        self._status = bui.textwidget(parent=self.root_widget,
            position=(18, 18), size=(self._width - 210, 26),
            text="Ready", h_align="left", v_align="center", scale=0.58,
            color=(0.58, 0.88, 1.0))
        bw(parent=self.root_widget, position=(self._width - 180, 14), size=(88, 32),
           button_type="square", label="↻ Refresh", text_scale=0.55,
           color=(0.08, 0.35, 0.62), textcolor=(1, 1, 1),
           on_activate_call=self.refresh_files)
        bw(parent=self.root_widget, position=(self._width - 88, 14), size=(70, 32),
           button_type="square", label="PYC", text_scale=0.58,
           color=(0.45, 0.12, 0.24), textcolor=(1, 1, 1),
           on_activate_call=self.confirm_delete_all_pyc)
        self._scroll = bui.scrollwidget(parent=self.root_widget,
            position=(16, 56), size=(self._width - 32, self._height - 194),
            highlight=False, capture_arrows=True)
        self._scroll_w = self._width - 32
        self._scroll_h = self._height - 194
        self._content = bui.containerwidget(parent=self._scroll,
            size=(self._scroll_w, self._scroll_h), background=False)
        self.refresh_files()

    def refresh_files(self):
        try:
            for child in self._content.get_children():
                child.delete()
        except Exception:
            pass
        try:
            files = []
            for name in _sb_os.listdir(self.mod_path):
                path = _sb_os.path.join(self.mod_path, name)
                if _sb_os.path.isfile(path):
                    files.append({"name": name, "path": path,
                                  "size": _sb_os.path.getsize(path)})
            files.sort(key=lambda item: item["name"].casefold())
            if not files:
                bui.textwidget(parent=self._content,
                    position=(12, self._scroll_h - 55),
                    size=(self._scroll_w - 24, 42), text="No files found in the mods folder",
                    h_align="center", v_align="center", scale=0.72,
                    color=(1.0, 0.78, 0.25))
                bui.textwidget(edit=self._status, text="0 files")
                return
            row_h = 34
            content_h = max(self._scroll_h, len(files) * row_h + 20)
            bui.containerwidget(edit=self._content, size=(self._scroll_w, content_h))
            for idx, item in enumerate(files):
                y = content_h - row_h - 8 - idx * row_h
                row_bg = (0.055, 0.12, 0.27) if idx % 2 == 0 else (0.04, 0.085, 0.21)
                bw(parent=self._content, position=(5, y - 2),
                   size=(self._scroll_w - 10, row_h - 2), button_type="square",
                   label="", color=row_bg, enable_sound=False)
                name = item["name"]
                if len(name) > 42:
                    name = name[:39] + "..."
                if item["name"].endswith(".py"):
                    file_color = (0.45, 1.0, 0.64)
                elif item["name"].endswith(".pyc"):
                    file_color = (1.0, 0.63, 0.65)
                elif item["name"].endswith(".json"):
                    file_color = (1.0, 0.88, 0.35)
                else:
                    file_color = (0.86, 0.93, 1.0)
                bui.textwidget(parent=self._content,
                    position=(14, y + 2), size=(self._scroll_w - 230, 24),
                    text=name, h_align="left", v_align="center", scale=0.59,
                    color=file_color)
                size = item["size"]
                size_text = ("%0.1f MB" % (size / 1048576.0) if size >= 1048576
                             else ("%0.1f KB" % (size / 1024.0) if size >= 1024
                                   else "%d B" % size))
                bui.textwidget(parent=self._content,
                    position=(self._scroll_w - 195, y + 2), size=(90, 24),
                    text=size_text, h_align="right", v_align="center", scale=0.52,
                    color=(0.62, 0.78, 0.96))
                bw(parent=self._content, position=(self._scroll_w - 88, y + 1),
                   size=(32, 25), button_type="square", label="🗑",
                   text_scale=0.55, color=(0.55, 0.07, 0.14),
                   textcolor=(1, 1, 1),
                   on_activate_call=lambda p=item["path"], n=item["name"]: self.confirm_delete_file(p, n))
            bui.textwidget(edit=self._status, text="%d files • mods folder" % len(files))
        except Exception as exc:
            try:
                bui.textwidget(parent=self._content,
                    position=(12, self._scroll_h - 55),
                    size=(self._scroll_w - 24, 42),
                    text="Error: " + str(exc)[:100],
                    h_align="center", v_align="center", scale=0.65,
                    color=(1.0, 0.5, 0.5))
                bui.textwidget(edit=self._status, text="Could not read mods folder")
            except Exception:
                pass

    def _confirm_window(self, title, confirm_label, callback):
        width, height = 360, 150
        try:
            sw, sh = bui.get_virtual_screen_size()
        except Exception:
            sw, sh = 800, 600
        x, y = max(10, (sw - width) * 0.5), max(10, (sh - height) * 0.5)
        win = bui.containerwidget(parent=gsw("overlay_stack"),
            position=(x, y), size=(width, height), transition="in_scale",
            scale=1.0, color=(0.055, 0.035, 0.12))
        bui.textwidget(parent=win, position=(18, 82), size=(width - 36, 42),
            text=title, h_align="center", v_align="center", scale=0.68,
            color=(1.0, 0.86, 0.65))
        bw(parent=win, position=(width - 48, height - 48), size=(32, 32),
           button_type="square", label="✕", text_scale=0.7,
           color=(0.4, 0.08, 0.12), textcolor=(1, 1, 1),
           on_activate_call=lambda: bui.containerwidget(edit=win, transition="out_scale"))
        def confirmed():
            try:
                callback()
            finally:
                try: bui.containerwidget(edit=win, transition="out_scale")
                except Exception: pass
        bw(parent=win, position=(width / 2 - 65, 22), size=(130, 36),
           button_type="square", label=confirm_label, text_scale=0.65,
           color=(0.55, 0.07, 0.14), textcolor=(1, 1, 1),
           on_activate_call=confirmed)

    def confirm_delete_file(self, file_path, file_name):
        def delete():
            try:
                _sb_os.remove(file_path)
                push("Deleted: " + file_name, color=(0.35, 1.0, 0.55))
                self.refresh_files()
            except Exception as exc:
                push("Delete failed: " + str(exc)[:80], color=(1, 0.3, 0.3))
        self._confirm_window('Delete "%s"?' % file_name[:36], "🗑 DELETE", delete)

    def confirm_delete_all_pyc(self):
        def delete_all():
            deleted = 0
            try:
                for name in _sb_os.listdir(self.mod_path):
                    if name.endswith(".pyc"):
                        try:
                            _sb_os.remove(_sb_os.path.join(self.mod_path, name))
                            deleted += 1
                        except Exception:
                            pass
                push("Deleted %d .pyc files" % deleted, color=(0.35, 1.0, 0.55))
                self.refresh_files()
            except Exception as exc:
                push("Delete failed: " + str(exc)[:80], color=(1, 0.3, 0.3))
        self._confirm_window("Delete all .pyc cache files?", "DELETE PYC", delete_all)


class _WelcomeSettingsWindow(_SBPanel):
    def __init__(self):
        super().__init__("✉ SERVER WELCOME MESSAGE", accent=(1.0, 0.35, 0.72), height=520)
        try: bui.containerwidget(edit=self.root_widget, color=(0.24, 0.025, 0.13))
        except Exception: pass
        self._toggle = bw(parent=self.root_widget, position=(25, self._height - 155),
            size=(190, 42), button_type="square",
            label="WELCOME: " + ("ON" if _sb_welcome_enabled else "OFF"), text_scale=0.7,
            color=(0.04, 0.35, 0.2) if _sb_welcome_enabled else (0.32, 0.08, 0.1),
            textcolor=(1, 1, 1), on_activate_call=self._toggle_enabled)
        bui.textwidget(parent=self.root_widget, position=(25, self._height - 215),
            size=(self._width - 50, 35), text="Message sent about 2 seconds after joining a server",
            h_align="left", v_align="center", scale=0.72, color=(0.65, 0.82, 0.92))
        bui.textwidget(parent=self.root_widget, position=(25, self._height - 270),
            size=(self._width - 50, 28), text="EDIT YOUR WELCOME TEXT", h_align="left",
            v_align="center", scale=0.72, color=(1.0, 0.8, 0.25))
        self._field = bui.textwidget(parent=self.root_widget,
            position=(25, self._height - 335), size=(self._width - 50, 50),
            text=_sb_welcome_message, editable=True, max_chars=180,
            color=(1.0, 1.0, 1.0), h_align="left", v_align="center", scale=0.8)
        bw(parent=self.root_widget, position=(25, 20), size=(self._width - 50, 44),
            button_type="square", label="SAVE WELCOME SETTINGS", text_scale=0.8,
            color=(0.38, 0.25, 0.04), textcolor=(1, 1, 1), on_activate_call=self._save)

    def _toggle_enabled(self):
        global _sb_welcome_enabled
        _sb_welcome_enabled = not _sb_welcome_enabled
        _sb_save_welcome()
        try:
            bui.buttonwidget(edit=self._toggle,
                label="WELCOME: " + ("ON" if _sb_welcome_enabled else "OFF"),
                color=(0.04, 0.35, 0.2) if _sb_welcome_enabled else (0.32, 0.08, 0.1))
        except Exception: pass

    def _save(self):
        global _sb_welcome_message
        try: _sb_welcome_message = str(bui.textwidget(query=self._field))[:180]
        except Exception: pass
        _sb_save_welcome()
        try: push("Welcome message saved ✓", color=(0.25, 1, 0.65))
        except Exception: pass

# End StudioBon V2 feature pack.
# ---------------------------------------------------------------------------


_BUTTON_CALLBACKS = {
    "ping": _on_ping_press,
    "ip": _on_ip_press,
    "fix": _on_fix_press,
    "calc": lambda: _on_calc_press(_get_live_party_window()) if _get_live_party_window() is not None else None,
    "bon": _on_timer_press,
    "mlon": _on_mlon_press,
    "radar": _open_studiobon_radar,
}

# --- قلاب زدن به خودِ پنجره‌ی پارتی (بدون دست‌کاری چیز دیگه‌ای توش) ---
_orig_party_init = party.PartyWindow.__init__


def _add_party_buttons():
    # ساخت دکمه‌ها را کمی بعد از پایان __init__ انجام می‌دهیم تا با lifecycle
    # پنجره‌ی Party در API 9 تداخل نداشته باشد.
    window = _get_live_party_window()
    if window is None:
        return
    try:
        root = window._root_widget
        if not _widget_exists(root):
            return
        global _live_party_root, _live_party_dims
        _live_party_root = root
        _live_party_dims = (window._width, window._height)
        for key in ("ping", "ip", "calc", "bon", "mlon", "fix", "radar"):
            try:
                if _create_icon_button(key) is None:
                    raise RuntimeError("couldn't create button widget")
            except Exception as e:
                try:
                    push(f"StudioBon error: {e}", color=(1, 0.3, 0.3))
                except Exception:
                    pass
                print(f"StudioBon: couldn't add {key} button: {e}")
    except Exception as e:
        print(f"StudioBon: party button setup failed: {e}")


def _patched_party_init(self, *args, **kwargs):
    _orig_party_init(self, *args, **kwargs)

    global _live_party_window_ref, _live_party_root, _live_party_dims
    _live_party_window_ref = weakref.ref(self)
    _live_party_root = self._root_widget
    _live_party_dims = (self._width, self._height)
    try:
        teck(0.05, _add_party_buttons)
    except Exception:
        _add_party_buttons()



party.PartyWindow.__init__ = _patched_party_init

# Incoming chat hook: the PartyWindow API exposes on_chat_message for new
# messages; _add_msg is also patched so history is handled consistently.
_orig_party_on_chat_message = getattr(party.PartyWindow, "on_chat_message", None)
_orig_party_add_msg = getattr(party.PartyWindow, "_add_msg", None)

def _patched_party_on_chat_message(self, msg):
    # Preserve the original AutoBuy path; additional features observe the same incoming event.
    _autobuy_handle_incoming(msg)
    _sb_v3_process_danger_message(msg)
    _sb_v3_process_secure_message(msg)
    try:
        _sb_parse_server_ping_message(msg)
        _sb_auto_chat_handle_incoming(msg)
    except Exception:
        pass
    if _orig_party_on_chat_message is not None:
        return _orig_party_on_chat_message(self, _finglish_convert_text(msg))
    if not bui.app.config.resolve("Chat Muted"):
        self._add_msg(_finglish_convert_text(msg))

if _orig_party_on_chat_message is not None:
    party.PartyWindow.on_chat_message = _patched_party_on_chat_message

if _orig_party_add_msg is not None:
    def _patched_party_add_msg(self, msg):
        # Some BombSquad builds route remote chat lines through _add_msg
        # without calling on_chat_message. Observe this path too; duplicate
        # protection in _sb_auto_chat_handle_incoming prevents double replies.
        try:
            _sb_auto_chat_handle_incoming(msg)
        except Exception:
            pass
        return _orig_party_add_msg(self, _finglish_convert_text(msg))
    party.PartyWindow._add_msg = _patched_party_add_msg



# ---------------------------------------------------------------------------
# نام سازنده / شناسه‌ی نسخه
# عمداً هیچ Activity.on_transition_in هوکی اینجا نداریم؛
# بعضی نسخه‌های BombSquad ممکن است در زمان transition، ClassicAppMode را فعال نکنند.
WATERMARK_TEXT = "StudioBon"
# ---------------------------------------------------------------------------


def _announce_loaded():
    try:
        push("@StudioBon on Telegram🤩", color=(0.3, 1, 0.3))
        # Re-show after two seconds so the startup notice remains visible longer.
        teck(2.0, _announce_loaded_refresh)
    except Exception:
        pass


def _announce_loaded_refresh():
    try:
        push("@StudioBon on Telegram🤩", color=(0.3, 1, 0.3))
    except Exception:
        pass




class StudioBon_Mod_v1(Plugin):

    def on_app_running(self) -> None:
        teck(1.5, _announce_loaded)

    def has_settings_ui(self) -> bool:
        # همین باعث میشه دکمه‌ی «تنظیمات» کنار این مود توی لیست افزونه‌ها ظاهر بشه
        return True

    def show_settings_ui(self, source_widget) -> None:
        _open_settings_hub()

    def __del__(self):
        try:
            _ping_thread.stop()
        except Exception:
            pass


# ba_meta export babase.Plugin
class StudioBon_Mod_V2_F_CHANNEL(StudioBon_Mod_v1):
    """StudioBon plugin export for BombSquad API 9."""
    pass
