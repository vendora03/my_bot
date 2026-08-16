from services import settings as Set
import sys, time, bot_instance, asyncio
from datetime import datetime, timedelta
from config import ADMIN_IDS

async def Send_Message_Admin(message):
    await bot_instance.bot.send_message(
        chat_id=ADMIN_IDS,
        text=message,
        parse_mode="HTML"
    )
def maintenance(state):
    state = state.lower()
    settings = Set.Settings()
    settings.set("maintenance", state)
    if state == "true":
        maintenance_start = str(int(time.time()))
        waktu_mulai = datetime.fromtimestamp(int(maintenance_start))
        settings.set("maintenance_start", maintenance_start)
        print(f"[INFO] BOT IN MAINTENANCE MODE\nTime: {waktu_mulai.strftime("%d/%m/%Y %H:%M:%S")}")
        asyncio.run(Send_Message_Admin(f"<b>[INFO] BOT IN MAINTENANCE MODE</b>\nTime: {waktu_mulai.strftime("%d/%m/%Y %H:%M:%S")}"))
    else:
        maintenance_start = int(settings.get("maintenance_start"))
        raw_durasi = int(time.time()) - maintenance_start
        durasi = str(timedelta(seconds=raw_durasi))
        print(f"[INFO] BOT IN WORKING MODE\nDuration: {durasi}")
        settings.set("maintenance_start", "")
        asyncio.run(Send_Message_Admin(f"<b>[INFO] BOT IN WORKING MODE</b>\nDuration: {durasi}"))

if __name__ == "__main__":
    task = sys.argv[1].lower() if len(sys.argv) > 1 else None
    if len(sys.argv) > 2:
        sys.exit()
    if task in ["true", "false"]:
        maintenance(task)