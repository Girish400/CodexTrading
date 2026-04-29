# Session Memory Design

## Goal

Preserve useful project context across sessions by capturing tool usage observations, compressing them into semantic summaries, and retrieving the most relevant knowledge for future work.

## What Is Stored

- Session metadata: title, objective, status, start time, end time
- Tool observations: tool name, observation kind, content, tags, metadata
- Semantic summaries: generated when a session is closed
- Pinned facts: durable project truths worth carrying forward
- Open items: unfinished work that should surface in later sessions

## Storage Model

The implementation stores memory in a SQLite database at `.gstrading/memory.db` by default.

Tables:

- `sessions`
- `observations`
- `summaries`
- `pinned_facts`
- `open_items`

## Semantic Retrieval

This implementation uses lightweight semantic retrieval with normalized token weights:

1. Tokenize summaries and incoming queries.
2. Remove common stop words.
3. Build normalized term-weight maps.
4. Rank summaries by overlap score plus recency ordering.

This gives useful retrieval without requiring an external embedding service. If you later add embeddings, the same storage model can hold vector references or precomputed embeddings.

## Workflow

1. Start a session:

```powershell
python main.py memory start --project GSTrading --title "Morning handoff" --objective "Continue rules engine design"
```

2. Record observations:

```powershell
python main.py memory observe --project GSTrading --session-id <id> --tool pytest --kind test --content "Ran pytest successfully"
python main.py memory observe --project GSTrading --session-id <id> --tool git --kind command --content "Updated src/gstrading/memory.py"
```

Automatic capture through a command wrapper:

```powershell
python main.py memory exec --project GSTrading --session-id <id> -- python -m pytest
```

Developer wrapper for the normal inner loop:

```powershell
.\dev.ps1 test
.\dev.ps1 lint
.\dev.ps1 build
.\dev.ps1 run -- python -m pytest tests/test_cli.py
```

3. Pin durable facts:

```powershell
python main.py memory pin --project GSTrading --category architecture --content "Market data ingestion uses ibapi and asyncio."
```

4. Track unfinished work:

```powershell
python main.py memory open-item --project GSTrading --session-id <id> --content "Add automatic shell observation capture"
```

5. Close the session and generate a semantic summary:

```powershell
python main.py memory close --project GSTrading --session-id <id>
```

6. Build a future-session brief:

```powershell
python main.py memory brief --project GSTrading --query "What matters before I continue the rules engine work?"
```

7. Close the active developer session when you want a handoff summary:

```powershell
.\dev.ps1 close
```

## Operational Notes

- Keep observations factual and concise.
- Do not store secrets in observation content or metadata.
- Prefer pinned facts for stable architecture decisions, environments, and recurring operating rules.
- Prefer open items for next actions, blockers, and unfinished verification work.
- Use `memory exec` when you want command usage and command output summarized automatically.
- Use `dev.ps1` or `dev.cmd` when you want common developer commands to be captured automatically without manually managing `memory exec`.
