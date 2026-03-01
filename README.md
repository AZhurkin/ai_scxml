# LangGraph vs Statechart (SCXML) — примеры 1–30

Этот проект содержит 30 примеров, где **одна и та же задача** реализована:
- слева: на **LangGraph** (через `StateGraph`)
- справа: на **Statechart** (SCXML + наш минимальный движок)

## Установка

```bash
pip install -r requirements.txt
```

> Примечание: `langgraph` подтянется из PyPI. Движок statechart входит в репозиторий.

## Запуск

В каждом примере:
- `python run_langgraph.py`
- `python run_statechart.py`

Примеры 15, 17 и 19 усилены краевыми случаями (компенсации/приоритет событий/пороговый join).
