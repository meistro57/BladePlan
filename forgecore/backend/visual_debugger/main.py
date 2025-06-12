"""Visual Debugger module.
Placeholder for visualizing cut plans.
"""

import argparse

from ...config.config import POOL


class VisualDebugger:
    def __init__(self):
        self.cnx = POOL.get_connection()

    def show_latest_plan(self):
        print("Showing latest cut plan... (placeholder)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visual Debugger test harness")
    parser.add_argument("--show", action="store_true", help="Show plan")
    args = parser.parse_args()

    debugger = VisualDebugger()
    if args.show:
        debugger.show_latest_plan()
    else:
        print("Nothing to do. Use --show to display plan.")
