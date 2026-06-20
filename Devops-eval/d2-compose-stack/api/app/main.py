from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg2
import psycopg2.extras

app = FastAPI(title="DevOps Eval API")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/devops_eval",
)


def get_conn():
    return psycopg2.connect(DATABASE_URL)


class JobCreate(BaseModel):
    payload: dict = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/jobs", status_code=201)
def create_job(body: JobCreate):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO jobs (payload, status) VALUES (%s, 'pending') RETURNING id, status",
                (psycopg2.extras.Json(body.payload),),
            )
            row = cur.fetchone()
            conn.commit()
    return {"job_id": row["id"], "status": row["status"]}


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, payload, status, created_at FROM jobs WHERE id = %s", (job_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job_id": row["id"], "payload": row["payload"], "status": row["status"], "created_at": str(row["created_at"])}
