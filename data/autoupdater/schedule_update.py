import time
import schedule
from data_loader import IndexUpdater
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_update():
    """Запуск обновления индекса."""
    try:
        logger.info("Запуск запланированного обновления индекса...")
        updater = IndexUpdater()
        stats = updater.update_index()
        logger.info(f"Обновление завершено: {stats}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении индекса: {e}")

def main():
    """Основная функция планировщика."""
    # Запускаем обновление сразу при старте
    run_update()
    
    # Настраиваем расписание (например, каждые 10 минут)
    schedule.every(10).minutes.do(run_update)
    
    # Или каждые 3 часа
    # schedule.every(3).hours.do(run_update)
    
    # Или каждый день в полночь
    # schedule.every().day.at("00:00").do(run_update)
    
    logger.info("Планировщик обновления запущен. Ctrl+C для остановки.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверяем расписание каждую минуту
    except KeyboardInterrupt:
        logger.info("Планировщик остановлен")

if __name__ == "__main__":
    main()