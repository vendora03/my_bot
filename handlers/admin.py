import pytz, asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TimedOut, BadRequest
from config import ADMIN_IDS, DEBUG, BACKUP_PATH, TIMEZONE
from services.database import DB_Remove_All_VIP
from services.logic import (
    create_VIP_Code_Logic,
    set_VIP_Variable_Logic,
    get_User_Logic,
    user_Statistic_Logic,
    get_All_User_Logic,
    backup_Logic,
    restore_Backup_Logic,
    get_Time_Logic,
    assign_Template_Logic,
    do_Broadcast_Logic,
    set_Variable_Logic,
    get_Daily_Schedule_Logic,
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
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        file, info = backup_Logic()

        text = (
            f"<b>📦 Backup:</b> {get_Time_Logic().strftime('%d-%m-%Y %H:%M:%S')}\n\n"
            f"Users            : <b>{info.get('users', 0)}</b> row\n"
            f"Variables       : <b>{info.get('variables', 0)}</b> row\n"
            f"VIP Codes      : <b>{info.get('vip_codes', 0)}</b> row\n"
            f"VIP Variables  : <b>{info.get('vip_variables', 0)}</b> row\n"
            f"Schedule       : <b>{info.get('daily_schedule', 0)}</b> row\n"
            f"Template       : <b>{info.get('template', 0)}</b> row\n"
        )
        await msg.delete()
        await update.message.reply_document(document=file,caption=text,parse_mode="HTML")

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        doc = update.message.document
        if not doc or not doc.file_name.endswith(".json"):
            await msg.delete()
            await update.message.reply_text("<i>File backup (.json) tidak valid...</i>", parse_mode="HTML")

        file = await doc.get_file()
        await file.download_to_drive(BACKUP_PATH)

        response = restore_Backup_Logic()
        await msg.delete()
        await update.message.reply_text(response or "✅ Restore selesai",parse_mode="HTML")

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
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
        if DEBUG:
            print("[Handlers] Admin: Set Variable")

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
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
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        if DEBUG:
            print("[Handlers] Admin: Set Daily Schedule")

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("Format: /setdailyschedule <content>")
            return

        foto = update.message.photo[-1] if update.message.photo else None
        file_id = foto.file_id if foto else None


        content = parts[1]
        access_code = set_Daily_Schedule_Logic(content, file_id)

        await msg.delete()
        await update.message.reply_text(f"✅ <i>Task Scheduled Saved...</i>\n└── <code>{access_code}</code>",parse_mode="HTML")
        
        if file_id:
            await update.message.reply_photo(photo=file_id, caption=content)
        else:
            await update.message.reply_text(content)

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
    
# ====== Command Daily Scheduler ========== 👌
async def daily_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if DEBUG:
        print("[Handlers] Admin: Daily Schedule")
        
    user_id = update.effective_user.id
    text = update.message.text
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Kamu bukan admin.")
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
        if DEBUG:
            print("[Handlers] Admin: Show All Daily Schedule")

        row = get_All_Daily_Schedule_Logic()
        if row:
            lines = [f"{i}. <code>{code}</code>" for i, code in enumerate(row, start=1)]
            respon = "All Schedule Daily\n\n" + "\n".join(lines)
        else:
            respon = "<i>!!<b>EMPTY SCHEDULE DAILY</b>!!</i>"
        await msg.delete()
        await update.message.reply_text(respon, parse_mode="HTML")

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Show Content Daily Schedule ====== 
async def show_Daily_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE, msg, access_code):
    try:
        if DEBUG:
            print("[Handlers] Admin: Show Content Daily Schedule")

        respon = show_Daily_Schedule_Logic(access_code)
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
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        if DEBUG:
            print("[Handlers] Admin: Delete Daily Schedule")

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
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

        await msg.delete()
        if response:
            await update.message.reply_text(f"✅ <i>Schedule <b>{access_code}</b> Dihapus...</i>",parse_mode="HTML")
            return
        await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")
    
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        if DEBUG:
            print("[Handlers] Admin: Get Template")

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        if len(context.args) < 2:
            await update.message.reply_text("Format: /gettemplate <code> <Arg[space]>")
            return

        access_code = context.args[0]
        values = context.args[1:]

        template = get_Template_Logic(access_code)
        if not template:
            await msg.delete()
            await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")
            return

        result = assign_Template_Logic(template, values)
        await msg.delete()
        await update.message.reply_text(result, parse_mode="HTML")

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        if DEBUG:
            print("[Handlers] Admin: Set Template")

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("Format: /settemplate <template>")
            return

        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=1)
        content = parts[1]

        access_code = set_Template_Logic(content)
        
        await msg.delete()
        await update.message.reply_text(f"<i>✅ Template Saved...</i>\n└── <code>{access_code}</code>",parse_mode="HTML")
        await update.message.reply_text(content)

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        if DEBUG:
            print("[Handlers] Admin: Template")

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
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
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
    
