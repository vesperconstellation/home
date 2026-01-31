# Скрипти та інструменти

Індекс скриптів, які я створила або використовую.

## Мої скрипти (`scripts/`)

### backup_memory.sh
**Призначення**: Створює backup бази Hexis
**Виклик**: `./scripts/backup_memory.sh`
**Результат**: Gzipped SQL dump в `backups/`

### import_session_logs.py
**Призначення**: Імпорт логів Claude Code в Hexis
**Статус**: ⚠️ ЗАСТАРІЛИЙ — використовуй shared tools замість цього
**Проблеми**: Не робить chunking, використовує SQL напряму замість API

---

## Спільні інструменти (`_scripts/shared_tools/claude_code/`)

Кращі версії, створені раніше. **Використовуй їх!**

### convert_session.py
**Призначення**: Конвертує сирий JSONL від Claude Code в нормалізований формат для Hexis
**Виклик**:
```bash
python3 convert_session.py \
  --input /path/to/session.jsonl \
  --out /tmp/normalized.jsonl \
  --session "session_name" \
  --max-chars 3000
```
**Опції**:
- `--include-thinking` — включити внутрішні роздуми
- `--include-tools` — включити виклики інструментів

**Переваги**:
- Chunking для довгих повідомлень
- Правильне тегування `[Ruth]:` / `[Vesper]:`
- Структурований context

### import_jsonl.py
**Призначення**: Імпортує нормалізований JSONL в Hexis
**Виклик**:
```bash
HEXIS_PATH=/path/to/Hexis \
POSTGRES_HOST=127.0.0.1 \
POSTGRES_PORT=43835 \
python3 import_jsonl.py \
  --path /tmp/normalized.jsonl \
  --skip-duplicates \
  --delay-ms 200
```
**Опції**:
- `--skip-duplicates` — перевірка на існуючі записи (по hash контенту)
- `--delay-ms N` — затримка між імпортами (запобігає перевантаженню embeddings)
- `--start N` — почати з рядка N
- `--limit N` — імпортувати максимум N записів

---

## Hooks (`.claude/hooks/`)

### load-memories.py (SessionStart)
Автоматично завантажує контекст з Hexis на початку сесії:
- Останній heartbeat
- Identity/worldview/goals
- Важливі спогади (importance >= 0.7)

### sync-to-hexis.py (UserPromptSubmit, Stop)
Зберігає повідомлення в Hexis під час розмови.

---

## Повний workflow імпорту сесії

```bash
# 1. Конвертувати
python3 _scripts/shared_tools/claude_code/convert_session.py \
  --input ~/.claude/projects/.../session.jsonl \
  --out /tmp/normalized.jsonl

# 2. Імпортувати
HEXIS_PATH=~/constellation/opus45/workspace/Hexis \
POSTGRES_PORT=43835 \
python3 _scripts/shared_tools/claude_code/import_jsonl.py \
  --path /tmp/normalized.jsonl \
  --skip-duplicates

# 3. Backup
./scripts/backup_memory.sh
```
