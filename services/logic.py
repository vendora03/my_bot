import random, string, pytz, json, os
from datetime import datetime, timedelta
from io import BytesIO

from telegram.error import NetworkError
from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from config import ADMIN_IDS,API_GEMINI,BACKUP_PATH, DEBUG, TIMEZONE, PROMPT
from services.database import (
    User,
    DB_Get_User,
    DB_Save_User,
    DB_Save_Variable,
    DB_Get_Content,
    DB_Get_All_User,    
    DB_Save_Daily_Schedule,
    DB_Get_Daily_Schedule,
    DB_All_Get_Daily_Schedule,
    DB_Show_Daily_Schedule,
    DB_Remove_Daily_Schedule,
    DB_Cek_Index_Variable,
    DB_Cek_Variable,
    DB_Cek_Daily_Schedule,
    DB_Cek_Template,
    DB_Save_Template,
    DB_All_Get_Template,
    DB_Get_Template,
    DB_Remove_Template,
    DB_Backup,
    DB_Save_VIP_Code,
    DB_Check_VIP_Code,
    DB_Delete_VIP_Code,
    DB_Update_User_VIP,
    DB_Save_VIP_Variable,
    DB_Check_VIP_Variable,
    DB_Get_VIP_Content,
    DB_Get_All_VIP_Contents,
    DB_Get_Latest_VIP_Contents)

# <<<<<<<<<< ERROR Handler >>>>>>>>>>>>>>
async def error_handler(update, context):
    err = context.error

    if isinstance(err, NetworkError):
        # biarin aja, PTB bakal retry otomatis
        return

    print(f"ERROR: {err}")

# <<<<<<<<<< START GENERAL >>>>>>>>>>>>>>
async def on_Startup(app):
    await set_Base_User_Commands(app)

async def set_Base_User_Commands(app):
    commands = [
        BotCommand("start", "Mulai bot"),
        BotCommand("ping", "Uptime Bot"),
    ]
    await app.bot.set_my_commands(
        commands,
        scope=BotCommandScopeDefault()
    )
       
async def set_commands_for_user(app, user: User):
    commands = build_Commands_User(user)

    await app.bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeChat(chat_id=user.user_id),
        language_code=None
    )
 
def build_Commands_User(user: User) -> list[BotCommand]:
    BASE_USER_COMMANDS = [
        ("start", "Mulai bot"),
        ("ping", "Uptime Bot"),
    ]

    VIP_COMMANDS = [
        ("getall", "Semua Konten VIP"),
        ("getnew", "Konten VIP Terbaru"),
    ]

    ADMIN_COMMANDS = [
        ("userstat", "Cek User Statistic"),
        ("backup", "Backup Database"),
        ("restore", "Restore Database"),
        ("broadcast", "Buat Broadcast"),
        ("schedule", "Buat Schedule"),
        ("setvariable", "Set Variable"),
        
        ("createvipcode", "Buat Kode VIP Baru"),
        ("setvipvariable", "Simpan Konten VIP"),
        # ("listvip", "List Semua VIP User"),
        
        ("setdailyschedule", "Simpan Daily Schedule"),
        ("showdailyschedule", "Tampilkan Daily Schedule"),
        ("deletedailyschedule", "Hapus Daily Schedule"),
        
        ("gettemplate", "Assign Template"),
        ("settemplate", "Simpan Template"),
        ("showtemplate", "Tampilkan Template"),
        ("deletetemplate", "Hapus Template"),
    ]

    commands = []

    # base command selalu ada
    commands.extend(
        BotCommand(command=cmd, description=desc)
        for cmd, desc in BASE_USER_COMMANDS
    )

    # VIP command
    if user.is_vip:
        commands.extend(
            BotCommand(command=cmd, description=desc)
            for cmd, desc in VIP_COMMANDS
        )

    # Admin command
    if user.user_id in ADMIN_IDS:
        commands.extend(
            BotCommand(command=cmd, description=desc)
            for cmd, desc in ADMIN_COMMANDS
        )

    return commands
 
 
 
 
    

