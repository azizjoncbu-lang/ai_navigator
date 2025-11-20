import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from rag_query import RAGQuery
import json

load_dotenv()

# RAG tizimini ishga tushirish
try:
    rag = RAGQuery()
    print("✅ RAG tizimi tayyor!")
except Exception as e:
    print(f"❌ RAG tizimini ishga tushirib bo'lmadi: {e}")
    exit(1)

# data.json ni yuklash
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot boshlanganida ishlaydigan funksiya"""
    welcome_message = """🏛 <b>Markaziy Bank Navigator Bot
    Muammoga duch kelsangiz @Husanov00 yoki @palmdemons ga murojat qiling</b>

Assalomu alaykum! Men sizga Markaziy bankning departamentlari va boshqarmalari haqida ma'lumot beraman.

<b>📋 Imkoniyatlar:</b>
• Departamentlar ro'yxatini ko'rish
• Departament va boshqarmalar haqida ma'lumot
• Telefon raqamlar va manzillar
• Rahbarlar haqida ma'lumot

<b>🔍 Qidiruv:</b>
Departament yoki boshqarma nomini yozing va men sizga ma'lumot beraman.

Masalan:
• "Axborot texnologiyalari"
• "Yuridik departament"
• "Inson resurslari"

<b>📱 Buyruqlar:</b>
/start - Botni ishga tushirish
/departments - Barcha departamentlar
/help - Yordam

