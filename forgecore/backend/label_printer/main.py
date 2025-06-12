"""Label Printer module.
Simulates printing labels for cut parts.
"""

import argparse

from ...config.config import POOL


class LabelPrinter:
    def __init__(self):
        self.cnx = POOL.get_connection()

    def print_labels_for_job(self, job_id: int):
        cursor = self.cnx.cursor()
        cursor.execute("SELECT id, part_length_inches FROM cut_parts WHERE job_id=%s", (job_id,))
        for part_id, length in cursor.fetchall():
            print(f"Printing label for part {part_id} - {length} in")
        cursor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Label Printer test harness")
    parser.add_argument("job_id", type=int, help="Job ID to print labels for")
    args = parser.parse_args()

    printer = LabelPrinter()
    printer.print_labels_for_job(args.job_id)
