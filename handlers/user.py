from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop
from telegram.error import TimedOut, BadRequest
from services.update_user import update_User_Activity_Logic
# from services.proccess_manager import ProccessManager
from services.logic import (
    Logic_Setup_Backup,
    Logic_Send_Log,
    Logic_Send_Backup_To_Admin,
    Logic_Send_Backup_To_Channel,
    Logic_Start_Info,
    Logic_Set_Next_User_Commands,
    Logic_Get_Time,
    Logic_Get_Variable,
    Logic_Get_User,
    Logic_Get_VIP_Variable,
    Logic_Activate_VIP,
    Logic_Get_All_VIP_Variable,
    Logic_Get_Latest_VIP_Variable)
from config import (
    # DEBUG,
    ADMIN_IDS, 
    START_TIME, 
    TIMEZONE)
from services.settings import Settings
import datetime, pytz, time, logging, asyncio
# from functools import wraps

# def proccess_handling(func):
#     @wraps(func)
#     # async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     #     user_id = update.effective_user.id
        
#     #     if ProccessManager.is_processing(user_id):
#     #         return  
        
#     #     ProccessManager.start_processing(user_id)
        
#     #     try:
#     #         await func(update, context)
#     #     finally:
#     #         ProccessManager.finish_processing(user_id)
    
#     # return wrapper  

async def maintenance_Handler(update, context):
    if not Settings.get("maintenance") == "true":
        return

    if update.effective_user and update.effective_user.id in ADMIN_IDS:
        return

    if update.effective_message:
        await update.effective_message.reply_text(
            "🔧 Bot sedang dalam maintenance.\n"
            "⏱ Time: 00:03:12"
        )

    raise ApplicationHandlerStop

async def start_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # if DEBUG:
        #     print("[Handlers] User: Start")
        await update.message.reply_text("❌ Tidak Ada Gempa Terbaru.")
    except TimedOut:
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

# @proccess_handling
async def user_Start_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_data = update_User_Activity_Logic(update.effective_user)
    await Logic_Set_Next_User_Commands(context, user_data)
    
    if not user_data.is_active:
        return
    
    text = update.message.text
    access_code = text.replace("/start","").strip()
    
    if not access_code:
        await start_Handler(update, context)
        return
    else:
        # if DEBUG:
        #     print(f"[Handlers] Kode: {access_code}")
        await Content_Handler(access_code, update, context)
        return
           
async def Content_Handler(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE ):
    # if DEBUG:
    #     print("[Handlers] User: Get Content")
    
    if access_code.startswith("NV1Px"):   
        await activate_VIP_Handler(access_code, update, context)
        return
    elif access_code.startswith("VV1Px"):
        await get_VIP_Content_Handler(access_code, update, context)
        return
    elif access_code.startswith("N0cTRaA"):
        await get_Reguler_Content_Handler(access_code, update, context)
        return
    else:
        await update.message.reply_text("❌ Tidak Ada Gempa Terbaru.")
           