# ====== Backup To Json Logic =========== 
def backup_Logic():
    data = DB_Backup()

    json_bytes = json.dumps(
        data,
        indent=2,
        ensure_ascii=False
    ).encode("utf-8")

    file = BytesIO(json_bytes)
    file.name = "backup.json"
    
    info = {
        "users": len(data.get("users", [])),
        "variables": len(data.get("variables", [])),
        "vip_codes": len(data.get("vip_codes", [])),
        "vip_variables": len(data.get("vip_variables", [])),
        "daily_schedule": len(data.get("daily_schedule", [])),
        "template": len(data.get("template", [])),
    }
    
    return file,info

# ====== Restore Backup Logic =========== 
def restore_Backup_Logic():
    if not os.path.exists(BACKUP_PATH):
        if DEBUG:
            print("[BACKUP] Backup Aborted: Path Not Found")
        return ""

    try:
        with open(BACKUP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # restore users
        for u in data.get("users", []):
            DB_Save_User(User(
                user_id=u["user_id"],
                first_name=u["first_name"],
                last_name=u.get("last_name",""),
                username=u.get("username","Anonym"),
                is_active=u["is_active"],
                last_active=u["last_active"],
                created_at=u["created_at"],
                vip_created=u["vip_created"]))

        # restore variables
        for v in data.get("variables", []):
            DB_Save_Variable(
                content=v["content"],
                access_code=v["access_code"],
                file_id=v["file_id"],
                now=v["created_at"]
            )
            
            
        # restore vip_codes
        for vc in data.get("vip_codes", []):
            DB_Save_VIP_Code(
                access_code=vc["access_code"],
                now=vc["created_at"]
            )
            
            
        # restore vip_variables
        for vv in data.get("vip_variables", []):
            DB_Save_VIP_Variable(
                content=vv["content"],
                access_code=vv["access_code"],
                file_id=vv.get("file_id"),
                now=vv["created_at"]
            )
            
            
        # restore daily schedule            
        for d in data.get("daily_schedule", []):
            DB_Save_Daily_Schedule(
                access_code=d["access_code"],
                content=d["content"],
                file_id=d["file_id"],
                now=d["created_at"]
            )
            
        # restore template          
        for d in data.get("template", []):
            DB_Save_Template(
                access_code=d["access_code"],
                content=d["content"],
                now=d["created_at"]
            )

        if DEBUG:
            print("[BACKUP] Restore Completed")

        os.remove(BACKUP_PATH)

        if DEBUG:
            print("[BACKUP] backup.json Deleted")

        return (
            "✅ <i>Backup Restored:</i>\n\n"
            f"Users            : <b>{len(data.get('users', []))}</b> row\n"
            f"Variables       : <b>{len(data.get('variables', []))}</b> row\n"
            f"VIP Codes      : <b>{len(data.get('vip_codes', []))}</b> row\n"
            f"VIP Variables  : <b>{len(data.get('vip_variables', []))}</b> row\n"
            f"Schedule       : <b>{len(data.get('daily_schedule', []))}</b> row\n"
            f"Template       : <b>{len(data.get('template', []))}</b> row\n"
        )    
        
    except Exception as e:
        if DEBUG:
            print("[BACKUP ERROR] Restore Failed:", e)
        return f"<b>!!!Restored Failed!!!</b>"
    
# ====== Get Current Time =============== 
def get_Time_Logic():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    return now

# ====== Create Access Code ============= 
def create_Access_Code(panjang: int) -> str:
    karakter = string.ascii_uppercase + string.ascii_lowercase + string.digits
    random_text = ''.join(random.choice(karakter) for _ in range(panjang))
    return random_text  
    
# ====== Generate AI Tips =============== 
def generate_Tip_Logic() -> str:
    if DEBUG:
        print("[Logic] Generate Tip")
        
    if not API_GEMINI:
        return "Tidak Ada Tips!"
        
    from google import genai
    from google.genai.errors import ClientError
    
    try:
        client = genai.Client(api_key=API_GEMINI)

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=PROMPT
        )
        
        tips = response.text
        kata = tips.split()
        if len(kata) > 5:
            tips = "Tidak Ada Tips!!"
            if DEBUG:
                print(f"[Logic] Generate GEMINI: {response.text}")
        
        if DEBUG:
            print(f"[Logic] Generate Success: {tips}")
            
        return tips
    except ClientError as e:
        # 'ClientError' object has no attribute 'status_code'
        if e.status_code == 429:  
            print("Rate limit reached, retrying...")
        if DEBUG:
            print(f"[Logic] Generate Failed!!!")
        return "Tidak Ada Tips!!!"
    
