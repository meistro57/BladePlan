"""Drawing Parser module.
Simulate parsing a drawing file and extracting cut lengths.
"""

import argparse
import random
from pathlib import Path

from ...config.config import POOL


class DrawingParser:
    def __init__(self, drawings_dir: str = "./drawings"):
        self.drawings_dir = Path(drawings_dir)
        self.cnx = POOL.get_connection()

    def parse_drawing(self, filename: str) -> int:
        """Mock parse the drawing and return a random cut length in inches."""
        # Real implementation would open PDF/DXF and parse geometry
        return random.randint(10, 240)

    def process_unparsed_drawings(self):
        cursor = self.cnx.cursor()
        cursor.execute("SELECT id, filename FROM drawings WHERE parsed=0")
        for drawing_id, fname in cursor.fetchall():
            length = self.parse_drawing(fname)
            cursor.execute(
                "INSERT INTO cut_parts (part_length_inches, job_id) "
                "SELECT %s, job_id FROM drawings WHERE id=%s",
                (length, drawing_id),
            )
            cursor.execute("UPDATE drawings SET parsed=1 WHERE id=%s", (drawing_id,))
        self.cnx.commit()
        cursor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drawing Parser test harness")
    parser.add_argument("--process", action="store_true", help="Process drawings")
    args = parser.parse_args()

    parser_obj = DrawingParser()
    if args.process:
        parser_obj.process_unparsed_drawings()
        print("Processed drawings.")
    else:
        print("Nothing to do. Use --process to parse drawings.")
