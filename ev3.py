import threading
import time
import ev3_dc as ev3
from config import INSTRUMENTS, POSITIONED_INSTRUMENTS

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
        self._motor_locks = {}   # id(motor) -> lock, prevents overlapping moves on one motor
        self._positioned_instruments = {}  # instrument -> configured controller/hitter pairs
        self._status = {}        # instrument name -> True/False (fully usable or not)
        self._instruments_by_mac = {}  # mac -> list of instrument names that use it

    def connect(self):
        print("Connecting to EV3 bricks...")
        any_success = False

        # Step 1: connect to each unique brick MAC only once
        unique_macs = {loc["mac"] for locations in INSTRUMENTS.values() for loc in locations}
        unique_macs.update(
            location["mac"]
            for definition in POSITIONED_INSTRUMENTS.values()
            for pair in definition["pairs"].values()
            for location in (pair["controller"], pair["hitter"])
            if location.get("mac")
        )

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
            if instrument in POSITIONED_INSTRUMENTS:
                continue
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
                    self._motor_locks[id(motor)] = threading.Lock()
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

        # Step 3: set up reusable controller + hitter pairs for positioned instruments.
        self._positioned_instruments = {}
        for instrument, definition in POSITIONED_INSTRUMENTS.items():
            pairs = {}

            for pair_name, pair_config in definition["pairs"].items():
                controller_config = pair_config["controller"]
                hitter_config = pair_config["hitter"]
                controller_mac = controller_config.get("mac")
                hitter_mac = hitter_config.get("mac")

                if not controller_mac or not hitter_mac:
                    print(f"  {instrument} {pair_name}: pending configuration")
                    continue
                if (not self._brick_status.get(controller_mac, False)
                        or not self._brick_status.get(hitter_mac, False)):
                    print(f"  {instrument} {pair_name}: unavailable (brick not connected)")
                    continue

                try:
                    controller = ev3.Motor(
                        PORT_MAP[controller_config["port"]],
                        ev3_obj=self._bricks[controller_mac],
                    )
                    hitter = ev3.Motor(
                        PORT_MAP[hitter_config["port"]],
                        ev3_obj=self._bricks[hitter_mac],
                    )
                    self._motor_locks[id(controller)] = threading.Lock()
                    self._motor_locks[id(hitter)] = threading.Lock()
                    pairs[pair_name] = {
                        "controller": (controller, controller_mac),
                        "hitter": (hitter, hitter_mac),
                        "hitter_direction": pair_config.get("hitter_direction", "clockwise"),
                        "lock": threading.Lock(),
                    }
                    for mac in {controller_mac, hitter_mac}:
                        self._instruments_by_mac.setdefault(mac, [])
                        if instrument not in self._instruments_by_mac[mac]:
                            self._instruments_by_mac[mac].append(instrument)
                    print(f"  {instrument} {pair_name}: ready")
                except Exception as e:
                    print(f"  {instrument} {pair_name}: FAILED to set up - {e}")

            self._positioned_instruments[instrument] = {
                "pairs": pairs,
                "notes": definition["notes"],
                "defaults": definition["defaults"],
            }
            self._status[instrument] = bool(pairs)
            if not pairs:
                print(f"  {instrument}: no positioned pairs are ready")

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
        self._motor_locks = {}
        self._positioned_instruments = {}
        self._status = {}
        self.connected = False

    def is_instrument_connected(self, instrument):
        return self._status.get(instrument, False)

    def is_positioned_instrument(self, instrument):
        """Return whether this instrument uses controller + hitter pairs."""
        return instrument in POSITIONED_INSTRUMENTS

    def get_position_lead_seconds(self, instrument):
        """Return the configured controller lead time for a positioned instrument."""
        return POSITIONED_INSTRUMENTS[instrument]["defaults"]["position_lead_seconds"]

    def get_positioned_note_pair(self, instrument, note):
        """Return the configured pair name for a note, or None if unknown."""
        definition = POSITIONED_INSTRUMENTS.get(instrument, {})
        note_config = definition.get("notes", {}).get(note)
        return note_config.get("pair") if note_config else None

    def prepare_positioned_note(self, instrument, note, hit_degrees=None,
                                hit_speed=None, return_degrees=None):
        """
        Begin moving a positioned instrument's controller to its note angle.
        The returned request is triggered later by trigger_positioned_note(),
        allowing songs to prepare the controller before the audible hit beat.
        """
        if not self._status.get(instrument, False):
            print(f"Cannot prepare '{instrument}': not connected")
            return None

        state = self._positioned_instruments.get(instrument)
        if state is None:
            print(f"Cannot prepare '{instrument}': not a positioned instrument")
            return None
        note_config = state["notes"].get(note)
        if note_config is None:
            print(f"Cannot prepare '{instrument}': unknown note '{note}'")
            return None

        pair_name = note_config["pair"]
        pair = state["pairs"].get(pair_name)
        if pair is None:
            print(f"Cannot prepare '{instrument}' note '{note}': pair '{pair_name}' is unavailable")
            return None

        defaults = state["defaults"]
        hit_degrees = defaults["hit_degrees"] if hit_degrees is None else hit_degrees
        hit_speed = defaults["hit_speed"] if hit_speed is None else hit_speed
        return_degrees = hit_degrees if return_degrees is None else return_degrees
        request = {
            "ready": threading.Event(),
            "hit": threading.Event(),
            "cancel": threading.Event(),
            "instrument": instrument,
            "note": note,
            "pair": pair_name,
        }

        def _prepare_and_strike():
            controller, controller_mac = pair["controller"]
            hitter, hitter_mac = pair["hitter"]
            try:
                with pair["lock"]:
                    controller.start_move_to(
                        note_config["angle"],
                        speed=defaults["position_speed"],
                        brake=True,
                    )
                    while controller.busy:
                        time.sleep(0.01)
                    request["ready"].set()

                    # The song signals this event exactly at the note's beat.
                    # Polling also lets a stopped song release a prepared pair.
                    while not request["hit"].wait(0.05):
                        if request["cancel"].is_set():
                            return
                    if request["cancel"].is_set():
                        return
                    hitter_direction = pair["hitter_direction"]
                    direction_multiplier = {
                        "clockwise": 1,
                        "counterclockwise": -1,
                    }.get(hitter_direction)
                    if direction_multiplier is None:
                        raise ValueError(
                            f"invalid hitter direction '{hitter_direction}'"
                        )
                    hitter.start_move_by(
                        hit_degrees * direction_multiplier,
                        speed=hit_speed,
                        brake=True,
                    )
                    while hitter.busy:
                        time.sleep(0.01)
                    hitter.start_move_by(
                        -return_degrees * direction_multiplier,
                        speed=hit_speed,
                        brake=True,
                    )
                    while hitter.busy:
                        time.sleep(0.01)
            except Exception as e:
                request["ready"].set()
                self._brick_status[controller_mac] = False
                self._brick_status[hitter_mac] = False
                self._status[instrument] = False
                print(f"  {instrument} {pair_name}: positioned strike failed - {e}")

        threading.Thread(target=_prepare_and_strike, daemon=True).start()
        return request

    def trigger_positioned_note(self, request):
        """Trigger a previously prepared positioned note at its scheduled beat."""
        if request is not None:
            request["hit"].set()

    def cancel_positioned_note(self, request):
        """Release a prepared pair without striking it."""
        if request is not None:
            request["cancel"].set()

    def play_positioned_note(self, instrument, note, hit_degrees=None,
                             hit_speed=None, return_degrees=None):
        """Prepare and strike one positioned note for manual controls."""
        request = self.prepare_positioned_note(
            instrument, note, hit_degrees, hit_speed, return_degrees,
        )
        if request is None:
            return False

        def _trigger_when_ready():
            request["ready"].wait()
            self.trigger_positioned_note(request)

        threading.Thread(target=_trigger_when_ready, daemon=True).start()
        return True

    def send_command(
        self,
        command,
        key=None,
        duration=0.3,
        speed=50,
        direction="clockwise",
        degrees=None,
        return_degrees=None,
    ):
        """
        Fires motor(s) for this instrument.
        - If key is None: fires ALL motors for this instrument together
          (good for simple instruments, or manual "hit everything" testing).
        - If key is given (an index into that instrument's motor list):
          fires ONLY that specific motor - use this for big instruments
          where each motor covers a different key/section (e.g. SARON key 0, 1, 2...).
        - degrees optionally moves each motor by a fixed number of degrees.
          It then immediately returns the motor to its starting position. Use
          return_degrees to calibrate a different return distance; otherwise
          the forward degree value is reused. When degrees is omitted,
          duration-based movement is used as before.
        - direction may be "clockwise" or "counterclockwise". It applies to
          both movement modes and defaults to "clockwise" so existing callers
          keep their current behavior.
        Returns True if sent, False if unavailable.
        """
        if self.is_positioned_instrument(command):
            notes = POSITIONED_INSTRUMENTS[command]["notes"]
            default_note = next(iter(notes), None)
            if default_note is None:
                print(f"Cannot send '{command}': no notes are configured")
                return False
            return self.play_positioned_note(
                command,
                default_note,
                hit_degrees=degrees,
                hit_speed=speed,
                return_degrees=return_degrees,
            )

        if not self._status.get(command, False):
            print(f"Cannot send '{command}': not connected")
            return False

        direction_map = {
            "clockwise": 1,
            "counterclockwise": -1,
        }
        if direction not in direction_map:
            print(f"Cannot send '{command}': invalid direction '{direction}' "
                  "(use 'clockwise' or 'counterclockwise')")
            return False
        motor_direction = direction_map[direction]

        if degrees is not None:
            if not isinstance(degrees, int) or isinstance(degrees, bool) or degrees <= 0:
                print(f"Cannot send '{command}': degrees must be a positive integer")
                return False
            movement_degrees = degrees * motor_direction
            if return_degrees is None:
                return_degrees = degrees
            if (not isinstance(return_degrees, int)
                    or isinstance(return_degrees, bool)
                    or return_degrees <= 0):
                print(f"Cannot send '{command}': return_degrees must be a positive integer")
                return False
            return_movement_degrees = -return_degrees * motor_direction

        motors = self._motors[command]  # list of (motor, mac) tuples

        if key is not None:
            if key < 0 or key >= len(motors):
                print(f"Cannot send '{command}': key {key} out of range (0-{len(motors) - 1})")
                return False
            target_motors = [motors[key]]
        else:
            target_motors = motors

        def _run_motor(motor, mac, motor_lock):
            try:
                # Keep a degree-based strike together so its return completes
                # before another command acquires this motor's lock.
                with motor_lock:
                    if degrees is None:
                        motor.start_move_for(
                            duration=duration,
                            speed=speed,
                            direction=motor_direction,
                        )
                    else:
                        motor.start_move_by(
                            movement_degrees,
                            speed=speed,
                            brake=True,
                        )
                        while motor.busy:
                            time.sleep(0.01)
                        motor.start_move_by(
                            return_movement_degrees,
                            speed=speed,
                            brake=True,
                        )
                        while motor.busy:
                            time.sleep(0.01)
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
            motor_lock = self._motor_locks.get(id(motor))
            if motor_lock is None:
                print(f"Cannot send '{command}': motor lock unavailable")
                return False
            t = threading.Thread(target=_run_motor, args=(motor, mac, motor_lock), daemon=True)
            threads.append(t)
            t.start()

        label = f"{command}[{key}]" if key is not None else command
        if degrees is not None:
            label += f" ({degrees} degrees out, {return_degrees} degrees back, {direction})"
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
