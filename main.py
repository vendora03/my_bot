import pytz
import time as waktu
from datetime import time
from telegram.ext import Application,CommandHandler,MessageHandler, filters
from services.settings import Settings
from services.database import init_db
from services.logic import (
    init_settings, 
    error_handler,
    on_Startup, 
    restore_Backup_Logic,
    generate_Tip_Logic,
    # get_Daily_Schedule_Logic,
    send_Backup_Logic,
    send_Log_Logic)
from handlers.user import (
    user_Start_Handler,
    ping_Handler,
    send_VIP_All_Package_Handler,
    get_Latest_VIP_Content_Handler)
from config import (
    # DEBUG, 
    BOT_TOKEN, 
    TIP, 
    ADMIN_IDS, 
    TIMEZONE)
from handlers.admin import (
    log_Handler,
    settings_Handler,
    list_VIP_Users_Handler,
    set_VIP_Variable_Handler,
    create_VIP_Code_Handler,
    # remove_All_VIP_Handler,
    user_Statistic_Handler,
    backup_Handler,
    restore_Handler,
    schedule_command,
    do_Broadcast_Handler,
    set_Variable_Handler,
    set_Daily_Schedule_Handler,
    daily_Schedule_Handler,
    delete_Daily_Schedule_Handler,
    get_Template_Handler,
    set_Template_Handler,
    template_Handler,
    delete_Template_Handler)

from flask import Flask
from threading import Thread
from services.logger import AppLogger
import logging


# flask_app = Flask(__name__)


# @flask_app.route('/')
# def health_check():
#     return "Bot is running!", 200

# def run_flask():
#     flask_app.run(host='0.0.0.0', port=8080)

async def generate_tip_job(context=None) -> str:
    global TIP
    TIP = generate_Tip_Logic()
    if Settings.is_logging():
        logging.info(f"[BOT] TIP updated: {TIP}")
        
async def daily_Task(context):
    # content = get_Daily_Schedule_Logic()
    # if content:
    #     if Settings.is_logging():
    #         logging.info("[Bot] Sending Daily Schedule")
    #     for admin_id in ADMIN_IDS:
    #         await context.bot.send_message(chat_id=admin_id, text=content)
    # else:
    #     if Settings.is_logging():
    #         logging.info("[Bot] Empty Daily Schedule!!!")
    
    await send_Backup_Logic(context)
    waktu.sleep(0.2)
    await send_Log_Logic(context)
    
def main():
    AppLogger.setup()
    init_db()
    init_settings()
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    
    global TIP
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum diset")

 
    
    # print("[SYSTEM] Starting Flask Health Check...")
    # daemon = Thread(target=run_flask, daemon=True)
    # daemon.start()

    # init restore backup
    response = restore_Backup_Logic()
    if response:
        if Settings.is_logging:
            logging.info(response.replace("<b>","").replace("</b>",""))

    if TIP == "Tidak Ada Tips":
        # TIP = generate_Tip_Logic()
        TIP = "Minum air cukup"
        
    if Settings.is_logging():
        logging.info("[BOT] Starting in DEBUG mode (long polling)")

        
    # build application
    app = Application.builder().token(BOT_TOKEN).build()
    app.post_init = on_Startup

    # register handlers
    # USER
    app.add_handler(CommandHandler("start", user_Start_Handler))
    app.add_handler(CommandHandler("ping", ping_Handler))
    
    # USER VIP
    app.add_handler(CommandHandler("getall", send_VIP_All_Package_Handler))
    app.add_handler(CommandHandler("getnew", get_Latest_VIP_Content_Handler))
    
    # ADMIN
    # app.add_handler(CommandHandler("removeallvip", remove_All_VIP_Handler))
    app.add_handler(CommandHandler("userstat", user_Statistic_Handler))
    app.add_handler(CommandHandler("log", log_Handler))
    app.add_handler(CommandHandler("backup", backup_Handler))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.CaptionRegex(r"^/restore"),restore_Handler))   
    app.add_handler(CommandHandler("broadcast",do_Broadcast_Handler))
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/schedule") | filters.Regex(r"^/schedule"),schedule_command))
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/setvariable") | filters.Regex(r"^/setvariable"),set_Variable_Handler))
    
    app.add_handler(CommandHandler("settings", settings_Handler))
    
    app.add_handler(CommandHandler("createvipcode", create_VIP_Code_Handler))
    app.add_handler(CommandHandler("setvipvariable", set_VIP_Variable_Handler))
    app.add_handler(CommandHandler("listvip", list_VIP_Users_Handler))
    
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/setdailyschedule") | filters.Regex(r"^/setdailyschedule"),set_Daily_Schedule_Handler))
    app.add_handler(CommandHandler("showdailyschedule", daily_Schedule_Handler))
    app.add_handler(CommandHandler("deletedailyschedule",delete_Daily_Schedule_Handler))
    
    app.add_handler(CommandHandler("gettemplate",get_Template_Handler))
    app.add_handler(CommandHandler("settemplate",set_Template_Handler))
    app.add_handler(CommandHandler("showtemplate",template_Handler))
    app.add_handler(CommandHandler("deletetemplate",delete_Template_Handler))
    app.add_error_handler(error_handler)

    app.job_queue.run_repeating(generate_tip_job, interval=216000)
    
    tz = pytz.timezone(TIMEZONE)
    scheduled_time = time(hour=0, minute=1, tzinfo=tz)  
    app.job_queue.run_daily(daily_Task, scheduled_time) 
    
    if Settings.is_logging():
        logging.info("[BOT] Bot Running...")
        print("[BOT] Bot Running...")
    
    app.run_polling()

        
if __name__ == "__main__":
    main()
