import sqlite3, logging
from config import (
    # DEBUG,
    DB_PATH)
from models.user_model import User

# ====== [DB] Connection Handler ======== 
def get_connection():
    return sqlite3.connect(DB_PATH)

# ====== [DB] Creating Table Data ======= 
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE ON CONFLICT IGNORE,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            is_vip INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vip_created TIMESTAMP 
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_code TEXT NOT NULL UNIQUE ON CONFLICT IGNORE,
            content TEXT NOT NULL,
            file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """) 
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_code VARCHAR(6) NOT NULL UNIQUE ON CONFLICT IGNORE,
            content TEXT NOT NULL,
            file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """) 
   
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_code VARCHAR(6) NOT NULL UNIQUE ON CONFLICT IGNORE,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """) 
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vip_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_code TEXT NOT NULL UNIQUE ON CONFLICT IGNORE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vip_variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_code TEXT NOT NULL UNIQUE ON CONFLICT IGNORE,
            content TEXT NOT NULL,
            file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP
        )
    """)
    
    
    conn.commit()
    conn.close()

    logging.info("[DB] Database initialized")

# ====== [DB] Insert User =============== 
def DB_Save_User(user_model: User):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (
                user_id, first_name, last_name, username,
                is_vip, is_active, last_active, created_at, vip_created
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                username = excluded.username,
                last_active = excluded.last_active,
                is_vip = excluded.is_vip,
                vip_created = CASE
                    WHEN users.is_vip = 0 AND excluded.is_vip = 1
                    THEN excluded.vip_created
                    ELSE users.vip_created
                END
        """, (
            user_model.user_id,
            user_model.first_name,
            user_model.last_name,
            user_model.username,
            int(user_model.is_vip),
            int(user_model.is_active),
            user_model.last_active,         
            user_model.created_at,          
            user_model.vip_created if user_model.is_vip else None  
        ))

        conn.commit()

        # if DEBUG:
        #     print(f"[DB] User saved: {user_model.user_id}")

    except Exception as e:
        logging.error("[DB ERROR]", e)
        raise

    finally:
        conn.close()


# ====== [DB] Insert Variable =========== 
def DB_Save_Variable(content, access_code, file_id, now):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO variables (access_code, content, file_id, created_at) VALUES (?, ?, ?, ?)", (access_code, content, file_id, now))

    conn.commit()
    # if DEBUG:
    #     print(f"[DB] Content: {content}")
    #     print(f"[DB] Variable saved: {access_code}")

    conn.close()

# ====== [DB] Insert Daily Schedule ===== 
def DB_Save_Daily_Schedule(access_code,content,file_id,now):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO daily_schedule (access_code, content, file_id, created_at) VALUES (?, ?, ?, ?)", (access_code, content, file_id, now))

    conn.commit()
    # if DEBUG:
    #     print(f"[DB] Content: {content}")
    #     print(f"[DB] Variable saved: {access_code}")

    conn.close()
    return access_code
    
    
# ====== [DB] Insert Template =========== 
def DB_Save_Template(access_code,content,now):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO template (access_code, content, created_at) VALUES (?, ?, ?)", (access_code,content,now))

    conn.commit()
    # if DEBUG:
    #     print(f"[DB] Content: {content}")
    #     print(f"[DB] Variable saved: {access_code}")

    conn.close()
    return access_code
    

# ====== [DB] Get List All Template ===== 
def DB_All_Get_Template():
    # if DEBUG:
    #     print("[DB] Get All Template")
        
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT access_code FROM template")
    alls = cursor.fetchall()
    conn.close()
    return [row[0] for row in alls] if alls else []

# ====== [DB] Show Content Template =====
def DB_Get_Template(access_code: str):
    # if DEBUG:
    #     print("[DB] Get Content Template")
        
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM template WHERE access_code = ?",(access_code,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return ""
    
# ====== [DB] Delete Template ===========
def DB_Remove_Template(access_code) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM template WHERE access_code = ?",(access_code,))

        conn.commit()
        # if DEBUG:
        #     print(f"[DB] Template Removed")
        return cursor.rowcount > 0
    finally:
        conn.close()
  
    
# ====== [DB] Count Total Variable ======
def DB_Cek_Index_Variable() -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM variables")
    total_data = int(cursor.fetchone()[0])
    conn.close()
    return total_data

# ====== [DB] Cek Variable Exist ========
def DB_Get_User(user_id: str) -> User:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, first_name, last_name, username, is_vip, is_active, last_active, created_at, vip_created FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    
    return User(
        user_id=row[0],
        first_name=row[1],
        last_name=row[2],
        username=row[3],
        is_vip=row[4],
        is_active=row[5],
        last_active=row[6],
        created_at=row[7],
        vip_created=row[8],
    )


# ====== [DB] Cek Variable Exist ========
def DB_Cek_Variable(access_code: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM variables WHERE access_code = ? LIMIT 1",
        (access_code,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return True  
    return False  

# ====== [DB] Cek Daily_Schedule Exist ===
def DB_Cek_Daily_Schedule(access_code: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM daily_schedule WHERE access_code = ? LIMIT 1",
        (access_code,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return True   
    return False   

# ====== [DB] Cek Template Exist ========
def DB_Cek_Template(access_code: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM template WHERE access_code = ? LIMIT 1",
        (access_code,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return True   
    return False  

# ====== [DB] Get Daily Auto ============
def DB_Get_Daily_Schedule() -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, content FROM daily_schedule ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        conn.close()
        return ""

    schedule_id, content = row
    cursor.execute("DELETE FROM daily_schedule WHERE id = ?",(schedule_id,))
    conn.commit()
    conn.close()

    return content



# ====== [DB] Get List All Schedule  ====
def DB_All_Get_Daily_Schedule():
    # if DEBUG:
    #     print("[DB] Get All Daily Schedule")
        
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT access_code FROM daily_schedule")
    alls = cursor.fetchall()
    conn.close()
    return [row[0] for row in alls] if alls else []

# ====== [DB] Show Content Schedule =====
def DB_Show_Daily_Schedule(access_code: str):
    # if DEBUG:
    #     print("[DB] Get Content Daily Schedule")
        
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT content, file_id FROM daily_schedule WHERE access_code = ?",(access_code,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "content": row[0],
            "file_id": row[1]
        }
    return {}

# ====== [DB] Get Variable ==============
def DB_Get_Content(access_code: str):
    # if DEBUG:
    #     print("[DB] Get Content")
        
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT content, file_id FROM variables WHERE access_code = ? ",(access_code,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "content": row[0],
            "file_id": row[1]
        }
    return {}


# ====== [DB] Get All User ==============
def DB_Get_All_User():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, is_vip, is_active, last_active, created_at, vip_created FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "user_id": row[0],
            "is_vip": row[1],
            "is_active": row[2],
            "last_active": row[3],
            "created_at": row[4],
            "vip_created": row[5]
        }
        for row in rows
    ]

# ====== [DB] Delete Schedule Auto ======
def DB_Remove_Daily_Schedule(access_code) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_schedule WHERE access_code = ?",(access_code,))

        conn.commit()
        # if DEBUG:
        #     print(f"[DB] Schedule Removed")
        return cursor.rowcount > 0
    finally:
        conn.close()
        
# ====== [DB] Backup To Json ============
def DB_Backup():
    conn = get_connection()    
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    backup = {}

    # USERS
    cursor.execute("""
        SELECT user_id, first_name, last_name, username, is_vip, is_active, last_active, created_at, vip_created
        FROM users
    """)
    backup["users"] = [dict(row) for row in cursor.fetchall()]

    # VARIABLES
    cursor.execute("""
        SELECT access_code,  content, file_id, created_at
        FROM variables
    """)
    backup["variables"] = [dict(row) for row in cursor.fetchall()]

    # VIP CODES
    cursor.execute("""
        SELECT access_code, created_at
        FROM vip_codes
    """)
    backup["vip_codes"] = [dict(row) for row in cursor.fetchall()]

    # VIP VARIABLES
    cursor.execute("""
        SELECT access_code, content, file_id, created_at
        FROM vip_variables
    """)
    backup["vip_variables"] = [dict(row) for row in cursor.fetchall()]
    
    
    # DAILY SCHEDULE
    cursor.execute("""
        SELECT access_code, content, file_id, created_at
        FROM daily_schedule
    """)
    backup["daily_schedule"] = [dict(row) for row in cursor.fetchall()]

    # TEMPLATE
    cursor.execute("""
        SELECT access_code, content, created_at
        FROM template
    """)
    backup["template"] = [dict(row) for row in cursor.fetchall()]
    
    # BOT SETTINGS
    cursor.execute("""
        SELECT key, value, updated_at
        FROM bot_settings
    """)
    backup["bot_settings"] = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return backup





# <<<<<<<< START VIP CODE >>>>>>>>>>>>>>>

# ====== [DB] Insert VIP Code ============
def DB_Save_VIP_Code(access_code: str, now):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO vip_codes (access_code, created_at) 
        VALUES (?, ?)
    """, (access_code, now))
    
    conn.commit()
    logging.info(f"[DB] VIP Code saved: {access_code}")
    conn.close()
    return access_code

