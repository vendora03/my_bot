import logging, os, json, sys
from services import database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
restore_json = os.path.join(BASE_DIR, "restore.json")

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

conn = database.DB_Get_Connection()
if "variables" in data:
    database.DB_Drop_Table_Variable(conn)    
    database.DB_Create_Table_Variable(conn)
    
if "vip_variables" in data:
    database.DB_Drop_Table_VIP_Variable(conn)
    database.DB_Create_Table_VIP_Variable(conn)
    
for key, values in data.items():
    if key == "variables":
        rows = [
            (isi["access_code"], isi["content"], isi["file_id"], isi["created_at"])
            for isi in values
        ]
        database.DB_Save_All_Variable(rows, conn)
        
    elif key == "vip_variables":
        rows = [
            (isi["access_code"], isi["content"], isi["file_id"], isi["created_at"])
            for isi in values
        ]
        database.DB_Save_All_VIP_Variable(rows, conn)
        
conn.commit()
conn.close()


print("=============== RESULT ===============")
no = 0
for key, values in data.items():
    no += 1
    print(f"{no}. {key}: {len(values)} Items [SAVED]")
print("======================================")



