import random, string, pytz, json, os, logging
from datetime import datetime, timedelta
from io import BytesIO
from services.settings import Settings
from telegram.error import NetworkError, TimedOut, BadRequest
from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    # DEBUG,
    ADMIN_IDS, 
    CHANNEL_ID,
    API_GEMINI, 
    BACKUP_PATH, 
    TIMEZONE, 
    PROMPT, 
    SETTINGS_SCHEMA,
    DEFAULT_SETTINGS)
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


def init_settings():
    for key, value in DEFAULT_SETTINGS.items():
        Settings.set(key, value)
        
# <<<<<<<<<< ERROR Handler >>>>>>>>>>>>>>
async def error_handler(update, context):
    err = context.error

    if isinstance(err, TimedOut):
        logging.warning(f"TimeOut: {err}")
        return
    
    if isinstance(err, NetworkError):
        logging.warning(f"Network Issues: {err}")
        return
    
    if Settings.is_logging():
        logging.info(f"ERROR: {err}")

def format_Help_Logic():
    lines = ["format penggunaan:"]
    for key, t in SETTINGS_SCHEMA.items():
        if t == "bool":
            lines.append(f"/settings {key} true|false")
        else:
            lines.append(f"/settings {key} <teks>")
    return "\n".join(lines)

# <<<<<<<<<< START GENERAL >>>>>>>>>>>>>>
async def on_Startup(app):
    for id_chat in ADMIN_IDS:
        await app.bot.send_message(
            chat_id=id_chat,
            text=f"🚀 Bot Start Up\nTime: {get_Time_Logic().strftime('%H:%M:%S %d-%m-%Y')}",
            parse_mode="HTML"
        )
    await restore_From_Channel_Pin_Logic(app)
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
        ("tutorial", "Cek Sendiri Dah"),
    ]

    VIP_COMMANDS = [
        ("getall", "Semua Konten VIP"),
        ("getnew", "Konten VIP Terbaru"),
    ]

    ADMIN_COMMANDS = [
        ("userstat", "Cek User Statistic"),
        ("settings", "Pengaturan Bot"),
        ("log", "Get Log Data"),
        ("backup", "Backup Database"),
        ("restore", "Restore Database"),
        ("broadcast", "Buat Broadcast"),
        ("schedule", "Buat Schedule"),
        ("setvariable", "Set Variable"),
        
        ("createvipcode", "Buat Kode VIP Baru"),
        ("setvipvariable", "Simpan Konten VIP"),
        ("listvip", "List Semua VIP User"),
        
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
 
def build_Join_Button_Logic():
    buttons = []
    
    raw_group = Settings.get_group()  
    if not raw_group:
        return None
    
    rows = raw_group.split() 
        
    for chat_id in rows[1::2]:
        if chat_id.startswith("https"):
            buttons.append([
                InlineKeyboardButton(
                    f"Join",
                    url=chat_id
                )
            ])

    if not buttons:
        return None
    
    return InlineKeyboardMarkup(buttons)

async def is_user_joined(app, user_id: int, chat_id: str) -> bool:
    try:
        member = await app.bot.get_chat_member(chat_id, user_id)
        return member.status in ("member", "administrator", "creator")
    except BadRequest:
        return False
    
async def cek_Subscribe_Logic(update, context, user_id) -> bool:
    if not Settings.start_info_enabled():
        return True

    raw_group = Settings.get_group()
    if not raw_group:
        return True

    groups = raw_group.split()          
    id_groups = groups[0::2]          

    for id_group in id_groups:
        if not await is_user_joined(context, user_id, int(id_group)):
            keyboard = build_Join_Button_Logic()
            start_info = Settings.get_start_info()
            if "@user" in start_info:
                await update.message.reply_text(
                    start_info.replace("@user", update.effective_user.first_name),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    start_info,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
            return False   

    return True
  
      
# <<<<<<<<<< START ADMIN >>>>>>>>>>>>>>
async def send_Log_Logic(context):
    file = "app.log"
    
    if not os.path.exists(file):
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text= "❌ <i>Gagal mendapat file</i>",
                parse_mode="HTML")
        if Settings.is_logging():
            logging.warning("Log file not found")
        return

    text = (
        f"<b>📝 Log\nTime:</b> {get_Time_Logic().strftime('%H:%M:%S %d-%m-%Y')}\n\n"
    )
    for admin_id in ADMIN_IDS:
        await context.bot.send_document(chat_id=admin_id,document=file,caption=text,parse_mode="HTML")
    
async def send_Backup_To_Admin_Logic(context, file, info):
    file.seek(0)
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_document(
                chat_id=admin_id,
                document=file,
                caption=info,
                parse_mode="HTML"
            )
            # if DEBUG:
            #     logging.info(f"[BACKUP] Sent to admin {admin_id}")
        except Exception as e:
            if Settings.is_logging():
                logging.error(f"[BACKUP] Failed to send to admin {admin_id}: {e}")
        
        file.seek(0)
    
async def send_Backup_To_Channel_Logic(context, file, info):
    if not CHANNEL_ID:
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"❌ <i>Channel Database Not Found...</i>",
                parse_mode="HTML"
            )
        if Settings.is_logging():
            logging.warning("[BACKUP] CHANNEL_ID not set up")

    file.seek(0)
    
    try:
        msg = await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=file,
            caption=info,
            parse_mode="HTML"
        )
        
        await context.bot.pin_chat_message(
            chat_id=CHANNEL_ID,
            message_id=msg.message_id,
            disable_notification=True  
        )
        # if DEBUG:
        #     logging.info(f"[BACKUP] Sent to channel and pinned")
        
    except Exception as e:
        if Settings.is_logging():
            logging.error(f"[BACKUP] Failed to send to channel: {e}")
        
