"""
Focused diagnostic: plays ONE Saron note at a time via the real on-brick
timeline path (same compile_song_timelines/play_song used by production
songs), so a single controller/hitter move can be watched in isolation
after a bytecode fix - without running the full song and its repeated
motor stress.

Usage:
    python test/test_single_saron_note.py "Saron 5"

If no note name is given, defaults to "Saron 5" (right pair, angle -45),
since that is the pair/angle that was misbehaving.
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ev3 import EV3
from songs import compile_song_timelines, play_song


def main():
    note_name = sys.argv[1] if len(sys.argv) > 1 else "Saron 5"

    print("=" * 65)
    print("SINGLE SARON NOTE TEST")
    print("=" * 65)
    print(f"Note: {note_name}")

    ev3_system = EV3()
    single_note_song = [
        {"instrument": "SARON", "note": note_name, "beat": 0.0},
    ]

    try:
        print("\n[1/3] Connecting to EV3 bricks...")
        ev3_system.connect()
        print("Connected bricks:", list(ev3_system._bricks.keys()))

        print("\n[2/3] Compiling single-note timeline...")
        timelines = compile_song_timelines(single_note_song)
        for mac, bytecode in timelines.items():
            print(f"  * Brick {mac}: {len(bytecode)} bytes bytecode")

        print("\n[3/3] Playing single note...")
        print("Watch: controller should swing to its position, hitter should")
        print("strike and return. Ctrl+C immediately if anything looks wrong.\n")

        start_time = time.perf_counter()
        play_song(ev3_system, single_note_song)
        elapsed = time.perf_counter() - start_time

        print(f"\nCompleted in {elapsed:.2f} seconds.")
        print("=" * 65)

    except KeyboardInterrupt:
        print("\nInterrupted by user! Stopping all motors immediately...")
        ev3_system.stop_all_motors()
    except Exception as e:
        print(f"\nError during motor test: {e}")
        ev3_system.stop_all_motors()
        raise
    finally:
        print("\nDisconnecting EV3 bricks...")
        ev3_system.disconnect()
        print("Done.")


if __name__ == "__main__":
    main()
