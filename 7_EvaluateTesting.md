# 7. Аналитика покрытия и качества базы знаний

## 1. Скрипт логирования запросов

Для возможности тестирования качества ответов бота, а так же для возможности использования бота в формате Telegram-чата, скрипт консольного бота из задания 5 [/data/5_securedConsoleBot.py](/data/5_securedConsoleBot.py) был разбит на отдельные модули, и доработан. 

### Описание файлов проекта бота

Теперь проект бота имеет структуру:

Основной класс запуска бота:
- [BotRunner.py](/sprint7/git2/data/7_RagBotAsProject/BotRunner.py)

Классы, реализующие режимы запуска:
- [AutoTestMode.py](/sprint7/git2/data/7_RagBotAsProject/AutoTestMode.py)
- [ConsoleMode.py](/sprint7/git2/data/7_RagBotAsProject/ConsoleMode.py)
- [TelegramBotMode.py](/sprint7/git2/data/7_RagBotAsProject/TelegramBotMode.py)

И дополнительные классы:
- [BeerSynonymExpander.py](/sprint7/git2/data/7_RagBotAsProject/BeerSynonymExpander.py) - класс для обагащения запроса синонимами (помагает лучше искать релевантные чанки)
- [BotConfiguration.py](/sprint7/git2/data/7_RagBotAsProject/BotConfiguration.py) - настройки конфигурации
- [Logger.py](/sprint7/git2/data/7_RagBotAsProject/Logger.py) - логгер в формате JSONL
- [OperationMode.py](/sprint7/git2/data/7_RagBotAsProject/OperationMode.py) - режимы запуска
- [RagBot.py](/sprint7/git2/data/7_RagBotAsProject/RagBot.py) - основной класс логики бота

### Инициализация

Установить зависимости
```bash
python -m venv .venv
source .venv/bin/activate
pip install langchain faiss-cpu sentence-transformers chromadb langchain langchain-text-splitters openai requests python-telegram-bot
```

Установить ENV-переменные (либо значения в файле .env)
(подробнее было в [4. Реализация RAG-бота с техниками промптинга](/4_RAGbotImplementation.md))
```
export YANDEX_API_KEY=_api_ключ 
export YANDEX_FOLDER_ID=ваш_folder_id
export TELEGRAM_BOT_TOKEN=telegram_токен # нужен только для запуска в режиме телеграм-бота
```

### Команды запуска

```bash
# Консольный режим (по умолчанию)
python ./data/7_RagBotAsProject/BotRunner.py

# Консольный режим явно
python ./data/7_RagBotAsProject/BotRunner.py --mode console

# Запуск телеграм бота
python ./data/7_RagBotAsProject/BotRunner.py --mode telegram

# Запуск автотестов
python ./data/7_RagBotAsProject/BotRunner.py --mode autotest

# Запуск автотестов с кастомным файлом вопросов
python ./data/7_RagBotAsProject/BotRunner.py --mode autotest --test-file ./my_questions.txt

# Показать статистику
python ./data/7_RagBotAsProject/BotRunner.py --stats

```

### Пример логирования

Все запросы к боту логируются в формате JSONL. Пример [из лога](/sprint7/git2/data/7_RagBotAsProject/rag_bot_logs.jsonl):

```json
{
    "question": "Что такое IPA?",
    "timestamp": "2025-12-18T10:51:44.678217",
    "has_answer": true,
    "answer_length": 150,
    "is_successful": true,
    "sources_count": 3,
    "response_time_ms": 905,
    "answer_preview": "1. IPA (India Pale Ale) — это популярный сорт крафтового пива, который отличается высокой «ипастость..."
  },
  {
    "question": "Какие бывают сорта крафтового пива?",
    "timestamp": "2025-12-18T10:51:46.641765",
    "has_answer": true,
    "answer_length": 335,
    "is_successful": true,
    "sources_count": 3,
    "response_time_ms": 1963,
    "answer_preview": "1. India Pale Ale (IPA) — сорт крафтового пива с высокой крепостью и выраженной хмелевой горечью. Пр..."
  },
  {
    "question": "Расскажи про стауты",
    "timestamp": "2025-12-18T10:51:47.758421",
    "has_answer": true,
    "answer_length": 204,
    "is_successful": true,
    "sources_count": 3,
    "response_time_ms": 1116,
    "answer_preview": "1. Стауты — это тип пива, который отличается насыщенным вкусом и тёмным цветом. Они обычно имеют бол..."
  }
```

## 2. "Золотой набор" вопросов

На эти вопросы ответ должен быть успешным:
```
Galaxy стоит пробовать?
Что можешь сказать про Punk IPA?
Какую West Coast IPA стоит попробовать?
Посоветуй не кислый сидр?
Какой стаут стоит попробовать?
Что из Saldens достойно внимания?
```

На эти вопросы нет ответов:
```
Посоветуй что-нибудь от Zagovor?
Какие отзывы об ипе Атомная прачечная?
Что советуешь из топ10?
Какое шампанское порекомендуешь?
а что из вина порекомендуешь? 
```

## 3. Автотесты

Для запуска автотестов можно запустить скрипт командой:

```bash
python ./data/7_RagBotAsProject/BotRunner.py --mode autotest
```

### Скрины прогона автотестов:

![autotest1](/data/screens/autotest_1.png)

![autotest2](/data/screens/autotest_2.png)

![autotest3](/data/screens/autotest_3.png)

## 4. Отчет о прогоне тестов

Так же в результате прогона автотестов [создается файл отчета](/data/7_RagBotAsProject/logs/test_results_20251222_171050.json):

```json
[
  {
    "question": "Galaxy стоит пробовать?",
    "timestamp": "2025-12-22T17:10:36.828520",
    "has_answer": true,
    "answer_length": 193,
    "is_successful": true,
    "sources_count": 3,
    "response_time_ms": 976,
    "answer_preview": "1. Galaxy — это сорт крафтового пива, которое имеет интересное послевкусие. Оно долгое и хмельно-гор..."
  },
  {
    "question": "Что можешь сказать про Punk IPA?",
    "timestamp": "2025-12-22T17:10:37.964210",
    "has_answer": true,
    "answer_length": 195,
    "is_successful": true,
    "sources_count": 3,
    "response_time_ms": 1135,
    "answer_preview": "1. Punk IPA — это популярный сорт крафтового пива с крепостью 5,4%. ИПАстость, горечь и насыщенность..."
  },
  ...
]
```

## 5. Анализ статистики по ответам

Судя по логу со статистикой, на данный момент есть проблемы:
- Бот плохо отвечает на вопросы про напитки, отличные от пива.
- Система почти не отвечает на вопросы "назови топ5, топ10 ХХХ", "назови самый ХХХ"
- Вопросы про марки производителей ("назови лучшее от Saldens, Ganza ...") работают не точно - т.к. плохо синонимизированы названия компаний. 

## 6. Диаграмма принятия решений о качестве ответов

[SequenceDiagram.RagBot.Answer.puml](/data/SequenceDiagram.RagBot.Answer.puml)

![SequenceDiagram.RagBot.Answer.puml](/data/screens/SequenceDiagram.RagBot.Answer.png)
