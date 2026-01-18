import pytz, asyncio, logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TimedOut, BadRequest
from services.settings import Settings
from config import (
    # DEBUG,
    ADMIN_IDS, 
    BACKUP_PATH, 
    TIMEZONE, 
    SETTINGS_SCHEMA)
# from services.database import DB_Remove_All_VIP
from services.logic import (
    setup_Backup_Logic,
    send_Log_Logic,
    send_Backup_To_Admin_Logic,
    send_Backup_To_Channel_Logic,
    format_Help_Logic,
    create_VIP_Code_Logic,
    set_VIP_Variable_Logic,
    get_User_Logic,
    user_Statistic_Logic,
    get_All_User_Logic,
    restore_Backup_Logic,
    get_Time_Logic,
    assign_Template_Logic,
    do_Broadcast_Logic,
    set_Variable_Logic,
    set_Daily_Schedule_Logic,
    get_All_Daily_Schedule_Logic,
    show_Daily_Schedule_Logic,
    delete_Daily_Schedule_Logic,
    set_Template_Logic,
    get_All_Template_Logic,
    get_Template_Logic,
    delete_Template_Logic)
        
# ====== Cek Admin ======================== 
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
 
async def user_Statistic_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")

        users = get_All_User_Logic()
        result = user_Statistic_Logic(users)

        await msg.delete()
        await update.message.reply_text(result, parse_mode="HTML")
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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Log handler ====================== 👌
async def log_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/log]")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await send_Log_Logic(context)

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
    
    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Backup handler =================== 👌
async def backup_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/backup]")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        if msg and getattr(msg, "message_id", None):
            await msg.delete()
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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
    
    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
       
        
# ====== Restore handler ================== 👌       
async def restore_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/restore]")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        doc = update.message.document
        if not doc or not doc.file_name.endswith(".json"):
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("<i>File backup (.json) tidak valid...</i>", parse_mode="HTML")

        file = await doc.get_file()
        await file.download_to_drive(BACKUP_PATH)

        response = restore_Backup_Logic()
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(response or "✅ Restore selesai",parse_mode="HTML")

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")


    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Call Broadcast =================== 👌
async def do_Broadcast_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    success = 0
    failed = 0
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/broadcast]")
            return

        if not context.args:
            await update.message.reply_text("❓ <i>Content Is Empty...</i>",parse_mode="HTML")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=1)
        content = parts[1]
        users_data = do_Broadcast_Logic()

        tasks = [
            context.bot.send_message(chat_id=u["user_id"], text=content)
            for u in users_data if u.get("is_active")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success = sum(not isinstance(r, Exception) for r in results)
        failed = sum(isinstance(r, Exception) for r in results)
        await msg.delete()
        await update.message.reply_text(f"✅ <i>Broadcast Selesai</i>\nBerhasil: <b>{success}</b>\nGagal: <b>{failed}</b>",parse_mode="HTML")

    except TimedOut:
        await msg.delete()
        await update.message.reply_text(f"⚠️ <i>Koneksi Timeout, coba lagi...\nBerhasil: <b>{success}</b>\nGagal: <b>{failed}</b></i>", parse_mode="HTML")

    except Exception as e:
        await msg.delete()
        await update.message.reply_text(f"❌ <i>Request Failed, coba lagi...\nBerhasil: <b>{success}</b>\nGagal: <b>{failed}</b></i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Save Variable ==================== 
async def set_Variable_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Set Variable")

        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/setvariable]")
            return

        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("Format: /setvariable <content>")
            return

        foto = update.message.photo[-1] if update.message.photo else None
        file_id = foto.file_id if foto else None

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        content = parts[1]
        link_access = set_Variable_Logic(content, file_id)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("✅ <i>New Variable Saved...</i>", parse_mode="HTML")
        await update.message.reply_text(link_access)


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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
        



# <<<<<<<< START DAILY SCHEDULE >>>>>>>>>>>

# ====== Save Daily Scheduler ============= 
async def set_Daily_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Set Daily Schedule")

        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/setdaily]")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("Format: /setdailyschedule <content>")
            return

        foto = update.message.photo[-1] if update.message.photo else None
        file_id = foto.file_id if foto else None


        content = parts[1]
        access_code = set_Daily_Schedule_Logic(content, file_id)
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(f"✅ <i>Task Scheduled Saved...</i>\n└── <code>{access_code}</code>",parse_mode="HTML")
        
        if file_id:
            await update.message.reply_photo(photo=file_id, caption=content)
        else:
            await update.message.reply_text(content)

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
    
