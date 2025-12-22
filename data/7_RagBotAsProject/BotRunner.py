import os
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import argparse
from pathlib import Path
from BeerSynonymExpander import BeerSynonymExpander
from BotConfiguration import BotConfiguration
from Logger import Logger
from ConsoleMode import ConsoleMode
from TelegramBotMode import TelegramBotMode
from AutoTestMode import AutoTestMode
from RagBot import RAGBot
from OperationMode import OperationMode

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========

def main():
    """Главная функция с парсингом аргументов командной строки"""
    bot_config = BotConfiguration()
    parser = argparse.ArgumentParser(description='RAG-бот по крафтовому пиву')
    parser.add_argument('--mode', type=str, default='console',
                       choices=['console', 'telegram', 'autotest'],
                       help='Режим работы: console (по умолчанию), telegram, autotest')
    parser.add_argument('--test-file', type=str, default=bot_config.TEST_QUESTIONS_FILE,
                       help='Файл с тестовыми вопросами (для режима autotest)')
    parser.add_argument('--stats', action='store_true',
                       help='Показать статистику и выйти')
    
    args = parser.parse_args()
    
    # Инициализируем бота
    bot = RAGBot(bot_config)
    
    # Показываем статистику, если запрошено
    if args.stats:
        stats = bot.logger.get_stats()
        print("\n>>>> Статистика работы бота:")
        print(f"Всего запросов: {stats.get('total_queries', 0)}")
        print(f"Успешных ответов: {stats.get('successful_answers', 0)}")
        print(f"Средняя длина ответа: {stats.get('avg_answer_length', 0):.0f} символов")
        
        if stats.get('queries_by_mode'):
            print("\nЗапросы по режимам:")
            for mode, count in stats['queries_by_mode'].items():
                print(f"  {mode}: {count}")
        return
    
    # Выбираем режим работы
    if args.mode == 'console':
        console_mode = ConsoleMode(bot)
        console_mode.run()
    
    elif args.mode == 'telegram':
        if not bot_config.TELEGRAM_BOT_TOKEN:
            print("Ошибка: Токен Telegram бота не указан.")
            print("Укажите TELEGRAM_BOT_TOKEN в переменных окружения или .env файле")
            return
        
        telegram_mode = TelegramBotMode(bot, bot_config.TELEGRAM_BOT_TOKEN)
        telegram_mode.run()
    
    elif args.mode == 'autotest':
        if args.test_file:
            bot_config.TEST_QUESTIONS_FILE = args.test_file

        autotest_mode = AutoTestMode(bot, bot_config)      
        autotest_mode.run()

if __name__ == "__main__":
    main()