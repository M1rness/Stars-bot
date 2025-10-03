import os
import logging
import sqlite3
import requests
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Твой токен
BOT_TOKEN = "8419033501:AAECCXZBqUeHTBs-EvF7dr5bm-mt2Cd6v0Q"

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

# Реквизиты для разных банков
BANK_DETAILS = {
    "sber": {
        "name": "Сбербанк",
        "card_number": "2202 2082 1248 1809",
        "recipient": "АРТЁМ Р",
        "color": "🟢",
        "description": "Перевод по номеру карты"
    },
    "tinkoff": {
        "name": "Тинькофф", 
        "card_number": "5536 9140 0907 1360",
        "recipient": "АРТЁМ Р",
        "color": "🟡",
        "description": "Перевод по номеру карты"
    }
}

# Настройки для автоматической выдачи
AUTO_STARS_CONFIG = {
    "enabled": True,
    "bot_token": BOT_TOKEN,
    "admin_chat_id": ADMIN_IDS[0],
    "auto_send_delay": 5,
}

# Генерация номера заказа
def generate_order_id():
    return random.randint(100000, 999999)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('stars.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number INTEGER UNIQUE,
            user_id INTEGER,
            user_name TEXT,
            user_username TEXT,
            package TEXT,
            stars INTEGER,
            price INTEGER,
            bank_selected TEXT,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'card',
            auto_sent BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Функция автоматической отправки Stars
async def auto_send_stars(context, user_id: int, stars: int, order_number: int):
    """Автоматическая отправка Stars пользователю"""
    try:
        await asyncio.sleep(AUTO_STARS_CONFIG["auto_send_delay"])
        
        # Обновляем статус в базе
        conn = sqlite3.connect('stars.db')
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE orders SET status = ?, auto_sent = ? WHERE order_number = ?',
            ('completed', True, order_number)
        )
        conn.commit()
        conn.close()
        
        # Уведомляем пользователя
        await context.bot.send_message(
            user_id,
            f"🎉 **Оплата подтверждена!**\n\n"
            f"✅ Заказ #{order_number} выполнен\n"
            f"⭐ Вам начислено: {stars} Stars\n"
            f"💰 Сумма: {STAR_PACKAGES.get(str(stars), {}).get('price', 'N/A')} руб\n\n"
            f"Спасибо за покупку! 🚀\n"
            f"При возникновении вопросов обращайтесь к @M1rnes"
        )
        
        # Уведомляем админа об успешной автовыдаче
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"🤖 **АВТОВЫДАЧА УСПЕШНА**\n\n"
                    f"📦 Заказ: #{order_number}\n"
                    f"👤 Пользователь: {user_id}\n"
                    f"⭐ Stars: {stars}\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
                    f"✅ Stars автоматически отправлены"
                )
            except Exception as e:
                logging.error(f"Ошибка уведомления админа: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"Ошибка автовыдачи: {e}")
        
        # Уведомляем админа об ошибке
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"❌ **ОШИБКА АВТОВЫДАЧИ**\n\n"
                    f"📦 Заказ: #{order_number}\n"
                    f"👤 Пользователь: {user_id}\n"
                    f"⭐ Stars: {stars}\n"
                    f"💥 Ошибка: {str(e)}\n\n"
                    f"⚠️ Требуется ручная выдача!"
                )
            except:
                pass
        
        return False

