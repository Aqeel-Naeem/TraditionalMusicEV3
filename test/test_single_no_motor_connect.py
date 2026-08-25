"""
Minimal test: connects to ONE EV3 brick over Bluetooth, with NO motor
object created at all - confirms that a brick-level Bluetooth connection
works fine even with nothing physically plugged into it.

This is step 1 of testing a "master brick relays to other bricks" idea -
this script only proves the PC <-> single coordinator brick connection
works. It does NOT test any EV3-to-EV3 relay logic (that would be a
separate, much bigger piece of work - a program running on this brick
itself, not something this script does).

Usage:
    python test/test_single_no_motor_connect.py <brick_mac>
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ev3_dc as ev3


def main():
    if len(sys.argv) < 2:
        print("Usage: python test/test_single_no_motor_connect.py <brick_mac>")
        return

    mac = sys.argv[1]

    print(f"Connecting to {mac} (no motor will be touched)...")
    try:
        brick = ev3.EV3(protocol=ev3.BLUETOOTH, host=mac)
        print("Connected successfully:", brick)

        # Prove the connection is actually alive, without touching any
        # motor - battery level is a safe, motor-free way to confirm the
        # brick is really responding, not just that the socket opened.
        print(f"Battery: {brick.battery.percentage}%")

    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        raise
    finally:
        try:
            brick.__del__()
            print("Disconnected.")
        except Exception:
            pass


if __name__ == "__main__":
    main()