# ====== Command Daily Scheduler ========== 👌
async def daily_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if DEBUG:
    #     print("[Handlers] Admin: Daily Schedule")
        
    user = update.effective_user
    if not is_admin(user.id):
        last_name = user.last_name or ""
        username = f"(@{user.username})" if user.username else ""
        logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/daily_schedule]")
        return
    
    msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
    
    if not context.args:
        
        await show_All_Daily_Schedule_Handler(update, context, msg)
        return
    
    access_code = context.args[0]
    await show_Daily_Schedule_Handler(update, context, msg, access_code)
    
# ====== Show All Daily Schedule ========== 
async def show_All_Daily_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE, msg):
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Show All Daily Schedule")

        row = get_All_Daily_Schedule_Logic()
        if row:
            lines = [f"{i}. <code>{code}</code>" for i, code in enumerate(row, start=1)]
            respon = "All Schedule Daily\n\n" + "\n".join(lines)
        else:
            respon = "<i>!!<b>EMPTY SCHEDULE DAILY</b>!!</i>"
            
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(respon, parse_mode="HTML")

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Show Content Daily Schedule ====== 
async def show_Daily_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE, msg, access_code):
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Show Content Daily Schedule")

        respon = show_Daily_Schedule_Logic(access_code)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        if respon:
            file_id = respon.get("file_id")
            content = respon.get("content")

            if file_id:
                await update.message.reply_photo(photo=file_id,caption=content)
            else:
                await update.message.reply_text(content)
        else:
            await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Delete Daily Schedule ============ 👌
async def delete_Daily_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Delete Daily Schedule")

        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/deletedailyschedule]")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Format: /deletedailyschedule <code>")
            return

        if len(context.args) > 2:
            await update.message.reply_text("Format: /deletedailyschedule <code>")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        access_code = context.args[0]
        response = delete_Daily_Schedule_Logic(access_code)

        if msg and getattr(msg, "message_id", None):
            await msg.delete()
            
        if response:
            await update.message.reply_text(f"✅ <i>Schedule <b>{access_code}</b> Dihapus...</i>",parse_mode="HTML")
            return
        await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")
    
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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
            
# <<<<<<<< END DAILY SCHEDULE >>>>>>>>>>>




# <<<<<<<<<<<< START TEMPLATE >>>>>>>>>>>>>

# ====== Get Template ===================== 
async def get_Template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Get Template")

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        if len(context.args) < 2:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("Format: /gettemplate <code> <Arg[space]>")
            return

        access_code = context.args[0]
        values = context.args[1:]

        template = get_Template_Logic(access_code)
        if not template:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")
            return

        result = assign_Template_Logic(template, values)
        if msg and getattr(msg, "message_id", None):
                await msg.delete()
        await update.message.reply_text(result, parse_mode="HTML")

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
        
# ====== Save Template ==================== 
async def set_Template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Set Template")

        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/settemplate]")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Format: /settemplate <template>")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=1)
        content = parts[1]

        access_code = set_Template_Logic(content)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(f"<i>✅ Template Saved...</i>\n└── <code>{access_code}</code>",parse_mode="HTML")
        await update.message.reply_text(content)

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
    
# ====== Command Template ================= 
async def template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Template")

        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/template]")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        if not context.args:
            await show_All_Template_Handler(update, context, msg)
            return

        access_code = context.args[0]
        await show_Template_Handler(update, context, msg, access_code)

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
    
