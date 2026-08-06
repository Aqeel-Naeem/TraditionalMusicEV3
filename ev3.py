import threading
import ev3_dc as ev3
from config import INSTRUMENTS

PORT_MAP = {
    "A": ev3.PORT_A,
    "B": ev3.PORT_B,
    "C": ev3.PORT_C,
    "D": ev3.PORT_D,
}


class EV3:
    """
    Manages connections to multiple EV3 bricks. Instruments that share
    the same MAC address (same physical brick, different port) reuse a
    single Bluetooth connection. An instrument can also have MULTIPLE
    motors (e.g. SARON on Port A and Port C of the same brick), which
    fire together whenever that instrument is triggered.
    """

    def __init__(self):
        self.connected = False
        self._bricks = {}        # mac -> ev3.EV3 connection object (one per unique brick)
        self._brick_status = {}  # mac -> True/False (connected or not)
        self._motors = {}        # instrument name -> list of (motor, mac) tuples
        self._status = {}        # instrument name -> True/False (fully usable or not)
        self._instruments_by_mac = {}  # mac -> list of instrument names that use it

    def connect(self):
        print("Connecting to EV3 bricks...")
        any_success = False

        # Step 1: connect to each unique brick MAC only once
        unique_macs = {loc["mac"] for locations in INSTRUMENTS.values() for loc in locations}

        for mac in unique_macs:
            try:
                brick = ev3.EV3(protocol=ev3.BLUETOOTH, host=mac)
                self._bricks[mac] = brick
                self._brick_status[mac] = True
                any_success = True
                print(f"  Brick {mac}: connected")
            except Exception as e:
                self._brick_status[mac] = False
                print(f"  Brick {mac}: FAILED to connect - {e}")

        # Step 2: create Motor object(s) for each instrument, using shared brick connections
        self._instruments_by_mac = {}

        for instrument, locations in INSTRUMENTS.items():
            motors = []  # list of (motor, mac) tuples, so failures can be traced to a brick
            all_ok = True

            for loc in locations:
                mac = loc["mac"]
                self._instruments_by_mac.setdefault(mac, [])
                if instrument not in self._instruments_by_mac[mac]:
                    self._instruments_by_mac[mac].append(instrument)

                if not self._brick_status.get(mac, False):
                    all_ok = False
                    print(f"  {instrument}: motor on brick {mac} unavailable (brick not connected)")
                    continue

                try:
                    brick = self._bricks[mac]
                    motor = ev3.Motor(PORT_MAP[loc["port"]], ev3_obj=brick)
                    motors.append((motor, mac))
                except Exception as e:
                    all_ok = False
                    print(f"  {instrument}: FAILED to set up motor on {mac} port {loc['port']} - {e}")

            self._motors[instrument] = motors
            self._status[instrument] = all_ok and len(motors) > 0

            if self._status[instrument]:
                port_list = ", ".join(f"{loc['mac']}:{loc['port']}" for loc in locations)
                print(f"  {instrument}: ready ({len(motors)} motor(s) - {port_list})")
            else:
                print(f"  {instrument}: NOT fully ready ({len(motors)}/{len(locations)} motor(s) available)")

        self.connected = any_success

        if not any_success:
            raise ConnectionError("No EV3 bricks connected successfully.")

        print("EV3 connection phase complete (see above for per-instrument status).")

    def disconnect(self):
        print("Disconnecting all EV3 bricks...")
        for mac, brick in self._bricks.items():
            try:
                brick.__del__()
                print(f"  Brick {mac}: disconnected")
            except Exception as e:
                print(f"  Brick {mac}: error while disconnecting - {e}")

        self._bricks = {}
        self._brick_status = {}
        self._motors = {}
        self._status = {}
        self.connected = False

    def is_instrument_connected(self, instrument):
        return self._status.get(instrument, False)

    def send_command(self, command, key=None, duration=0.3, speed=50):
        """
        Fires motor(s) for this instrument.
        - If key is None: fires ALL motors for this instrument together
          (good for simple instruments, or manual "hit everything" testing).
        - If key is given (an index into that instrument's motor list):
          fires ONLY that specific motor - use this for big instruments
          where each motor covers a different key/section (e.g. SARON key 0, 1, 2...).
        Returns True if sent, False if unavailable.
        """
        if not self._status.get(command, False):
            print(f"Cannot send '{command}': not connected")
            return False

        motors = self._motors[command]  # list of (motor, mac) tuples

        if key is not None:
            if key < 0 or key >= len(motors):
                print(f"Cannot send '{command}': key {key} out of range (0-{len(motors) - 1})")
                return False
            target_motors = [motors[key]]
        else:
            target_motors = motors

        def _run_motor(motor, mac):
            try:
                motor.start_move_for(duration=duration, speed=speed)
            except Exception as e:
                # A motor command failing mid-performance usually means that
                # brick's connection dropped - mark BOTH the specific brick
                # and this instrument as down, so status checks (and battery
                # checks, which skip down bricks) reflect it correctly.
                print(f"  {command}: motor command failed on brick {mac} - {e}")
                self._brick_status[mac] = False
                self._status[command] = False

        threads = []
        for motor, mac in target_motors:
            t = threading.Thread(target=_run_motor, args=(motor, mac), daemon=True)
            threads.append(t)
            t.start()

        label = f"{command}[{key}]" if key is not None else command
        print(f"Sent command: {label} ({len(target_motors)} motor(s))")
        return True

    def get_battery_levels(self):
        """
        Returns a dict of {mac: percentage} for each currently connected brick.
        Bricks already known to be down are skipped (marked None) instead of
        being queried, since querying a dead connection can hang.
        """
        levels = {}
        for mac, brick in self._bricks.items():
            if not self._brick_status.get(mac, False):
                levels[mac] = None
                continue
            try:
                levels[mac] = brick.battery.percentage
            except Exception as e:
                print(f"  Could not read battery for {mac}: {e}")
                levels[mac] = None
                self._brick_status[mac] = False
        return levels

    def health_check(self):
        """
        Actively checks every brick that's CURRENTLY marked as connected,
        even if nothing has tried to send it a command recently. This is
        what catches a brick that has silently gone offline while idle
        (e.g. before it's ever been triggered) - without this, the status
        grid would keep showing it as "Connected" until something finally
        tried to use it and failed.

        Should be called periodically in the background (see gui.py),
        NOT while a song is actively playing, since it sends its own
        Bluetooth traffic and could interfere with timing-sensitive
        motor commands.
        """
        for mac, brick in self._bricks.items():
            if not self._brick_status.get(mac, False):
                continue  # already known to be down, no need to re-check

            try:
                _ = brick.battery  # lightweight query, just to confirm the brick still responds
            except Exception as e:
                print(f"  Health check: brick {mac} is no longer responding - {e}")
                self._brick_status[mac] = False
                for instrument in self._instruments_by_mac.get(mac, []):
                    self._status[instrument] = False