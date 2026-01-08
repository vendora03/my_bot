from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TimedOut,BadRequest
from services.update_user import update_User_Activity_Logic
from services.logic import (
    User,
    set_commands_for_user,
    get_Time_Logic,
    get_Content_Logic,
    get_User_Logic,
    set_User_Logic,
    get_VIP_Content_Logic,
    activate_VIP_Logic,
    get_All_VIP_Contents_Logic,
    get_Latest_VIP_Contents_Logic)
from config import ADMIN_IDS,START_TIME,DEBUG,TIMEZONE,TIP
import datetime,pytz
import time



async def start_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if DEBUG:
            print("[Handlers] User: Start")
        await update.message.reply_text("❌ Tidak Ada Gempa Terbaru.")
    except TimedOut:
        await update.message.reply_text("⚠️ <i>Koneksi Timeout, coba lagi...</i>", parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text("❌ <i>Request Failed, coba lagi...</i>", parse_mode="HTML")

    
    
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
        if DEBUG:
            print(f"[Handlers] Kode: {access_code}")
        await Content_Handler(access_code, user_data.user_id, update, context)
        return
        
async def Content_Handler(access_code: str, user_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE ):
    if DEBUG:
        print("[Handlers] User: Get Content")
    
    # Check jika ini kode aktivasi VIP (NV1P-)
    if access_code.startswith("NV1Px"):
        await activate_VIP_Handler(access_code, user_id, update, context)
        return
    # Check jika ini konten VIP (VV1P-)
    elif access_code.startswith("VV1Px"):
        await get_VIP_Content_Handler(access_code, user_id, update, context)
        return
    elif access_code.startswith("N0cTRaA"):
        await get_Reguler_Content_Handler(access_code, update, context)
        return
    else:
        await update.message.reply_text("❌ Tidak Ada Gempa Terbaru.")
    
       

# ====== Handle VIP Activation =============
async def activate_VIP_Handler(access_code: str, user_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        if DEBUG:
            print(f"[Handlers] VIP Activation: {access_code}")
        
        msg = await update.message.reply_text("<i>Checking...</i>",parse_mode="HTML")
        user_data = get_User_Logic(user_id)
        if user_data.is_vip:
            dt = datetime.datetime.strptime(user_data.vip_created, "%Y-%m-%d %H:%M:%S")
            new_date = dt.strftime("%d-%m-%Y %H:%M:%S")
            await msg.delete()
            await update.message.reply_text(f"ℹ️ <i>Akun Sudah VIP\nTime: {new_date}\nPendaftaran Dibatalkan.</i>",parse_mode="HTML")
            return
        
        vip_created = get_Time_Logic().strftime("%Y-%m-%d %H:%M:%S")
        result = activate_VIP_Logic(access_code, user_id, vip_created)
        
        if not result["success"]:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            await update.message.reply_text(result["message"],parse_mode="HTML")
            return
            
        # Notify admin
        username = result.get("username", "Anonym")
        admin_message = (
            f"🎉 <b>VIP Baru!</b>\n\n"
            f"👤 User: {user_data.first_name} (@{username})\n"
            f"🆔 ID: <code>{user_id}</code>\n"
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
                if DEBUG:
                    print(f"[Handler] Failed to notify admin {admin_id}: {e}")
        user_data = get_User_Logic(user_id)
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await send_VIP_All_Package_Handler(update, context)
        await update.message.reply_text("✅ <i><b>Anda Sekarang VIP!\nGunakan Menu Baru</b></i>",parse_mode="HTML")
        await set_commands_for_user(context, user_data)
        
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

# ====== Handle VIP Content Access =========
async def get_VIP_Content_Handler(access_code: str, user_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        if DEBUG:
            print(f"[Handlers] VIP Content Access: {access_code}")
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        result = get_VIP_Content_Logic(access_code, user_id)
        
        if not result["success"]:
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
            await msg.delete()
            await update.message.reply_photo(
                photo=file_id,
                caption=content
            )
        else:
            await msg.delete()
            await update.message.reply_text(content, parse_mode="HTML")
            
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

# ====== Handle Reguler Content Access =====
async def get_Reguler_Content_Handler(access_code: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        if DEBUG:
            print(f"[Handlers] Reguler Content Access: {access_code}")
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        respon = get_Content_Logic(access_code)
        if respon:
            file_id = respon.get("file_id")
            content = respon.get("content")
            if file_id:
                await msg.delete()
                await update.message.reply_photo(
                    photo=file_id,
                    caption=content 
                )
            else:
                await msg.delete()
                await update.message.reply_text(content)
        else:
            await msg.delete()
            await update.message.reply_text(f"❌ <i><b>Not Found...</b></i>",parse_mode="HTML")
            
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

# ====== Send VIP Welcome Package ==========
async def send_VIP_All_Package_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        if DEBUG:
            print(f"[Handlers] Sending All VIP Contents")
            
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
                
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =("🔒 <b>Konten VIP</b>\n\n"
                "Konten ini hanya tersedia untuk member VIP.\n\n"
                "💎 <b>Keuntungan VIP:</b>\n"
                "• Akses ke semua konten eksklusif\n"
                "• Update konten premium setiap hari\n"
                "• Prioritas support\n\n"
                "💰 <b>Harga VIP:</b> Rp 50.000/bulan\n\n"
                "Hubungi admin untuk upgrade ke VIP!")
            await update.message.reply_text(reply ,parse_mode="HTML")
            return
        
        package = get_All_VIP_Contents_Logic()
        
        if not package:
            await msg.delete()
            await update.message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>",parse_mode="HTML")
            return
        
        await msg.delete()
        for idx, item in enumerate(package, 1):
            # Send VIP content
            file_id = item.get("file_id")
            content = item.get("content")
            
            if file_id:
                await update.message.reply_photo(photo=file_id,caption=content)
            else:
                await update.message.reply_text(content, parse_mode="HTML")
            time.sleep(1)
            
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

# ====== Get Latest VIP Content  ===========
async def get_Latest_VIP_Content_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        user_data = update_User_Activity_Logic(update.effective_user)
        if DEBUG:
            print(f"[Handlers] Get Latest VIP Content")
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
        if not user_data.is_vip:
            if msg and getattr(msg, "message_id", None):
                await msg.delete()
            reply =("🔒 <b>Konten VIP</b>\n\n"
                "Konten ini hanya tersedia untuk member VIP.\n\n"
                "💎 <b>Keuntungan VIP:</b>\n"
                "• Akses ke semua konten eksklusif\n"
                "• Update konten premium setiap hari\n"
                "• Prioritas support\n\n"
                "💰 <b>Harga VIP:</b> Rp 50.000/bulan\n\n"
                "Hubungi admin untuk upgrade ke VIP!")
            await update.message.reply_text(reply ,parse_mode="HTML")
            return
        
        result = get_Latest_VIP_Contents_Logic()
        
        if not result:
            await msg.delete()
            await update.message.reply_text("⚠️ <i><b>Konten VIP Tidak Tersedia...</b></i>",parse_mode="HTML")
            return
        
        # Send VIP content
        file_id = result.get("file_id")
        content = result.get("content")
        
        await msg.delete()
        if file_id:
            await update.message.reply_photo(photo=file_id,caption=content)
        else:
            await update.message.reply_text(content, parse_mode="HTML")
            
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



# ====== Handle PING =======================
async def ping_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = None
    try:
        update_User_Activity_Logic(update.effective_user)
        global TIP
        start = time.time()
        
        msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")
        
        end = time.time()
        ping_ms = int((end - start) * 1000)
        
        if DEBUG:
            print("[Handlers] User: Ping")
        
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
        startup_text = START_TIME.strftime("%d-%m-%Y %H:%M:%S")
        if not TIP:
            TIP = "Tidak Ada Tips."
            
        massage_uptime = (
            f"🏓 Pong\n\n│🚀  StartUP\n├───  <b>{startup_text}</b>\n│🕑  UpTime\n├───  <b>{uptime_text}</b>\n│📡  Ping \n├───  <b>{ping_ms} ms</b>\n│💡  Tips\n└───  <b>{TIP}</b>\n"
        )
        
        if msg and getattr(msg, "message_id", None):
            await msg.delete()
        await update.message.reply_text(massage_uptime,parse_mode="HTML") 
        if DEBUG:
            massage_debug = (
                            f"🚀 {'StartUP':10}: {startup_text}\n"
                            f"🕑 {'UpTime':10}: {uptime_text}\n"
                            f"📡 {'Ping':10}: {ping_ms} ms\n"
                            f"💡 {'Tips':10}: {TIP}")
            print(f"[PING] User: Ping \n\n{massage_debug}")
            
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