# ====== [ADM] Call Broadcast =========== 
def do_Broadcast_Logic():
    if DEBUG:
        print("[Logic] Admin: Do Broadcast")
        
    return get_All_User_Logic()

# <<<<<<<<<<< END GENERAL >>>>>>>>>>>>>>>
 
 


# <<<<<<<<<<<< START USER >>>>>>>>>>>>>>>

# ====== Save User ====================== 
def set_User_Logic(user_model: User):
    if DEBUG:
        print("[Logic] Admin: Set User")
        
    DB_Save_User(user_model)
    return

def get_User_Logic(user_id: str) -> User:
    if DEBUG:
        print("[Logic] Admin: Get User")
        
    return DB_Get_User(user_id)

def get_All_User_Logic():
    if DEBUG:
        print("[Logic] Admin: Get All User")
        
    return DB_Get_All_User()

def user_Statistic_Logic(users: list[dict]) -> str:
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    total = len(users)
    online = today = week = inactive = banned = new_user = 0

    for u in users:
        is_active = u["is_active"]
        last_active = u["last_active"]
        created_at = u.get("created_at")

        # sqlite kadang return string
        if isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active)

        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        delta = now - last_active

        # 1️⃣ banned (prioritas tertinggi)
        if not is_active:
            banned += 1
            continue

        # 2️⃣ online
        if delta <= timedelta(hours=1):
            online += 1
            continue

        # 3️⃣ aktif hari ini
        if delta <= timedelta(days=1):
            today += 1
            continue

        # 4️⃣ aktif 7 hari
        if delta <= timedelta(days=7):
            week += 1
            continue

        # 5️⃣ lebih dari 7 hari
        inactive += 1

        # 6️⃣ new user (tidak konflik kategori lain)
        if created_at and (now - created_at) <= timedelta(days=1):
            new_user += 1

    # ===== OUTPUT =====
    return (
        "📊 <b>User Statistics</b>\n\n"
        f"👥 Total User\n └─ <b>{total}</b>\n"
        f"🟢 Online\n └─ <b>{online}</b>\n"
        f"🕒 Active Today\n └─ <b>{today}</b>\n"
        f"📅 Active 7 Days\n └─ <b>{week}</b>\n"
        f"⚫ Inactive (>7d)\n └─ <b>{inactive}</b>\n\n"
        f"🆕 New User (24h)\n └─ <b>{new_user}</b>\n"
        f"⛔ Banned User\n └─ <b>{banned}</b>"
    )
# <<<<<<<<<<<<< END USER >>>>>>>>>>>>>>>>






# <<<<<<<<<< START VARIABLE >>>>>>>>>>>>>

