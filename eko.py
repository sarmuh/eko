import logging
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from savol import questions  # savol.py faylidan questions ro'yxatini import qilish

# Logging sozlamalari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Asosiy menyuni inline klaviatura sifatida ko'rsatish
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🚀 Bosh Menyu", callback_data="/start"), InlineKeyboardButton("🤝 Yordam", callback_data="/help")],
        [InlineKeyboardButton("🧠 Testni boshlash", callback_data="/quiz"), InlineKeyboardButton("📊 Statistika", callback_data="/stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start buyrug'i: KI guruhiga xush kelibsiz xabari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name if user.first_name else user.username if user.username else "Foydalanuvchi"
    welcome_message = (
        f"🇺🇿 Assalomu alaykum, {user_name}! AMI-222 guruhi a'zolari uchun Dinshunoslik fanidan yakuniy imtihonga tayyorlanish botiga xush kelibsiz! 🎓\n\n"
        "🔹 25 ta tasodifiy savoldan iborat test boshlash uchun Testni boshlash tugmasiga bosing\n"
    )
    query = update.callback_query
    if query:
        await query.message.reply_text(welcome_message, reply_markup=get_main_menu())
        await query.answer()
    else:
        await update.message.reply_text(welcome_message, reply_markup=get_main_menu())

# Yordam buyrug'i
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "📚 Bot yordami:\n\n"
        "🔹 /start - Botni qayta ishga tushirish va xush kelibsiz xabarini ko'rish\n"
        "🔹 /quiz - 25 ta tasodifiy savoldan iborat test boshlash\n"
        "🔹 /stats - Umumiy statistikangizni ko'rish\n\n"
        "Bot faqat kiritilgan savollardan foydalanadi va har doim tasodifiy tartibda taqdim etadi."
    )
    query = update.callback_query
    if query:
        await query.message.reply_text(help_message, reply_markup=get_main_menu())
        await query.answer()
    else:
        await update.message.reply_text(help_message, reply_markup=get_main_menu())

# Statistika buyrug'i
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data.get('stats', {'tests': 0, 'total_correct': 0, 'best_score': 0})
    tests = user_data['tests']
    total_correct = user_data['total_correct']
    best_score = user_data['best_score']

    if tests == 0:
        message = "📊 Hozircha hech qanday statistika yo'q. /quiz orqali testni boshlang!"
    else:
        possible_total_questions_per_test = 25
        possible_total_questions = tests * possible_total_questions_per_test
        avg_score = (total_correct / possible_total_questions) * 100 if possible_total_questions > 0 else 0
        best_score_points = best_score * 2  # Eng yaxshi natijani ball sifatida ko'rsatish

        message = (
            f"📊 Sizning statistikangiz:\n\n"
            f"🔢 Jami testlar soni: {tests}\n"
            f"✅ Jami to'g'ri javoblar: {total_correct}/{possible_total_questions}\n"
            f"📈 O'rtacha ball: {avg_score:.2f}%\n"
            f"🏆 Eng yaxshi natija: {best_score}/{possible_total_questions_per_test} (Ball: {best_score_points}/{possible_total_questions_per_test * 2})\n\n"
            f"🔄 Yana sinab ko'rish uchun Testni boshlashni bosing!"
        )

    query = update.callback_query
    if query:
        await query.message.reply_text(message, reply_markup=get_main_menu())
        await query.answer()
    else:
        await update.message.reply_text(message, reply_markup=get_main_menu())

# Quiz buyrug'i: 25 ta savol
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    required_questions_count = 25
    if len(questions) < required_questions_count:
        message = f"❌ Savollar ro'yxati yetarli emas. Testni boshlash uchun kamida {required_questions_count} ta savol bo'lishi kerak. Hozirda {len(questions)} ta savol bor. Iltimos, savollar faylini tekshiring."
        query = update.callback_query
        if query:
            await query.message.reply_text(message, reply_markup=get_main_menu())
            await query.answer()
        else:
            await update.message.reply_text(message, reply_markup=get_main_menu())
        return

    context.user_data['index'] = 0
    context.user_data['answers'] = []
    context.user_data['shuffled'] = random.sample(questions, required_questions_count)

    start_message = "Quiz boshlandi! 🧠"
    query = update.callback_query
    if query:
        await query.message.reply_text(start_message)
        await query.answer()
        await send_question(query.message, context)
    else:
        await update.message.reply_text(start_message)
        await send_question(update.message, context)

# Test yakunlanganda statistikani yangilash va ko'rsatish
# Test yakunlanganda statistikani yangilash va ko'rsatish
async def send_question(message, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data.get('index', 0)
    shuffled_questions = context.user_data.get('shuffled', [])
    total_questions_in_quiz = len(shuffled_questions)

    if index >= total_questions_in_quiz:
        correct = sum(1 for a in context.user_data['answers'] if a.get('is_correct', False))
        score = correct * 2  # Har bir to'g'ri javob uchun 2 ball
        percentage = (correct / total_questions_in_quiz) * 100 if total_questions_in_quiz > 0 else 0

        # Statistikani yangilash
        user_data = context.user_data.get('stats', {'tests': 0, 'total_correct': 0, 'best_score': 0})
        user_data['tests'] = user_data.get('tests', 0) + 1
        user_data['total_correct'] = user_data.get('total_correct', 0) + correct
        user_data['best_score'] = max(user_data.get('best_score', 0), correct)
        context.user_data['stats'] = user_data

        # Natija xabari - yangi va tushunarli format
        result_message = (
            "🎉 *Test Yakunlandi!* 🎉\n\n"
            f"📝 *Jami savollar soni:* {total_questions_in_quiz}\n"
            f"✅ *To'g'ri javoblar:* {correct}\n"
            f"❌ *Noto'g'ri javoblar:* {total_questions_in_quiz - correct}\n"
            f"📊 *Foiz:* {percentage:.1f}%\n"
            f"⭐ *Ball:* {score}/{total_questions_in_quiz * 2}\n\n"
        )

        # Baholash tizimi qo'shamiz
        if percentage >= 90:
            result_message += "💎 *A'lo!* Siz juda yaxshi bilasiz!\n"
        elif percentage >= 70:
            result_message += "👍 *Yaxshi!* Yaxshi natija ko'rsatdingiz!\n"
        elif percentage >= 50:
            result_message += "😊 *Qoniqarli!* Yana bir bor urinib ko'ring!\n"
        else:
            result_message += "📚 *Qayta o'rganish kerak!* Yaxshiroq tayyorlaning!\n"

        result_message += "\n🔄 Yangi test boshlash uchun /quiz buyrug'ini yuboring"

        # Ma'lumotlarni tozalash
        keys_to_clear = ['index', 'answers', 'shuffled', 'current_question_text',
                         'current_options_data', 'correct_answer_text',
                         'current_message_id', 'current_chat_id']
        for key in keys_to_clear:
            if key in context.user_data:
                del context.user_data[key]

        # Tugmalar bilan birga yuborish
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yangi Test", callback_data="/quiz")],
            [InlineKeyboardButton("📊 Statistika", callback_data="/stats"),
             InlineKeyboardButton("🏠 Bosh Menyu", callback_data="/start")]
        ])

        await message.reply_text(result_message, reply_markup=reply_markup, parse_mode='Markdown')
        return

    question_full_text = shuffled_questions[index]
    lines = question_full_text.strip().split('\n')

    question_text_lines = []
    option_lines = []
    found_options_start = False

    for line in lines:
        stripped_line_for_check = line.strip().lstrip('*').strip()
        if stripped_line_for_check.startswith(('A)', 'B)', 'C)', 'D)')):
            found_options_start = True
            option_lines.append(line)
        elif not found_options_start:
            question_text_lines.append(line)

    question_text = "\n".join(question_text_lines).strip()
    options_raw = option_lines

    if not options_raw:
        logger.error(f"Could not parse options for question at index {index}: {question_full_text}")
        await message.reply_text(f"❌ Savol №{index + 1}ni tahlil qilishda xato yuz berdi. Keyingi savolga o'tilmoqda.", reply_markup=get_main_menu())
        context.user_data['index'] += 1
        context.user_data['answers'].append({
            'question': question_text if question_text else question_full_text[:100] + ("..." if len(question_full_text) > 100 else ""),
            'correct': "Noma'lum",
            'is_correct': False,
            'user_answer': "Tahlil xatosi"
        })
        await send_question(message, context)
        return

    options_data_for_shuffle = []
    correct_option_text = None

    for opt_line in options_raw:
        is_correct = opt_line.strip().startswith('*')
        cleaned_line = opt_line.strip().lstrip('*').strip()

        option_text = cleaned_line
        if len(cleaned_line) > 1 and cleaned_line[0].isalpha() and cleaned_line[1] == ')':
            if len(cleaned_line) > 2 and cleaned_line[2] == ' ':
                option_text = cleaned_line[3:].strip()
            else:
                option_text = cleaned_line[2:].strip()

        options_data_for_shuffle.append((option_text, is_correct))
        if is_correct:
            correct_option_text = option_text

    if correct_option_text is None:
        logger.error(f"Could not find correct option text for question at index {index}: {question_full_text}")
        await message.reply_text(f"❌ Savol №{index + 1}ning to'g'ri javobini aniqlashda xato. Keyingi savolga o'tilmoqda.", reply_markup=get_main_menu())
        context.user_data['index'] += 1
        context.user_data['answers'].append({
            'question': question_text if question_text else question_full_text[:100] + ("..." if len(question_full_text) > 100 else ""),
            'correct': 'Aniqlanmadi',
            'is_correct': False,
            'user_answer': "Format xatosi (to'g'ri javob yo'q)"
        })
        await send_question(message, context)
        return

    random.shuffle(options_data_for_shuffle)

    context.user_data['current_question_text'] = question_text
    context.user_data['current_options_data'] = options_data_for_shuffle
    context.user_data['correct_answer_text'] = correct_option_text

    keyboard = [[InlineKeyboardButton(opt_text, callback_data=f"answer_{i}")]
                for i, (opt_text, is_correct_flag) in enumerate(options_data_for_shuffle)]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        sent_message = await message.reply_text(
            f"❓ Savol {index + 1}/{total_questions_in_quiz}:\n{question_text}",
            reply_markup=reply_markup
        )
        context.user_data['current_message_id'] = sent_message.message_id
        context.user_data['current_chat_id'] = sent_message.chat_id

    except Exception as e:
        logger.error(f"Savol yuborishda xato: {e}")
        await message.reply_text("❌ Savolni ko'rsatishda texnik xato yuz berdi. Iltimos, /quiz ni qayta ishlatib ko'ring.", reply_markup=get_main_menu())
        if 'index' in context.user_data:
            error_question_text = context.user_data.get('current_question_text', context.user_data.get('shuffled', [f"Savol #{index+1}"]))
            error_correct_answer = context.user_data.get('correct_answer_text', 'Aniqlanmadi')
            context.user_data['answers'].append({
                'question': error_question_text if isinstance(error_question_text, str) else str(error_question_text)[:100] + ("..." if len(str(error_question_text)) > 100 else ""),
                'correct': error_correct_answer,
                'is_correct': False,
                'user_answer': "Ko'rsatish xatosi"
            })
            context.user_data['index'] += 1

