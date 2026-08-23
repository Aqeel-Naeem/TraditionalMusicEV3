"""
Standalone diagnostic test script for On-Brick Local Timeline motor playback.
Tests all motors across all connected bricks step-by-step with live console feedback.
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ev3 import EV3
from songs import SONGS, compile_song_timelines, play_song


def main():
    print("=" * 65)
    print("TRADITIONAL MUSIC EV3 - ON-BRICK TIMELINE MOTOR DIAGNOSTIC")
    print("=" * 65)

    ev3_system = EV3()

    try:
        print("\n[1/3] Connecting to EV3 bricks...")
        ev3_system.connect()
        print("Connected bricks:", list(ev3_system._bricks.keys()))

        print("\n[2/3] Compiling 'Test Motors' timeline...")
        notes = SONGS["Test Motors"]
        timelines = compile_song_timelines(notes)

        print(f"Compiled {len(timelines)} brick timeline(s):")
        for mac, bytecode in timelines.items():
            connected_status = "ONLINE" if ev3_system._brick_status.get(mac, False) else "OFFLINE"
            print(f"  * Brick {mac} ({connected_status}): {len(bytecode)} bytes bytecode")

        print("\n[3/3] Starting 'Test Motors' On-Brick Local Timeline...")
        print("Sequence:")
        print("  1. SARON Left Notes 1 to 4 (every 1.5s)")
        print("  2. SARON Right Notes 5 to 8 (every 1.5s)")
        print("  3. GENDANG Keys 0 and 1 (every 1.5s)")
        print("  4. GONG Keys 0 and 1 (every 1.5s)")
        print("  5. GAMELAN 1 Ports A, B, C (every 1.5s)")
        print("  6. GAMELAN 2 Ports A, B, C (every 1.5s)")
        print("  7. GAMELAN 3 Ports A, B, C (every 1.5s)")
        print("  8. ENSEMBLE SYNCHRONIZATION STRIKE (all instruments fire together)")
        print("\nPlaying... (Press Ctrl+C to stop early)\n")

        start_time = time.perf_counter()
        play_song(ev3_system, notes)
        elapsed = time.perf_counter() - start_time

        print(f"\nCompleted in {elapsed:.2f} seconds.")
        print("=" * 65)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
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
