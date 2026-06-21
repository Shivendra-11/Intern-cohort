"""Generate a runnable Node/Express ledger API under workspace."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.json_writer import JsonWriter

PROJECT_FILES: dict[str, str] = {
    "package.json": textwrap.dedent("""\
        {
          "name": "ledger-node-api",
          "version": "1.0.0",
          "description": "In-memory ledger API with Express and Zod",
          "main": "server.js",
          "scripts": {
            "start": "node server.js",
            "test": "jest --runInBand"
          },
          "dependencies": {
            "express": "^4.19.2",
            "zod": "^3.23.8"
          },
          "devDependencies": {
            "jest": "^29.7.0",
            "supertest": "^7.0.0"
          }
        }
    """),
    "server.js": textwrap.dedent("""\
        'use strict';

        const express = require('express');
        const transactionsRouter = require('./routes/transactions');

        const app = express();
        app.use(express.json());
        app.use('/', transactionsRouter);

        const PORT = process.env.PORT || 3000;

        if (require.main === module) {
          app.listen(PORT, () => {
            console.log(`Ledger API listening on http://127.0.0.1:${PORT}`);
          });
        }

        module.exports = app;
    """),
    "routes/transactions.js": textwrap.dedent("""\
        'use strict';

        const express = require('express');
        const { z } = require('zod');

        const router = express.Router();

        const TransactionSchema = z.object({
          amount: z.number().positive('amount must be greater than 0'),
          type: z.enum(['credit', 'debit']),
          description: z.string().max(200).optional().nullable(),
        });

        const transactions = [];
        let nextId = 1;

        function resetStore() {
          transactions.length = 0;
          nextId = 1;
        }

        router.post('/transactions', (req, res) => {
          const parsed = TransactionSchema.safeParse(req.body);
          if (!parsed.success) {
            return res.status(400).json({ error: parsed.error.flatten() });
          }
          const tx = {
            id: nextId++,
            ...parsed.data,
            description: parsed.data.description ?? null,
          };
          transactions.push(tx);
          return res.status(201).json(tx);
        });

        router.get('/transactions', (_req, res) => {
          res.json(transactions);
        });

        router.get('/balance', (_req, res) => {
          const credits = transactions
            .filter((t) => t.type === 'credit')
            .reduce((sum, t) => sum + t.amount, 0);
          const debits = transactions
            .filter((t) => t.type === 'debit')
            .reduce((sum, t) => sum + t.amount, 0);
          res.json({
            balance: credits - debits,
            credits,
            debits,
            count: transactions.length,
          });
        });

        module.exports = router;
        module.exports.resetStore = resetStore;
    """),
    "README.md": textwrap.dedent("""\
        # Ledger API (Node / Express / Zod)

        In-memory transaction ledger with Zod validation and Jest + Supertest tests.

        ## Endpoints

        | Method | Path | Description |
        |--------|------|-------------|
        | POST | `/transactions` | Create transaction (400 on invalid input) |
        | GET | `/transactions` | List all transactions |
        | GET | `/balance` | Credits minus debits |

        Body: `{ "amount": <number > 0>, "type": "credit"|"debit", "description"?: string }`

        ## Install

        ```bash
        npm install
        ```

        ## Run

        ```bash
        npm start
        ```

        ```bash
        curl -X POST http://127.0.0.1:3000/transactions \\
          -H 'content-type: application/json' \\
          -d '{"amount": 100, "type": "credit"}'
        curl http://127.0.0.1:3000/balance
        ```

        ## Test

        ```bash
        npm test
        ```
    """),
    "tests/test_create.test.js": textwrap.dedent("""\
        'use strict';

        const request = require('supertest');
        const app = require('../server');
        const { resetStore } = require('../routes/transactions');

        beforeEach(() => resetStore());

        test('creates a transaction', async () => {
          const res = await request(app)
            .post('/transactions')
            .send({ amount: 25, type: 'credit' });
          expect(res.status).toBe(201);
          expect(res.body.id).toBe(1);
          expect(res.body.amount).toBe(25);
        });

        test('rejects non-positive amount with 400', async () => {
          const zero = await request(app)
            .post('/transactions')
            .send({ amount: 0, type: 'credit' });
          expect(zero.status).toBe(400);

          const negative = await request(app)
            .post('/transactions')
            .send({ amount: -5, type: 'debit' });
          expect(negative.status).toBe(400);
        });
    """),
    "tests/test_list.test.js": textwrap.dedent("""\
        'use strict';

        const request = require('supertest');
        const app = require('../server');
        const { resetStore } = require('../routes/transactions');

        beforeEach(() => resetStore());

        test('lists transactions', async () => {
          await request(app).post('/transactions').send({ amount: 10, type: 'debit' });
          const res = await request(app).get('/transactions');
          expect(res.status).toBe(200);
          expect(res.body).toHaveLength(1);
        });
    """),
    "tests/test_balance.test.js": textwrap.dedent("""\
        'use strict';

        const request = require('supertest');
        const app = require('../server');
        const { resetStore } = require('../routes/transactions');

        beforeEach(() => resetStore());

        test('computes balance as credits minus debits', async () => {
          await request(app).post('/transactions').send({ amount: 100, type: 'credit' });
          await request(app).post('/transactions').send({ amount: 40, type: 'debit' });
          const res = await request(app).get('/balance');
          expect(res.body.balance).toBe(60);
          expect(res.body.count).toBe(2);
        });
    """),
}


@dataclass
class BuildProof:
    test_command: str = "npm test"
    test_exit_code: int = 1
    test_stdout: str = ""
    test_stderr: str = ""
    smoke_command: str = ""
    smoke_exit_code: int = 1
    smoke_output: str = ""
    passed: int | None = None
    failed: int | None = None

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
class NodeBuildResult:
    repo_name: str
    project_path: str
    files: list[str] = field(default_factory=list)
    status: str = "FAILED"
    proof: BuildProof = field(default_factory=BuildProof)

    def to_status_json(self) -> dict:
        return {
            "project": "node",
            "repo_name": self.repo_name,
            "project_path": self.project_path,
            "status": self.status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack": {
                "framework": "express",
                "validation": "zod",
                "testing": "jest+supertest",
            },
            "endpoints": [
                {"method": "POST", "path": "/transactions"},
                {"method": "GET", "path": "/transactions"},
                {"method": "GET", "path": "/balance"},
            ],
            "files": self.files,
            "proof": self.proof.to_dict(),
        }


class NodeBuilder:
    """Scaffold Express + Zod ledger API and prove with Jest."""

    def __init__(self, workspace_root: str = "workspace") -> None:
        self.workspace_root = workspace_root
        self.json_writer = JsonWriter()

    def build(
        self,
        repo_path: str,
        *,
        run_proof: bool = True,
        output_dir: str | None = None,
    ) -> NodeBuildResult:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"not a directory: {repo_path}")

        repo_name = self.repo_name(repo_path)
        project_path = output_dir or os.path.join(
            self.workspace_root,
            repo_name,
            "generated_projects",
            "node",
        )

        files = self._write_project(project_path)
        proof = BuildProof()
        status = "GENERATED"

        if run_proof:
            proof = self._prove(project_path)
            status = "SUCCESS" if proof.test_exit_code == 0 else "FAILED"

        result = NodeBuildResult(
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

    def _write_project(self, project_path: str) -> list[str]:
        created: list[str] = []
        for rel, content in PROJECT_FILES.items():
            path = os.path.join(project_path, rel)
            os.makedirs(os.path.dirname(path) or project_path, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            created.append(os.path.abspath(path))
        return created

    def _prove(self, project_path: str) -> BuildProof:
        proof = BuildProof()

        install = subprocess.run(
            ["npm", "install"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        if install.returncode != 0:
            proof.test_stderr = (install.stderr or install.stdout or "npm install failed").strip()
            return proof

        proc = subprocess.run(
            ["npm", "test", "--", "--runInBand"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        proof.test_command = "npm test -- --runInBand"
        proof.test_exit_code = proc.returncode
        proof.test_stdout = (proc.stdout or "").strip()
        proof.test_stderr = (proc.stderr or "").strip()
        self._parse_jest_counts(proof)

        smoke_script = textwrap.dedent(
            """
            const request = require('supertest');
            const app = require('./server');
            const { resetStore } = require('./routes/transactions');
            (async () => {
              resetStore();
              const created = await request(app)
                .post('/transactions')
                .send({ amount: 30, type: 'credit' });
              const listed = await request(app).get('/transactions');
              const balance = await request(app).get('/balance');
              if (created.status !== 201) throw new Error('POST failed: ' + created.status);
              if (listed.status !== 200) throw new Error('GET list failed');
              if (balance.body.balance !== 30) throw new Error('balance mismatch');
              console.log('POST /transactions ->', created.status, created.body);
              console.log('GET /balance ->', balance.status, balance.body);
            })().catch((e) => { console.error(e); process.exit(1); });
            """
        ).strip()
        smoke = subprocess.run(
            ["node", "-e", smoke_script],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        proof.smoke_command = "Supertest smoke (POST/GET /transactions, GET /balance)"
        proof.smoke_exit_code = smoke.returncode
        proof.smoke_output = ((smoke.stdout or "") + (smoke.stderr or "")).strip()

        return proof

    @staticmethod
    def _parse_jest_counts(proof: BuildProof) -> None:
        combined = proof.test_stdout + "\n" + proof.test_stderr
        m = re.search(r"Tests:\s+(?:(\d+) failed,\s*)?(\d+) passed", combined)
        if m:
            proof.failed = int(m.group(1) or 0)
            proof.passed = int(m.group(2))
        m = re.search(r"(\d+) passed,\s*(\d+) total", combined)
        if m and proof.passed is None:
            proof.passed = int(m.group(1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate Node/Express ledger project")
    ap.add_argument("repo", help="repository path (used for workspace repo_name)")
    ap.add_argument("--workspace", default="workspace")
    ap.add_argument("--output-dir", help="override project output directory")
    ap.add_argument("--no-proof", action="store_true", help="skip test/smoke proof")
    args = ap.parse_args(argv)

    try:
        result = NodeBuilder(workspace_root=args.workspace).build(
            args.repo,
            run_proof=not args.no_proof,
            output_dir=args.output_dir,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Node project {result.status}")
    print(f"  path   : {result.project_path}")
    print(f"  status : {os.path.join(result.project_path, 'status.json')}")
    if result.proof.test_stdout:
        print(f"  tests  : {result.proof.test_stdout.splitlines()[-3:]}")
    if result.proof.smoke_output:
        print(f"  smoke  : {result.proof.smoke_output}")
    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
