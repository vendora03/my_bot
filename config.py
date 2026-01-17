import os
import datetime,pytz
from dotenv import load_dotenv

load_dotenv()

# ==== SETTINGS 
SETTINGS_SCHEMA = {
    "debug": "bool",
    "start_info_state": "bool",
    "start_info": "text",
    "vip_info_state": "bool",
    "vip_info": "text",
    "group": "text",
    "tips": "text",
}

# ===== BASE =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== BOT =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = "Gempa Lokal"
TIMEZONE = os.getenv("TIMEZONE", "Asia/Jakarta")

# ===== API GEMINI =====
API_GEMINI = os.getenv("API_GEMINI",False)

# ===== START TIME =====
tz = pytz.timezone(TIMEZONE)
START_TIME = datetime.datetime.now(tz)

# ===== DAILY SCHEDULE =====
DAILY_UPDATE = os.getenv("DAILY_UPDATE", "false").lower() == "true"

# ===== DATABASE =====
DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(BASE_DIR, "data", "bot.db")
)

# ===== BACKUP =======
BACKUP_PATH = os.getenv(
    "BACKUP_PATH",
    os.path.join(BASE_DIR, "backup.json")
)

# ===== PROMPT ======
PROMPT = os.getenv("GEMINi")

DEBUG = False

# ==== GET SETTINGS ====
IS_LOG = os.getenv("IS_LOG", "false").lower() 
START_INFO_STATE = os.getenv("DAILY_UPDATE", "false").lower() 
START_INFO = "HI @user\nKamu Belum bergabung Nih\nGabung Terlebih dahulu sebelum akses content\n"
VIP_INFO_STATE = os.getenv("DAILY_UPDATE", "false").lower() 
VIP_INFO = "Content Locked\nAkses Content Dengan VIP\n\n-Langsung Nonton\n-Akses All Konten\n\n"
GROUP = os.getenv("GROUP", "")
TIPS = os.getenv("TIPS","Tidak Ada Tips")


# ==== SET SETTINGS ====
DEFAULT_SETTINGS = {
    "debug": IS_LOG,
    "start_info_state": START_INFO_STATE,
    "start_info": START_INFO,
    "vip_info_state": VIP_INFO_STATE,
    "vip_info": VIP_INFO,
    "group": GROUP,
    "tips": TIPS,
}

# ===== ADMIN ID =======
_admin_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = (
    list(map(int, _admin_ids.split(",")))
    if _admin_ids
    else []
)

# ===== ADMIN ID =======
CHANNEL_ID = os.getenv("CHANNEL_ID", "")