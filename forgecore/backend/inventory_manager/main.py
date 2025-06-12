"""Inventory Manager module.
Returns lists of available stock and remnants.
"""

import argparse
from typing import List, Tuple

from ...config.config import POOL


class InventoryManager:
    def __init__(self):
        self.cnx = POOL.get_connection()

    def get_stock(self, include_remnants: bool = True) -> List[Tuple]:
        cursor = self.cnx.cursor()
        if include_remnants:
            cursor.execute("SELECT id, length_inches, is_remnant FROM materials")
        else:
            cursor.execute("SELECT id, length_inches, is_remnant FROM materials WHERE is_remnant=0")
        rows = cursor.fetchall()
        cursor.close()
        return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inventory Manager test harness")
    parser.add_argument("--no-remnants", action="store_true", help="Exclude remnants")
    args = parser.parse_args()

    manager = InventoryManager()
    stock = manager.get_stock(include_remnants=not args.no_remnants)
    print("Stock:")
    for row in stock:
        print(row)
