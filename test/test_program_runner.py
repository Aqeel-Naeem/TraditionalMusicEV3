"""
Validates ev3_program_runner.py's upload+trigger mechanism using the
SMALLEST possible EV3 Classroom program, before trusting it with any
real Saron program.

Before running this:
  1. In EV3 Classroom, build the simplest possible test program: one
     "Move Motor for Duration" block on Port A, 1 second, then Stop.
     (Anything simple and safe to watch - the point is only to prove
     upload+trigger works, not to test real song logic.)
  2. Export/download it as a .rbf file to your computer.
  3. Set RBF_PATH below to that file's path.
  4. Set TEST_MAC to a brick you're OK watching move briefly.

Usage:
    python test/test_program_runner.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ev3_dc as ev3
from ev3_program_runner import upload_program, start_program

# ------------------------------------------------------------------
# EDIT THESE BEFORE RUNNING
# ------------------------------------------------------------------
RBF_PATH = "PUT_YOUR_TEST_RBF_PATH_HERE.rbf"
TEST_MAC = "00:16:53:41:95:2e"  # any brick you're OK watching move briefly
REMOTE_PATH = "/home/root/lms2012/prjs/EV3TestProgram/EV3TestProgram.rbf"
# ------------------------------------------------------------------


def main():
    if not os.path.isfile(RBF_PATH):
        print(f"RBF_PATH does not exist: {RBF_PATH}")
        print("Build a simple test program in EV3 Classroom first (see docstring).")
        return

    print("Connecting...")
    brick = ev3.EV3(protocol=ev3.BLUETOOTH, host=TEST_MAC)

    try:
        print(f"Uploading {RBF_PATH} -> {REMOTE_PATH} ...")
        upload_program(brick, RBF_PATH, REMOTE_PATH)
        print("Upload complete.")

        print("Starting program...")
        start_program(brick, REMOTE_PATH)
        print("Start command sent. Watch the brick now.")

        time.sleep(5)
        print("Done watching window. If the motor moved as expected, the")
        print("upload+trigger mechanism works.")

    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        raise
    finally:
        brick.__del__()
        print("Disconnected.")


if __name__ == "__main__":
    main()
