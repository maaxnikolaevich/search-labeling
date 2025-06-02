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
cd src && uvicorn main:app --port=8000 --reload
```

- Запуск в Docker через make
```bash
make build
```
```bash
make run
```
- Накатываем миграции
```bash
make migrate
```