# ====== Show All Template ================ 
async def show_All_Template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE, msg):
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Show All Template")

        row = get_All_Template_Logic()
        if row:
            lines = [f"{i}. <code>{code}</code>" for i, code in enumerate(row, start=1)]
            respon = "All Template\n\n" + "\n".join(lines)
        else:
            respon = "<i>!!<b>EMPTY Template</b>!!</i>"
            
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(respon, parse_mode="HTML")

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Show Content Template ============ 
async def show_Template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE, msg, access_code):
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Show Content Template")

        respon = get_Template_Logic(access_code)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if respon:
            await update.message.reply_text(respon)
        else:
            await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Delete Template ================== 👌
async def delete_Template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        # if DEBUG:
        #     print("[Handlers] Admin: Delete Template")

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Format: /deletetemplate <code>")
            return

        if len(context.args) > 2:
            await update.message.reply_text("Format: /deletetemplate <code>")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        access_code = context.args[0]
        response = delete_Template_Logic(access_code)
       
        if response:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(f"✅ <i>Template <b>{access_code}</b> Dihapus...</i>",parse_mode="HTML")
            return

        await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")


    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# <<<<<<<<<<<<<< END TEMPLATE >>>>>>>>>>>>>



# <<<<<<<<<<<< START VIP >>>>>>>>>>>>>>>>>>

# ====== [ADMIN] Create VIP Code ============
async def create_VIP_Code_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/createVIP]")
            return
        
        # if DEBUG:
        #     print("[Handlers] Admin: Create VIP Code")
            
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        result = create_VIP_Code_Logic()
        
        message = (
            "✅ <b>Kode VIP Berhasil Dibuat!</b>\n\n"
            f"🔑 Code: <code>{result['access_code']}</code>\n"
            f"🔗 Link: {result['link']}\n\n"
        )
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(message, parse_mode="HTML")
        
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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== [ADMIN] Set VIP Variable ===========
async def set_VIP_Variable_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/setvipvariable]")
            return
        
        # if DEBUG:
        #     print("[Handlers] Admin: Set VIP Variable")
        
        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("Format: /setvipvariable <content>")
            return

        foto = update.message.photo[-1] if update.message.photo else None
        file_id = foto.file_id if foto else None
        content = parts[1]

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        link_access = set_VIP_Variable_Logic(content, file_id)
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("✅ <i>New Variable Saved...</i>", parse_mode="HTML")
        await update.message.reply_text(link_access)
        
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        if Settings.is_logging():
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== [ADMIN] List All VIP Users =========
async def list_VIP_Users_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/listvip]")
            return
        
        # if DEBUG:
        #     print("[Handlers] Admin: List VIP Users")
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        users = get_All_User_Logic()
        
        vip_users = [u for u in users if u.get("is_vip", False)]
        
        if not vip_users:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("📊 <i><b>Belum ada VIP user...</b></i>",parse_mode="HTML")
            return
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        message = f"👑 <b>VIP Users ({len(vip_users)}):</b>\n\n"
        for idx, u in enumerate(vip_users, 1):
            user_info = get_User_Logic(u["user_id"])
            username = user_info.username
            first_name = user_info.first_name
            dt = datetime.strptime(u["vip_created"], "%Y-%m-%d %H:%M:%S")
            new_date = dt.strftime("%H:%M:%S %d-%m-%Y")
            message += f"{idx}. {first_name} (@{username})\n"
            message += f"   ID: <code>{u['user_id']}</code>\n"
            message += f"   Time: <code>{new_date}</code>\n\n"
            
            # Split message if too long
            if len(message) > 3500:
                await update.message.reply_text(message, parse_mode="HTML")
                message = ""
        
        if message.strip():
            await update.message.reply_text(message, parse_mode="HTML")
            
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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")


    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
        
# <<<<<<<<<<<<< END VIP >>>>>>>>>>>>>>>>>>>


# async def remove_All_VIP_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.effective_user.id
    
#     if not is_admin(user_id):
#         await update.message.reply_text("❌ Unauthorized")
#         return
#     msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
#     # DB_Remove_All_VIP()
#     await msg.delete()
#     await update.message.reply_text("✅ <b>Selesai...</b>", parse_mode="HTML")




