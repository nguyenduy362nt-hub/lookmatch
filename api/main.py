from fastapi import FastAPI

app = FastAPI(title="LookMatch API", version="0.1.0")


@app.get("/")
def root():
    return {"name": "LookMatch API", "version": app.version}


@app.get("/health")
def health():
    return {"status": "ok"}
