from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TimedOut, BadRequest
from services.update_user import update_User_Activity_Logic
from services.proccess_manager import ProccessManager
from services.logic import (
    setup_Backup_Logic,
    send_Log_Logic,
    send_Backup_To_Admin_Logic,
    send_Backup_To_Channel_Logic,
    cek_Subscribe_Logic,
    set_commands_for_user,
    get_Time_Logic,
    get_Content_Logic,
    get_User_Logic,
    get_VIP_Content_Logic,
    activate_VIP_Logic,
    get_All_VIP_Contents_Logic,
    get_Latest_VIP_Contents_Logic)
from config import (
    # DEBUG,
    ADMIN_IDS, 
    START_TIME, 
    TIMEZONE)
from services.settings import Settings
import datetime, pytz, time, logging, asyncio

def proccess_handling(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if ProccessManager.is_processing(user_id):
            return  
        
        ProccessManager.start_processing(user_id)
        
        try:
            await func(update, context)
        finally:
            ProccessManager.finish_processing(user_id)
    
    return wrapper  


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

@proccess_handling
async def user_Start_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_data = update_User_Activity_Logic(update.effective_user)
    await set_commands_for_user(context, user_data)
    
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
        await cek_Subscribe_Logic(update, context, user_data.user_id)
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
        respon = get_Content_Logic(access_code)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if respon:
            file_id = respon.get("file_id")
            content = respon.get("content")
            if file_id:
                await update.message.reply_photo(
                    photo=file_id,
                    caption=content
                )
            else:
                await update.message.reply_text(content, disable_web_page_preview=True)
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
        await cek_Subscribe_Logic(update, context, user_data.user_id)
        if Settings.is_logging():
            logging.info(f"[Handlers] VIP Activation: {access_code}")
        
        msg = await update.message.reply_text("<i>Checking...</i>",parse_mode="HTML")
        user_data = get_User_Logic(user_data.user_id)
        if user_data.is_vip:
            dt = datetime.datetime.strptime(user_data.vip_created, "%Y-%m-%d %H:%M:%S")
            new_date = dt.strftime("%H:%M:%S %d-%m-%Y")
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(f"ℹ️ <i>Akun Sudah VIP\nTime: {new_date}\nPendaftaran Dibatalkan.</i>",parse_mode="HTML")
            return
        
        vip_created = get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S")
        result = activate_VIP_Logic(access_code, user_data.user_id, vip_created)
        
        if not result["success"]:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(result["message"],parse_mode="HTML")
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
        user_data = get_User_Logic(user_data.user_id)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await send_VIP_All_Package_Handler(update, context)
        await update.message.reply_text("✅ <i><b>Anda Sekarang VIP!\nGunakan Menu Baru</b></i>",parse_mode="HTML")
        await set_commands_for_user(context, user_data)
        file, info = setup_Backup_Logic()
        await send_Backup_To_Admin_Logic(context, file, info)
        await send_Log_Logic(context)
        await send_Backup_To_Channel_Logic(context, file, info)
        
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
        await cek_Subscribe_Logic(update, context, user_data.user_id)
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.message.reply_text(reply ,parse_mode="HTML")
            return
        
        result = get_VIP_Content_Logic(access_code)
        
        if not result["success"]:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(
                result.get("message","❌ Tidak Dapat Akses VIP"),
                parse_mode="HTML"
            )
            return
        
        # Send VIP content
        file_id = result.get("file_id")
        content = result.get("content")
        
        if file_id:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_photo(
                photo=file_id,
                caption=content
            )
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
@proccess_handling
async def send_VIP_All_Package_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if DEBUG:
        #     print(f"[Handlers] Sending All VIP Contents")
        
        await cek_Subscribe_Logic(update, context, user_data.user_id)
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
                
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.message.reply_text(reply ,parse_mode="HTML")
            return

        package = get_All_VIP_Contents_Logic()

        if not package:
            await msg.delete()
            await update.message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>",parse_mode="HTML")
            return
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        for idx, item in enumerate(package, 1):
            # Send VIP content
            file_id = item.get("file_id")
            content = item.get("content")
            
            if file_id:
                await update.message.reply_photo(photo=file_id,caption=content)
            else:
                await update.message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
            asyncio.sleep(1)
            
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
@proccess_handling
async def get_Latest_VIP_Content_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if DEBUG:
        #     print(f"[Handlers] Get Latest VIP Content")
        await cek_Subscribe_Logic(update, context, user_data.user_id)
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.message.reply_text(reply ,parse_mode="HTML")
            return
        
        result = get_Latest_VIP_Contents_Logic()
        
        if not result:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>",parse_mode="HTML")
            return
        
        # Send VIP content
        file_id = result.get("file_id")
        content = result.get("content")
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if file_id:
            await update.message.reply_photo(photo=file_id,caption=content)
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
@proccess_handling
async def ping_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # await cek_Subscribe_Logic(update, context, user_data.user_id)
        start = time.time()
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
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
        await update.message.reply_text(massage_uptime,parse_mode="HTML") 
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
@proccess_handling        
async def tutorial_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        await cek_Subscribe_Logic(update, context, user_data.user_id)
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
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
            
            