async def restore_From_Channel_Pin_Logic(app):
    if not CHANNEL_ID:
        for admin_id in ADMIN_IDS:
            await app.bot.send_message(
                chat_id=admin_id,
                text=f"❌ <i>Channel Database Not Found...</i>",
                parse_mode="HTML"
            )
        if Settings.is_logging():
            logging.warning("[RESTORE] CHANNEL_ID not set up")
    
    try:
        chat = await app.bot.get_chat(CHANNEL_ID)
        
        if not chat.pinned_message:
            if Settings.is_logging():
                logging.warning("[RESTORE] No pinned message in channel")
            return
        
        pinned_msg = chat.pinned_message
        
        if not pinned_msg.document:
            if Settings.is_logging():
                logging.warning("[RESTORE] Pinned message has no document")
            return
        
        file_id = pinned_msg.document.file_id
        new_file = await app.bot.get_file(file_id)
        
        await new_file.download_to_drive(BACKUP_PATH)
        
        result = restore_Backup_Logic()
                
        if result:
            for admin_id in ADMIN_IDS:
                await app.bot.send_message(
                    chat_id=admin_id,
                    text=result,
                    parse_mode="HTML"
                )
    except Exception as e:
        if Settings.is_logging():
            logging.error(f"[RESTORE] Failed To Restore Backup From Channel: {e}")

async def backup_to_channel_job(context):
    file, info = setup_Backup_Logic()
    await send_Backup_To_Channel_Logic(context, file, info)
    
# <<<<<<<<<< END ADMIN >>>>>>>>>>>>>>


# ====== Backup To Json Logic =========== 
def setup_Backup_Logic():
    data = DB_Backup()

    json_bytes = json.dumps(
        data,
        indent=4,
        ensure_ascii=False
    ).encode("utf-8")

    file = BytesIO(json_bytes)
    file.name = "backup.json"
    
    info = (
        f"<b>📦 Backup:</b> {get_Time_Logic().strftime('%H:%M:%S %d-%m-%Y')}\n\n"
        f"Users: <b>{len(data.get('users', []))}</b> row\n"
        f"Schedule: <b>{len(data.get('daily_schedule', []))}</b> row\n"
        f"Template: <b>{len(data.get('template', []))}</b> row\n"
        f"Variables: <b>{len(data.get('variables', []))}</b> row\n"
        f"VIP Codes: <b>{len(data.get('vip_codes', []))}</b> row\n"
        f"Bot Settings: <b>{len(data.get('bot_settings', []))}</b> row\n"
        f"VIP Variables: <b>{len(data.get('vip_variables', []))}</b> row\n"
    )
    
    return file,info