# ====== Handle Reguler Content Access =====
async def get_Reguler_Content_Handler(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if DEBUG:
        #     print(f"[Handlers] Reguler Content Access: {access_code}")
        is_join = await Logic_Start_Info(update, context, user_data.user_id)
        if not is_join:
            return
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
        respon = Logic_Get_Variable(access_code)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if respon:
            file_id = respon.get("file_id")
            content = respon.get("content")
            if file_id:
                await update.message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
            else:
                await update.message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await update.message.reply_text(f"❌ <i><b>Not Found...</b></i>",parse_mode="HTML")
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Handle VIP Activation =============
async def activate_VIP_Handler(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        
        is_join = await Logic_Start_Info(update, context, user_data.user_id)
        if not is_join:
            return
        
        if Settings.is_logging():
            logging.info(f"[Handlers] VIP Activation: {access_code}")
        
        msg = await update.message.reply_text("<i>Checking...</i>", parse_mode="HTML")
        user_data = Logic_Get_User(user_data.user_id)
        if user_data.is_vip:
            dt = datetime.datetime.strptime(user_data.vip_created, "%Y-%m-%d %H:%M:%S")
            new_date = dt.strftime("%H:%M:%S %d-%m-%Y")
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(f"ℹ️ <i>Akun Sudah VIP\nTime: {new_date}\nPendaftaran Dibatalkan.</i>", parse_mode="HTML")
            return
        
        vip_created = Logic_Get_Time().strftime("%Y-%m-%d %H:%M:%S")
        result = Logic_Activate_VIP(access_code, user_data.user_id, vip_created)
        
        if not result["success"]:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(result["message"], parse_mode="HTML")
            return
            
        # Notify admin
        admin_message = (
            f"🎉 <b>VIP Baru!</b>\n\n"
            f"👤 User: {user_data.first_name + user_data.last_name} (@{user_data.username})\n"
            f"🆔 ID: <code>{user_data.user_id}</code>\n"
            f"📅 Time: <code>{vip_created}</code>\n"
            f"🔑 Code: <code>{access_code}</code>"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode="HTML"
                )
            except Exception as e:
                if Settings.is_logging():
                    logging.warning(f"[Handler] Failed to notify admin {admin_id}: {e}")
        user_data = Logic_Get_User(user_data.user_id)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await send_VIP_All_Package_Handler(update, context)
        await update.message.reply_text("✅ <i><b>Anda Sekarang VIP!\nGunakan Menu Baru</b></i>", parse_mode="HTML")
        await Logic_Set_Next_User_Commands(context, user_data)
        file, info = Logic_Setup_Backup()
        await Logic_Send_Backup_To_Admin(context, file, info)
        await Logic_Send_Log(context)
        await Logic_Send_Backup_To_Channel(context, file, info)
        
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Handle VIP Content Access =========
async def get_VIP_Content_Handler(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print(f"[Handlers] VIP Content Access: {access_code}")
        user_data = update_User_Activity_Logic(update.effective_user)
        is_join = await Logic_Start_Info(update, context, user_data.user_id)
        if not is_join:
            return
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.message.reply_text(reply, parse_mode="HTML")
            return
        
        result = Logic_Get_VIP_Variable(access_code)
        
        if not result["success"]:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(result.get("message","❌ Tidak Dapat Akses VIP"), parse_mode="HTML")
            return
        
        # Send VIP content
        file_id = result.get("file_id")
        content = result.get("content")
        
        if file_id:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
        else:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass



# ====== Send VIP Welcome Package ==========
# @proccess_handling
async def send_VIP_All_Package_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if DEBUG:
        #     print(f"[Handlers] Sending All VIP Contents")
        
        await Logic_Start_Info(update, context, user_data.user_id)
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
                
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.message.reply_text(reply, parse_mode="HTML")
            return

        package = Logic_Get_All_VIP_Variable()

        if not package:
            await msg.delete()
            await update.message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>", parse_mode="HTML")
            return
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        for idx, item in enumerate(package, 1):
            # Send VIP content
            file_id = item.get("file_id")
            content = item.get("content")
            
            if file_id:
                await update.message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
            else:
                await update.message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
            await asyncio.sleep(1)
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
     
    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Get Latest VIP Content  ===========
# @proccess_handling
async def get_Latest_VIP_Content_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if DEBUG:
        #     print(f"[Handlers] Get Latest VIP Content")
        await Logic_Start_Info(update, context, user_data.user_id)
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.message.reply_text(reply, parse_mode="HTML")
            return
        
        result = Logic_Get_Latest_VIP_Variable()
        
        if not result:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>", parse_mode="HTML")
            return
        
        # Send VIP content
        file_id = result.get("file_id")
        content = result.get("content")
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if file_id:
            await update.message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
        else:
            await update.message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass



# ====== Handle PING =======================
# @proccess_handling
async def ping_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # await Logic_Start_Info(update, context, user_data.user_id)
        start = time.time()
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        end = time.time()
        ping_ms = int((end - start) * 1000)
        
        # if DEBUG:
        #     print("[Handlers] User: Ping")
        
        tz = pytz.timezone(TIMEZONE)
        now = datetime.datetime.now(tz)
        
        uptime = now - START_TIME
        total_seconds = int(uptime.total_seconds())
        
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            uptime_text = f"{days} day {hours} hour"
        elif hours > 0:
            uptime_text = f"{hours} hour {minutes} min"
        elif minutes > 0:
            uptime_text = f"{minutes} min"
        else:
            uptime_text = f"{seconds} sec"

        # format tanggal dan jam startup
        startup_text = START_TIME.strftime("%H:%M:%S %d-%m-%Y")
        if not Settings.get('tips'):
            Settings.set('tips', "Tidak Ada Tips.")
            
        massage_uptime = (
            f"🏓 Pong\n\n│🚀  StartUP\n├───  <b>{startup_text}</b>\n│🕑  UpTime\n├───  <b>{uptime_text}</b>\n│📡  Ping \n├───  <b>{ping_ms} ms</b>\n│💡  Tips\n└───  <b>{Settings.get('tips')}</b>\n"
        )
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(massage_uptime, parse_mode="HTML") 
        # if DEBUG:
        #     massage_debug = (
        #                     f"🚀 {'StartUP':10}: {startup_text}\n"
        #                     f"🕑 {'UpTime':10}: {uptime_text}\n"
        #                     f"📡 {'Ping':10}: {ping_ms} ms\n"
        #                     f"💡 {'Tips':10}: {TIP}")
        #     print(f"[PING] User: Ping \n\n{massage_debug}")
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
            
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Handle TUTORIAL ===================    
# @proccess_handling        
async def tutorial_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        await Logic_Start_Info(update, context, user_data.user_id)
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        # if DEBUG:
        #     print("[Handlers] User: Tutorial")
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        tutorial_info = Settings.get("tutorial_info")
        if tutorial_info:
            await update.message.reply_text(tutorial_info, parse_mode="HTML", disable_web_page_preview=True) 
            return
        return 
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
            
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass         
            
            