## Приложение оценки и разметки поисковой выдачи 

## Установка для разработки:

- Устанавливаем [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Устанавливаем зависимости

```bash
uv sync
```

- Настраивам перемнные в `.env`

```bash
cp .env.example .env
```

- Запуск

```bash
uvicorn src.main:app --port=8000 --reload
```
