from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class TransactionIn(BaseModel):
    amount: float
    kind: str


@app.post("/transactions")
def create_transaction(tx: TransactionIn):
    return {"ok": True}


@app.get("/transactions")
def list_transactions():
    return []


@app.get("/balance")
def get_balance():
    return {"balance": 0}
