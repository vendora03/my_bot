import random, string, pytz, json, os, logging
from datetime import datetime, timedelta
from io import BytesIO
from services.settings import Settings
from services import database
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
    DEFAULT_SETTINGS,
    BASE_DIR)

async def Logic_Cek_Request(context):
    MESSAGE_FILE = os.path.join(BASE_DIR, "request_message.json")
    if not os.path.exists(MESSAGE_FILE):
        return

    try:
        with open(MESSAGE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        message = data.get("message")
        file_id = data.get("file_id")

        if not message:
            return

        if not file_id or file_id == "None" or file_id == "null":
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=data["message"],
                    parse_mode="HTML"
                )
            data = {"message": "", "file_id": None}
            with open(MESSAGE_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            return
        
        file = await context.bot.get_file(file_id)
    
        file_path = file.file_path.lower()
    
        if file_path.endswith((".jpg", ".jpeg", ".png", ".webp")):
            for admin_id in ADMIN_IDS:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=data["message"],
                    parse_mode="HTML"
                )
    
        elif file_path.endswith((".zip", ".rar", ".7z", ".txt", ".pdf")):
            for admin_id in ADMIN_IDS:
                await context.bot.send_document(
                    chat_id=admin_id,
                    document=file_id,
                    caption=data["message"],
                    parse_mode="HTML"
                )
    
        else:
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=data["message"],
                    parse_mode="HTML"
                )

        data = {"message": "", "file_id": None}
        with open(MESSAGE_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"[MESSAGE REQUEST] {e}")
        
def Logic_init_settings():
    for key, value in DEFAULT_SETTINGS.items():
        Settings.set(key, value)
        
# <<<<<<<<<< ERROR Handler >>>>>>>>>>>>>>
async def Logic_error_handler(update, context):
    err = context.error

    if isinstance(err, TimedOut):
        logging.warning(f"TimeOut: {err}")
        return
    
    if isinstance(err, NetworkError):
        logging.warning(f"Network Issues: {err}")
        return
    
    if Settings.is_logging():
        logging.info(f"ERROR: {err}")

def Logic_Format_Help():
    lines = ["format penggunaan:"]
    for key, t in SETTINGS_SCHEMA.items():
        if key == "maintenance_start":
            continue
        if t == "bool":
            lines.append(f"/settings {key} true|false")
        else:
            lines.append(f"/settings {key} <teks>")
    return "\n".join(lines)

# <<<<<<<<<< START GENERAL >>>>>>>>>>>>>>
async def Logic_On_Startup(app):
    for id_chat in ADMIN_IDS:
        await app.bot.send_message(
            chat_id=id_chat,
            text=f"🚀 Bot Start Up\nTime: {Logic_Get_Time().strftime('%H:%M:%S %d-%m-%Y')}",
            parse_mode="HTML"
        )
    await Logic_Restore_From_Channel(app)
    await Logic_Set_Base_User_Commands(app)
  

async def Logic_Set_Base_User_Commands(app):
    commands = [
        BotCommand("start", "Mulai bot"),
        BotCommand("ping", "Uptime Bot"),
    ]
    await app.bot.set_my_commands(
        commands,
        scope=BotCommandScopeDefault()
    )
       
async def Logic_Set_Next_User_Commands(app, user: database.User):
    commands = User_Commands(user)

    await app.bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeChat(chat_id=user.user_id),
        language_code=None
    )
 
def User_Commands(user: database.User) -> list[BotCommand]:
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
        ("setvariable", "Set Variable"),
        ("broadcast", "Buat Broadcast"),
        
        ("settings", "Pengaturan Bot"),
        ("maintenance", "Maintenance Bot"),
        ("log", "Get Log Data"),
        ("backup", "Backup Database"),
        ("restore", "Restore Database"),
        
        ("createvipcode", "Buat Kode VIP Baru"),
        ("setvipvariable", "Simpan Konten VIP"),
        ("listvip", "List Semua VIP User"),
        
        ("schedule", "Buat Schedule"),
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
 
def Join_Button():
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

async def Is_User_Joined(app, user_id: int, chat_id: str) -> bool:
    try:
        member = await app.bot.get_chat_member(chat_id, user_id)
        return member.status in ("member", "administrator", "creator")
    except BadRequest:
        return False
    
