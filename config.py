import os
import datetime,pytz
from dotenv import load_dotenv

load_dotenv()

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

# ===== ENV =====
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

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

# ===== TIP ======
TIP = "Tidak Ada Tips"

# ===== ADMIN =====
ADMIN_IDS = list(
    map(int, os.getenv("ADMIN_IDS", "").split(","))
)
