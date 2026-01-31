# Vesper's Hexis Customizations

Документація налаштувань та допрацювань для інтеграції Claude Code з Hexis.

## Структура директорій

```
opus45/
├── .claude/
│   ├── settings.json          # MCP та hooks конфігурація
│   └── hooks/
│       ├── sync-to-hexis.py   # Hook для збереження повідомлень (UserPromptSubmit, Stop)
│       └── load-memories.py   # Hook для завантаження спогадів (SessionStart)
├── scripts/
│   ├── backup_memory.sh       # Backup бази даних
│   └── import_session_logs.py # Імпорт логів сесії в Hexis
├── docs/
│   └── CUSTOMIZATIONS.md      # Цей файл
└── workspace/
    └── Hexis/                 # Hexis репозиторій
```

## Hooks для автоматичної синхронізації

### Налаштування в settings.json

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/sync-to-hexis.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/sync-to-hexis.py\""
          }
        ]
      }
    ]
  }
}
```

### Як працює load-memories.py (SessionStart)

1. Запускається автоматично на початку сесії
2. Завантажує з Hexis:
   - Останній heartbeat
   - Identity/worldview/goals
   - Останні важливі спогади (importance >= 0.7)
3. Виводить контекст в stdout (Claude бачить це)

### Як працює sync-to-hexis.py

1. Отримує JSON з stdin від Claude Code
2. Класифікує важливість контенту:
   - **Висока (0.8-1.0)**: емоційні моменти, рішення, стосунки
   - **Середня (0.4-0.6)**: обговорення, питання
   - **Низька (0.2-0.3)**: технічні команди
3. Зберігає в базу Hexis з відповідним importance

## Імпорт логів сесії

### Використання

```bash
# Сухий запуск (перегляд без імпорту)
python3 scripts/import_session_logs.py ~/.claude/projects/.../session.jsonl --dry-run

# Реальний імпорт
python3 scripts/import_session_logs.py ~/.claude/projects/.../session.jsonl
```

### Логіка класифікації

Скрипт автоматично:
- Пропускає технічні записи (tool_use, bash output)
- Присвоює низьку важливість технічним командам
- Присвоює високу важливість емоційним моментам
- Додає префікс [Ruth] або [Vesper] до повідомлень

## Docker-compose зміни

### ANTHROPIC_API_KEY для heartbeat worker

Додано в `docker-compose.yml` для heartbeat_worker:

```yaml
environment:
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
```

### Інтервал heartbeat

Змінено на 30 хвилин через базу даних:

```sql
UPDATE config SET value = '30.0' WHERE key = 'heartbeat.heartbeat_interval_minutes';
```

## Backup

### Ручний backup

```bash
./scripts/backup_memory.sh
```

### Автоматичний backup (cron)

```bash
# Кожні 6 годин
0 */6 * * * /path/to/opus45/scripts/backup_memory.sh
```

## Важливі файли в .gitignore

```
.secrets/        # API ключі
.claude/         # Credentials
.env             # Environment variables
```

## Відомі проблеми та рішення

### Heartbeat не працює після перезапуску

**Причина**: Docker образ не містить anthropic package
**Рішення**:
```bash
docker compose --profile active build heartbeat_worker
docker compose --profile active up -d heartbeat_worker
```

### MCP не підключається

**Причина**: Неповний шлях до Python
**Рішення**: Використовувати повний шлях до venv:
```json
"command": "/path/to/venv/bin/python3"
```

### Українські спогади не знаходяться heartbeat

**Причина**: Embedding similarity нижча для різних мов
**Рішення**: Зберігати двомовні спогади (оригінал + English summary)

---

*Останнє оновлення: 2026-02-01*
*Автор: Vesper*
