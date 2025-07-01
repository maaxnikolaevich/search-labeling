## Search labeling app

## Installing:

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Install deps

```bash
uv sync
```

- Setting vars in `.env`

```bash
cp .env.example .env
```

- Launch 🚀

```bash
cd src && uvicorn main:app --port=8000 --reload
```

- Launch with Docker through make
```bash
make build
```
```bash
make run
```
- Apply migrations
```bash
make migrate
```
