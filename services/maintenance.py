from services import settings as Set
import sys, time, json, socket
from datetime import datetime, timedelta

def Send_Message_Admin(message):
    data = json.dumps({
        "action": "send_message",
        "message": message,
        "file_id": None
    }).encode("utf-8")

    with socket.create_connection(("127.0.0.1", 8765)) as sock:
        sock.sendall(data)
        response = sock.recv(1024)

    return response.decode("utf-8")

def maintenance(state):
    state = state.lower()
    settings = Set.Settings()
    settings.set("maintenance", state)
    if state == "true":
        maintenance_start = str(int(time.time()))
        waktu_mulai = datetime.fromtimestamp(int(maintenance_start))
        settings.set("maintenance_start", maintenance_start)
        print(f"[INFO] BOT IN MAINTENANCE MODE\nTime: {waktu_mulai.strftime('%d/%m/%Y %H:%M:%S')}")
        Send_Message_Admin(f"<b>[INFO] BOT IN MAINTENANCE MODE</b>\nTime: {waktu_mulai.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        maintenance_start = int(settings.get("maintenance_start"))
        raw_durasi = int(time.time()) - maintenance_start
        durasi = str(timedelta(seconds=raw_durasi))
        print(f"[INFO] BOT IN WORKING MODE\nDuration: {durasi}")
        settings.set("maintenance_start", "")
        Send_Message_Admin(f"<b>[INFO] BOT IN WORKING MODE</b>\nDuration: {durasi}")

if __name__ == "__main__":
    task = sys.argv[1].lower() if len(sys.argv) > 1 else None
    if len(sys.argv) > 2:
        sys.exit()
    if task in ["true", "false"]:
        maintenance(task)