async def scheduled_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        user_data = get_All_User_Logic()
        message = context.job.data.get("message")
        file_id = context.job.data.get("file_id")

        if not message:
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"❌ <i>Schedule Tidak Ada Pesan</i>\nTime: {get_Time_Logic().strftime('%H:%M:%S %d-%m-%Y')}",
                    parse_mode="HTML"
                )
            return

        tasks = []
        for user in user_data:
            if user.get("is_active"):
                if file_id:
                    tasks.append(
                        context.bot.send_photo(
                            chat_id=user["user_id"],
                            photo=file_id,
                            caption=message
                        )
                    )
                else:
                    tasks.append(
                        context.bot.send_message(
                            chat_id=user["user_id"],
                            text=message
                        )
                    )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = sum(not isinstance(r, Exception) for r in results)
        failed = sum(isinstance(r, Exception) for r in results)
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin_id, text=f"✅ <i>Daily Schedule Selesai</i>\nBerhasil: <b>{success}</b>\nGagal: <b>{failed}</b>",parse_mode="HTML")
    except TimedOut:
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin_id, text="⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")
        if Settings.is_logging():
            logging.warning("[TIMEOUT] Koneksi Timeout...")
    except Exception as e:
        if Settings.is_logging():
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin_id, text="❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        
async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/schedule]")
            return


        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=3)
        if len(parts) < 4:
            await update.message.reply_text(
                "Format: /schedule HH:MM DD-MM-YYYY <pesan>"
            )
            return

        time_str = parts[1]
        date_str = parts[2]
        message_text = parts[3]
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        tz = pytz.timezone(TIMEZONE)
        dt_str = f"{time_str} {date_str}"

        try:
            dt = tz.localize(datetime.strptime(dt_str, "%H:%M %d-%m-%Y"))
        except ValueError:
            await msg.delete()
            await update.message.reply_text("❌ Format tanggal salah.\nGunakan: YYYY-MM-DD HH:MM")
            return

        delay = (dt - datetime.now(tz)).total_seconds()
        if delay <= 0:
            await msg.delete()
            await update.message.reply_text("⛔ <i>Waktu sudah lewat...</i>",parse_mode="HTML")
            return

        file_id = None
        if update.message.photo:
            file_id = update.message.photo[-1].file_id

        context.job_queue.run_once(
            callback=scheduled_job,
            when=delay,
            data={
                "message": message_text,
                "file_id": file_id
            }
        )
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(f"✅ <i>Task scheduled at {dt.strftime('%H:%M %d-%m-%Y')}...</i>",parse_mode="HTML")

        if file_id:
            await update.message.reply_photo(photo=file_id, caption=message_text)
        else:
            await update.message.reply_text(message_text)

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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass


# <<<<<<<<<<<< START Settings >>>>>>>>>>>>>
async def settings_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user = update.effective_user
        if not is_admin(user.id):
            last_name = user.last_name or ""
            username = f"(@{user.username})" if user.username else ""
            logging.info(f"{user.first_name + last_name}({username}) mencoba akses command [/settings]")
            return
        
        # if DEBUG:
        #     print("[Handlers] Admin: Settings Bot")
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")        
        # if not context.arg:
        #     if msg and getattr(msg, "message_id", None):
        #         await msg.delete()
        #     await update.message.reply_text("Format:\n\n" + await format_Help_Logic())
        #     return
        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=2)
        
        if len(parts) <= 1:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("Format:\n\n" + format_Help_Logic())
            return
        
        key = parts[1]
        raw_value = parts[2]

        is_valid = (
            len(parts) >= 2
            and key in SETTINGS_SCHEMA
            and (
                (SETTINGS_SCHEMA[key] == "bool"
                and raw_value.lower() in ("true", "false"))
                or
                (SETTINGS_SCHEMA[key] == "text"
                and raw_value.strip())
            )
        )
        
        if not is_valid:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text("Format:\n\n" + format_Help_Logic())
            return

        value_type = SETTINGS_SCHEMA[key]
        
        value = raw_value.lower() if value_type == "bool" else raw_value
        Settings.set(key, value)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(f"✅ <i>Setting <b>`{key}`</b> Saved...</i>",parse_mode="HTML")
          
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
            logging.error(f"[ERROR] Something Wrong... -> {e}")
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
# <<<<<<<<<<<< END Settings >>>>>>>>>>>>>>>
