from services import settings as Set
import sys

if len(sys.argv) > 2:
    sys.exit()
    
task = sys.argv[1].lower() if len(sys.argv) > 1 else None

settings = Set.Settings()

if task in ["true","false"]:
    settings.set("maintenance", task)
    if task == "true":
        print("[INFO] BOT IN MAINTENANCE MODE")
    else:
        print("[INFO] BOT IN WORKING MODE")
     
        