# ====== Restore Backup Logic =========== 
def restore_Backup_Logic():
    if not os.path.exists(BACKUP_PATH):
        # if DEBUG:
        #     print("[BACKUP] Backup Aborted: Path Not Found")
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
                is_vip=u["is_vip"],
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
            
        # restore bot_settings          
        for d in data.get("bot_settings", []):
            Settings.set(
                key=d["key"],
                value=d["value"]
            )

        if Settings.is_logging():
            logging.info("[BACKUP] Restore Completed")

        os.remove(BACKUP_PATH)

        # if DEBUG:
        #     print("[BACKUP] backup.json Deleted")

        return (
            "✅ <i>Backup Restored:</i>\n\n"
            f"Users: <b>{len(data.get('users', []))}</b> row\n"
            f"Schedule: <b>{len(data.get('daily_schedule', []))}</b> row\n"
            f"Template: <b>{len(data.get('template', []))}</b> row\n"
            f"Variables: <b>{len(data.get('variables', []))}</b> row\n"
            f"VIP Codes: <b>{len(data.get('vip_codes', []))}</b> row\n"
            f"Bot Settings: <b>{len(data.get('bot_settings', []))}</b> row\n"
            f"VIP Variables: <b>{len(data.get('vip_variables', []))}</b> row\n"
        )    
        
    except Exception as e:
        if Settings.is_logging():
            logging.error("[BACKUP ERROR] Restore Failed:", e)
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
    if Settings.is_logging():
        logging.info("[Logic] Generate Tips")
        
    if not API_GEMINI:
        return "Tidak Ada Tips!!!"
        
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
            tips = "Tidak Ada Tips"
            if Settings.is_logging():
                logging.info(f"[Logic] To Long Generate GEMINI: {response.text}")
        
        if Settings.is_logging():
            logging.info(f"[Logic] Generate Success: {tips}")
            
        return tips
    except ClientError as e:
        if Settings.is_logging():
            logging.error(f"[Logic] Generate Failed!!!: {e}")
        return "Tidak Ada Tips!!"
    
# ====== [ADM] Call Broadcast =========== 
def do_Broadcast_Logic():
    # if DEBUG:
    #     print("[Logic] Admin: Do Broadcast")
        
    return get_All_User_Logic()

# <<<<<<<<<<< END GENERAL >>>>>>>>>>>>>>>
 
 


# <<<<<<<<<<<< START USER >>>>>>>>>>>>>>>

# ====== Save User ====================== 
def set_User_Logic(user_model: User):
    # if DEBUG:
    #     print("[Logic] Admin: Set User")
        
    DB_Save_User(user_model)
    return

def get_User_Logic(user_id: str) -> User:
    # if DEBUG:
    #     print("[Logic] Admin: Get User")
        
    return DB_Get_User(user_id)

def get_All_User_Logic():
    # if DEBUG:
    #     print("[Logic] Admin: Get All User")
        
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

        if isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active)

        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        delta = now - last_active

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
    # if DEBUG:
    #     print("[Logic] Admin: Set Variable")
        
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
    # if DEBUG:
    #     print("[Logic] Get Content")
        
    return DB_Get_Content(access_code)

# <<<<<<<<<<< END VARIABLE >>>>>>>>>>>>>>



# <<<<<<<< START DAILY SCHEDULE >>>>>>>>>

