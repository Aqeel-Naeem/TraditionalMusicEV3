import time
import ev3_dc as ev3


# ============================================================
# EV3 LOCAL TIMING PROOF-OF-CONCEPT
# ============================================================

# GAMELAN 1 from config.py
EV3_MAC = "00:16:53:41:90:6e"
MOTOR_PORT = ev3.PORT_A

# Test settings
SPEED = 30

# Each movement will be 180 degrees.
# This makes the movement easy to see.
MOVEMENT_DEGREES = 180

# Time between completed movements.
GAP_TIME_MS = 1000

# Number of movements.
MOVEMENTS = 3


def build_local_timeline():
    """
    Build ONE direct-command program.

    The EV3 receives the entire sequence at once.

    For each movement:

        1. Move motor 180 degrees
        2. EV3 waits until the movement finishes
        3. EV3 waits 1 second locally
        4. Start the next movement

    Python does not send anything between movements.
    """

    ops = []

    for movement in range(MOVEMENTS):

        # ----------------------------------------------------
        # Move the motor a fixed number of degrees.
        # ----------------------------------------------------
        ops.extend((
            ev3.opOutput_Step_Speed,

            ev3.LCX(0),                 # LAYER
            ev3.LCX(MOTOR_PORT),        # NOS

            ev3.LCX(SPEED),             # SPEED

            ev3.LCX(0),                 # STEP1 / ramp-up
            ev3.LCX(MOVEMENT_DEGREES),  # STEP2 / movement
            ev3.LCX(0),                 # STEP3 / ramp-down

            ev3.LCX(0),                 # BRAKE = coast
        ))

        # ----------------------------------------------------
        # Start the movement.
        # ----------------------------------------------------
        ops.extend((
            ev3.opOutput_Start,

            ev3.LCX(0),                 # LAYER
            ev3.LCX(MOTOR_PORT),
        ))

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Wait until THIS motor movement has finished.
        #
        # This happens inside the EV3.
        # ----------------------------------------------------
        ops.extend((
            ev3.opOutput_Ready,

            ev3.LCX(0),                 # LAYER
            ev3.LCX(MOTOR_PORT),
        ))

        # ----------------------------------------------------
        # After the movement has finished, wait 1 second
        # before starting the next movement.
        #
        # This timer also runs inside the EV3.
        # ----------------------------------------------------
        if movement < MOVEMENTS - 1:

            ops.extend((
                ev3.opTimer_Wait,
                ev3.LCX(GAP_TIME_MS),
                ev3.LVX(0),

                ev3.opTimer_Ready,
                ev3.LVX(0),
            ))

    # --------------------------------------------------------
    # Safety stop at the end.
    # --------------------------------------------------------
    ops.extend((
        ev3.opOutput_Stop,
        ev3.LCX(0),
        ev3.LCX(MOTOR_PORT),
        ev3.LCX(0),                     # BRAKE = coast
    ))

    return b"".join(ops)


def main():

    print("=" * 60)
    print("EV3 LOCAL TIMING TEST")
    print("=" * 60)

    print(f"Target EV3       : {EV3_MAC}")
    print("Motor            : PORT_A")
    print(f"Movements        : {MOVEMENTS}")
    print(f"Movement         : {MOVEMENT_DEGREES} degrees")
    print(f"Speed            : {SPEED}")
    print(f"Gap              : {GAP_TIME_MS} ms")

    print()
    print("Expected behavior:")
    print()
    print("  MOVE 180 degrees")
    print("  STOP")
    print("  WAIT 1 second")
    print("  MOVE 180 degrees")
    print("  STOP")
    print("  WAIT 1 second")
    print("  MOVE 180 degrees")
    print("  STOP")
    print()
    print("The COMPLETE sequence is sent in ONE command.")
    print("Python does not send commands between movements.")
    print()

    # Build the complete EV3 program.
    ops = build_local_timeline()

    print(f"Direct command size: {len(ops)} bytes")
    print("Connecting...")

    try:

        with ev3.EV3(
            protocol=ev3.BLUETOOTH,
            host=EV3_MAC,
        ) as brick:

            brick.verbosity = 1
            brick.sync_mode = ev3.SYNC

            print("Connected.")
            print("Sending ONE complete local timeline...")
            print()

            start = time.perf_counter()

            # Send the complete sequence to the EV3.
            #
            # local_mem=4 is required by LVX(0), which is used
            # by the EV3 timer.
            brick.send_direct_cmd(
                ops,
                local_mem=4,
                sync_mode=ev3.SYNC,
            )

            elapsed = time.perf_counter() - start

            print()
            print(
                f"Command completed in {elapsed:.3f} seconds"
            )

            print()
            print("Observe the motor.")
            print("Expected: 3 separate 180-degree movements.")
            print("There should be a ~1 second pause between them.")
            print()

    except Exception as exc:

        print()
        print("TEST FAILED")
        print(f"{type(exc).__name__}: {exc}")
        raise

    print("=" * 60)


if __name__ == "__main__":
    main()