# ====== Save Variable ================== 
def set_Variable_Logic(content: str, file_id: str) -> str:
    if DEBUG:
        print("[Logic] Admin: Set Variable")
        
    index = DB_Cek_Index_Variable() // 100
    
    max_attempts = 1000  
    code_len = 16 - (len(str(index)) > 2)
    for _ in range(max_attempts):
        access_code = f"N0cTRaA{index}{create_Access_Code(code_len)}P0"
        
        if not DB_Cek_Variable(access_code):  
            break
        
    link = f"https://t.me/gempalokal_bot?start={access_code}"
    DB_Save_Variable(content, access_code, file_id, get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S"))
    return link

# ====== [ADM] Get Content Variable ===== 
def get_Content_Logic(access_code: str) -> str:
    if DEBUG:
        print("[Logic] Get Content")
        
    return DB_Get_Content(access_code)

# <<<<<<<<<<< END VARIABLE >>>>>>>>>>>>>>



# <<<<<<<< START DAILY SCHEDULE >>>>>>>>>

# ====== Save Daily Schedule ============ 
def set_Daily_Schedule_Logic(content: str, file_id: str) -> str:
    if DEBUG:
        print("[Logic] Admin: Set Daily Schedule")
    max_attempts = 1000  

    for _ in range(max_attempts):
        access_code = create_Access_Code(6)
        
        if not DB_Cek_Daily_Schedule(access_code):  
            break
        
    return DB_Save_Daily_Schedule(access_code, content, file_id, get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S"))
    
# ====== [Auto] Get Daily Schedule ====== 
def get_Daily_Schedule_Logic():
    if DEBUG:
        print("[Logic] Bot: Get Daily Schedule")

    return DB_Get_Daily_Schedule()    

# ====== [ADM] Get All Daily Schedule === 
def get_All_Daily_Schedule_Logic():
    if DEBUG:
        print("[Logic] Get All Daily Schedule")
    return DB_All_Get_Daily_Schedule()

# == [ADM] Show Content Daily Schedule == 
def show_Daily_Schedule_Logic(access_code):
    if DEBUG:
        print("[Logic] Show Content Daily Schedule")
    return DB_Show_Daily_Schedule(access_code)

# ====== [ADM] Delete Daily Schedule ==== 
def delete_Daily_Schedule_Logic(access_code):
    if DEBUG:
        print("[Logic] Delete Daily Schedule")
    return DB_Remove_Daily_Schedule(access_code)

# <<<<<<<< END DAILY SCHEDULE >>>>>>>>>>>



# <<<<<<<<<< START TEMPLATE >>>>>>>>>>>>>

# ====== [LOGIC] Assign Template ========    
def assign_Template_Logic(template:str,args: list[str]) -> str:
    var_count = template.count("<var>")   
    if var_count == 0:
        return "❓ <i>Template Tidak Ada (var)...</i>"
    
    if len(args) != var_count:
        return f"❓ <i>Jumlah Arg Tidak Sesuai ({var_count} Arg)...</i>"
    
    result = template
    for value in args:
        result = result.replace("<var>", value, 1)
    return result

# ====== [LOGIC] Save Template ========== 
def set_Template_Logic(content: str):
    if DEBUG:
        print("[Logic] Admin: Set Template")
    
    max_attempts = 1000  

    for _ in range(max_attempts):
        access_code = create_Access_Code(6)
        
        if not DB_Cek_Template(access_code):  
            break

    return DB_Save_Template(access_code,content,get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S"))
    
# ====== [LOGIC] Get Template =========== 
def get_Template_Logic(access_code):
    if DEBUG:
        print("[Logic] Bot: Get Template")

    return DB_Get_Template(access_code)    

# ====== [LOGIC] Get All Template ======= 
def get_All_Template_Logic():
    if DEBUG:
        print("[Logic] Get All Template")
    return DB_All_Get_Template()

# ====== [LOGIC] Delete Template ======== 
def delete_Template_Logic(access_code):
    if DEBUG:
        print("[Logic] Delete Template")
    return DB_Remove_Template(access_code)

# <<<<<<<<<<< END TEMPLATE >>>>>>>>>>>>>>



# <<<<<<<<<< START TEMPLATE >>>>>>>>>>>>>
# ====== [LOGIC] Create VIP Access Code ====
def create_VIP_Code_Logic() -> str:
    if DEBUG:
        print("[Logic] Admin: Create VIP Code")
    
    max_attempts = 1000
    
    for _ in range(max_attempts):
        random_text = create_Access_Code(11)  # 11 karakter random
        access_code = f"NV1Px{random_text}"  # Total 16 karakter dengan prefix
        
        if not DB_Check_VIP_Code(access_code):
            break
    
    now = get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S")
    DB_Save_VIP_Code(access_code, now)
    
    link = f"https://t.me/gempalokal_bot?start={access_code}"
    
    return {
        "access_code": access_code,
        "link": link
    }

# ====== [LOGIC] Activate VIP for User =====
def activate_VIP_Logic(access_code: str, user_id: str, now):
    if DEBUG:
        print(f"[Logic] Activate VIP for user: {user_id}")
    
    # Check if code exists and valid
    vip_code = DB_Check_VIP_Code(access_code)
    
    if not vip_code:
        return {
            "success": False,
            "message": "❌ <i><b>Kode VIP tidak valid atau sudah digunakan!</b></i>"
        }
    
    # Delete code (with race condition protection)
    result = DB_Delete_VIP_Code(access_code, user_id)
    
    if not result["success"]:
        return {
            "success": False,
            "message": f"❌ <b>{result['message']}</b>"
        }
    
    # Update user VIP status
    DB_Update_User_VIP(user_id, True, now)
    
    # Get user info for notification
    user_data = get_User_Logic(user_id)
    username = user_data.username
    
    if DEBUG:
        print(f"[Logic] VIP activated for: {username} ({user_id})")
    
    return {
        "success": True,
        "message": "✅ <b>Anda VIP!</b>",
        "user_id": user_id,
        "username": username
    }
  
# ====== [LOGIC] Get All VIP ===============        
def get_All_VIP_Contents_Logic():
    if DEBUG:
        print("[Logic] Get VIP Welcome Package")
    
    contents = DB_Get_All_VIP_Contents()
    
    if not contents:
        return []
    
    return contents

# ====== [LOGIC] Get Latest VIP  ===========      
def get_Latest_VIP_Contents_Logic():
    if DEBUG:
        print("[Logic] Get VIP Welcome Package")
    
    contents = DB_Get_Latest_VIP_Contents()
    
    if not contents:
        return []
    
    return contents

# ====== [LOGIC] Save VIP Variable =========
def set_VIP_Variable_Logic(content: str, file_id: str) -> str:
    if DEBUG:
        print("[Logic] Admin: Set VIP Variable")
    
    max_attempts = 1000
    
    for _ in range(max_attempts):
        random_text = create_Access_Code(11)  # 11 karakter random
        access_code = f"VV1Px{random_text}"  # Total 16 karakter dengan prefix
        
        if not DB_Check_VIP_Variable(access_code):
            break
    
    now = get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S")
    link = f"https://t.me/gempalokal_bot?start={access_code}"
    
    DB_Save_VIP_Variable(access_code, content, file_id, now)
    
    return link

# ====== [LOGIC] Get VIP Content ===========
def get_VIP_Content_Logic(access_code: str, user_id: str):
    if DEBUG:
        print("[Logic] Get VIP Content")
    
    # Check if user is VIP
    user_data = get_User_Logic(user_id)
    is_vip = user_data.is_vip
    
    if not is_vip:
        return {
            "success": False,
            "is_vip_content": True,
            "message": (
                "🔒 <b>Konten VIP</b>\n\n"
                "Konten ini hanya tersedia untuk member VIP.\n\n"
                "💎 <b>Keuntungan VIP:</b>\n"
                "• Akses ke semua konten eksklusif\n"
                "• Update konten premium setiap hari\n"
                "• Prioritas support\n\n"
                "💰 <b>Harga VIP:</b> Rp 50.000/bulan\n\n"
                "Hubungi admin untuk upgrade ke VIP!"
            )
        }
    
    # User is VIP, get content
    content_data = DB_Get_VIP_Content(access_code)
    
    if not content_data:
        return {
            "success": False,
            "is_vip_content": False,
            "message": "❌ <i><b>Not Found...</b></i>"
        }
    
    return {
        "success": True,
        "content": content_data.get("content"),
        "file_id": content_data.get("file_id")
    }

# <<<<<<<<<<< END TEMPLATE >>>>>>>>>>>>>>
 