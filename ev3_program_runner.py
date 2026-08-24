"""
Upload and run standalone EV3 Classroom (.rbf) programs from Python.

This is an ALTERNATIVE to songs.py's compile_song_timelines() bytecode
compiler: instead of Python hand-building per-note motor bytecode, each
song's motor logic is built and tested inside LEGO's own EV3 Classroom
app, and this module just uploads the compiled program to a brick and
starts it. That sidesteps the fine-grained direct-command issues (signed
vs unsigned fields, relative vs absolute movement, etc.) that showed up
while building the Python-side timeline compiler.

Kept separate from ev3.py/songs.py on purpose, so the existing working
local-timeline system stays untouched as a fallback.

VERIFICATION STATUS:
- upload_program() uses ev3_dc's own documented, tested FileSystem API.
- start_program() is built from a well-established EV3 direct-commands
  reference (ev3directcommands.blogspot.com, "Lesson 2: pre-loaded
  programs"), consistent with the opProgram_Start / opFile / USER_SLOT
  constants already defined in ev3_dc's own constants.py - but it has
  NOT been verified against real hardware in this project yet. Test it
  with the smallest possible program first (see test/test_program_runner.py).
"""

import threading

import ev3_dc as ev3
from ev3_dc.file import FileSystem

# opFile sub-command: load a program file into the brick's memory.
# Not exposed by ev3_dc's constants.py - sourced from the EV3 direct
# commands protocol reference (see module docstring).
LOAD_IMAGE = b'\x08'


def upload_program(brick, local_path, remote_path, check=True):
    """
    Uploads a compiled EV3 Classroom program (.rbf) to the brick's file
    system.

    brick
      an ev3_dc.EV3 connection (e.g. EV3()._bricks[mac] from ev3.py)
    local_path
      path to the .rbf file on this computer
    remote_path
      destination path on the brick, e.g.
      '/home/root/lms2012/prjs/SaronLeft/SaronLeft.rbf'
    check
      skip the upload if an identical file (same size + MD5) already
      exists at remote_path
    """
    fs = FileSystem(ev3_obj=brick)
    fs.load_file(local_path, remote_path, check=check)


def start_program(brick, remote_path, sync_mode=None):
    """
    Starts a program already uploaded to the brick's file system.

    Sequence per the EV3 direct-command protocol: LOAD_IMAGE loads the
    file into brick memory and writes back its SIZE and IP (image
    pointer) into local memory; opProgram_Start then reads those same
    values to launch it. local_mem=8 holds SIZE (offset 0) and IP
    (offset 4), each a 4-byte value.

    Uses SYNC by default so a wrong path or other failure raises a
    DirCmdError here instead of silently doing nothing - this only waits
    for the brief "started" acknowledgment, not for the program itself
    to finish, so it's not a long wait even in SYNC mode.
    """
    ops = b''.join((
        ev3.opFile,
        LOAD_IMAGE,
        ev3.USER_SLOT,
        ev3.LCS(remote_path),
        ev3.LVX(0),   # SIZE (output)
        ev3.LVX(4),   # IP (output)
        ev3.opProgram_Start,
        ev3.USER_SLOT,
        ev3.LVX(0),   # SIZE (input, from LOAD_IMAGE above)
        ev3.LVX(4),   # IP (input, from LOAD_IMAGE above)
        ev3.LCX(0),   # DEBUG = off
    ))
    brick.send_direct_cmd(ops, local_mem=8, sync_mode=sync_mode or ev3.SYNC)


def play_programs(ev3_system, brick_program_map):
    """
    Triggers an already-downloaded program on multiple bricks at once -
    the GUI-facing entry point: "press a button, every relevant brick
    plays the program that's already on it."

    ev3_system
      the connected ev3.EV3() instance from ev3.py (has ._bricks,
      ._brick_status)
    brick_program_map
      {mac: remote_path} - which program to start on each brick

    Each brick is started from its own thread, all launched together,
    the same concurrency pattern songs.py's play_song() uses for the
    compiled-bytecode timelines - so multiple bricks start as close
    together in time as possible.
    """
    def _start_and_report(mac, brick, remote_path):
        try:
            start_program(brick, remote_path)
            print(f"  Brick {mac}: program started ({remote_path})")
        except Exception as e:
            print(f"  Brick {mac}: FAILED to start program ({remote_path}) - {e}")

    threads = []
    for mac, remote_path in brick_program_map.items():
        brick = ev3_system._bricks.get(mac)
        if brick is None or not ev3_system._brick_status.get(mac, False):
            print(f"Skipping brick {mac}: not connected")
            continue
        t = threading.Thread(
            target=_start_and_report,
            args=(mac, brick, remote_path),
            daemon=True,
            name=f"program-start-{mac}",
        )
        threads.append(t)

    print(f"Starting {len(threads)} EV3 program(s)...")
    for t in threads:
        t.start()
