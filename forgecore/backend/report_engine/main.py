"""Report Engine module.
Generates simple job reports.
"""

import argparse

from ...config.config import POOL


class ReportEngine:
    def __init__(self):
        self.cnx = POOL.get_connection()

    def job_report(self, job_id: int):
        cursor = self.cnx.cursor()
        cursor.execute(
            "SELECT part_length_inches FROM cut_parts WHERE job_id=%s", (job_id,)
        )
        lengths = [row[0] for row in cursor.fetchall()]
        cursor.close()
        total = sum(lengths)
        print(f"Job {job_id} total inches: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Report Engine test harness")
    parser.add_argument("job_id", type=int, help="Job ID to report on")
    args = parser.parse_args()

    engine = ReportEngine()
    engine.job_report(args.job_id)