# Inline tugma bosilganda javob qayta ishlash
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    await query.answer()

    if data in ["/start", "/help", "/quiz", "/stats"]:
        if data == "/start":
            await start(update, context)
        elif data == "/help":
            await help_command(update, context)
        elif data == "/quiz":
            keys_to_clear = ['index', 'answers', 'shuffled', 'current_question_text',
                            'current_options_data', 'correct_answer_text',
                            'current_message_id', 'current_chat_id']
            for key in keys_to_clear:
                if key in context.user_data:
                    del context.user_data[key]
            await quiz(update, context)
        elif data == "/stats":
            await stats(update, context)
        return

    if data.startswith("answer_") and 'current_question_text' in context.user_data and 'current_options_data' in context.user_data:
        try:
            option_index = int(data.split("_")[1])
            if 0 <= option_index < len(context.user_data['current_options_data']):
                chosen_option_text, chosen_is_correct = context.user_data['current_options_data'][option_index]
                is_correct = chosen_is_correct
                user_answer = chosen_option_text
                question_text = context.user_data.get('current_question_text', 'Savol matni topilmadi')
                correct_answer_text = context.user_data.get('correct_answer_text', "'To'g'ri javob topilmadi'")

                context.user_data['answers'].append({
                    'question': question_text,
                    'correct': correct_answer_text,
                    'is_correct': is_correct,
                    'user_answer': user_answer
                })
                context.user_data['index'] += 1

                if is_correct:
                    await query.message.reply_text("✅ To'g'ri javob! Keyingi savolga o'ting.")
                else:
                    await query.message.reply_text(f"❌ Noto'g'ri. To'g'ri javob: {correct_answer_text}")

                await send_question(query.message, context)

            else:
                logger.error(f"Invalid option index ({option_index}) in callback data: {data}")
                await query.message.reply_text("❌ Noto'g'ri variant tanlandi. Iltimos, qayta urinib ko'ring.", reply_markup=get_main_menu())

        except Exception as e:
            logger.error(f"Error processing answer callback: {e}")
            await query.message.reply_text("❌ Javobni qayta ishlashda texnik xato yuz berdi. Iltimos, /quiz ni qayta ishlatib ko'ring.", reply_markup=get_main_menu())
            if 'index' in context.user_data and 'current_question_text' in context.user_data:
                error_question_text = context.user_data.get('current_question_text', 'Savol matni topilmadi')
                error_correct_answer = context.user_data.get('correct_answer_text', 'Aniqlanmadi')
                context.user_data['answers'].append({
                    'question': error_question_text,
                    'correct': error_correct_answer,
                    'is_correct': False,
                    'user_answer': "Qayta ishlash xatosi"
                })
                context.user_data['index'] += 1
                await send_question(query.message, context)

    else:
        logger.warning(f"Unknown callback query received: {data}")
        await query.message.reply_text("❓ Noma'lum buyruq yoki holat. Iltimos, menyudan foydalaning.", reply_markup=get_main_menu())

# Xato boshqaruvi
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} xato keltirib chiqardi: {context.error}")
    error_message = "❌ Kutilmagan xato yuz berdi. Iltimos, qaytadan urinib ko'ring yoki /help ni bosing."
    try:
        if update.effective_message:
            await update.effective_message.reply_text(error_message, reply_markup=get_main_menu())
        elif update.effective_chat:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message, reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Xato xabarini yuborishda ham xato yuz berdi: {e}")

# Asosiy funksiya
def main():
    try:
        application = ApplicationBuilder().token("8160423747:AAEkMiIsS_MQfXW5ZiWU9qQnTQGYbhJfOEs").build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("quiz", quiz))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats))
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_error_handler(error_handler)
        logger.info("Bot muvaffaqiyatli ishga tushdi. Polling boshlanmoqda...")
        application.run_polling(poll_interval=3)
    except Exception as e:
        logger.critical(f"Botni ishga tushirishda xato: {e}")

if __name__ == "__main__":
    main()