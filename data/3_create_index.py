import json
import os
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ====== НАСТРОЙКИ ======

POSTS_DIR = "./data/knowledge-base/posts"
CHROMA_DIR = "./data/knowledge-base/chroma_db"
COLLECTION_NAME = "gooddrink"

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE = 800       # символы (прибл. 150–250 слов)
CHUNK_OVERLAP = 100

# =======================


# ====== ИНИЦИАЛИЗАЦИЯ ======

print(">>>>> Загружаем embedding-модель...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

print(">>>>> Инициализируем ChromaDB...")
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " ", ""]
)

# ====== ОБРАБОТКА ПОСТОВ ======

documents = []
metadatas = []
ids = []

chunk_counter = 0

post_files = sorted(Path(POSTS_DIR).glob("*.json"))

print(f">>>>> Найдено постов: {len(post_files)}")

for post_file in post_files:
    with open(post_file, "r", encoding="utf-8") as f:
        post = json.load(f)

    text = post["content"]["text"]
    metadata_base = post["metadata"]
    post_uid = post["post_uid"]

    if not text.strip():
        continue

    chunks = text_splitter.split_text(text)

    for i, chunk in enumerate(chunks):
        chunk_id = f"{post_uid}_chunk_{i:02d}"

        documents.append(chunk)
        metadatas.append({
            **{
                **metadata_base,
                "hashtags": " ".join(metadata_base.get("hashtags", []))
            },
            "post_uid": post_uid,
            "chunk_index": i,
            "source_file": post_file.name
        })
        ids.append(chunk_id)

        chunk_counter += 1

print(f">>>> Всего чанков: {chunk_counter}")

# ====== ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ ======

print(">>>>> Считаем эмбеддинги...")
embeddings = embedding_model.encode(
    documents,
    show_progress_bar=True
).tolist()

# ====== ЗАГРУЗКА В CHROMA ======

print(">>>>> Загружаем в ChromaDB...")
collection.add(
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
    ids=ids
)

print(">>>>> Индекс успешно создан")
print(f">>>>> ChromaDB: {CHROMA_DIR}")
print(f">>>>> Коллекция: {COLLECTION_NAME}")
