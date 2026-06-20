from fastapi import FastAPI

app = FastAPI(title="DevOps Eval CI App")


@app.get("/")
def hello():
    return {"message": "hello from devops-eval ci app"}


@app.get("/health")
def health():
    return {"status": "ok"}
