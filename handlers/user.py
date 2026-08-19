import config, datetime, pytz, time, logging, asyncio

from services import logic
from services.settings import Settings
from services.update_user import update_User_Activity_Logic

from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop
from telegram.error import TimedOut, BadRequest, Forbidden
# from services.proccess_manager import ProccessManager
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

async def Handler_Join_Refresh_Callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data.split(":", 1)[1] if ":" in query.data else ""

    user_id = query.from_user.id
    missing = await logic.Logic_Get_Missing_Groups(context, user_id)

    if missing:
        new_keyboard = logic.Logic_Join_Button(missing, query.data)
        try:
            await query.edit_message_reply_markup(reply_markup=new_keyboard)
        except BadRequest as e:
            if "not modified" not in str(e).lower():
                if Settings.is_logging():
                    logging.warning(f"[REFRESH] edit_message_reply_markup gagal: {e}")
        await query.answer("❌ Masih ada grup yang belum kamu join.")
        return

    await query.answer("✅ Verifikasi berhasil!")

    try:
        await query.message.delete()
    except (BadRequest, Forbidden) as e:
        if Settings.is_logging():
            logging.warning(f"[REFRESH] Gagal hapus pesan requirement: {e}")

    # dispatch berdasarkan action
    if action == "getall":
        await Handler_Send_VIP_All_Package(update, context)
    elif action == "getnew":
        await Handler_Get_Latest_VIP_Content(update, context)
    elif action == "tutorial":
        await Handler_Tutorial(update, context)
    elif action:
        await Handler_Content(action, update, context)
    
async def Handler_Maintenance(update, context):
    if not Settings.get("maintenance") == "true":
        return

    if update.effective_user and update.effective_user.id in config.ADMIN_IDS:
        return

    if update.effective_message:
        await update.effective_message.reply_text(
            "🔧 Bot sedang dalam maintenance.\n"
            "⏱ Time: 00:03:12"
        )

    raise ApplicationHandlerStop

async def Handler_Start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # if config.DEBUG:
        #     print("[Handlers] User: Start")
        await update.effective_message.reply_text("❌ Tidak Ada Gempa Terbaru.")
    except TimedOut:
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.effective_message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.effective_message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

