import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Твой токен (будет из переменных окружения)
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Твой ID админа
ADMIN_IDS = [7871625571]

# Пакеты Telegram Stars
STAR_PACKAGES = {
    "50": {"stars": 50, "price": 79},
    "100": {"stars": 100, "price": 156},
    "200": {"stars": 200, "price": 311},
    "300": {"stars": 300, "price": 465},
    "400": {"stars": 400, "price": 620},
    "500": {"stars": 500, "price": 790},
    "600": {"stars": 600, "price": 930},
    "700": {"stars": 700, "price": 1100},
    "800": {"stars": 800, "price": 1259},
    "900": {"stars": 900, "price": 1400},
    "1000": {"stars": 1000, "price": 1600}
}

# База данных
def init_db():
    conn = sqlite3.connect('stars_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        registration_date TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stars_amount INTEGER,
        price REAL,
        status TEXT DEFAULT 'pending',
        order_date TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Регистрация пользователя
def register_user(user_id, username):
    conn = sqlite3.connect('stars_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, registration_date)
    VALUES (?, ?, ?)
    ''', (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

# Сохранение заказа
def save_order(user_id, stars_amount, price):
    conn = sqlite3.connect('stars_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO orders (user_id, stars_amount, price, order_date)
    VALUES (?, ?, ?, ?)
    ''', (user_id, stars_amount, price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return order_id

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username)
    
    keyboard = [
        [InlineKeyboardButton("⭐ Купить Stars", callback_data="buy_stars")],
        [InlineKeyboardButton("📊 Мои заказы", callback_data="my_orders"),
         InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "🛍️ Магазин Telegram Stars\n"
        "💎 Самые низкие цены\n"
        "📞 Для заказа пиши @M1rnes\n\n"
        "Выбери действие:",
        reply_markup=reply_markup
    )

# Показать пакеты Stars
async def show_star_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "🎁 Выбери пакет Stars:\n\n"
    for stars, info in STAR_PACKAGES.items():
        text += f"⭐ {stars} stars - {info['price']}₽\n"
    
    text += "\n💬 Для заказа пиши @M1rnes"
    
    keyboard = []
    for stars in STAR_PACKAGES.keys():
        keyboard.append([InlineKeyboardButton(
            f"⭐ {stars} stars - {STAR_PACKAGES[stars]['price']}₽", 
            callback_data=f"info_{stars}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

# Информация о пакете
async def show_package_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = query.data.split('_')[1]
    package_info = STAR_PACKAGES[package]
    
    keyboard = [
        [InlineKeyboardButton("💬 Заказать через @M1rnes", url="https://t.me/M1rnes")],
        [InlineKeyboardButton("🔙 Назад", callback_data="buy_stars")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎁 Пакет: ⭐ {package_info['stars']} stars\n"
        f"💰 Цена: {package_info['price']}₽\n\n"
        f"💬 Для заказа:\n"
        f"1. Напиши @M1rnes\n"
        f"2. Укажи пакет: {package} stars\n"
        f"3. Оплати через СБП\n"
        f"4. Получи Stars!\n\n"
        f"⏱️ Обычно отвечаю в течение 5 минут!",
        reply_markup=reply_markup
    )

# Мои заказы
async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    conn = sqlite3.connect('stars_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT stars_amount, price, order_date FROM orders 
    WHERE user_id = ? ORDER BY order_date DESC LIMIT 10
    ''', (user_id,))
    
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        text = "📭 У тебя пока нет заказов\n\n💬 Напиши @M1rnes для первого заказа!"
    else:
        text = "📋 Твои заказы:\n\n"
        for order in orders:
            stars, price, date = order
            text += f"⭐ {stars} stars - {price}₽\n📅 {date[:16]}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

# Помощь
async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "ℹ️ Помощь по покупке Stars\n\n"
        "⭐ <b>Как купить Stars:</b>\n"
        "1. Выбери пакет Stars\n"
        "2. Нажми 'Заказать через @M1rnes'\n"
        "3. Напиши мне в ЛС\n"
        "4. Оплати через СБП\n"
        "5. Получи Stars!\n\n"
        "💳 <b>Оплата:</b>\n"
        "• СБП на карту\n"
        "• Быстро и безопасно\n\n"
        "⏰ <b>Время выдачи:</b>\n"
        "Обычно 5-15 минут после оплаты\n\n"
        "📞 <b>Поддержка:</b>\n"
        "@M1rnes - отвечаю быстро!",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# Главное меню
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⭐ Купить Stars", callback_data="buy_stars")],
        [InlineKeyboardButton("📊 Мои заказы", callback_data="my_orders"),
         InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👋 Главное меню\n\n"
        "Выбери действие:",
        reply_markup=reply_markup
    )

# Основная функция
def main():
    init_db()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    
    # Callback-обработчики
    application.add_handler(CallbackQueryHandler(show_star_packages, pattern="^buy_stars$"))
    application.add_handler(CallbackQueryHandler(show_package_info, pattern="^info_"))
    application.add_handler(CallbackQueryHandler(show_my_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    
    # Запуск
    application.run_polling()

if __name__ == '__main__':
    main()
