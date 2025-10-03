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
    "500": {"stars": 500, "price": 775},
    "600": {"stars": 600, "price": 930},
    "700": {"stars": 700, "price": 1085}
}

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('stars.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            package TEXT,
            stars INTEGER,
            price INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Купить Stars", callback_data="buy_stars")],
        [InlineKeyboardButton("📊 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Добро пожаловать в магазин Telegram Stars! 🌟\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

# Показать пакеты Stars
async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for package_id, package in STAR_PACKAGES.items():
        button = InlineKeyboardButton(
            f"{package['stars']} Stars - {package['price']} руб",
            callback_data=f"package_{package_id}"
        )
        keyboard.append([button])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎁 Выберите пакет Stars:",
        reply_markup=reply_markup
    )

# Обработка выбора пакета
async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package_id = query.data.replace("package_", "")
    package = STAR_PACKAGES[package_id]
    
    # Здесь будет логика создания заказа
    await query.edit_message_text(
        f"📦 Вы выбрали:\n"
        f"⭐ {package['stars']} Stars\n"
        f"💵 Стоимость: {package['price']} руб\n\n"
        "Для оплаты свяжитесь с администратором: @ваш_админ"
    )

# Главное меню
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⭐ Купить Stars", callback_data="buy_stars")],
        [InlineKeyboardButton("📊 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Добро пожаловать в магазин Telegram Stars! 🌟\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

# Помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "ℹ️ Помощь:\n\n"
        "• Для покупки Stars нажмите 'Купить Stars'\n"
        "• Выберите подходящий пакет\n"
        "• Следуйте инструкциям для оплаты\n"
        "• При проблемах обращайтесь к @ваш_админ"
    )

# Основная функция
def main():
    # Инициализация базы данных
    init_db()
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_packages, pattern="buy_stars"))
    application.add_handler(CallbackQueryHandler(select_package, pattern="package_"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="back_to_main"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="help"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="my_orders"))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()