# @proccess_handling
async def Handler_User_Start(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_data = update_User_Activity_Logic(update.effective_user)
    await logic.Logic_Set_Next_User_Commands(context, user_data)
    
    if not user_data.is_active:
        return
    
    text = update.message.text
    access_code = text.replace("/start","").strip()
    
    if not access_code:
        await Handler_Start(update, context)
        return
    else:
        # if config.DEBUG:
        #     print(f"[Handlers] Kode: {access_code}")
        await Handler_Content(access_code, update, context)
        return
           
async def Handler_Content(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE ):
    # if config.DEBUG:
    #     print("[Handlers] User: Get Content")
    
    if access_code.startswith("NV1Px"):   
        await Handler_Activate_VIP(access_code, update, context)
        return
    elif access_code.startswith("VV1Px"):
        await Handler_Get_VIP_Content(access_code, update, context)
        return
    elif access_code.startswith("N0cTRaA"):
        await Handler_Get_Reguler_Content(access_code, update, context)
        return
    else:
        await update.effective_message.reply_text("❌ Tidak Ada Gempa Terbaru.")
           
# ====== Handle Reguler Content Access =====
async def Handler_Get_Reguler_Content(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if config.DEBUG:
        #     print(f"[Handlers] Reguler Content Access: {access_code}")
        is_join = await logic.Logic_Start_Info(update, context, user_data.user_id, access_code)
        if not is_join:
            return
        
        msg = await update.effective_message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
        respon = logic.Logic_Get_Variable(access_code)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if respon:
            file_id = respon.get("file_id")
            content = respon.get("content")
            if file_id:
                await update.effective_message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
            else:
                await update.effective_message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await update.effective_message.reply_text(f"❌ <i>Not Found...</i>",parse_mode="HTML")
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.effective_message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.effective_message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Handle VIP Activation =============
async def Handler_Activate_VIP(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        
        is_join = await logic.Logic_Start_Info(update, context, user_data.user_id, access_code)
        if not is_join:
            return
        
        if Settings.is_logging():
            logging.info(f"[Handlers] VIP Activation: {access_code}")
        
        msg = await update.effective_message.reply_text("<i>Checking...</i>", parse_mode="HTML")
        user_data = logic.Logic_Get_User(user_data.user_id)
        if user_data.is_vip:
            dt = datetime.datetime.strptime(user_data.vip_created, "%Y-%m-%d %H:%M:%S")
            new_date = dt.strftime("%H:%M:%S %d-%m-%Y")
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.effective_message.reply_text(f"ℹ️ <i>Akun Sudah VIP\nTime: {new_date}\nPendaftaran Dibatalkan.</i>", parse_mode="HTML")
            return
        
        vip_created = logic.Logic_Get_Time().strftime("%Y-%m-%d %H:%M:%S")
        result = logic.Logic_Activate_VIP(access_code, user_data.user_id, vip_created)
        
        if not result["success"]:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.effective_message.reply_text(result["message"], parse_mode="HTML")
            return
            
        # Notify admin
        admin_message = (
            f"🎉 <b>VIP Baru!</b>\n\n"
            f"👤 User: {user_data.first_name + user_data.last_name} (@{user_data.username})\n"
            f"🆔 ID: <code>{user_data.user_id}</code>\n"
            f"📅 Time: <code>{vip_created}</code>\n"
            f"🔑 Code: <code>{access_code}</code>"
        )
        
        for admin_id in config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode="HTML"
                )
            except Exception as e:
                if Settings.is_logging():
                    logging.warning(f"[Handler] Failed to notify admin {admin_id}: {e}")
        user_data = logic.Logic_Get_User(user_data.user_id)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await Handler_Send_VIP_All_Package(update, context)
        await update.effective_message.reply_text("✅ <i><b>Anda Sekarang VIP!\nGunakan Menu Baru</b></i>", parse_mode="HTML")
        await logic.Logic_Set_Next_User_Commands(context, user_data)
        file, info = logic.Logic_Setup_Backup()
        await logic.Logic_Send_Backup_To_Admin(context, file, info)
        await logic.Logic_Send_Log(context)
        await logic.Logic_Send_Backup_To_Channel(context, file, info)
        
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.effective_message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.effective_message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Handle VIP Content Access =========
async def Handler_Get_VIP_Content(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if config.DEBUG:
        #     print(f"[Handlers] VIP Content Access: {access_code}")
        user_data = update_User_Activity_Logic(update.effective_user)
        is_join = await logic.Logic_Start_Info(update, context, user_data.user_id, access_code)
        if not is_join:
            return
        
        msg = await update.effective_message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.effective_message.reply_text(reply, parse_mode="HTML")
            return
        
        result = logic.Logic_Get_VIP_Variable(access_code)
        
        if not result["success"]:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.effective_message.reply_text(result.get("message","❌ Tidak Dapat Akses VIP"), parse_mode="HTML")
            return
        
        # Send VIP content
        file_id = result.get("file_id")
        content = result.get("content")
        
        if file_id:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.effective_message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
        else:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.effective_message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.effective_message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.effective_message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass



# ====== Send VIP Welcome Package ==========
# @proccess_handling
async def Handler_Send_VIP_All_Package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if config.DEBUG:
        #     print(f"[Handlers] Sending All VIP Contents")
        
        is_join = await logic.Logic_Start_Info(update, context, user_data.user_id, "getall")
        if not is_join:
            return
        msg = await update.effective_message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
                
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.effective_message.reply_text(reply, parse_mode="HTML")
            return

        package = logic.Logic_Get_All_VIP_Variable()

        if not package:
            await msg.delete()
            await update.effective_message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>", parse_mode="HTML")
            return
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        for idx, item in enumerate(package, 1):
            # Send VIP content
            file_id = item.get("file_id")
            content = item.get("content")
            
            if file_id:
                await update.effective_message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
            else:
                await update.effective_message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
            await asyncio.sleep(1)
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.effective_message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.effective_message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
     
    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Get Latest VIP Content  ===========
# @proccess_handling
async def Handler_Get_Latest_VIP_Content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # if config.DEBUG:
        #     print(f"[Handlers] Get Latest VIP Content")
        is_join = await logic.Logic_Start_Info(update, context, user_data.user_id, "getall")
        if not is_join:
            return
        msg = await update.effective_message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =Settings.get_vip_info()
            await update.effective_message.reply_text(reply, parse_mode="HTML")
            return
        
        result = logic.Logic_Get_Latest_VIP_Variable()
        
        if not result:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.effective_message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>", parse_mode="HTML")
            return
        
        # Send VIP content
        file_id = result.get("file_id")
        content = result.get("content")
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if file_id:
            await update.effective_message.reply_photo(photo=file_id, caption=content, parse_mode="HTML")
        else:
            await update.effective_message.reply_text(content, parse_mode="HTML", disable_web_page_preview=True)
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
        await update.effective_message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.effective_message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass



# ====== Handle PING =======================
# @proccess_handling
async def Handler_Ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        # await logic.Logic_Start_Info(update, context, user_data.user_id)
        start = time.time()
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        end = time.time()
        ping_ms = int((end - start) * 1000)
        
        # if config.DEBUG:
        #     print("[Handlers] User: Ping")
        
        tz = pytz.timezone(config.TIMEZONE)
        now = datetime.datetime.now(tz)
        
        uptime = now - config.START_TIME
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
        startup_text = config.START_TIME.strftime("%H:%M:%S %d-%m-%Y")
        if not Settings.get('tips'):
            Settings.set('tips', "Tidak Ada Tips.")
            
        massage_uptime = (
            f"🏓 Pong\n\n│🚀  StartUP\n├───  <b>{startup_text}</b>\n│🕑  UpTime\n├───  <b>{uptime_text}</b>\n│📡  Ping \n├───  <b>{ping_ms} ms</b>\n│💡  Tips\n└───  <b>{Settings.get('tips')}</b>\n"
        )
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(massage_uptime, parse_mode="HTML") 
        # if config.DEBUG:
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
async def Handler_Tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        is_join = await logic.Logic_Start_Info(update, context, user_data.user_id, "tutorial")
        if not is_join:
            return
        
        msg = await update.effective_message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        
        # if config.DEBUG:
        #     print("[Handlers] User: Tutorial")
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        tutorial_info = Settings.get("tutorial_info")
        if tutorial_info:
            await update.effective_message.reply_text(tutorial_info, parse_mode="HTML", disable_web_page_preview=True) 
            return
        return 
            
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
            
        await update.effective_message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.warning(f"[ERROR] Something Wrong... -> {e}")
        await update.effective_message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass         
            
            