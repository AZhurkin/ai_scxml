# LangGraph vs Statechart (SCXML) 

Этот проект содержит примеры, где **одна и та же задача** реализована:
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
