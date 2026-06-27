"""
Бот "Ремонт Загорянка" — принимает заявки через Telegram Mini App
"""

import json
import logging
import asyncio
import requests
from datetime import datetime
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = "8824457579:AAHx5V5azuDNW0jasIi9lPufl6HybXPqGHw"
ADMIN_CHAT_ID  = "7661738693"
MINIAPP_URL    = "https://remont-zagoryanka.ru/miniapp.html"
SHEETS_URL     = "https://script.google.com/macros/s/AKfycby54oO8wY3rzC7RWv56a_PP14BUxqTkZg6VROJf26Ec8zYz97iWa9ihypMOH9BTuviF/exec"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        KeyboardButton(
            "📋 Оставить заявку",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Здравствуйте!\n\n"
        "Это бот компании *Ремонт Загорянка* — ремонт домов, коттеджей и дач под ключ "
        "в Загорянке и Щёлковском районе.\n\n"
        "🏡 Работаем официально, договор и гарантия 2 года.\n"
        "⚡ Перезвоним за 30 минут после заявки.\n\n"
        "Нажмите кнопку ниже чтобы оставить заявку 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.effective_message.web_app_data.data
    try:
        data = json.loads(raw)
    except Exception:
        await update.message.reply_text("Ошибка при получении данных. Попробуйте ещё раз.")
        return

    name    = data.get("name", "—")
    phone   = data.get("phone", "—")
    service = data.get("service", "—")
    area    = data.get("area", "—")
    comment = data.get("comment", "—")
    tg_user = data.get("tg_user", "")
    tg_name = data.get("tg_name", "")

    tg_link = f"@{tg_user}" if tg_user else tg_name or "неизвестен"

    notification = (
        "🔔 *Новая заявка с бота!*\n\n"
        f"👤 *Имя:* {name}\n"
        f"📞 *Телефон:* {phone}\n"
        f"🔧 *Вид работ:* {service}\n"
        f"📐 *Площадь:* {area}\n"
        f"💬 *Комментарий:* {comment}\n"
        f"📱 *Telegram:* {tg_link}\n\n"
        f"⏰ Перезвонить в течение 30 минут!"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=notification,
        parse_mode="Markdown"
    )

    # Записываем в Google Sheets
    try:
        requests.post(SHEETS_URL, json={
            "name":    name,
            "phone":   phone,
            "service": service,
            "area":    area,
            "comment": comment,
            "tg_user": tg_link,
            "source":  "Telegram бот",
            "date":    datetime.now().strftime("%d.%m.%Y %H:%M")
        }, timeout=10)
    except Exception as e:
        logging.warning(f"Sheets error: {e}")

    await update.message.reply_text(
        "✅ *Заявка принята!*\n\n"
        "Перезвоним вам в течение 30 минут.\n"
        "Работаем пн–сб с 8:00 до 20:00.\n\n"
        "Если срочно — звоните: *+7 (999) 123-45-67*",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        KeyboardButton(
            "📋 Оставить заявку",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Для оформления заявки нажмите кнопку ниже 👇\n\n"
        "Или звоните: *+7 (999) 123-45-67*\n"
        "Пн–Сб, 8:00 – 20:00",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Бот запущен!")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
