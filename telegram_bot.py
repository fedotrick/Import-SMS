import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram_import import import_message_to_excel

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота - должен быть передан как параметр или загружен из переменной окружения
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замените на реальный токен бота


class TelegramImportBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self.help))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_message = (
            "Привет! Это бот для импорта данных о плавках в электронный журнал.\n\n"
            "Просто отправьте мне сообщение со статистикой по смене, и я импортирую его в Excel файл.\n\n"
            "Формат сообщения должен содержать:\n"
            "- 📅 Дата: дата смены\n"
            "- 👨‍💼 Старший: имя старшего смены\n"
            "- 👥 Участники: список участников\n"
            "- Данные по плавкам с указанием:\n"
            " - Плавка (учетный номер)\n"
            "  - 🏷️ Кластер\n"
            "  - 🏭 Отливка\n"
            "  - ⚙️ Литниковая система\n"
            "  - 📦 Опоки\n"
            "  - 🌡️ Температура\n"
            "  - ⏰ Время заливки\n"
            "  - 💬 Комментарий\n\n"
            "Используйте команду /help для получения дополнительной информации."
        )
        await update.message.reply_text(welcome_message)
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = (
            "Инструкция по использованию бота:\n\n"
            "1. Подготовьте сообщение со статистикой по смене в следующем формате:\n\n"
            "📅 Дата: 01.11.2025\n"
            "👨‍💼 Старший: Петров\n"
            "👥 Участники (4):\n"
            "• Иванов\n"
            "• Сидоров\n"
            "• Козлов\n"
            "• Новиков\n\n"
            "🔥 ДЕТАЛИ ПЛАВОК:\n"
            "✅ 1. Плавка 11-001/25\n"
            "🏷️ Кластер: 5\n"
            "🏭 Отливка: Вороток\n"
            "⚙️ Литниковая система: Бумага\n"
            "📦 Опоки: 123, 124, 125, 126\n"
            "🌡️ Температура: 1550°C\n"
            "⏰ Время заливки: 14:30\n"
            "💬 Комментарий: Нормальная плавка\n"
            "📋 Маршрутная карта: 12345\n"
            "2. Отправьте это сообщение боту.\n"
            "3. Бот импортирует данные в Excel файл и сообщит о результате."
        )
        await update.message.reply_text(help_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        message_text = update.message.text
        user = update.effective_user
        
        logger.info(f"Получено сообщение от {user.username or user.first_name}: {message_text[:100]}...")
        
        try:
            # Импортируем сообщение в Excel
            success, result_message = import_message_to_excel(message_text)
            
            if success:
                response = f"✅ Успешно импортировано: {result_message}"
            else:
                response = f"❌ Ошибка при импорте: {result_message}"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            await update.message.reply_text(f"❌ Произошла ошибка при обработке сообщения: {str(e)}")
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск телеграм бота...")
        self.application.run_polling()


def main():
    """Основная функция для запуска бота"""
    # В реальном приложении токен должен быть загружен из переменной окружения
    bot_token = BOT_TOKEN
    if bot_token == "YOUR_BOT_TOKEN_HERE":
        print("Пожалуйста, укажите реальный токен бота в переменной BOT_TOKEN")
        return
    
    bot = TelegramImportBot(bot_token)
    bot.run()


if __name__ == "__main__":
    main()