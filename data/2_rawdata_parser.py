import json
import os
from pathlib import Path

# ====== НАСТРОЙКИ ======

INPUT_JSON = "./data/knowledge-base/exported_data_ipa/result.json"  # экспорт Telegram
OUTPUT_DIR = "./data/knowledge-base/posts"                          # куда сохранять посты

# =======================

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_text(text_field):
    """
    Telegram экспорт:
    - text может быть строкой
    - или списком (plain / hashtag / etc)
    """
    if isinstance(text_field, str):
        return text_field.strip()

    parts = []
    for item in text_field:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict) and "text" in item:
            parts.append(item["text"])
    return "".join(parts).strip()


def extract_hashtags(text_entities):
    hashtags = []
    for ent in text_entities or []:
        if ent.get("type") == "hashtag":
            hashtags.append(ent["text"].lstrip("#"))
    return hashtags


# ====== ЗАГРУЗКА ЭКСПОРТА ======

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

messages = data["messages"]

CHANNEL_NAME = data["name"]
CHANNEL_ID = data["id"]

posts = []
current_post = None


# ====== ГРУППИРОВКА СООБЩЕНИЙ В ПОСТЫ ======

for msg in messages:
    if msg.get("type") != "message":
        continue

    text = extract_text(msg.get("text", ""))
    has_text = bool(text)
    has_photo = "photo" in msg

    if has_text:
        # закрываем предыдущий пост
        if current_post:
            posts.append(current_post)

        post_id = msg["id"]
        post_uid = f"{CHANNEL_NAME.lower()}_{post_id:06d}"

        current_post = {
            "post_uid": post_uid,
            "content": {
                "text": text,
                "photos": []
            },
            "metadata": {
                "channel_name": CHANNEL_NAME,
                "channel_id": CHANNEL_ID,
                "post_id": post_id,
                "date": msg["date"],
                "date_unixtime": int(msg["date_unixtime"]),
                "hashtags": extract_hashtags(msg.get("text_entities")),
                "telegram_url": f"https://t.me/{CHANNEL_NAME}/{post_id}"
            }
        }

        if has_photo:
            current_post["content"]["photos"].append(msg["photo"])

    else:
        # сообщение без текста → фото к предыдущему посту
        if current_post and has_photo:
            current_post["content"]["photos"].append(msg["photo"])


# не забываем последний пост
if current_post:
    posts.append(current_post)


# ====== СОХРАНЕНИЕ ПОСТОВ ======

for i, post in enumerate(posts, start=1):
    filename = Path(OUTPUT_DIR) / f"{post['post_uid']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=2)

print(f">>>> Готово. Извлечено постов: {len(posts)}")
print(f">>>> Посты сохранены в папке: {OUTPUT_DIR}")