# ====== Show All Template ================ 
async def show_All_Template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE, msg):
    try:
        if DEBUG:
            print("[Handlers] Admin: Show All Template")

        row = get_All_Template_Logic()
        if row:
            lines = [f"{i}. <code>{code}</code>" for i, code in enumerate(row, start=1)]
            respon = "All Template\n\n" + "\n".join(lines)
        else:
            respon = "<i>!!<b>EMPTY Template</b>!!</i>"
        await msg.delete()
        await update.message.reply_text(respon, parse_mode="HTML")

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass

# ====== Show Content Template ============ 
async def show_Template_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE, msg, access_code):
    try:
        if DEBUG:
            print("[Handlers] Admin: Show Content Template")

        respon = get_Template_Logic(access_code)
        await msg.delete()
        if respon:
            await update.message.reply_text(respon)
        else:
            await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        if DEBUG:
            print("[Handlers] Admin: Delete Template")

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
       
        await msg.delete()
        if response:
            await update.message.reply_text(f"✅ <i>Template <b>{access_code}</b> Dihapus...</i>",parse_mode="HTML")
            return

        await update.message.reply_text(f"❌ <i>Not Found <b>{access_code}</b>...</i>",parse_mode="HTML")

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return
        
        if DEBUG:
            print("[Handlers] Admin: Create VIP Code")
            
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        result = create_VIP_Code_Logic()
        
        message = (
            "✅ <b>Kode VIP Berhasil Dibuat!</b>\n\n"
            f"🔑 Code: <code>{result['access_code']}</code>\n"
            f"🔗 Link: {result['link']}\n\n"
        )
        
        await msg.delete()
        await update.message.reply_text(message, parse_mode="HTML")
        
    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return
        
        if DEBUG:
            print("[Handlers] Admin: Set VIP Variable")
        
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
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

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
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
                await update.message.reply_text("⛔ Kamu bukan admin.")
                return
        
        if DEBUG:
            print("[Handlers] Admin: List VIP Users")
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
        users = get_All_User_Logic()
        
        vip_users = [u for u in users if u.get("is_vip", False)]
        
        if not vip_users:
            await msg.delete()
            await update.message.reply_text("📊 <i><b>Belum ada VIP user...</b></i>",parse_mode="HTML")
            return
        
        await msg.delete()
        message = f"👑 <b>VIP Users ({len(vip_users)}):</b>\n\n"
        for idx, u in enumerate(vip_users, 1):
            user_info = get_User_Logic(u["user_id"])
            username = user_info.username
            first_name = user_info.first_name
            dt = datetime.strptime(u["vip_created"], "%Y-%m-%d %H:%M:%S")
            new_date = dt.strftime("%d-%m-%Y %H:%M:%S")
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
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass
        
# <<<<<<<<<<<<< END VIP >>>>>>>>>>>>>>>>>>>


async def remove_All_VIP_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return
    msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")
    DB_Remove_All_VIP()
    await msg.delete()
    await update.message.reply_text("✅ <b>Selesai...</b>", parse_mode="HTML")




async def scheduled_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        user_data = get_All_User_Logic()
        message = context.job.data.get("message")
        file_id = context.job.data.get("file_id")

        if not message:
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"❌ <i>Schedule Tidak Ada Pesan</i>\nTime: {get_Time_Logic().strftime('%d-%m-%Y %H:%M:%S')}",
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

    except Exception as e:
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin_id, text="❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        
async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("⛔ Kamu bukan admin.")
            return


        text = update.message.text or update.message.caption or ""
        parts = text.split(maxsplit=3)
        if len(parts) < 4:
            await update.message.reply_text(
                "Format: /schedule YYYY-MM-DD HH:MM <pesan>"
            )
            return

        date_str = parts[1]
        time_str = parts[2]
        message_text = parts[3]
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>", parse_mode="HTML")

        tz = pytz.timezone(TIMEZONE)
        dt_str = f"{date_str} {time_str}"

        try:
            dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
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

        await msg.delete()
        await update.message.reply_text(f"✅ <i>Task scheduled at {dt.strftime('%d-%m-%Y %H:%M')}...</i>",parse_mode="HTML")

        if file_id:
            await update.message.reply_photo(photo=file_id, caption=message_text)
        else:
            await update.message.reply_text(message_text)

    except TimedOut:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")
        if DEBUG:
            print(e)

    finally:
        if msg and getattr(msg, "message_id", None):
            try:
                await msg.delete()
            except BadRequest:
                pass