Boshlash uchun quyidagi tugmalardan birini tanlang yoki so'rov yozing! 👇"""
    
    # Tugmalar
    keyboard = [
        [InlineKeyboardButton("📂 Barcha departamentlar", callback_data="all_departments")],
        [InlineKeyboardButton("🔍 Qidiruv", switch_inline_query_current_chat="")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam buyrug'i"""
    help_text = """ℹ️ <b>Yordam</b>

<b>🎯 Bot qanday ishlaydi?</b>

1️⃣ <b>Departamentlar ro'yxati</b>
   /departments - Barcha departamentlarni ko'rish

2️⃣ <b>Qidiruv</b>
   Departament nomini yozing va enter bosing.
   Masalan: "Axborot texnologiyalari"

3️⃣ <b>Batafsil ma'lumot</b>
   Departament tanlangandan keyin, agar u departamentda boshqarmalar bo'lsa, ularni ko'rasiz.
   Boshqarma tanlab, to'liq ma'lumot olasiz.

<b>📞 Qanday ma'lumotlar mavjud?</b>
• Departament/boshqarma nomi
• Telefon raqami (ichki)
• Joylashuv (qavat, xona)
• Rahbar ismi
• Vazifalar tavsifi

<b>💡 Maslahatlar:</b>
• Qisqa qilib yozing: "IT departamenti" yoki "Yuridik"
• Noto'g'ri yozilsa ham bot tushunadi
• Bir nechta variant bo'lsa, hammasi ko'rsatiladi

Savollar bo'lsa, /start bosing! 🚀"""
    
    keyboard = [[InlineKeyboardButton("🏠 Bosh sahifa", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')

async def show_all_departments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha departamentlarni ko'rsatish"""
    query = update.callback_query
    
    departments_text = "📂 <b>Markaziy Bank Departamentlari</b>\n\n"
    
    keyboard = []
    for i, dept in enumerate(data['departments'], 1):
        departments_text += f"{i}. {dept['name']}\n"
        dept_name_short = dept['name'][:40]
        # dept_ prefixi yo'q, faqat ID
        keyboard.append([InlineKeyboardButton(
            f"{i}. {dept_name_short}...", 
            callback_data=dept['id']  # Faqat ID: dept_01
        )])
    
    keyboard.append([InlineKeyboardButton("🏠 Bosh sahifa", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(departments_text, reply_markup=reply_markup, parse_mode='HTML')

async def show_department_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Departament batafsil ma'lumotini ko'rsatish"""
    query = update.callback_query
    dept_id = query.data  # To'g'ridan-to'g'ri ID: dept_01
    
    print(f"📋 Departament ID: {dept_id}")
    
    # Departamentni topish
    department = None
    for dept in data['departments']:
        if dept['id'] == dept_id:
            department = dept
            break
    
    if not department:
        print(f"❌ Departament topilmadi: {dept_id}")
        print(f"📊 Mavjud departamentlar: {[d['id'] for d in data['departments']]}")
        await query.answer("❌ Departament topilmadi!")
        return
    
    print(f"✅ Departament topildi: {department['name']}")
    
    # Ma'lumotni tayyorlash
    floor_text = department.get('floor', 'N/A')
    room_text = department.get('room', 'N/A')
    
    message = f"""🏢 <b>{department['name']}</b>

📋 <b>Index:</b> {department['index']}
📍 <b>Joylashuv:</b> {floor_text}-qavat, {room_text}-xona
📞 <b>Telefon:</b> {department['phone']}

💼 <b>Tavsif:</b>
{department.get('description', 'Malumot yoq')}
"""
    
    keyboard = []
    
    # Agar boshqarmalar bo'lsa
    if department.get('has_subdivisions', False):
        subdivisions = department.get('subdivisions', [])
        message += f"\n\n📂 <b>Boshqarmalar ({len(subdivisions)}):</b>"
        
        print(f"🔹 Boshqarmalar soni: {len(subdivisions)}")
        
        for subdiv in subdivisions:
            subdiv_name_short = subdiv['name'][:35]
            button_text = f"📁 {subdiv_name_short}..."
            callback_data = subdiv['id']  # Faqat ID: subdiv_01_01
            
            print(f"  ➕ Tugma qo'shildi: {button_text} -> {callback_data}")
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=callback_data
            )])
    else:
        message += "\n\nℹ️ Bu departamentda alohida boshqarmalar mavjud emas."
    
    keyboard.append([InlineKeyboardButton("◀️ Ortga", callback_data="all_departments")])
    keyboard.append([InlineKeyboardButton("🏠 Bosh sahifa", callback_data="start")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        print("✅ Xabar yuborildi")
    except Exception as e:
        print(f"❌ Xabar yuborishda xatolik: {e}")
        raise

async def show_subdivision_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boshqarma batafsil ma'lumotini ko'rsatish"""
    query = update.callback_query
    subdiv_id = query.data  # To'g'ridan-to'g'ri ID: subdiv_01_01
    
    print(f"📁 Boshqarma ID: {subdiv_id}")
    
    # Boshqarmani topish
    subdivision = None
    parent_dept = None
    
    for dept in data['departments']:
        if dept.get('has_subdivisions', False):
            for subdiv in dept.get('subdivisions', []):
                if subdiv['id'] == subdiv_id:
                    subdivision = subdiv
                    parent_dept = dept
                    break
        if subdivision:
            break
    
    if not subdivision:
        print(f"❌ Boshqarma topilmadi: {subdiv_id}")
        await query.answer("❌ Boshqarma topilmadi!")
        return
    
    print(f"✅ Boshqarma topildi: {subdivision['name']}")
    
    # Ma'lumotni tayyorlash
    floor_text = subdivision.get('floor', 'N/A')
    room_text = subdivision.get('room', 'N/A')
    phone_text = subdivision.get('phone', 'N/A')
    head_text = subdivision.get('head', 'Ma\'lumot yo\'q')
    
    message = f"""📁 <b>{subdivision['name']}</b>

🏢 <b>Departament:</b> {parent_dept['name']}

💼 <b>Vazifalar:</b>
{subdivision.get('description', 'Malumot yoq')}

📍 <b>Joylashuv:</b> {floor_text}-qavat, {room_text}-xona
📞 <b>Telefon:</b> {phone_text}
👤 <b>Rahbar:</b> {head_text}
"""
    
    keyboard = [
        [InlineKeyboardButton("◀️ Departamentga qaytish", callback_data=parent_dept['id'])],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        print("✅ Boshqarma ma'lumoti yuborildi")
    except Exception as e:
        print(f"❌ Xabar yuborishda xatolik: {e}")
        raise

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback tugmalarni qayta ishlash"""
    query = update.callback_query
    
    # Debug log
    print(f"🔍 Callback keldi: {query.data}")
    
    try:
        await query.answer()
        
        if query.data == "start":
            await start_callback(update, context)
        elif query.data == "all_departments":
            await show_all_departments(update, context)
        elif query.data == "help":
            await help_command(update, context)
        elif query.data.startswith("dept_"):
            # dept_01, dept_02... uchun
            await show_department_detail(update, context)
        elif query.data.startswith("subdiv_"):
            # subdiv_01_01... uchun
            await show_subdivision_detail(update, context)
        else:
            # Boshqa holatlar (masalan: start, help)
            print(f"⚠️ Standart callback: {query.data}")
            
    except Exception as e:
        print(f"❌ Callback xatosi: {e}")
        import traceback
        traceback.print_exc()
        await query.answer("❌ Xatolik yuz berdi!", show_alert=True)

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start callback uchun"""
    query = update.callback_query
    
    welcome_message = """🏛 <b>Markaziy Bank Navigator Bot</b>

Assalomu alaykum! Men sizga Markaziy bankning departamentlari va boshqarmalari haqida ma'lumot beraman.

Qidiruv uchun departament nomini yozing yoki quyidagi tugmalardan foydalaning! 👇"""
    
    keyboard = [
        [InlineKeyboardButton("📂 Barcha departamentlar", callback_data="all_departments")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi xabarlarini qayta ishlash"""
    user_message = update.message.text
    
    await update.message.reply_text("🔍 Qidiryapman...")
    
    try:
        # RAG orqali javob olish
        answer = rag.generate_answer(user_message)
        
        keyboard = [[InlineKeyboardButton("🏠 Bosh sahifa", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(answer, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        error_message = f"❌ Kechirasiz, xatolik yuz berdi: {str(e)}"
        await update.message.reply_text(error_message)

async def departments_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Departamentlar buyrug'i"""
    departments_text = "📂 <b>Markaziy Bank Departamentlari</b>\n\n"
    
    keyboard = []
    for i, dept in enumerate(data['departments'], 1):
        departments_text += f"{i}. {dept['name']}\n"
        dept_name_short = dept['name'][:40]
        # Faqat ID, dept_ prefixi yo'q
        keyboard.append([InlineKeyboardButton(
            f"{i}. {dept_name_short}...", 
            callback_data=dept['id']  # dept_01
        )])
    
    keyboard.append([InlineKeyboardButton("🏠 Bosh sahifa", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(departments_text, reply_markup=reply_markup, parse_mode='HTML')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatolarni qayta ishlash"""
    print(f"❌ Xatolik: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring yoki /start bosing."
        )

def main():
    """Bot asosiy funksiyasi"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN topilmadi! .env faylini tekshiring.")
        return
    
    print("🚀 Bot ishga tushirilmoqda...")
    
    application = Application.builder().token(token).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("departments", departments_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    print("✅ Bot ishga tushdi!")
    print("📱 Foydalanuvchilardan xabarlar kutilmoqda...")
    print("⛔ To'xtatish uchun Ctrl+C ni bosing.\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()