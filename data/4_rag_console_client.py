import os
import chromadb
from sentence_transformers import SentenceTransformer
import requests  # тут может понадобиться openai или что-то еще, если ask_llm будет работать через клиента

# ========== НАСТРОЙКИ ==========

CHROMA_DIR = "./data/knowledge-base/chroma_db"
COLLECTION_NAME = "gooddrink"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 4

# Yandex GPT
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")  # идентификатор каталога
YANDEX_MODEL = "yandexgpt-lite"

# ===============================

# ========== ИНИЦИАЛИЗАЦИЯ ==========

print(">>>>> Загружаем embedding-модель...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

print(">>>>> Подключаемся к ChromaDB...")
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)

print(">>>>> Инициализируем LLM...")

# ========== RAG-ФУНКЦИИ ==========

def retrieve_chunks(query: str, top_k: int = TOP_K):
    """Ищем релевантные чанки"""
    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({
            "text": doc,
            "metadata": meta
        })

    return chunks

def build_prompt(query: str, chunks: list[dict]) -> str:
    """Формируем prompt для LLM"""
    context_blocks = []

    for i, chunk in enumerate(chunks, start=1):
        block = (
            f"[Источник {i}]\n"
            f"{chunk['text']}\n"
            f"(Ссылка: {chunk['metadata']['telegram_url']})"
        )
        context_blocks.append(block)

    context = "\n\n".join(context_blocks)

    prompt = f"""
Ты — эксперт по крафтовому пиву.
Используй ТОЛЬКО информацию из источников ниже.
Отвечай по формату, указанному ниже.
Если информации недостаточно — честно скажи об этом.

ФОРМАТ ОТВЕТА:
1. Описание сорта
2. Ссылка

ПРИМЕР ОТВЕТА:
Q: Что можешь рассказать про punk ipa?
A: Punk IPA — это популярный сорт крафтового пива. Его можно встретить в барах на кранах разливного пива практически в любом городе. 
Подробнее смотри по ссылке: https://t.me/nice_ipa/115

ИСТОЧНИКИ:
{context}

ВОПРОС:
{query}

ОТВЕТ:
"""
    return prompt.strip()

# Клиент не нужен — используем requests для HTTP-запросов к API
def ask_llm(prompt: str) -> str:
    """Отправляем prompt в YandexGPT"""
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": "2000"
        },
        "messages": [
            {"role": "system", "text": "Ты полезный и точный помощник."},
            {"role": "user", "text": prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=body)
    
    
    if response.status_code != 200:
        raise Exception(f"Ошибка API: {response.status_code}, {response.text}")
    
    result = response.json()
    return result["result"]["alternatives"][0]["message"]["text"]

def rag_answer(query: str) -> str:
    """Полный RAG pipeline"""
    chunks = retrieve_chunks(query)

    if not chunks:
        return "К сожалению, по этому запросу ничего не найдено."

    prompt = build_prompt(query, chunks)
    answer = ask_llm(prompt)

    return answer

# ========== CLI ==========

if __name__ == "__main__":
    print(">>>>>> RAG-бот готов. Введите запрос:\n")

    while True:
        query = input(">>> ").strip()
        if not query:
            break

        answer = rag_answer(query)
        print("\n >>>>> Ответ:\n")
        print(answer)
        print("\n" + "=" * 60 + "\n")
