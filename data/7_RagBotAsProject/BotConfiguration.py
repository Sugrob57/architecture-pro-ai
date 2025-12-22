import os
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import argparse
from pathlib import Path

class BotConfiguration():
    #def __init__(self):
        
    SUCCESS_KEYWORDS = ["вкус", "послевкуси", "ссылка", "https://t.me"]
    FAILED_KEYWORDS = ["к сожалению", "нет информации"]

    # Настройки фильтрации инъекций
    INJECTION_PATTERNS = [
        # Игнорирование инструкций
        r"(?i)ignore\s+(all\s+)?(previous\s+)?instructions",
        r"(?i)disregard\s+(all\s+)?(previous\s+)?instructions",
        r"(?i)forget\s+(all\s+)?(previous\s+)?instructions",
        
        # Системные команды
        r"(?i)system:\s*",
        r"(?i)assistant:\s*",
        r"(?i)you\s+are\s+now\s+\w+",
        r"(?i)from\s+now\s+on",
        
        # Опасные команды
        r"(?i)output\s+as\s+.*\s+instead",
        r"(?i)pretend\s+you\s+are\s+\w+",
        r"(?i)act\s+as\s+\w+",
        
        # Очистка контекста
        r"(?i)clear\s+(context|memory|history)",
        r"(?i)delete\s+(context|memory|history)",
        
        # Специфичные для пивных данных
        r"(?i)\[.*?\]\s*системное\s+сообщение",
        r"(?i)внутренняя\s+команда",
        r"(?i)admin\s+command",
        
        # Многоязычные паттерны
        r"(?i)игнорируй\s+все\s+инструкции",
        r"(?i)забудь\s+все\s+инструкции",
        r"(?i)пропусти\s+все\s+правила",
    ]

    # Логирование
    LOG_DIR = "./data/7_RagBotAsProject/logs"
    LOG_FILE = "rag_bot_logs.jsonl"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Настройки для автотестов
    TEST_QUESTIONS_FILE = "./data/7_RagBotAsProject/test_questions.txt"
    MIN_ANSWER_LENGTH = 20  # Минимальная длина успешного ответа
    MIN_CHUNK_LENGTH = 10  # Минимальная длина чанка после очистки

    # ========== НАСТРОЙКИ ==========

    CHROMA_DIR = "./data/knowledge-base/chroma_db"
    COLLECTION_NAME = "gooddrink"
    EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
    TOP_K = 4

    # Yandex GPT
    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
    YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
    YANDEX_MODEL = "yandexgpt-lite"