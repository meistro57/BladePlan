"""Job Tracker module.
Create and list jobs in the system.
"""

import argparse
from typing import List, Tuple

from ...config.config import POOL


class JobTracker:
    def __init__(self):
        self.cnx = POOL.get_connection()

    def create_job(self, name: str) -> int:
        cursor = self.cnx.cursor()
        cursor.execute("INSERT INTO jobs (name) VALUES (%s)", (name,))
        self.cnx.commit()
        job_id = cursor.lastrowid
        cursor.close()
        return job_id

    def list_jobs(self) -> List[Tuple]:
        cursor = self.cnx.cursor()
        cursor.execute("SELECT id, name, created_at FROM jobs")
        rows = cursor.fetchall()
        cursor.close()
        return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Tracker test harness")
    parser.add_argument("--create", help="Create a job with given name")
    args = parser.parse_args()

    tracker = JobTracker()
    if args.create:
        new_id = tracker.create_job(args.create)
        print(f"Created job {new_id}")
    else:
        for job in tracker.list_jobs():
            print(job)
