import config, logging, pytz
import time as waktu
from datetime import time
from telegram import Update
from handlers import user, admin
from services import logic
from services.database import init_db
from services.settings import Settings
from services.logger import AppLogger
from telegram.ext import Application, CommandHandler, MessageHandler, filters, TypeHandler, CallbackQueryHandler

# from flask import Flask
# from threading import Thread


# flask_app = Flask(__name__)


# @flask_app.route('/')
# def health_check():
#     return "Bot is running!", 200

# def run_flask():
#     flask_app.run(host='0.0.0.0', port=8080)



async def generate_tip_job(context=None) -> str:
    tips = logic.Logic_Generate_Tips()
    Settings.set("tips", config.TIPS)
    if Settings.is_logging():
        logging.info(f"[BOT] TIP updated: {config.TIPS}")
        
async def daily_Task(context):
    # content = logic.Logic_Get_Daily_Schedule()
    # if content:
    #     if Settings.is_logging():
    #         logging.info("[Bot] Sending Daily Schedule")
    #     for admin_id in config.ADMIN_IDS:
    #         await context.bot.send_message(chat_id=admin_id, text=content)
    # else:
    #     if Settings.is_logging():
    #         logging.info("[Bot] Empty Daily Schedule!!!")
    
    file, info = logic.Logic_Setup_Backup()  
    
    await logic.Logic_Send_Backup_To_Admin(context, file, info)
    waktu.sleep(0.2)
    await logic.Logic_Send_Log(context)
    waktu.sleep(0.2)
    await logic.Logic_Send_Backup_To_Channel(context, file, info)
    
def main():
    AppLogger.setup()
    init_db()
    logic.Logic_init_settings()
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext._jobqueue").setLevel(logging.CRITICAL)
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
    
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum diset")

    # print("[SYSTEM] Starting Flask Health Check...")
    # daemon = Thread(target=run_flask, daemon=True)
    # daemon.start()

    # init restore backup

    if Settings.get("tips") == "Tidak Ada Tips":
        # Settings.set("tips",logic.Logic_Generate_Tips())
        pass
        
    if Settings.is_logging():
        logging.info("[BOT] Starting in DEBUG mode (long polling)")

        
    # build application
    app = Application.builder().token(config.BOT_TOKEN).concurrent_updates(True).build()
    app.post_init = logic.Logic_On_Startup

    # Maintenance Handler
    app.add_handler(TypeHandler(Update, user.Handler_Maintenance), group=-1)
    app.add_handler(CallbackQueryHandler(user.Handler_Join_Refresh_Callback, pattern=r"^refresh:"))
    
    # register handlers
    # USER
    app.add_handler(CommandHandler("start", user.Handler_User_Start, block=False))
    app.add_handler(CommandHandler("ping", user.Handler_Ping, block=False))
    app.add_handler(CommandHandler("tutorial", user.Handler_Tutorial, block=False))
    
    # USER VIP
    app.add_handler(CommandHandler("getall", user.Handler_Send_VIP_All_Package, block=False))
    app.add_handler(CommandHandler("getnew", user.Handler_Get_Latest_VIP_Content, block=False))
    
    # ADMIN
    # app.add_handler(CommandHandler("removeallvip", remove_All_VIP_Handler))
    app.add_handler(CommandHandler("userstat", admin.Handler_User_Statistic))
    app.add_handler(CommandHandler("log", admin.Handler_Log))
    app.add_handler(CommandHandler("backup", admin.Handler_Backup))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.CaptionRegex(r"^/restore"),admin.Handler_Restore))   
    app.add_handler(CommandHandler("broadcast",admin.Handler_Do_Broadcast))
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/schedule") | filters.Regex(r"^/schedule"),admin.Handler_Schedule_Command))
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/setvariable") | filters.Regex(r"^/setvariable"),admin.Handler_Set_Variable))
    
    app.add_handler(CommandHandler("settings", admin.Handler_Settings))
    app.add_handler(CommandHandler("maintenance", admin.Handler_Set_Maintenance))
    
    app.add_handler(CommandHandler("createvipcode", admin.Handler_Create_VIP_Code))
    app.add_handler(CommandHandler("setvipvariable", admin.Handler_Set_VIP_Variable))
    app.add_handler(CommandHandler("listvip", admin.Handler_List_VIP_Users))
    
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/setdailyschedule") | filters.Regex(r"^/setdailyschedule"),admin.Handler_Set_Daily_Schedule))
    app.add_handler(CommandHandler("showdailyschedule", admin.Handler_Daily_Schedule))
    app.add_handler(CommandHandler("deletedailyschedule",admin.Handler_Delete_Daily_Schedule))
    
    app.add_handler(CommandHandler("gettemplate",admin.Handler_Get_Template))
    app.add_handler(CommandHandler("settemplate",admin.Handler_Set_Template))
    app.add_handler(CommandHandler("showtemplate",admin.Handler_Template))
    app.add_handler(CommandHandler("deletetemplate",admin.Handler_Delete_Template))
    app.add_error_handler(logic.Logic_error_handler)

    app.job_queue.run_repeating(generate_tip_job, interval=216000)
    app.job_queue.run_repeating(logic.Logic_Backup_To_Channel_Job, interval=3600)
    app.job_queue.run_repeating(logic.Logic_Cek_Request, interval=2)
    tz = pytz.timezone(config.TIMEZONE)
    scheduled_time = time(hour=0, minute=1, tzinfo=tz)  
    app.job_queue.run_daily(daily_Task, scheduled_time) 
    
    if Settings.is_logging():
        logging.info("[BOT] Bot Running...")
        print("[BOT] Bot Running...")
    
    app.run_polling()

        
if __name__ == "__main__":
    main()
