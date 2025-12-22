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
from BeerSynonymExpander import BeerSynonymExpander
from BotConfiguration import BotConfiguration

@dataclass
class LogEntry:
    """Структура для записи логов"""
    query: str
    timestamp: str
    has_chunks: bool
    answer_length: int
    is_successful: bool
    sources: List[str]
    mode: str
    user_id: Optional[str] = None
    response_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ========== ЛОГИРОВАНИЕ ==========

class Logger:
    def __init__(self, botConfig: BotConfiguration):
        self.log_dir = Path(botConfig.LOG_DIR)
        self.log_file = self.log_dir / botConfig.LOG_FILE
        
        # Создаем директорию для логов, если её нет
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настраиваем логирование
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / 'rag_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_interaction(self, entry: LogEntry) -> None:
        """Записывает взаимодействие в JSONL файл"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json_line = json.dumps(entry.to_dict(), ensure_ascii=False)
                f.write(json_line + '\n')
            
            # Также логируем в обычный лог
            self.logger.info(f"Query: {entry.query[:50]}... | "
                           f"Success: {entry.is_successful} | "
                           f"Sources: {len(entry.sources)}")
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по логам"""
        stats = {
            "total_queries": 0,
            "successful_answers": 0,
            "avg_answer_length": 0,
            "queries_by_mode": {}
        }
        
        try:
            if not self.log_file.exists():
                return stats
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_length = 0
                
                for line in lines:
                    try:
                        entry = json.loads(line.strip())
                        stats["total_queries"] += 1
                        
                        mode = entry.get("mode", "unknown")
                        if mode not in stats["queries_by_mode"]:
                            stats["queries_by_mode"][mode] = 0
                        stats["queries_by_mode"][mode] += 1
                        
                        if entry.get("is_successful", False):
                            stats["successful_answers"] += 1
                        
                        total_length += entry.get("answer_length", 0)
                    
                    except json.JSONDecodeError:
                        continue
                
                if stats["total_queries"] > 0:
                    stats["avg_answer_length"] = total_length / stats["total_queries"]
        
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
        
        return stats
