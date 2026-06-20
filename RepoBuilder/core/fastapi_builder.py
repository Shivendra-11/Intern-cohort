"""Generate a runnable FastAPI ledger service under workspace."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.json_writer import JsonWriter

PROJECT_FILES: Dict[str, str] = {
    "requirements.txt": textwrap.dedent("""\
        fastapi>=0.110
        uvicorn>=0.27
        httpx>=0.27
        pytest>=8.0
    """),
    "pytest.ini": textwrap.dedent("""\
        [pytest]
        pythonpath = .
        testpaths = tests
    """),
    "models.py": textwrap.dedent("""\
        from typing import List, Literal, Optional

        from pydantic import BaseModel, Field


        class TransactionIn(BaseModel):
            \"\"\"Create payload — amount must be positive (gt=0).\"\"\"
            amount: float = Field(..., gt=0, description="Positive amount")
            type: Literal["credit", "debit"]
            description: Optional[str] = Field(default=None, max_length=200)


        class Transaction(TransactionIn):
            id: int


        class Balance(BaseModel):
            balance: float
            credits: float
            debits: float
            count: int
    """),
    "routes.py": textwrap.dedent("""\
        from itertools import count
        from typing import List

        from fastapi import APIRouter

        from models import Balance, Transaction, TransactionIn

        router = APIRouter()

        _transactions: List[Transaction] = []
        _ids = count(1)


        def reset_store() -> None:
            global _ids
            _transactions.clear()
            _ids = count(1)


        @router.post("/transactions", response_model=Transaction, status_code=201)
        def create_transaction(payload: TransactionIn) -> Transaction:
            tx = Transaction(id=next(_ids), **payload.model_dump())
            _transactions.append(tx)
            return tx


        @router.get("/transactions", response_model=List[Transaction])
        def list_transactions() -> List[Transaction]:
            return _transactions


        @router.get("/balance", response_model=Balance)
        def get_balance() -> Balance:
            credits = sum(t.amount for t in _transactions if t.type == "credit")
            debits = sum(t.amount for t in _transactions if t.type == "debit")
            return Balance(
                balance=credits - debits,
                credits=credits,
                debits=debits,
                count=len(_transactions),
            )
    """),
    "app.py": textwrap.dedent("""\
        from fastapi import FastAPI

        from routes import router

        app = FastAPI(title="Ledger Service", version="1.0.0")
        app.include_router(router)
    """),
    "README.md": textwrap.dedent("""\
        # Ledger Service (FastAPI)

        In-memory transaction ledger with Pydantic validation.

        ## Endpoints

        | Method | Path | Description |
        |--------|------|-------------|
        | POST | `/transactions` | Create transaction (422 if invalid) |
        | GET | `/transactions` | List all transactions |
        | GET | `/balance` | Credits minus debits |

        Body: `{ "amount": <float > 0>, "type": "credit"|"debit", "description"?: string }`

        ## Install

        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        ```

        ## Run

        ```bash
        uvicorn app:app --reload
        ```

        ```bash
        curl -X POST http://127.0.0.1:8000/transactions \\
          -H 'content-type: application/json' \\
          -d '{"amount": 100, "type": "credit"}'
        curl http://127.0.0.1:8000/balance
        ```

        ## Test

        ```bash
        pytest -q
        ```
    """),
    "tests/test_create_transaction.py": textwrap.dedent("""\
        from fastapi.testclient import TestClient

        from app import app
        from routes import reset_store

        client = TestClient(app)


        def setup_function():
            reset_store()


        def test_create_transaction_happy_path():
            resp = client.post(
                "/transactions", json={"amount": 50, "type": "credit"}
            )
            assert resp.status_code == 201
            body = resp.json()
            assert body["id"] == 1
            assert body["amount"] == 50


        def test_non_positive_amount_rejected():
            resp = client.post(
                "/transactions", json={"amount": 0, "type": "credit"}
            )
            assert resp.status_code == 422

            resp2 = client.post(
                "/transactions", json={"amount": -10, "type": "debit"}
            )
            assert resp2.status_code == 422
    """),
    "tests/test_get_transactions.py": textwrap.dedent("""\
        from fastapi.testclient import TestClient

        from app import app
        from routes import reset_store

        client = TestClient(app)


        def setup_function():
            reset_store()


        def test_list_transactions():
            client.post("/transactions", json={"amount": 10, "type": "debit"})
            client.post("/transactions", json={"amount": 20, "type": "credit"})
            resp = client.get("/transactions")
            assert resp.status_code == 200
            assert len(resp.json()) == 2
    """),
    "tests/test_balance.py": textwrap.dedent("""\
        from fastapi.testclient import TestClient

        from app import app
        from routes import reset_store

        client = TestClient(app)


        def setup_function():
            reset_store()


        def test_balance_after_mixed_transactions():
            client.post("/transactions", json={"amount": 100, "type": "credit"})
            client.post("/transactions", json={"amount": 30, "type": "debit"})
            client.post("/transactions", json={"amount": 10, "type": "debit"})
            balance = client.get("/balance").json()
            assert balance["credits"] == 100
            assert balance["debits"] == 40
            assert balance["balance"] == 60
            assert balance["count"] == 3
    """),
}


@dataclass
class BuildProof:
    test_command: str = "pytest -q"
    test_exit_code: int = 1
    test_stdout: str = ""
    test_stderr: str = ""
    smoke_command: str = ""
    smoke_exit_code: int = 1
    smoke_output: str = ""
    passed: Optional[int] = None
    failed: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "test_command": self.test_command,
            "test_exit_code": self.test_exit_code,
            "test_stdout": self.test_stdout,
            "test_stderr": self.test_stderr,
            "smoke_command": self.smoke_command,
            "smoke_exit_code": self.smoke_exit_code,
            "smoke_output": self.smoke_output,
            "passed": self.passed,
            "failed": self.failed,
        }


@dataclass
class FastAPIBuildResult:
    repo_name: str
    project_path: str
    files: List[str] = field(default_factory=list)
    status: str = "FAILED"
    proof: BuildProof = field(default_factory=BuildProof)

    def to_status_json(self) -> dict:
        return {
            "project": "fastapi",
            "repo_name": self.repo_name,
            "project_path": self.project_path,
            "status": self.status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "endpoints": [
                {"method": "POST", "path": "/transactions"},
                {"method": "GET", "path": "/transactions"},
                {"method": "GET", "path": "/balance"},
            ],
            "files": self.files,
            "proof": self.proof.to_dict(),
        }


class FastAPIBuilder:
    """Scaffold FastAPI ledger API and prove it with pytest."""

    ENDPOINTS = [
        ("POST", "/transactions"),
        ("GET", "/transactions"),
        ("GET", "/balance"),
    ]

    def __init__(self, workspace_root: str = "workspace") -> None:
        self.workspace_root = workspace_root
        self.json_writer = JsonWriter()

    def build(
        self,
        repo_path: str,
        *,
        run_proof: bool = True,
        output_dir: Optional[str] = None,
    ) -> FastAPIBuildResult:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"not a directory: {repo_path}")

        repo_name = self.repo_name(repo_path)
        project_path = output_dir or os.path.join(
            self.workspace_root,
            repo_name,
            "generated_projects",
            "fastapi",
        )

        files = self._write_project(project_path)
        proof = BuildProof()
        status = "GENERATED"

        if run_proof:
            proof = self._prove(project_path)
            status = "SUCCESS" if proof.test_exit_code == 0 else "FAILED"

        result = FastAPIBuildResult(
            repo_name=repo_name,
            project_path=os.path.abspath(project_path),
            files=files,
            status=status,
            proof=proof,
        )

        self.json_writer.write(
            os.path.join(project_path, "status.json"),
            result.to_status_json(),
        )
        return result

    @staticmethod
    def repo_name(repo_path: str) -> str:
        return os.path.basename(repo_path.rstrip(os.sep)) or "repository"

    def _write_project(self, project_path: str) -> List[str]:
        created: List[str] = []
        for rel, content in PROJECT_FILES.items():
            path = os.path.join(project_path, rel)
            os.makedirs(os.path.dirname(path) or project_path, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            created.append(os.path.abspath(path))
        return created

    def _prove(self, project_path: str) -> BuildProof:
        proof = BuildProof()
        venv = os.path.join(project_path, ".venv")
        subprocess.run(
            [sys.executable, "-m", "venv", venv],
            cwd=project_path,
            check=False,
            capture_output=True,
        )
        pip = os.path.join(venv, "bin", "pip")
        pytest_bin = os.path.join(venv, "bin", "pytest")
        python = os.path.join(venv, "bin", "python")

        if not os.path.isfile(pip):
            proof.test_stderr = "Could not create virtualenv"
            return proof

        subprocess.run(
            [pip, "install", "-q", "-r", "requirements.txt"],
            cwd=project_path,
            check=False,
            capture_output=True,
        )

        proc = subprocess.run(
            [pytest_bin, "-q"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        proof.test_command = "pytest -q"
        proof.test_exit_code = proc.returncode
        proof.test_stdout = (proc.stdout or "").strip()
        proof.test_stderr = (proc.stderr or "").strip()
        self._parse_pytest_counts(proof)

        # Smoke: hit endpoints via inline TestClient script.
        smoke_script = textwrap.dedent(
            """
            from fastapi.testclient import TestClient
            from app import app
            from routes import reset_store
            reset_store()
            c = TestClient(app)
            r1 = c.post("/transactions", json={"amount": 25, "type": "credit"})
            r2 = c.get("/transactions")
            r3 = c.get("/balance")
            assert r1.status_code == 201, r1.text
            assert r2.status_code == 200
            assert r3.json()["balance"] == 25
            print("POST /transactions ->", r1.status_code, r1.json())
            print("GET /balance ->", r3.status_code, r3.json())
            """
        ).strip()
        smoke = subprocess.run(
            [python, "-c", smoke_script],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        proof.smoke_command = "TestClient smoke (POST/GET /transactions, GET /balance)"
        proof.smoke_exit_code = smoke.returncode
        proof.smoke_output = ((smoke.stdout or "") + (smoke.stderr or "")).strip()

        return proof

    @staticmethod
    def _parse_pytest_counts(proof: BuildProof) -> None:
        import re

        combined = proof.test_stdout + "\n" + proof.test_stderr
        m = re.search(r"(\d+) passed", combined)
        if m:
            proof.passed = int(m.group(1))
        m = re.search(r"(\d+) failed", combined)
        if m:
            proof.failed = int(m.group(1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate FastAPI ledger project")
    ap.add_argument("repo", help="repository path (used for workspace repo_name)")
    ap.add_argument("--workspace", default="workspace")
    ap.add_argument("--output-dir", help="override project output directory")
    ap.add_argument("--no-proof", action="store_true", help="skip test/smoke proof")
    args = ap.parse_args(argv)

    try:
        result = FastAPIBuilder(workspace_root=args.workspace).build(
            args.repo,
            run_proof=not args.no_proof,
            output_dir=args.output_dir,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"FastAPI project {result.status}")
    print(f"  path   : {result.project_path}")
    print(f"  status : {os.path.join(result.project_path, 'status.json')}")
    if result.proof.test_stdout:
        print(f"  tests  : {result.proof.test_stdout}")
    if result.proof.smoke_output:
        print(f"  smoke  : {result.proof.smoke_output}")
    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