# ====== [DB] Update User VIP Status ======
def DB_Update_User_VIP(user_id: str, is_vip: bool, now):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET is_vip = ?, vip_created = ?
        WHERE user_id = ?
    """, (int(is_vip), now, user_id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    logging.info(f"[DB] User VIP status updated: {user_id} -> {is_vip}")
    
    return affected > 0

# ====== [DB] Check VIP Code Exist & Valid ==
def DB_Check_VIP_Code(access_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT access_code 
        FROM vip_codes 
        WHERE access_code = ?
        LIMIT 1
    """, (access_code,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"access_code": row[0]}
    return None

# ====== [DB] Delete VIP Code (with race condition prevention) ====
def DB_Delete_VIP_Code(access_code: str, user_id: str):
    conn = get_connection()
    conn.isolation_level = 'EXCLUSIVE'  
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT access_code FROM vip_codes 
            WHERE access_code = ? 
        """, (access_code,))
        
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "message": "Kode VIP tidak valid atau sudah digunakan"}
        
        cursor.execute("""
            DELETE FROM vip_codes 
            WHERE access_code = ?
        """, (access_code,))
        
        if cursor.rowcount == 0:
            return {"success": False, "message": "Kode VIP sudah digunakan oleh user lain"}
        
        conn.commit()
        
        logging.info(f"[DB] VIP Code deleted, used by: {user_id}")
        
        return {"success": True, "message": "Kode VIP berhasil digunakan"}
        
    except Exception as e:
        conn.rollback()
        logging.error(f"[DB ERROR] VIP Code deletion failed: {e}")
        return {"success": False, "message": "Terjadi kesalahan"}
    finally:
        conn.close()

# <<<<<<<< END VIP CODE >==>>>>>>>>>>>>>>


# def DB_Remove_All_VIP():
#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute("""
#         UPDATE users
#         SET is_vip = 0
#         WHERE is_vip = 1
#     """)

