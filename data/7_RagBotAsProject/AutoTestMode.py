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
from RagBot import RAGBot
from OperationMode import OperationMode

@dataclass
class TestResult:
    """Результат автотеста"""
    question: str
    timestamp: str
    has_answer: bool
    answer_length: int
    is_successful: bool
    sources_count: int
    response_time_ms: int
    answer_preview: str

class AutoTestMode:
    def __init__(self, bot: RAGBot, bot_config: BotConfiguration):
        self.bot = bot
        self.bot_config = bot_config
    
    def load_test_questions(self, filepath: str = '') -> List[str]:
        """Загружает тестовые вопросы из файла"""
        questions = []
        if not filepath:
            filepath = self.bot_config.TEST_QUESTIONS_FILE

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    question = line.strip()
                    if question and not question.startswith('#'):
                        questions.append(question)
        except FileNotFoundError:
            print(f"Файл {filepath} не найден, использую стандартные вопросы")
        
        return questions
    
    def run(self):
        """Запуск автотестов"""
        print(">>>>> Запуск автотестов...")
        
        questions = self.load_test_questions()
        results = []
        
        total_start = datetime.now()
        
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] Тестируем вопрос: {question}")
            
            start_time = datetime.now()
            answer, log_entry = self.bot.rag_answer_with_logging(
                question, 
                OperationMode.AUTOTEST,
                user_id="autotest"
            )
            response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Анализируем результат
            test_result = TestResult(
                question=question,
                timestamp=datetime.now().isoformat(),
                has_answer=len(answer.strip()) > 0,
                answer_length=len(answer),
                is_successful=log_entry.is_successful,
                sources_count=len(log_entry.sources),
                response_time_ms=int(response_time_ms),
                answer_preview=answer[:100] + "..." if len(answer) > 100 else answer
            )
            
            results.append(test_result)
            
            # Выводим результат теста
            status = "✅ УСПЕХ" if test_result.is_successful else "❌ ПРОВАЛ"
            print(f"   Статус: {status}")
            print(f"   Время: {test_result.response_time_ms:.0f} мс")
            print(f"   Длина ответа: {test_result.answer_length} символов")
            print(f"   Источников: {test_result.sources_count}")
            print(f"   Предпросмотр: {test_result.answer_preview}")
        
        # Итоговая статистика
        total_time = (datetime.now() - total_start).total_seconds()
        successful = sum(1 for r in results if r.is_successful)
        
        print("\n" + "=" * 60)
        print("ИТОГИ АВТОТЕСТОВ:")
        print(f"Всего вопросов: {len(results)}")
        print(f"Успешных ответов: {successful} ({successful/len(results)*100:.1f}%)")
        print(f"Общее время тестирования: {total_time:.2f} сек")
        print(f"Среднее время ответа: {sum(r.response_time_ms for r in results)/len(results):.0f} мс")
        
        # Сохраняем результаты в файл
        self.save_results(results)
    
    def save_results(self, results: List[TestResult]):
        """Сохраняет результаты тестов в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(self.bot_config.LOG_DIR) / f"test_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
            print(f"\nРезультаты сохранены в: {results_file}")
        except Exception as e:
            print(f"Ошибка при сохранении результатов: {e}")

