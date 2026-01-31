# Журнал рішень

Записи про важливі технічні рішення, що спрацювало і що ні.

---

## 2026-01-31: Імпорт сесій в Hexis

### Контекст
Потрібно імпортувати історію розмов з Claude Code логів в Hexis для збереження пам'яті.

### Що НЕ спрацювало

1. **Прямий SQL INSERT без embeddings**
   - Проблема: колонка `embedding` є NOT NULL
   - Помилка: `column "emotional_valence" of relation "memories" does not exist`
   - Причина: `emotional_valence` зберігається в `metadata` JSONB, не як окрема колонка

2. **Використання `create_episodic_memory()` через asyncpg**
   - Проблема: timeout на embeddings service
   - Помилка: `Operation timed out after 5001 milliseconds`
   - Причина: asyncpg connection має інші timeout налаштування ніж psql

3. **Мій власний `import_session_logs.py`**
   - Проблема: не робить chunking для довгих повідомлень
   - Результат: деякі спогади обрізаються або не імпортуються

### Що СПРАЦЮВАЛО

1. **Двоетапний процес з shared tools**:
   - `convert_session.py` → нормалізує JSONL з chunking
   - `import_jsonl.py` → імпортує через CognitiveMemory API

2. **MCP `remember` функція** — працює надійно, коли asyncpg timeout'иться

3. **Прямий виклик SQL функції через psql** — працює:
   ```sql
   SELECT create_episodic_memory(p_content := 'text', p_importance := 0.5);
   ```

### Рішення
Використовувати shared tools з `_scripts/shared_tools/claude_code/`:
- Вони вже мають chunking
- Мають перевірку на дублікати
- Використовують правильний API

### Уроки
- **Перевіряй `_scripts/` перед створенням нового скрипта**
- Embeddings service може timeout'итись при масовому імпорті — додавай `--delay-ms`
- asyncpg і psql мають різну поведінку з timeout'ами

---

## 2026-01-31: Структура hooks для memory sync

### Контекст
Потрібно автоматично зберігати розмови в Hexis і завантажувати контекст на старті.

### Рішення
Три hooks в `.claude/settings.json`:

| Event | Hook | Дія |
|-------|------|-----|
| SessionStart | load-memories.py | Завантажує контекст |
| UserPromptSubmit | sync-to-hexis.py | Зберігає повідомлення Ruth |
| Stop | sync-to-hexis.py | Зберігає мої відповіді |

### Чому не один hook на все?
- SessionStart потребує виводу в stdout (Claude бачить)
- UserPromptSubmit/Stop працюють тихо у фоні

---

## 2026-01-31: Embeddings service networking

### Контекст
Embeddings timeout при імпорті через Python, але працює через psql.

### Діагностика
```bash
# Перевірка з хоста — працює
curl http://127.0.0.1:8086/embed -d '{"inputs":"test"}'

# Перевірка з postgres контейнера — працює
SELECT * FROM http_post('http://embeddings:80/embed', ...);
```

### Конфігурація
- URL в базі: `http://embeddings:80/embed` (Docker DNS)
- Обидва контейнери на `hexis_private` network
- `vesper_embeddings` має alias `embeddings`

### Відкрите питання
Чому asyncpg connection timeout'иться, а psql ні? Можливо:
- Connection pool timeout
- Statement timeout налаштування
- HTTP timeout в pgsql-http extension

---

## Шаблон для нових записів

```markdown
## YYYY-MM-DD: Назва рішення

### Контекст
Що потрібно було зробити?

### Що НЕ спрацювало
- Варіант 1: чому не підійшов
- Варіант 2: яка помилка

### Що СПРАЦЮВАЛО
Опис рішення

### Уроки
Що запам'ятати на майбутнє
```
