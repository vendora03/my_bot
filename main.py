import asyncio,pytz
from datetime import datetime,time
from telegram.ext import Application,CommandHandler,MessageHandler, filters
from services.database import init_db
from services.logic import error_handler,on_Startup, restore_Backup_Logic,generate_Tip_Logic,get_Daily_Schedule_Logic
from handlers.user import user_Start_Handler,ping_Handler,send_VIP_All_Package_Handler,get_Latest_VIP_Content_Handler
from config import BOT_TOKEN, DEBUG, TIP, ADMIN_IDS, TIMEZONE
from handlers.admin import (
    list_VIP_Users_Handler,
    set_VIP_Variable_Handler,
    create_VIP_Code_Handler,
    remove_All_VIP_Handler,
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

flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    # Koyeb secara default membaca port 8080
    flask_app.run(host='0.0.0.0', port=8080)

async def generate_tip_job(context=None) -> str:
    global TIP
    TIP = generate_Tip_Logic()
    if DEBUG:
        print(f"[BOT] TIP updated: {TIP}")
        
async def daily_Task(context):
    content = get_Daily_Schedule_Logic()
    if content:
        print("[Bot] Sending Daily Schedule")
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin_id, text=content)
    else:
        print("[Bot] Empty Daily Schedule!!!")
    
def main():
    global TIP
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum diset")

    # init database
    init_db()
    
    print("[SYSTEM] Starting Flask Health Check...")
    daemon = Thread(target=run_flask, daemon=True)
    daemon.start()

    # init restore backup
    response = restore_Backup_Logic()
    if response:
        print(response.replace("<b>","").replace("</b>",""))

    if TIP == "Tidak Ada Tips":
        # TIP = generate_Tip_Logic()
        TIP = "Minum air cukup"
        
    if DEBUG:
        print("[BOT] Starting in DEBUG mode (long polling)")

        
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
    app.add_handler(CommandHandler("removeallvip", remove_All_VIP_Handler))
    app.add_handler(CommandHandler("userstat", user_Statistic_Handler))
    app.add_handler(CommandHandler("backup", backup_Handler))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.CaptionRegex(r"^/restore"),restore_Handler))   
    app.add_handler(CommandHandler("broadcast",do_Broadcast_Handler))
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/schedule") | filters.Regex(r"^/schedule"),schedule_command))
    app.add_handler(MessageHandler(filters.CaptionRegex(r"^/setvariable") | filters.Regex(r"^/setvariable"),set_Variable_Handler))
    
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
    scheduled_time = time(hour=21, minute=36, tzinfo=tz)  
    app.job_queue.run_daily(daily_Task, scheduled_time) 
    
    if DEBUG:
        print("[BOT] Bot Running...")
    
    app.run_polling()

        
if __name__ == "__main__":
    main()
