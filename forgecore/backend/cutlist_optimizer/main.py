"""Cutlist Optimizer module.
Loads parts and available materials from the database
and matches best cuts from available stock.
"""

import argparse
from typing import List, Tuple

from ...config.config import POOL


class CutlistOptimizer:
    def __init__(self):
        self.cnx = POOL.get_connection()

    def get_parts_and_stock(self) -> Tuple[List[Tuple], List[Tuple]]:
        """Load cut parts and materials from DB."""
        cursor = self.cnx.cursor()
        cursor.execute("SELECT id, part_length_inches, job_id FROM cut_parts")
        parts = cursor.fetchall()
        cursor.execute("SELECT id, length_inches FROM materials WHERE is_remnant=0")
        stock = cursor.fetchall()
        cursor.close()
        return parts, stock

    def optimize(self):
        """Placeholder optimization algorithm."""
        parts, stock = self.get_parts_and_stock()
        # Basic first-fit decreasing algorithm (placeholder)
        parts = sorted(parts, key=lambda x: x[1], reverse=True)
        assignments = []
        for part in parts:
            for mat in stock:
                if mat[1] >= part[1]:
                    assignments.append((part[0], mat[0]))
                    mat_list = list(mat)
                    mat_list[1] -= part[1]
                    stock[stock.index(mat)] = tuple(mat_list)
                    break
        return assignments


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cutlist Optimizer test harness")
    parser.add_argument("--run", action="store_true", help="Run optimization")
    args = parser.parse_args()

    optimizer = CutlistOptimizer()
    if args.run:
        result = optimizer.optimize()
        print("Assignments:", result)
    else:
        parts, stock = optimizer.get_parts_and_stock()
        print("Parts:", parts)
        print("Stock:", stock)