# ====== Save Daily Schedule ============ 
def set_Daily_Schedule_Logic(content: str, file_id: str) -> str:
    # if DEBUG:
    #     print("[Logic] Admin: Set Daily Schedule")
    max_attempts = 1000  

    for _ in range(max_attempts):
        access_code = create_Access_Code(6)
        
        if not DB_Cek_Daily_Schedule(access_code):  
            break
        
    return DB_Save_Daily_Schedule(access_code, content, file_id, get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S"))
    
# ====== [Auto] Get Daily Schedule ====== 
def get_Daily_Schedule_Logic():
    # if DEBUG:
    #     print("[Logic] Bot: Get Daily Schedule")

    return DB_Get_Daily_Schedule()    

# ====== [ADM] Get All Daily Schedule === 
def get_All_Daily_Schedule_Logic():
    # if DEBUG:
    #     print("[Logic] Get All Daily Schedule")
    return DB_All_Get_Daily_Schedule()

# == [ADM] Show Content Daily Schedule == 
def show_Daily_Schedule_Logic(access_code):
    # if DEBUG:
    #     print("[Logic] Show Content Daily Schedule")
    return DB_Show_Daily_Schedule(access_code)

# ====== [ADM] Delete Daily Schedule ==== 
def delete_Daily_Schedule_Logic(access_code):
    # if DEBUG:
    #     print("[Logic] Delete Daily Schedule")
    return DB_Remove_Daily_Schedule(access_code)

# <<<<<<<< END DAILY SCHEDULE >>>>>>>>>>>



# <<<<<<<<<< START TEMPLATE >>>>>>>>>>>>>

# ====== [LOGIC] Assign Template ========    
def assign_Template_Logic(template:str,args: list[str]) -> str:
    # if DEBUG:
    #     print("[Logic] Assign Template")
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
    # if DEBUG:
    #     print("[Logic] Admin: Set Template")
    
    max_attempts = 1000  

    for _ in range(max_attempts):
        access_code = create_Access_Code(6)
        
        if not DB_Cek_Template(access_code):  
            break

    return DB_Save_Template(access_code,content,get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S"))
    
# ====== [LOGIC] Get Template =========== 
def get_Template_Logic(access_code):
    # if DEBUG:
    #     print("[Logic] Bot: Get Template")

    return DB_Get_Template(access_code)    

# ====== [LOGIC] Get All Template ======= 
def get_All_Template_Logic():
    # if DEBUG:
    #     print("[Logic] Get All Template")
    return DB_All_Get_Template()

# ====== [LOGIC] Delete Template ======== 
def delete_Template_Logic(access_code):
    # if DEBUG:
    #     print("[Logic] Delete Template")
    return DB_Remove_Template(access_code)

# <<<<<<<<<<< END TEMPLATE >>>>>>>>>>>>>>



# <<<<<<<<<< START TEMPLATE >>>>>>>>>>>>>
# ====== [LOGIC] Create VIP Access Code ====
def create_VIP_Code_Logic() -> str:
    # if DEBUG:
    #     print("[Logic] Admin: Create VIP Code")
    
    max_attempts = 1000
    
    for _ in range(max_attempts):
        random_text = create_Access_Code(11)  
        access_code = f"NV1Px{random_text}"  
        
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
    if Settings.is_logging():
        logging.info(f"[Logic] Activate VIP for user: {user_id}")
    
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
    
    if Settings.is_logging():
        logging.info(f"[Logic] VIP activated for: {user_data.first_name}(@{user_data.username}) ({user_id})")
    
    return {
        "success": True,
        "message": f"🎉 <b>Selamat {user_data.first_name} Kamu VIP!\nKamu mendapatkan command baru</b>",
    }
  
# ====== [LOGIC] Get All VIP ===============        
def get_All_VIP_Contents_Logic():
    # if DEBUG:
    #     print("[Logic] Get VIP Welcome Package")
    
    contents = DB_Get_All_VIP_Contents()

    if not contents:
        return []
    
    return contents

# ====== [LOGIC] Get Latest VIP  ===========      
def get_Latest_VIP_Contents_Logic():
    # if DEBUG:
    #     print("[Logic] Get VIP Welcome Package")
    
    contents = DB_Get_Latest_VIP_Contents()
    
    if not contents:
        return []
    
    return contents

# ====== [LOGIC] Save VIP Variable =========
def set_VIP_Variable_Logic(content: str, file_id: str) -> str:
    # if DEBUG:
    #     print("[Logic] Admin: Set VIP Variable")
    
    max_attempts = 1000
    
    for _ in range(max_attempts):
        random_text = create_Access_Code(11)  
        access_code = f"VV1Px{random_text}"  
        
        if not DB_Check_VIP_Variable(access_code):
            break
    
    now = get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S")
    link = f"https://t.me/gempalokal_bot?start={access_code}"
    
    DB_Save_VIP_Variable(access_code, content, file_id, now)
    
    return link

# ====== [LOGIC] Get VIP Content ===========
def get_VIP_Content_Logic(access_code: str):
    # if DEBUG:
    #     print("[Logic] Get VIP Content")
    
    content_data = DB_Get_VIP_Content(access_code)
    
    if not content_data:
        return {
            "success": False,
            "message": "❌ <i><b>Not Found...</b></i>"
        }
    
    return {
        "success": True,
        "content": content_data.get("content"),
        "file_id": content_data.get("file_id")
    }

# <<<<<<<<<<< END TEMPLATE >>>>>>>>>>>>>>
 
