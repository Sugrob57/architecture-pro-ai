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
from BotConfiguration import BotConfiguration
from Logger import Logger
from RagBot import RAGBot
from OperationMode import OperationMode


# Telegram Bot
class TelegramBotMode:
    def __init__(self, bot: RAGBot, token: str):
        self.bot = bot
        self.token = token
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_text = (
            "Привет! Я бот-эксперт по крафтовому пиву 🍺\n\n"
            "Задайте мне вопрос о сортах пива, вкусовых качествах "
            "или других напитках, и я постараюсь помочь!\n\n"
            "Примеры вопросов:\n"
            "• Что такое IPA?\n"
            "• Расскажи про стауты\n"
            "• Какое пиво самое популярное?"
        )
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "Как пользоваться ботом:\n\n"
            "Просто напишите вопрос о крафтовом пиве или других напитках.\n"
            "Я найду информацию в своей базе знаний и отвечу на ваш вопрос.\n\n"
            "Команды:\n"
            "/start - Начало работы\n"
            "/help - Эта справка\n"
            "/stats - Статистика работы бота\n"
            "/about - О боте"
        )
        await update.message.reply_text(help_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats"""
        stats = self.bot.logger.get_stats()
        
        stats_text = (
            "📊 Статистика бота:\n\n"
            f"Всего запросов: {stats.get('total_queries', 0)}\n"
            f"Успешных ответов: {stats.get('successful_answers', 0)}\n"
            f"Средняя длина ответа: {stats.get('avg_answer_length', 0):.0f} символов\n"
        )
        
        # Добавляем статистику по режимам
        if stats.get('queries_by_mode'):
            stats_text += "\n📈 По режимам:\n"
            for mode, count in stats['queries_by_mode'].items():
                stats_text += f"  {mode}: {count}\n"
        
        await update.message.reply_text(stats_text)
    
    async def about_command(self, Update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /about"""
        about_text = (
            "🤖 RAG-бот по крафтовому пиву\n\n"
            "Этот бот использует технологию RAG (Retrieval-Augmented Generation) "
            "для поиска информации о крафтовом пиве в специализированной базе знаний.\n\n"
            "Технологии:\n"
            "• ChromaDB - векторная база данных\n"
            "• Sentence Transformers - эмбеддинги\n"
            "• YandexGPT - генерация ответов\n\n"
            "Бот может работать в нескольких режимах и логирует все взаимодействия."
        )
        await update.message.reply_text(about_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_message = update.message.text
        user_id = str(update.effective_user.id)
        
        # Отправляем статус "печатает"
        await update.message.chat.send_action(action="typing")
        
        try:
            # Получаем ответ
            answer, log_entry = self.bot.rag_answer_with_logging(
                user_message,
                OperationMode.TELEGRAM,
                user_id
            )
            
            # Отправляем ответ
            await update.message.reply_text(answer)
            
            # Если ответ неуспешный, предлагаем задать другой вопрос
            if not log_entry.is_successful:
                await update.message.reply_text(
                    "Возможно, я не совсем понял ваш вопрос. "
                    "Попробуйте переформулировать или задать другой вопрос о пиве."
                )
        
        except Exception as e:
            self.bot.logger.logger.error(f"Telegram bot error: {e}")
            await update.message.reply_text(
                "Произошла ошибка при обработке запроса. "
                "Пожалуйста, попробуйте позже."
            )
    
    def run(self):
        """Запуск телеграм-бота"""
        if not self.token:
            raise ValueError("Telegram bot token not provided. Set TELEGRAM_BOT_TOKEN environment variable.")
        
        print(">>>>> Запуск Telegram бота...")
        
        # Создаем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("about", self.about_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Запускаем бота
        print(">>>>> Бот запущен. Нажмите Ctrl+C для остановки.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
