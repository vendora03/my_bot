import sys, time
from services import settings as Set
from services.logic import Send_Message_Admin
from datetime import datetime, timedelta


def maintenance(state):
    state = str(state).lower()
    settings = Set.Settings()
    if state == "true":
        if settings.get("maintenance") == state:
            maintenance_start = int(settings.get("maintenance_start"))
            raw_durasi = int(time.time()) - maintenance_start
            durasi = str(timedelta(seconds=raw_durasi))
            print(f"==============================\n[INFO] BOT ALREADY IN MAINTENANCE\nDuration: {durasi}\n==============================")    
            Send_Message_Admin(f"<i><b>[INFO] BOT ALREADY IN MAINTENANCE</b></i>\nDuration: {durasi}", None)
            return
        
        settings.set("maintenance", state)
        maintenance_start = str(int(time.time()))
        waktu_mulai = datetime.fromtimestamp(int(maintenance_start))
        settings.set("maintenance_start", maintenance_start)
        print(f"==============================\n[INFO] BOT IN MAINTENANCE MODE\nTime: {waktu_mulai.strftime('%d/%m/%Y %H:%M:%S')}\n==============================")
        Send_Message_Admin(f"<i><b>[INFO] BOT IN MAINTENANCE MODE</b></i>\nTime: {waktu_mulai.strftime('%d/%m/%Y %H:%M:%S')}", None)
    else:
        if settings.get("maintenance") == state:
            print(f"==========================\n[INFO] BOT IN WORKING MODE\n==========================")
            Send_Message_Admin(f"<i><b>[INFO] BOT IN WORKING MODE</b></i>", None)
            return
        
        maintenance_start = int(settings.get("maintenance_start"))
        raw_durasi = int(time.time()) - maintenance_start
        durasi = str(timedelta(seconds=raw_durasi))
        print(f"==========================\n[INFO] BOT IN WORKING MODE\nDuration: {durasi}\n==========================")
        settings.set("maintenance", state)
        settings.set("maintenance_start", "")
        Send_Message_Admin(f"<i><b>[INFO] BOT IN WORKING MODE</b></i>\nDuration: {durasi}", None)

if __name__ == "__main__":
    task = sys.argv[1].lower() if len(sys.argv) > 1 else None
    if len(sys.argv) > 2:
        sys.exit()
    if task in ["true", "false"]:
        maintenance(task)