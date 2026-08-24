"""
Lists files/folders on an EV3 brick's file system, so you can find the
exact path where EV3 Classroom put a downloaded program. Read-only -
doesn't touch config.py/ev3.py/songs.py, doesn't move any motors.

Usage:
    python test/list_ev3_files.py <brick_mac> [path]

If no path is given, starts at the usual EV3 Classroom projects folder
and lists what's there; pass a folder name shown in the output to look
deeper (e.g. python test/list_ev3_files.py 00:16:53:41:95:2e /home/root/lms2012/prjs/MyProject).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ev3_dc as ev3
from ev3_dc.file import FileSystem

DEFAULT_PATH = "/home/root/lms2012/prjs"


def main():
    if len(sys.argv) < 2:
        print("Usage: python test/list_ev3_files.py <brick_mac> [path]")
        return

    mac = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PATH

    print(f"Connecting to {mac}...")
    brick = ev3.EV3(protocol=ev3.BLUETOOTH, host=mac)

    try:
        fs = FileSystem(ev3_obj=brick)
        print(f"Listing {path} ...")
        folders, files = fs.list_dir(path)
        print("\nFolders:")
        for f in folders:
            print(f"  {path.rstrip('/')}/{f}/")
        print("\nFiles:")
        for name, size, md5 in files:
            print(f"  {path.rstrip('/')}/{name}  ({size} bytes)")
        if not folders and not files:
            print("  (empty)")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        raise
    finally:
        brick.__del__()
        print("\nDisconnected.")


if __name__ == "__main__":
    main()
