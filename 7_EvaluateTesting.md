# 7. Аналитика покрытия и качества базы знаний

## Логирование ответов

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
YANDEX_API_KEY=_api_ключ 
YANDEX_FOLDER_ID=ваш_folder_id
TELEGRAM_BOT_TOKEN=telegram_токен # нужен только для запуска в режиме телеграм-бота
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










## Решение

- [ ] 1. **Внесите искусственные пробелы в базу**
    Удалите 2-3 ключевые сущности из вашей базы знаний. Например, упоминания планеты VoidCore, персонажа Xarn Velgor и концепта Synth Flux. Так вы сможете протестировать, как ваш чат-бот себя ведёт при отсутствии нужной информации.
- [ ] 2. **Напишите скрипт логирования запросов**
	Каждый запрос к боту должен сохраняться в лог с полями:
	- текст запроса,
	- timestamp,
	- были ли найдены чанки,
	- длина ответа,
	- флаг «успешный ответ» (по длине, осмысленности или по ключевым словам),
	- найденные источники.
	Можно вести лог в `CSV`, `JSONL` или SQLite — любой формат, пригодный для анализа.

- [ ] 3. **Сформируйте «золотой набор» вопросов**
	Подготовьте 10–15 вопросов, покрывающих разные аспекты вашей базы:
	- 6–8 вопросов на **известные темы** (бот должен ответить),
	- 3–5 вопросов на **удалённые или отсутствующие** (бот должен не ответить корректно).

- [ ] 4. **Проведите автоматическое тестирование**
	Запустите скрипт, который:
	- по очереди будет задавать вопросы из набора,
	- сохранит результат в лог,
	- оценит, был ли ответ корректным (например: `ответ найден: да/нет`
	    - `оценка полноты`).

- [ ] 5. **Проанализируйте логи**
	Выявите:
	- По каким темам бот часто не отвечает.
	- Где выдаёт нерелевантные источники.
	- Где нужно **расширить или переписать** базу знаний.

- [ ] 6. **Нарисуйте диаграмму**
	Постройте диаграмму последовательности (sequence diagram), которая покажет:
	- Как обрабатывается запрос.
	- Как происходит процесс оценки.
	- Где может происходить сбой (например, пустой индекс, невалидный чанк, генерация ответа).
