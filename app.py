# --- إدارة الملفات ---
@bot.callback_query_handler(func=lambda c: c.data == "my_files")
def my_files(call):
    uid = str(call.from_user.id)
    db = load_db()
    user_files = db["users"].get(uid, {})

    if not user_files:
        return bot.answer_callback_query(call.id, "❌ ليس لديك ملفات مرفوعة.")

    kb = types.InlineKeyboardMarkup()
    for fname, info in user_files.items():
        status_icon = "⏳" if info["status"] == "pending" else "✅"
        kb.add(types.InlineKeyboardButton(f"{status_icon} {fname}", callback_data=f"manage_{fname}"))
    
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text("📂 إليك قائمة ملفاتك:", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("manage_"))
def manage_file(call):
    fname = call.data.split("_")[1]
    uid = str(call.from_user.id)
    db = load_db()
    file_info = db["users"][uid].get(fname)

    kb = types.InlineKeyboardMarkup()
    if file_info["status"] == "approved":
        kb.add(
            types.InlineKeyboardButton("▶️ تشغيل", callback_data=f"run_{fname}"),
            types.InlineKeyboardButton("⏹ إيقاف", callback_data=f"stop_{fname}")
        )
    kb.add(types.InlineKeyboardButton("🗑️ حذف الملف", callback_data=f"del_{fname}"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="my_files"))

    bot.edit_message_text(f"🛠 إدارة الملف: {fname}\nالحالة: {file_info['status']}", 
                          call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# --- تنفيذ الأوامر (Run, Stop, Delete) ---
@bot.callback_query_handler(func=lambda c: True)
def handle_all_callbacks(call):
    uid = str(call.from_user.id)
    data = call.data

    # موافقة الأدمن
    if data.startswith("adm_app_"):
        _, _, target_uid, fname = data.split("_")
        db = load_db()
        db["users"][target_uid][fname]["status"] = "approved"
        save_db(db)
        bot.send_message(target_uid, f"✅ وافق المطور على ملفك {fname}. يمكنك الآن تشغيله من 'ملفاتي'.")
        bot.edit_message_caption("✅ تمت الموافقة بنجاح", call.message.chat.id, call.message.message_id)

    elif data == "back_home":
        bot.edit_message_text("🏠 القائمة الرئيسية", call.message.chat.id, call.message.message_id, reply_markup=main_markup())

    elif data.startswith("run_"):
        fname = data.split("_")[1]
        path = os.path.join(UPLOAD_DIR, uid, fname)
        if path in running_processes:
            return bot.answer_callback_query(call.id, "⚠️ الملف يعمل بالفعل!")
        
        proc = subprocess.Popen([sys.executable, path])
        running_processes[path] = proc
        bot.answer_callback_query(call.id, "🚀 تم بدء التشغيل بنجاح", show_alert=True)

    elif data.startswith("stop_"):
        fname = data.split("_")[1]
        path = os.path.join(UPLOAD_DIR, uid, fname)
        if path in running_processes:
            running_processes[path].terminate()
            del running_processes[path]
            bot.answer_callback_query(call.id, "⏹ تم إيقاف الملف", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ الملف ليس قيد التشغيل")

    elif data.startswith("del_"):
        fname = data.split("_")[1]
        path = os.path.join(UPLOAD_DIR, uid, fname)
        if path in running_processes:
            running_processes[path].terminate()
            del running_processes[path]
        
        if os.path.exists(path): os.remove(path)
        db = load_db()
        if fname in db["users"][uid]:
            del db["users"][uid][fname]
            save_db(db)
        bot.answer_callback_query(call.id, "🗑️ تم الحذف")
        my_files(call)

# --- التشغيل ---
if name == "main":
    # تشغيل سيرفر الويب في خلفية منفصلة
    threading.Thread(target=run_web_server, daemon=True).start()
    print("🚀 السيرفر يعمل على منفذ 8080...")
    print("🤖 البوت يعمل الآن...")
    bot.infinity_polling()
