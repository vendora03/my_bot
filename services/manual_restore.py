import sqlite3, logging, os, json, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
restore_json = os.path.join(BASE_DIR, "restore.json")
db_path = os.path.join(BASE_DIR, "data", "bot_kulu.db")

if not os.path.exists(restore_json):
    print("File Not Found -> restore.json")
    sys.exit()
    
with open(restore_json, "r", encoding="utf-8") as f_json:
    try:
        data = json.load(f_json)
    except json.JSONDecodeError:
        print("[MANUAL RESTORE] FILE CORRUPT -> restore.json")
        sys.exit()
    
print("\n======= MANUAL RESTORE PROGRAM =======")
print(f"All Key: {len(data)}")

no = 0
for key, values in data.items():
    no += 1
    print(f"{no}. {key}: {len(values)} Items")

user_input = input("Continue? [Enter/Input Value]: ")
if user_input:
    print("=============== CANCEL ===============\n")
    sys.exit()
    
VALID_KEYS = {"variables", "vip_variables"}
invalid_keys = set(data) - VALID_KEYS
if invalid_keys:
    print("[MANUAL RESTORE] Key Invalid...")
    logging.info("[MANUAL RESTORE] FAILED RESTORE -> Key invalid...")
    print("=============== CANCEL ===============\n")
    sys.exit()
        
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    if "variables" in data:
        cursor.execute("DROP TABLE IF EXISTS variables")
            
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_code TEXT NOT NULL UNIQUE ON CONFLICT IGNORE,
                content TEXT NOT NULL,
                file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """) 
    if "vip_variables" in data:
        cursor.execute("DROP TABLE IF EXISTS vip_variables")
            
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vip_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_code TEXT NOT NULL UNIQUE ON CONFLICT IGNORE,
                content TEXT NOT NULL,
                file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """) 
        
    for key, values in data.items():
        if key == "variables":
            rows = [
                (isi["access_code"], isi["content"], isi["file_id"], isi["created_at"])
                for isi in values
            ]
            cursor.executemany("""
                INSERT INTO variables (access_code, content, file_id, created_at)
                VALUES (?, ?, ?, ?)
            """, rows)
        elif key == "vip_variables":
            rows = [
                (isi["access_code"], isi["content"], isi["file_id"], isi["created_at"])
                for isi in values
            ]
            cursor.executemany("""
                INSERT INTO vip_variables (access_code, content, file_id, created_at)
                VALUES (?, ?, ?, ?)
            """, rows)


print("=============== RESULT ===============")
no = 0
for key, values in data.items():
    no += 1
    print(f"{no}. {key}: {len(values)} Items [SAVED]")
print("======================================")



