import os
import requests
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from pathlib import Path
from BotConfiguration import BotConfiguration
from Logger import Logger
from RagBot import RAGBot
from OperationMode import OperationMode

class ConsoleMode:
    def __init__(self, bot: RAGBot):
        self.bot = bot
    
    def run(self):
        """Запуск консольного режима"""
        print(">>>>>> RAG-бот готов. Введите запрос (пустая строка для выхода):\n")
        
        while True:
            try:
                query = input(">>> ").strip()
                if not query:
                    break
                
                start_time = datetime.now()
                answer = self.bot.rag_answer(query, OperationMode.CONSOLE)
                response_time = (datetime.now() - start_time).total_seconds()
                
                print(f"\n>>>>> Ответ (за {response_time:.2f} сек):\n")
                print(answer)
                print("\n" + "=" * 60 + "\n")
            
            except KeyboardInterrupt:
                print("\n\nЗавершение работы...")
                break
            except Exception as e:
                print(f"\nОшибка: {e}")
                print("Попробуйте еще раз...\n")
