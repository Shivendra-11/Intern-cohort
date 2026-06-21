import os
import time

import psycopg2

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/devops_eval",
)
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "2"))


def process_pending():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE jobs SET status = 'processed'
                WHERE id = (
                    SELECT id FROM jobs WHERE status = 'pending'
                    ORDER BY id LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id
                """
            )
            row = cur.fetchone()
            conn.commit()
            if row:
                job_id = row[0]
                print(f"processed job {job_id}", flush=True)
                return job_id
    return None


def main():
    print("worker started", flush=True)
    while True:
        try:
            process_pending()
        except Exception as exc:
            print(f"worker error: {exc}", flush=True)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
