

# async def set_Schedule_Handler(update: Update, context: ContextTypes.DEFAULT_TYPE):    
#     if DEBUG:
#         print("[Handlers] Admin: Set Daily Schedule")
        
#     user_id = update.effective_user.id
#     if not is_admin(user_id):
#         await update.message.reply_text("⛔ Kamu bukan admin.")
#         return
    
#     if len(context.args) < 2:
#         await update.message.reply_text("Format: /schedule YYYY-MM-DD HH:MM <pesan>")
#         return
    
#     msg = await update.message.reply_text("<i>Tunggu Sebentar...</i>",parse_mode="HTML")

#     # Ambil 2 arg pertama sebagai tanggal & jam
#     date_str = context.args[0]
#     time_str = context.args[1]
    
#     dt_str = f"{date_str} {time_str}"
#     tz = pytz.timezone(TIMEZONE)
#     dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
#     waktu = dt - datetime.now(tz)
    
#     content = " ".join(context.args[2:])
  
#     # Schedule job sekali jalan
#     context.job_queue.run_once(
#         callback=scheduled_job,
#         when=waktu.total_seconds(),
#         data={
#             "chat_id": ADMIN_IDS,
#             "message": content
#         }
#     )
    
#     # set_Daily_Schedule_Logic(content,waktu)
#     await msg.delete()
#     await update.message.reply_text(f"Task scheduled at {dt.strftime('%Y-%m-%d %H:%M')}")
#     await update.message.reply_text(content)
    
    
    
    
    