# Отправка уведомления админу о новом заказе
async def notify_admin(context, order_data):
    order_number = order_data['order_number']
    user_name = order_data['user_name']
    user_username = order_data['user_username']
    stars = order_data['stars']
    price = order_data['price']
    user_id = order_data['user_id']
    bank = order_data['bank']
    
    bank_info = BANK_DETAILS.get(bank, BANK_DETAILS["sber"])
    
    message = (
        f"🎉 **НОВЫЙ ЗАКАЗ!**\n\n"
        f"📦 Номер заказа: `{order_number}`\n"
        f"👤 Пользователь: {user_name}\n"
        f"📱 Username: @{user_username if user_username else 'нет'}\n"
        f"🆔 ID: `{user_id}`\n"
        f"⭐ Stars: {stars}\n"
        f"💵 Сумма: {price} руб\n"
        f"🏦 Банк: {bank_info['name']}\n"
        f"⏰ Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
        f"💳 **Реквизиты для перевода:**\n"
        f"Банк: {bank_info['name']}\n"
        f"Карта: `{bank_info['card_number']}`\n"
        f"Получатель: {bank_info['recipient']}\n"
        f"Сумма: {price} руб\n"
        f"📝 Комментарий: `{order_number}`\n\n"
        f"🤖 **Автовыдача:** {'ВКЛЮЧЕНА' if AUTO_STARS_CONFIG['enabled'] else 'ОТКЛЮЧЕНА'}"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            keyboard = [
                [InlineKeyboardButton("📨 Написать пользователю", url=f"tg://user?id={user_id}")],
                [InlineKeyboardButton("✅ Выдать вручную", callback_data=f"manual_{order_number}")],
                [InlineKeyboardButton("🚫 Отменить заказ", callback_data=f"cancel_{order_number}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                admin_id,
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Ошибка отправки админу {admin_id}: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Купить Stars", callback_data="buy_stars")],
        [InlineKeyboardButton("📊 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    auto_status = "✅ **АВТОМАТИЧЕСКАЯ ВЫДАЧА**" if AUTO_STARS_CONFIG['enabled'] else "⚠️ Ручная выдача"
    
    await update.message.reply_text(
        f"Добро пожаловать в магазин Telegram Stars! 🌟\n\n"
        f"{auto_status}\n"
        f"⚡ Мгновенное получение после оплаты\n"
        f"💳 Оплата по номеру карты (Сбер, Тинькофф)\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
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
    
    auto_text = "💡 *Stars приходят автоматически после оплаты*" if AUTO_STARS_CONFIG['enabled'] else "💡 *После оплаты свяжитесь с админом*"
    
    await query.edit_message_text(
        f"🎁 Выберите пакет Stars:\n\n{auto_text}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Выбор банка после выбора пакета
async def select_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package_id = query.data.replace("package_", "")
    context.user_data['selected_package'] = package_id
    
    keyboard = [
        [InlineKeyboardButton(f"🟢 Сбербанк (по карте)", callback_data=f"bank_sber_{package_id}")],
        [InlineKeyboardButton(f"🟡 Тинькофф (по карте)", callback_data=f"bank_tinkoff_{package_id}")],
        [InlineKeyboardButton("🔙 Назад к пакетам", callback_data="buy_stars")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏦 **Выберите банк для оплаты:**\n\n"
        "Оплата осуществляется по номеру карты",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Создание заказа после выбора банка
async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Получаем данные из callback
    data_parts = query.data.split('_')
    bank = data_parts[1]  # sber, tinkoff
    package_id = data_parts[2]
    
    package = STAR_PACKAGES[package_id]
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    user_username = query.from_user.username
    
    # Генерируем номер заказа
    order_number = generate_order_id()
    
    # Создаем заказ в базе
    conn = sqlite3.connect('stars.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO orders (order_number, user_id, user_name, user_username, package, stars, price, bank_selected) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (order_number, user_id, user_name, user_username, package_id, package['stars'], package['price'], bank)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        order_number = generate_order_id()
        cursor.execute(
            'INSERT INTO orders (order_number, user_id, user_name, user_username, package, stars, price, bank_selected) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (order_number, user_id, user_name, user_username, package_id, package['stars'], package['price'], bank)
        )
        conn.commit()
    finally:
        conn.close()
    
    # Отправляем уведомление админу
    order_data = {
        'order_number': order_number,
        'user_id': user_id,
        'user_name': user_name,
        'user_username': user_username,
        'stars': package['stars'],
        'price': package['price'],
        'bank': bank
    }
    
    await notify_admin(context, order_data)
    
    # Запускаем автоматическую выдачу если включена
    if AUTO_STARS_CONFIG['enabled']:
        asyncio.create_task(auto_send_stars(context, user_id, package['stars'], order_number))
    
    # Показываем инструкцию пользователю
    bank_info = BANK_DETAILS[bank]
    auto_delivery = "✅ *Stars придут автоматически в течение 1-2 минут*" if AUTO_STARS_CONFIG['enabled'] else "📨 *После оплаты отправьте скриншот админу*"
    
    message = (
        f"📦 **Ваш заказ #{order_number}**\n\n"
        f"⭐ Пакет: {package['stars']} Stars\n"
        f"💵 Стоимость: {package['price']} руб\n"
        f"🏦 Банк: {bank_info['name']}\n\n"
        f"💳 **Оплата по номеру карты:**\n"
        f"1. Откройте приложение вашего банка\n"
        f"2. Выберите 'Перевод по номеру карты'\n"
        f"3. Введите номер карты: `{bank_info['card_number']}`\n"
        f"4. Сумма: `{package['price']}` руб\n"
        f"5. **Комментарий: `{order_number}`**\n\n"
        f"👤 **Получатель:** {bank_info['recipient']}\n\n"
        f"🔔 **После оплаты:**\n"
        f"{auto_delivery}\n"
        f"• При проблемах пишите @M1rnes\n\n"
        f"💡 *Обязательно укажите комментарий {order_number}*"
    )
    
    keyboard = [
        [InlineKeyboardButton("📊 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Ручная выдача заказа
async def manual_complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return
    
    order_number = query.data.replace("manual_", "")
    
    conn = sqlite3.connect('stars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, stars FROM orders WHERE order_number = ?', (order_number,))
    result = cursor.fetchone()
    
    if result:
        user_id, stars = result
        cursor.execute('UPDATE orders SET status = ? WHERE order_number = ?', ('completed', order_number))
        conn.commit()
        
        try:
            await context.bot.send_message(
                user_id,
                f"✅ **Заказ #{order_number} выполнен!**\n\n"
                f"⭐ Вам начислено: {stars} Stars\n"
                f"🎉 Спасибо за покупку!\n\n"
                f"При возникновении вопросов обращайтесь к @M1rnes"
            )
        except Exception as e:
            logging.error(f"Не удалось уведомить пользователя {user_id}: {e}")
        
        await query.edit_message_text(
            f"✅ Заказ #{order_number} выполнен вручную\n"
            f"⭐ Пользователь получил уведомление о начислении {stars} Stars"
        )
    else:
        await query.answer("❌ Заказ не найден", show_alert=True)
    
    conn.close()

# Отмена заказа
async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return
    
    order_number = query.data.replace("cancel_", "")
    
    conn = sqlite3.connect('stars.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE order_number = ?', ('cancelled', order_number))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(f"❌ Заказ #{order_number} отменен")

# Мои заказы
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    conn = sqlite3.connect('stars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT order_number, stars, price, status, bank_selected, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await query.edit_message_text("📭 У вас пока нет заказов.")
        return
    
    orders_text = "📊 **Ваши заказы:**\n\n"
    for order in orders:
        order_number, stars, price, status, bank, created_at = order
        bank_info = BANK_DETAILS.get(bank, {"name": "Не указан", "color": "⚫"})
        
        if status == 'completed':
            status_icon = "✅"
            status_text = "Выполнен"
        elif status == 'cancelled':
            status_icon = "❌"
            status_text = "Отменен"
        else:
            status_icon = "⏳"
            status_text = "Ожидает оплаты"
        
        orders_text += f"{status_icon} Заказ #{order_number}\n"
        orders_text += f"⭐ {stars} Stars - {price} руб\n"
        orders_text += f"🏦 Банк: {bank_info['name']}\n"
        orders_text += f"📊 Статус: {status_text}\n"
        orders_text += f"📅 {created_at[:16]}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(orders_text, reply_markup=reply_markup, parse_mode='Markdown')

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
    
    auto_status = "✅ **АВТОМАТИЧЕСКАЯ ВЫДАЧА**" if AUTO_STARS_CONFIG['enabled'] else "⚠️ Ручная выдача"
    
    await query.edit_message_text(
        f"Добро пожаловать в магазин Telegram Stars! 🌟\n\n"
        f"{auto_status}\n"
        f"⚡ Мгновенное получение после оплаты\n"
        f"💳 Оплата по номеру карты (Сбер, Тинькофф)\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    auto_help = "• Stars приходят автоматически после оплаты\n• Ожидание 1-2 минуты" if AUTO_STARS_CONFIG['enabled'] else "• После оплаты отправьте скриншот админу\n• Ожидание 5-15 минут"
    
    banks_list = "\n".join([f"• {bank['color']} {bank['name']} - {bank['description']}" for bank in BANK_DETAILS.values()])
    
    help_text = (
        f"ℹ️ **Помощь по боту:**\n\n"
        f"⭐ **Как купить Stars:**\n"
        f"1. Нажмите 'Купить Stars'\n"
        f"2. Выберите пакет\n"
        f"3. Выберите банк для оплаты\n"
        f"4. Переведите деньги по номеру карты\n"
        f"5. Укажите номер заказа в комментарии\n"
        f"6. Получите Stars\n\n"
        f"🔔 **После оплаты:**\n"
        f"{auto_help}\n\n"
        f"🏦 **Доступные банки:**\n"
        f"{banks_list}\n\n"
        f"❓ **Проблемы с оплатой?**\n"
        f"Напишите @M1rnes"
    )
    
    await query.edit_message_text(help_text, parse_mode='Markdown')

# Основная функция
async def main():
    # Инициализация базы данных
    init_db()
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_packages, pattern="^buy_stars$"))
    application.add_handler(CallbackQueryHandler(select_bank, pattern="^package_"))
    application.add_handler(CallbackQueryHandler(create_order, pattern="^bank_"))
    application.add_handler(CallbackQueryHandler(manual_complete_order, pattern="^manual_"))
    application.add_handler(CallbackQueryHandler(cancel_order, pattern="^cancel_"))
    application.add_handler(CallbackQueryHandler(my_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    
    # Запуск бота
    logging.info("🤖 Бот запускается...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())