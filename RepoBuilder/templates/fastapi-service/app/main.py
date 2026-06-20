"""A small transaction-ledger service built with FastAPI.

Endpoints:
  POST /transactions   create a transaction (validated)
  GET  /transactions   list all transactions
  GET  /balance        current balance (credits - debits)

State is kept in memory (a simple list) to keep the example self-contained.
Written to run on Python 3.9+ (uses typing.Optional / typing.List, not PEP 604).
"""
from __future__ import annotations

from itertools import count
from typing import List, Literal, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Ledger Service", version="1.0.0")

# --- in-memory store ---------------------------------------------------------
_transactions: List["Transaction"] = []
_ids = count(1)


def reset_store() -> None:
    """Clear all state. Used by tests for isolation."""
    global _ids
    _transactions.clear()
    _ids = count(1)


# --- models / validation -----------------------------------------------------
class TransactionIn(BaseModel):
    """Input payload. Pydantic enforces these rules and FastAPI returns 422 on failure."""
    amount: float = Field(..., gt=0, description="Positive amount of money")
    type: Literal["credit", "debit"]
    description: Optional[str] = Field(default=None, max_length=200)


class Transaction(TransactionIn):
    id: int


class Balance(BaseModel):
    balance: float
    credits: float
    debits: float
    count: int


# --- routes ------------------------------------------------------------------
@app.post("/transactions", response_model=Transaction, status_code=201)
def create_transaction(payload: TransactionIn) -> Transaction:
    tx = Transaction(id=next(_ids), **payload.model_dump())
    _transactions.append(tx)
    return tx


@app.get("/transactions", response_model=List[Transaction])
def list_transactions() -> List[Transaction]:
    return _transactions


@app.get("/balance", response_model=Balance)
def get_balance() -> Balance:
    credits = sum(t.amount for t in _transactions if t.type == "credit")
    debits = sum(t.amount for t in _transactions if t.type == "debit")
    return Balance(
        balance=credits - debits,
        credits=credits,
        debits=debits,
        count=len(_transactions),
    )
