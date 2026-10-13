from fastapi import FastAPI

app = FastAPI(title="Ingryd")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