#     conn.commit()
#     conn.close()

#     # if DEBUG:
#     #     print("[DB] All VIP users have been reset to non-VIP")




# <<<<<<<< START VIP VARIABLE >>>>>>>>>>>

# ====== [DB] Insert VIP Variable =========
def DB_Save_VIP_Variable(access_code, content, file_id, now):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO vip_variables (access_code, content, file_id, created_at) 
        VALUES (?, ?, ?, ?)
    """, (access_code, content, file_id, now))
    
    conn.commit()
    # if DEBUG:
    #     print(f"[DB] VIP Variable saved: {access_code}")
    conn.close()

# ====== [DB] Check VIP Variable Exist ====
def DB_Check_VIP_Variable(access_code: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 1 FROM vip_variables 
        WHERE access_code = ? 
        LIMIT 1
    """, (access_code,))
    
    row = cursor.fetchone()
    conn.close()
    
    return row is not None

# ====== [DB] Get VIP Content =============
def DB_Get_VIP_Content(access_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT content, file_id 
        FROM vip_variables 
        WHERE access_code = ?
    """, (access_code,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "content": row[0],
            "file_id": row[1]
        }
    return None

# ====== [DB] Get All VIP Contents ========
def DB_Get_All_VIP_Contents():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT content, file_id
        FROM vip_variables 
        ORDER BY created_at ASC 
    """)
    
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "content": row[0],
            "file_id": row[1]
        }
        for row in rows
    ]
    
# ====== [DB] Get Latest VIP Contents =====
def DB_Get_Latest_VIP_Contents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, file_id
        FROM vip_variables
        ORDER BY created_at DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "content": row[0],
        "file_id": row[1]
    }
    
# <<<<<<<< END VIP VARIABLE >>>>>>>>>>>>>

    
# <<<<<<<< START Bot Settings >>>>>>>>>>>

# ====== [DB] Set Bot Setting ===========
def DB_Set_Bot_Settings(key: str, value: str, now: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO bot_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value, now))
        
        conn.commit()
        
        # if DEBUG:
        #     print(f"[DB] Bot setting saved: {key}")
        
        return True
        
    except Exception as e:
        logging.error(f"[DB ERROR] Failed to save bot setting: {e}")
        return False
        
    finally:
        conn.close()


# ====== [DB] Get Bot Setting ===============
def DB_Get_Bot_Settings(key: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT value 
        FROM bot_settings 
        WHERE key = ?
    """, (key,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # if DEBUG:
        #     print(f"[DB] Bot setting retrieved: {key}")
        return row[0]
    
    # if DEBUG:
    #     print(f"[DB] Bot setting not found: {key}")
    return None
    
    
# <<<<<<<< END Bot Settings >>>>>>>>>>>>>
    
    