async def Logic_Set_Join_Button(update, context, user_id) -> bool:
    if not Settings.start_info_enabled():
        return True

    raw_group = Settings.get_group()
    if not raw_group:
        return True

    groups = raw_group.split()          
    id_groups = groups[0::2]          

    for id_group in id_groups:
        if not await Is_User_Joined(context, user_id, int(id_group)):
            keyboard = Join_Button()
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
async def Logic_Send_Log(context):
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
        f"<b>📝 Log\nTime:</b> {Logic_Get_Time().strftime('%H:%M:%S %d-%m-%Y')}\n\n"
    )
    for admin_id in ADMIN_IDS:
        await context.bot.send_document(chat_id=admin_id,document=file,caption=text,parse_mode="HTML")
    
async def Logic_Send_Backup_To_Admin(context, file, info):
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
    
async def Logic_Send_Backup_To_Channel(context, file, info):
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
        
async def Logic_Restore_From_Channel(app):
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
        
        result = Logic_Restore_Backup()
                
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

async def Logic_Backup_To_Channel_Job(context):
    file, info = Logic_Setup_Backup()
    await Logic_Send_Backup_To_Channel(context, file, info)

def Send_Message_Admin(message, file_id):
    MESSAGE_FILE = os.path.join(BASE_DIR, "request_message.json")
    data = {"message": message, "file_id": file_id}
    with open(MESSAGE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# <<<<<<<<<< END ADMIN >>>>>>>>>>>>>>


# ====== [LOGIC] Set Backup  ============ 
def Logic_Setup_Backup():
    data = database.DB_Backup()

    json_bytes = json.dumps(
        data,
        indent=4,
        ensure_ascii=False
    ).encode("utf-8")

    file = BytesIO(json_bytes)
    file.name = "backup.json"
    
    info = (
        f"<b>📦 Backup:</b> {Logic_Get_Time().strftime('%H:%M:%S %d-%m-%Y')}\n\n"
        f"Users: <b>{len(data.get('users', []))}</b> row\n"
        f"Schedule: <b>{len(data.get('daily_schedule', []))}</b> row\n"
        f"Template: <b>{len(data.get('template', []))}</b> row\n"
        f"Variables: <b>{len(data.get('variables', []))}</b> row\n"
        f"VIP Codes: <b>{len(data.get('vip_codes', []))}</b> row\n"
        f"Bot Settings: <b>{len(data.get('bot_settings', []))}</b> row\n"
        f"VIP Variables: <b>{len(data.get('vip_variables', []))}</b> row\n"
    )
    
    return file,info

# ====== [LOGIC] Restore Backup ========= 
def Logic_Restore_Backup():
    if not os.path.exists(BACKUP_PATH):
        # if DEBUG:
        #     print("[BACKUP] Backup Aborted: Path Not Found")
        return ""

    try:
        with open(BACKUP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # restore users
        for u in data.get("users", []):
            database.DB_Save_User(database.User(
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
            database.DB_Save_Variable(
                content=v["content"],
                access_code=v["access_code"],
                file_id=v["file_id"],
                now=v["created_at"]
            )
            
            
        # restore vip_codes
        for vc in data.get("vip_codes", []):
            database.DB_Save_VIP_Code(
                access_code=vc["access_code"],
                now=vc["created_at"]
            )
            
            
        # restore vip_variables
        for vv in data.get("vip_variables", []):
            database.DB_Save_VIP_Variable(
                content=vv["content"],
                access_code=vv["access_code"],
                file_id=vv.get("file_id"),
                now=vv["created_at"]
            )
            
            
        # restore daily schedule            
        for d in data.get("daily_schedule", []):
            database.DB_Save_Daily_Schedule(
                access_code=d["access_code"],
                content=d["content"],
                file_id=d["file_id"],
                now=d["created_at"]
            )
            
        # restore template          
        for d in data.get("template", []):
            database.DB_Save_Template(
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
def Logic_Get_Time():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    return now

# ====== [Create Access Code ============= 
def Create_Access_Code(panjang: int) -> str:
    karakter = string.ascii_uppercase + string.ascii_lowercase + string.digits
    random_text = ''.join(random.choice(karakter) for _ in range(panjang))
    return random_text  
    
# ====== [LOGIC] Generate AI Tips ======= 
def Logic_Generate_Tips() -> str:
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
    
# ====== [LOGIC] Call Broadcast ========= 
def Logic_Broadcast():
    # if DEBUG:
    #     print("[Logic] Admin: Do Broadcast")
        
    return Logic_Get_All_User()

# <<<<<<<<<<< END GENERAL >>>>>>>>>>>>>>>
 
 


# <<<<<<<<<<<< START USER >>>>>>>>>>>>>>>

# ====== Save User ====================== 
def Logic_Set_User(user_model: database.User):
    # if DEBUG:
    #     print("[Logic] Admin: Set User")
        
    database.DB_Save_User(user_model)
    return

def Logic_Get_User(user_id: str) -> database.User:
    # if DEBUG:
    #     print("[Logic] Admin: Get User")
        
    return database.DB_Get_User(user_id)

def Logic_Get_All_User():
    # if DEBUG:
    #     print("[Logic] Admin: Get All User")
        
    return database.DB_Get_All_User()

def Logic_User_Statistic(users: list[dict]) -> str:
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

        # 6️⃣ new user (tidak konflik kategori lain)
        if created_at and (now - created_at) <= timedelta(days=1):
            new_user += 1
            
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

# ====== [LOGIC] Save Variable ========== 
def Logic_Set_Variable(content: str, file_id: str) -> str:
    # if DEBUG:
    #     print("[Logic] Admin: Set Variable")
        
    index = database.DB_Cek_Index_Variable() // 100
    
    max_attempts = 1000  
    code_len = 16 - (len(str(index)) > 2)
    for _ in range(max_attempts):
        access_code = f"N0cTRaA{index}{Create_Access_Code(code_len)}P0"
        
        if not database.DB_Cek_Variable(access_code):  
            break
        
    link = f"https://t.me/gempalokal_bot?start={access_code}"
    database.DB_Save_Variable(content, access_code, file_id, Logic_Get_Time().strftime("%Y-%m-%d %H:%M:%S"))
    return link

# ====== [LOGIC] Get Variable ===========
def Logic_Get_Variable(access_code: str) -> str:
    # if DEBUG:
    #     print("[Logic] Get Content")
        
    return database.DB_Get_Variable(access_code)

# <<<<<<<<<<< END VARIABLE >>>>>>>>>>>>>>



# <<<<<<<< START DAILY SCHEDULE >>>>>>>>>

# ====== [LOGIC] Save Daily Schedule ====
def Logic_Set_Daily_Schedule(content: str, file_id: str) -> str:
    # if DEBUG:
    #     print("[Logic] Admin: Set Daily Schedule")
    max_attempts = 1000  

    for _ in range(max_attempts):
        access_code = Create_Access_Code(6)
        
        if not database.DB_Cek_Daily_Schedule(access_code):  
            break
        
    return database.DB_Save_Daily_Schedule(access_code, content, file_id, Logic_Get_Time().strftime("%Y-%m-%d %H:%M:%S"))
    
# ====== [LOGIC] Get Daily Schedule ===== 
def Logic_Get_Daily_Schedule():
    # if DEBUG:
    #     print("[Logic] Bot: Get Daily Schedule")

    return database.DB_Get_Daily_Schedule()    

# ====== [LOGIC] Get All Daily Schedule = 
def Logic_Get_All_Daily_Schedule():
    # if DEBUG:
    #     print("[Logic] Get All Daily Schedule")
    return database.DB_Get_All_Daily_Schedule()

# ====== [LOGIC] Show Daily Schedule ==== 
def Logic_Show_Daily_Schedule(access_code):
    # if DEBUG:
    #     print("[Logic] Show Content Daily Schedule")
    return database.DB_Show_Daily_Schedule(access_code)

# ====== [LOGIC] Delete Daily Schedule == 
def Logic_Delete_Daily_Schedule(access_code):
    # if DEBUG:
    #     print("[Logic] Delete Daily Schedule")
    return database.DB_Remove_Daily_Schedule(access_code)

# <<<<<<<< END DAILY SCHEDULE >>>>>>>>>>>



# <<<<<<<<<< START TEMPLATE >>>>>>>>>>>>>

# ====== [LOGIC] Assign Template ========    
def Logic_Assign_Template(template:str,args: list[str]) -> str:
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
def Logic_Set_Template(content: str):
    # if DEBUG:
    #     print("[Logic] Admin: Set Template")
    
    max_attempts = 1000  

    for _ in range(max_attempts):
        access_code = Create_Access_Code(6)
        
        if not database.DB_Cek_Template(access_code):  
            break

    return database.DB_Save_Template(access_code,content,Logic_Get_Time().strftime("%Y-%m-%d %H:%M:%S"))
    
# ====== [LOGIC] Get Template =========== 
def Logic_Get_Template(access_code):
    # if DEBUG:
    #     print("[Logic] Bot: Get Template")

    return database.DB_Get_Template(access_code)    

# ====== [LOGIC] Get All Template ======= 
def Logic_Get_All_Template():
    # if DEBUG:
    #     print("[Logic] Get All Template")
    return database.DB_Get_All_Template()

# ====== [LOGIC] Delete Template ======== 
def Logic_Delete_Template(access_code):
    # if DEBUG:
    #     print("[Logic] Delete Template")
    return database.DB_Remove_Template(access_code)

# <<<<<<<<<<< END TEMPLATE >>>>>>>>>>>>>>



# <<<<<<<<<< START VIP CODE >>>>>>>>>>>>>
# ====== [LOGIC] Create VIP Access Code ====
def Logic_Create_VIP_Code() -> str:
    # if DEBUG:
    #     print("[Logic] Admin: Create VIP Code")
    
    max_attempts = 1000
    
    for _ in range(max_attempts):
        random_text = Create_Access_Code(11)  
        access_code = f"NV1Px{random_text}"  
        
        if not database.DB_Check_VIP_Code(access_code):
            break
    
    now = Logic_Get_Time().strftime("%Y-%m-%d %H:%M:%S")
    database.DB_Save_VIP_Code(access_code, now)
    
    link = f"https://t.me/gempalokal_bot?start={access_code}"
    
    return {
        "access_code": access_code,
        "link": link
    }

# ====== [LOGIC] Activate VIP for User =====
def Logic_Activate_VIP(access_code: str, user_id: str, now):
    if Settings.is_logging():
        logging.info(f"[Logic] Activate VIP for user: {user_id}")
    
    vip_code = database.DB_Check_VIP_Code(access_code)
    
    if not vip_code:
        return {
            "success": False,
            "message": "❌ <i><b>Kode VIP tidak valid atau sudah digunakan!</b></i>"
        }
    
    # Delete code (with race condition protection)
    result = database.DB_Delete_VIP_Code(access_code, user_id)
    
    if not result["success"]:
        return {
            "success": False,
            "message": f"❌ <b>{result['message']}</b>"
        }
    
    # Update user VIP status
    database.DB_Update_User_VIP(user_id, True, now)
    
    # Get user info for notification
    user_data = Logic_Get_User(user_id)
    
    if Settings.is_logging():
        logging.info(f"[Logic] VIP activated for: {user_data.first_name}(@{user_data.username}) ({user_id})")
    
    return {
        "success": True,
        "message": f"🎉 <b>Selamat {user_data.first_name} Kamu VIP!\nKamu mendapatkan command baru</b>",
    }
  
# ====== [LOGIC] Save VIP Variable =========
def Logic_Set_VIP_Variable(content: str, file_id: str) -> str:
    # if DEBUG:
    #     print("[Logic] Admin: Set VIP Variable")
    
    max_attempts = 1000
    
    for _ in range(max_attempts):
        random_text = Create_Access_Code(11)  
        access_code = f"VV1Px{random_text}"  
        
        if not database.DB_Check_VIP_Variable(access_code):
            break
    
    now = Logic_Get_Time().strftime("%Y-%m-%d %H:%M:%S")
    link = f"https://t.me/gempalokal_bot?start={access_code}"
    
    database.DB_Save_VIP_Variable(access_code, content, file_id, now)
    
    return link

# ====== [LOGIC] Get VIP Content ===========
def Logic_Get_VIP_Variable(access_code: str):
    # if DEBUG:
    #     print("[Logic] Get VIP Content")
    
    content_data = database.DB_Get_VIP_Variable(access_code)
    
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

# ====== [LOGIC] Get All VIP ===============        
def Logic_Get_All_VIP_Variable():
    # if DEBUG:
    #     print("[Logic] Get VIP Welcome Package")
    
    contents = database.DB_Get_All_VIP_Variable()

    if not contents:
        return []
    
    return contents

# ====== [LOGIC] Get Latest VIP  ===========      
def Logic_Get_Latest_VIP_Variable():
    # if DEBUG:
    #     print("[Logic] Get VIP Welcome Package")
    
    contents = database.DB_Get_Latest_VIP_Variable()
    
    if not contents:
        return []
    
    return contents

# <<<<<<<<<<< END VIP CODE >>>>>>>>>>>>>>
 
