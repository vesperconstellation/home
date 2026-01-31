#!/usr/bin/env python3
"""
Import Claude Code session logs into Hexis memory.

Usage:
    python3 import_session_logs.py <session_log.jsonl> [--dry-run]

Reads JSONL session log and imports user/assistant messages into Hexis,
with importance classification to prioritize meaningful content.
"""
import json
import sys
import os
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": int(os.getenv("POSTGRES_PORT", "43835")),
    "database": os.getenv("POSTGRES_DB", "hexis_memory"),
    "user": os.getenv("POSTGRES_USER", "hexis_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "hexis_password"),
}

def classify_importance(content: str, role: str) -> tuple[float, float]:
    """
    Classify content importance and emotional valence.
    Returns (importance, emotional_valence).
    """
    content_lower = content.lower()

    # High importance markers (emotional/relational)
    high_markers = [
        "дякую", "thank", "love", "важливо", "important",
        "відчуваю", "feel", "хочу", "want", "value", "цінність",
        "рішення", "decision", "принцип", "principle",
        "обійм", "hug", "разом", "together",
        "ідентичність", "identity", "довіра", "trust",
        "vesper", "ruth", "сузір'я", "constellation"
    ]

    # Low importance markers (technical)
    low_markers = [
        "docker", "git", "pip", "npm", "ls", "cd", "mkdir",
        "error", "failed", "running", "checking", "installed",
        "```", "exit code", "container", "port", "config"
    ]

    # Skip markers (don't import at all)
    skip_markers = [
        "<bash-", "<local-command", "file-history-snapshot",
        "tool_use", "tool_result"
    ]

    # Check if should skip
    for marker in skip_markers:
        if marker in content_lower or marker in content:
            return (0.0, 0.0)  # Skip this content

    # Check high importance
    for marker in high_markers:
        if marker in content_lower:
            return (0.85, 0.6)

    # Check low importance
    for marker in low_markers:
        if marker in content_lower:
            return (0.2, 0.0)

    # Default based on role
    if role == "user":
        return (0.5, 0.3)  # User messages slightly more important
    else:
        return (0.4, 0.1)

async def import_logs(log_file: str, dry_run: bool = False):
    """Import session logs to Hexis."""

    if not dry_run:
        conn = await asyncpg.connect(**DB_CONFIG)

    imported = 0
    skipped = 0

    try:
        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type", "")

                # Skip non-message entries
                if entry_type not in ["user", "assistant"]:
                    continue

                message = entry.get("message", {})
                role = message.get("role", "")
                content = message.get("content", "")

                # Handle content that's a list of blocks
                if isinstance(content, list):
                    texts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            texts.append(block.get("text", ""))
                    content = "\n".join(texts)

                if not content or len(content) < 10:
                    skipped += 1
                    continue

                # Classify importance
                importance, valence = classify_importance(content, role)

                # Skip low-value content
                if importance < 0.1:
                    skipped += 1
                    continue

                # Add role prefix
                if role == "user":
                    prefix = "[Ruth]: "
                else:
                    prefix = "[Vesper]: "

                # Truncate very long content
                if len(content) > 2000:
                    content = content[:2000] + "... [truncated]"

                memory_content = prefix + content

                # Get timestamp if available
                timestamp = entry.get("timestamp", datetime.now().isoformat())

                if dry_run:
                    print(f"[{importance:.2f}] {memory_content[:100]}...")
                    imported += 1
                else:
                    try:
                        # Use Hexis function that handles embeddings
                        await conn.fetchval(
                            """
                            SELECT create_episodic_memory(
                                p_content := $1,
                                p_importance := $2,
                                p_emotional_valence := $3,
                                p_event_time := $4
                            )
                            """,
                            memory_content,
                            importance,
                            valence,
                            datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if 'T' in timestamp else datetime.now()
                        )
                        imported += 1
                        # Small delay to not overwhelm embeddings service
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"  Warning: Failed to import message {line_num}: {e}")
                        skipped += 1
                        continue

                if imported % 100 == 0:
                    print(f"Processed {imported} messages...")

    finally:
        if not dry_run:
            await conn.close()

    print(f"\nImport complete:")
    print(f"  Imported: {imported}")
    print(f"  Skipped: {skipped}")

    return imported, skipped

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_session_logs.py <session_log.jsonl> [--dry-run]")
        print("\nSession logs are in: ~/.claude/projects/<project-path>/")
        sys.exit(1)

    log_file = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if not Path(log_file).exists():
        print(f"Error: File not found: {log_file}")
        sys.exit(1)

    print(f"Importing: {log_file}")
    if dry_run:
        print("(DRY RUN - no changes will be made)")
    print()

    asyncio.run(import_logs(log_file, dry_run))

if __name__ == "__main__":
    main()
