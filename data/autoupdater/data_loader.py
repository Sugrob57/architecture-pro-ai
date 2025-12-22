import json
import os
import hashlib
import traceback
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Tuple, Optional, Any
import sys

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ====== НАСТРОЙКИ ======
POSTS_DIR = "./data/knowledge-base/posts"
CHROMA_DIR = "./data/knowledge-base/chroma_db"
LOGS_DIR = "./data/autoupdater/logs"
COLLECTION_NAME = "gooddrink"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("index_update.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Файл для хранения хэшей документов
HASH_STORE_FILE = Path(CHROMA_DIR) / "document_hashes.json"

# Файл для хранения информации об ошибках
ERROR_LOG_FILE = "index_errors.json"
# =======================

class DocumentProcessingError(Exception):
    """Кастомное исключение для ошибок обработки документов."""
    pass

class IndexUpdater:
    def __init__(self, max_retries: int = 3):
        """
        Инициализация компонентов для обновления индекса.
        
        Args:
            max_retries: Максимальное количество попыток при ошибках
        """
        self.max_retries = max_retries
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.text_splitter = None
        self.document_hashes = {}
        self.error_log = self.load_error_log()
        
        self.init_with_error_handling()
    
    def init_with_error_handling(self):
        """Инициализация с обработкой ошибок."""
        try:
            logger.info(">>>>> Инициализация IndexUpdater...")
            
            # Проверяем существование директории с данными
            posts_path = Path(POSTS_DIR)
            if not posts_path.exists():
                logger.error(f"Директория с данными не найдена: {POSTS_DIR}")
                os.makedirs(POSTS_DIR, exist_ok=True)
                logger.info(f"Создана директория: {POSTS_DIR}")
            
            # Загружаем embedding-модель с повторными попытками
            logger.info(">>>>> Загружаем embedding-модель...")
            for attempt in range(self.max_retries):
                try:
                    self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                    logger.info(">>>>> Модель успешно загружена")
                    break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Попытка {attempt + 1} загрузки модели не удалась: {e}")
                        time.sleep(2 ** attempt)  # Экспоненциальная задержка
                    else:
                        logger.error(f"Не удалось загрузить модель после {self.max_retries} попыток: {e}")
                        raise DocumentProcessingError(f"Ошибка загрузки модели: {e}")
            
            # Инициализируем ChromaDB
            logger.info(">>>>> Инициализируем ChromaDB...")
            try:
                self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
                self.collection = self.chroma_client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f">>>>> Коллекция '{COLLECTION_NAME}' готова")
            except Exception as e:
                logger.error(f"Ошибка инициализации ChromaDB: {e}")
                # Пробуем создать новую коллекцию
                try:
                    self.collection = self.chroma_client.create_collection(name=COLLECTION_NAME)
                except:
                    raise DocumentProcessingError(f"Критическая ошибка ChromaDB: {e}")
            
            # Инициализируем сплиттер текста
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            
            # Загружаем сохраненные хэши документов
            self.document_hashes = self.load_document_hashes()
            
            logger.info(">>>>> Инициализация завершена")
            
        except Exception as e:
            logger.critical(f"Критическая ошибка при инициализации: {e}")
            logger.critical(traceback.format_exc())
            raise
    
    def load_document_hashes(self) -> Dict[str, str]:
        """Загружает сохраненные хэши документов из файла."""
        try:
            if HASH_STORE_FILE.exists():
                with open(HASH_STORE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка чтения файла хэшей (неверный формат JSON): {e}")
            # Создаем резервную копию поврежденного файла
            backup_file = HASH_STORE_FILE.with_suffix('.json.bak')
            try:
                if HASH_STORE_FILE.exists():
                    HASH_STORE_FILE.rename(backup_file)
                    logger.info(f"Создана резервная копия поврежденного файла: {backup_file}")
            except:
                pass
        except Exception as e:
            logger.error(f"Ошибка при загрузке хэшей: {e}")
        
        return {}
    
    def load_error_log(self) -> Dict[str, Any]:
        """Загружает лог ошибок."""
        try:
            if Path(ERROR_LOG_FILE).exists():
                with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {"errors": [], "failed_files": {}}
    
    def save_error_log(self):
        """Сохраняет лог ошибок."""
        try:
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.error_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения лога ошибок: {e}")
    
    def log_file_error(self, file_path: Path, error: str, error_type: str = "processing"):
        """Логирует ошибку обработки файла."""
        file_name = file_path.name
        error_entry = {
            "file": file_name,
            "path": str(file_path),
            "error": error,
            "type": error_type,
            "timestamp": datetime.now().isoformat()
        }
        
        self.error_log["errors"].append(error_entry)
        
        # Сохраняем информацию о проблемных файлах
        if file_name not in self.error_log["failed_files"]:
            self.error_log["failed_files"][file_name] = []
        
        self.error_log["failed_files"][file_name].append({
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "type": error_type
        })
        
        # Ограничиваем историю ошибок для каждого файла
        if len(self.error_log["failed_files"][file_name]) > 10:
            self.error_log["failed_files"][file_name] = self.error_log["failed_files"][file_name][-10:]
        
        self.save_error_log()
    
    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Вычисляет хэш файла с обработкой ошибок."""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Ошибка чтения файла для хэширования {file_path}: {e}")
            self.log_file_error(file_path, str(e), "hash_calculation")
            return None
    
    def validate_json_file(self, file_path: Path) -> bool:
        """Проверяет валидность JSON файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    logger.warning(f"Файл пуст: {file_path.name}")
                    return False
                
                # Быстрая проверка синтаксиса
                json.loads(content)
                return True
        except json.JSONDecodeError as e:
            logger.error(f"Невалидный JSON в файле {file_path.name}: {e}")
            self.log_file_error(file_path, f"Invalid JSON: {e}", "validation")
            return False
        except UnicodeDecodeError as e:
            logger.error(f"Ошибка кодировки в файле {file_path.name}: {e}")
            self.log_file_error(file_path, f"Encoding error: {e}", "validation")
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки файла {file_path.name}: {e}")
            self.log_file_error(file_path, str(e), "validation")
            return False
    
    def find_changed_documents(self) -> Tuple[List[Path], List[str]]:
        """
        Находит новые и измененные документы с обработкой ошибок.
        """
        logger.info(f">>>>> Сканируем директорию: {POSTS_DIR}")
        
        try:
            posts_path = Path(POSTS_DIR)
            if not posts_path.exists():
                logger.error(f"Директория не существует: {POSTS_DIR}")
                return [], []
            
            current_files = list(posts_path.glob("*.json"))
            logger.info(f">>>>> Найдено файлов: {len(current_files)}")
            
            new_or_changed = []
            deleted_files = []
            skipped_files = []
            
            # Проверяем существующие файлы на изменения
            for file_path in current_files:
                try:
                    # Проверяем валидность файла
                    if not self.validate_json_file(file_path):
                        skipped_files.append(file_path.name)
                        continue
                    
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash is None:
                        skipped_files.append(file_path.name)
                        continue
                    
                    file_name = file_path.name
                    
                    if file_name not in self.document_hashes:
                        new_or_changed.append(file_path)
                        logger.info(f"Новый файл: {file_name}")
                    elif self.document_hashes[file_name] != file_hash:
                        new_or_changed.append(file_path)
                        logger.info(f"Измененный файл: {file_name}")
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки файла {file_path.name}: {e}")
                    self.log_file_error(file_path, str(e), "scanning")
                    skipped_files.append(file_path.name)
            
            # Находим удаленные файлы
            stored_files = set(self.document_hashes.keys())
            current_file_names = {f.name for f in current_files}
            
            for stored_file in stored_files:
                if stored_file not in current_file_names:
                    deleted_files.append(stored_file)
                    logger.info(f"Удаленный файл: {stored_file}")
            
            logger.info(f">>>>> Новых/измененных: {len(new_or_changed)}, "
                       f"Удаленных: {len(deleted_files)}, "
                       f"Пропущенных: {len(skipped_files)}")
            
            if skipped_files:
                logger.warning(f"Пропущенные файлы из-за ошибок: {skipped_files}")
            
            return new_or_changed, deleted_files
            
        except Exception as e:
            logger.error(f"Критическая ошибка при сканировании директории: {e}")
            logger.error(traceback.format_exc())
            return [], []
    
    def safe_json_load(self, file_path: Path) -> Optional[Dict]:
        """Безопасная загрузка JSON с повторными попытками."""
        for attempt in range(self.max_retries):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Попытка {attempt + 1} чтения {file_path.name} не удалась: {e}")
                    time.sleep(1)
                else:
                    logger.error(f"Не удалось прочитать {file_path.name} после {self.max_retries} попыток: {e}")
                    self.log_file_error(file_path, f"JSON decode error: {e}", "reading")
                    return None
            except Exception as e:
                logger.error(f"Ошибка чтения файла {file_path.name}: {e}")
                self.log_file_error(file_path, str(e), "reading")
                return None
        return None
    
    def process_document(self, file_path: Path) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Обрабатывает один документ с обработкой ошибок.
        """
        file_name = file_path.name
        
        try:
            # Загружаем JSON
            post = self.safe_json_load(file_path)
            if post is None:
                return [], [], []
            
            # Проверяем структуру данных
            required_fields = ["content", "metadata", "post_uid"]
            for field in required_fields:
                if field not in post:
                    error_msg = f"Отсутствует обязательное поле: {field}"
                    logger.error(f"{error_msg} в файле {file_name}")
                    self.log_file_error(file_path, error_msg, "validation")
                    return [], [], []
            
            text = post.get("content", {}).get("text", "")
            if not isinstance(text, str):
                error_msg = f"Поле 'text' должно быть строкой, получено: {type(text)}"
                logger.error(f"{error_msg} в файле {file_name}")
                self.log_file_error(file_path, error_msg, "validation")
                return [], [], []
            
            metadata_base = post.get("metadata", {})
            if not isinstance(metadata_base, dict):
                error_msg = f"Поле 'metadata' должно быть словарем, получено: {type(metadata_base)}"
                logger.error(f"{error_msg} в файле {file_name}")
                self.log_file_error(file_path, error_msg, "validation")
                return [], [], []
            
            post_uid = post.get("post_uid", "")
            if not post_uid:
                logger.warning(f"Пустой post_uid в файле {file_name}, будет использовано имя файла")
                post_uid = file_name
            
            if not text.strip():
                logger.warning(f"Пустой текст в файле: {file_name}")
                return [], [], []
            
            # Разбиваем текст на чанки
            try:
                chunks = self.text_splitter.split_text(text)
            except Exception as e:
                logger.error(f"Ошибка разбивки текста в файле {file_name}: {e}")
                self.log_file_error(file_path, f"Text splitting error: {e}", "processing")
                return [], [], []
            
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                try:
                    chunk_id = f"{post_uid}_chunk_{i:04d}"
                    
                    # Подготавливаем метаданные
                    hashtags = metadata_base.get("hashtags", [])
                    if isinstance(hashtags, list):
                        hashtags_str = " ".join(hashtags)
                    else:
                        hashtags_str = str(hashtags)
                    
                    metadata = {
                        **metadata_base,
                        "hashtags": hashtags_str,
                        "post_uid": post_uid,
                        "chunk_index": i,
                        "source_file": file_name,
                        "last_updated": datetime.now().isoformat(),
                        "chunk_size": len(chunk)
                    }
                    
                    documents.append(chunk)
                    metadatas.append(metadata)
                    ids.append(chunk_id)
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки чанка {i} в файле {file_name}: {e}")
                    continue
            
            if documents:
                logger.info(f"Обработан {file_name}: {len(documents)} чанков")
            else:
                logger.warning(f"Не удалось создать чанки из файла: {file_name}")
            
            return documents, metadatas, ids
            
        except Exception as e:
            logger.error(f"Критическая ошибка обработки файла {file_name}: {e}")
            logger.error(traceback.format_exc())
            self.log_file_error(file_path, f"Critical error: {e}", "processing")
            return [], [], []
    
    def remove_document_chunks(self, file_name: str) -> int:
        """Удаляет все чанки документа из базы данных с обработкой ошибок."""
        removed_count = 0
        try:
            # Находим все чанки, связанные с этим файлом
            for attempt in range(self.max_retries):
                try:
                    results = self.collection.get(
                        where={"source_file": file_name},
                        include=["metadatas"]
                    )
                    
                    if results and results['ids']:
                        chunk_ids = results['ids']
                        self.collection.delete(ids=chunk_ids)
                        removed_count = len(chunk_ids)
                        logger.info(f"Удалено {removed_count} чанков из файла: {file_name}")
                        break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Попытка {attempt + 1} удаления чанков файла {file_name} не удалась: {e}")
                        time.sleep(1)
                    else:
                        logger.error(f"Не удалось удалить чанки файла {file_name}: {e}")
            
            # Удаляем хэш файла из хранилища
            if file_name in self.document_hashes:
                del self.document_hashes[file_name]
            
        except Exception as e:
            logger.error(f"Ошибка при удалении чанков файла {file_name}: {e}")
        
        return removed_count
    
    def add_chunks_to_collection(self, documents: List[str], metadatas: List[Dict], 
                                 ids: List[str], batch_size: int = 100) -> bool:
        """Добавляет чанки в коллекцию с пакетной обработкой."""
        if not documents:
            return True
        
        try:
            total_chunks = len(documents)
            logger.info(f"Генерируем эмбеддинги для {total_chunks} чанков...")
            
            # Генерируем эмбеддинги пакетами
            all_embeddings = []
            for i in range(0, total_chunks, batch_size):
                batch_end = min(i + batch_size, total_chunks)
                batch_docs = documents[i:batch_end]
                
                logger.info(f"Обработка пакета {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size}")
                
                try:
                    batch_embeddings = self.embedding_model.encode(
                        batch_docs,
                        show_progress_bar=False,
                        batch_size=32,
                        convert_to_tensor=False
                    ).tolist()
                    all_embeddings.extend(batch_embeddings)
                except Exception as e:
                    logger.error(f"Ошибка генерации эмбеддингов для пакета: {e}")
                    # Пропускаем проблемный пакет, но продолжаем
                    all_embeddings.extend([None] * len(batch_docs))
            
            # Фильтруем успешно обработанные чанки
            successful_indices = [i for i, emb in enumerate(all_embeddings) if emb is not None]
            
            if not successful_indices:
                logger.error("Не удалось сгенерировать эмбеддинги ни для одного чанка")
                return False
            
            successful_docs = [documents[i] for i in successful_indices]
            successful_metas = [metadatas[i] for i in successful_indices]
            successful_ids = [ids[i] for i in successful_indices]
            successful_embs = [all_embeddings[i] for i in successful_indices]
            
            logger.info(f"Успешно обработано {len(successful_docs)} из {total_chunks} чанков")
            
            # Добавляем в коллекцию
            self.collection.add(
                documents=successful_docs,
                embeddings=successful_embs,
                metadatas=successful_metas,
                ids=successful_ids
            )
            
            logger.info(f"Добавлено {len(successful_docs)} чанков в ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Критическая ошибка при добавлении чанков в коллекцию: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def update_index(self) -> Dict[str, Any]:
        """Основной метод обновления индекса с обработкой ошибок."""
        logger.info("=" * 60)
        logger.info(f"НАЧАЛО ОБНОВЛЕНИЯ ИНДЕКСА: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        stats = {
            "processed_files": 0,
            "added_chunks": 0,
            "removed_chunks": 0,
            "deleted_files": 0,
            "failed_files": 0,
            "start_time": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        try:
            # Шаг 1: Находим изменения
            changed_files, deleted_files = self.find_changed_documents()
            stats["processed_files"] = len(changed_files)
            stats["deleted_files"] = len(deleted_files)
            
            # Шаг 2: Удаляем чанки удаленных файлов
            for deleted_file in deleted_files:
                removed = self.remove_document_chunks(deleted_file)
                stats["removed_chunks"] += removed
            
            # Шаг 3: Обрабатываем новые/измененные файлы
            all_documents = []
            all_metadatas = []
            all_ids = []
            failed_files = []
            
            for file_path in changed_files:
                file_name = file_path.name
                
                # Для измененных файлов сначала удаляем старые чанки
                if file_name in self.document_hashes:
                    removed = self.remove_document_chunks(file_name)
                    stats["removed_chunks"] += removed
                
                # Обрабатываем документ
                documents, metadatas, ids = self.process_document(file_path)
                
                if documents:
                    all_documents.extend(documents)
                    all_metadatas.extend(metadatas)
                    all_ids.extend(ids)
                    
                    # Обновляем хэш файла
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash:
                        self.document_hashes[file_name] = file_hash
                    else:
                        failed_files.append(file_name)
                        stats["failed_files"] += 1
                else:
                    failed_files.append(file_name)
                    stats["failed_files"] += 1
            
            # Шаг 4: Добавляем чанки в коллекцию
            if all_documents:
                success = self.add_chunks_to_collection(all_documents, all_metadatas, all_ids)
                if success:
                    stats["added_chunks"] = len(all_documents)
            
            # Шаг 5: Сохраняем обновленные хэши
            try:
                self.save_document_hashes()
            except Exception as e:
                logger.error(f"Ошибка сохранения хэшей: {e}")
            
            # Шаг 6: Логируем итоги
            stats["status"] = "completed"
            stats["end_time"] = datetime.now().isoformat()
            stats["failed_files_list"] = failed_files
            
            self.log_update_summary(stats)
            
            return stats
            
        except Exception as e:
            logger.critical(f"Критическая ошибка в процессе обновления индекса: {e}")
            logger.critical(traceback.format_exc())
            
            stats["status"] = "failed"
            stats["error"] = str(e)
            stats["end_time"] = datetime.now().isoformat()
            
            return stats
    
    def save_document_hashes(self):
        """Сохраняет хэши документов в файл с обработкой ошибок."""
        try:
            HASH_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Создаем временный файл для атомарной записи
            temp_file = HASH_STORE_FILE.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_hashes, f, indent=2, ensure_ascii=False)
            
            # Атомарно заменяем старый файл новым
            if HASH_STORE_FILE.exists():
                HASH_STORE_FILE.unlink()
            temp_file.rename(HASH_STORE_FILE)
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении хэшей: {e}")
            # Пробуем сохранить резервную копию
            try:
                backup_file = HASH_STORE_FILE.with_suffix('.json.backup')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.document_hashes, f)
                logger.info(f"Создана резервная копия хэшей: {backup_file}")
            except:
                pass
    
    def log_update_summary(self, stats: Dict[str, Any]):
        """Логирует итоги обновления."""
        logger.info("=" * 60)
        logger.info("ИТОГИ ОБНОВЛЕНИЯ:")
        logger.info(f"  Статус: {stats.get('status', 'unknown')}")
        logger.info(f"  Обработано файлов: {stats.get('processed_files', 0)}")
        logger.info(f"  Добавлено чанков: {stats.get('added_chunks', 0)}")
        logger.info(f"  Удалено чанков: {stats.get('removed_chunks', 0)}")
        logger.info(f"  Удалено файлов: {stats.get('deleted_files', 0)}")
        logger.info(f"  Файлов с ошибками: {stats.get('failed_files', 0)}")
        
        if stats.get('failed_files_list'):
            logger.info(f"  Проблемные файлы: {stats['failed_files_list']}")
        
        # Получаем общую статистику коллекции
        try:
            total_in_collection = self.collection.count()
            logger.info(f"  Всего чанков в коллекции: {total_in_collection}")
        except Exception as e:
            logger.warning(f"Не удалось получить статистику коллекции: {e}")
        
        # Время выполнения
        if 'start_time' in stats and 'end_time' in stats:
            try:
                start = datetime.fromisoformat(stats['start_time'])
                end = datetime.fromisoformat(stats['end_time'])
                duration = end - start
                logger.info(f"  Время выполнения: {duration}")
            except:
                pass
        
        logger.info("=" * 60)
        logger.info("ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
        logger.info("=" * 60)

def main():
    """Основная функция для запуска обновления с обработкой ошибок."""
    try:
        updater = IndexUpdater(max_retries=3)
        
        # Обычное обновление
        stats = updater.update_index()
        
        # Выводим краткую статистику
        print("\n" + "="*60)
        print("СВОДКА ОБНОВЛЕНИЯ:")
        print(f"  Статус: {stats.get('status', 'unknown')}")
        print(f"  Добавлено: {stats.get('added_chunks', 0)} чанков")
        print(f"  Удалено: {stats.get('removed_chunks', 0)} чанков")
        print(f"  Файлов обработано: {stats.get('processed_files', 0)}")
        print(f"  Файлов с ошибками: {stats.get('failed_files', 0)}")
        print("="*60)
        
        # Если были ошибки, показываем подробности
        if stats.get('failed_files', 0) > 0:
            print("\nВНИМАНИЕ: Некоторые файлы не были обработаны!")
            print(f"Подробности в логе ошибок: {ERROR_LOG_FILE}")
        
        return stats
        
    except Exception as e:
        logger.critical(f"Критическая ошибка в main(): {e}")
        logger.critical(traceback.format_exc())
        print(f"\n КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("Подробности в логе: index_update.log")
        return {"status": "critical_error", "error": str(e)}

if __name__ == "__main__":
    import time  # Импортируем здесь, чтобы избежать циклических импортов
    main()