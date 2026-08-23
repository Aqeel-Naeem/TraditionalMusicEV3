import queue
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
        self._brick_queues = {}          # mac -> queue.Queue (one per connected brick)
        self._brick_workers = {}         # mac -> Thread (persistent worker per brick)

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

        # Start one persistent worker thread per connected brick for real-time manual commands.
        for mac in self._bricks:
            if self._brick_status.get(mac, False):
                q = queue.Queue()
                self._brick_queues[mac] = q
                t = threading.Thread(
                    target=self._brick_worker,
                    args=(mac, q),
                    daemon=True,
                    name=f"ev3-worker-{mac}",
                )
                t.start()
                self._brick_workers[mac] = t
                print(f"  Brick {mac}: worker thread started")

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

        # Stop all running motors/timelines first
        self.stop_all_motors()

        # Signal each worker to exit and wait for it to drain its queue.
        for mac, q in self._brick_queues.items():
            q.put(None)  # sentinel: worker exits its loop on None
        for mac, t in self._brick_workers.items():
            t.join(timeout=2.0)

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
        self._brick_queues = {}
        self._brick_workers = {}
        self.connected = False

    def _brick_worker(self, mac, q):
        """
        Persistent worker thread for real-time manual commands on a single EV3 brick.
        """
        while True:
            cmd = q.get()
            if cmd is None:
                q.task_done()
                break
            try:
                cmd()
            except Exception as e:
                print(f"  Worker for brick {mac}: command failed - {e}")
            finally:
                q.task_done()

    def play_timeline(self, mac, bytecode):
        """
        Sends and executes a compiled on-brick timeline direct command.
        Uses ASYNC mode so the Bluetooth socket is not blocked waiting for reply.
        """
        if not self._brick_status.get(mac, False):
            print(f"Cannot play timeline on brick {mac}: brick not connected")
            return False
        try:
            brick = self._bricks.get(mac)
            if brick is None:
                return False
            brick.send_direct_cmd(bytecode, local_mem=4, sync_mode=ev3.ASYNC)
            return True
        except Exception as e:
            print(f"Timeline playback error on brick {mac}: {e}")
            return False

    def stop_all_motors(self):
        """
        Broadcasts an immediate stop and program termination command across all connected bricks
        to abort any running on-brick timelines and actively brake all motors.
        """
        stop_ops = b''.join((
            # Stop running VM program threads in Slot 0, Slot 1 (Direct commands), Slot 2
            ev3.opProgram_Stop, ev3.LCX(0),
            ev3.opProgram_Stop, ev3.LCX(1),
            ev3.opProgram_Stop, ev3.LCX(2),
            # Brake and stop all motor outputs on ports A, B, C, D
            ev3.opOutput_Stop, ev3.LCX(0), ev3.LCX(15), ev3.LCX(1),
        ))
        for mac, brick in self._bricks.items():
            if not self._brick_status.get(mac, False):
                continue
            try:
                # Clear pending commands in worker queue if any
                q = self._brick_queues.get(mac)
                if q is not None:
                    while not q.empty():
                        try:
                            q.get_nowait()
                            q.task_done()
                        except queue.Empty:
                            break
                brick.send_direct_cmd(stop_ops, sync_mode=ev3.ASYNC)
            except Exception as e:
                print(f"Error stopping brick {mac}: {e}")

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

    def send_command(
        self,
        command,
        key=None,
        duration=0.3,
        speed=50,
        direction="clockwise",
        degrees=None,
        return_degrees=None,
        degree=None,
    ):
        """
        Fires motor(s) for this instrument (manual UI buttons, voice commands, gestures).
        - For standard instruments (Gong, Gendang, Gamelan): fires assigned motors.
        - For positioned instruments (Saron): directly fires hitter motor(s) for an immediate,
          responsive manual strike test matching all other instrument buttons.
        """
        if degrees is None and degree is not None:
            degrees = degree

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

        # Handle SARON (Positioned Instruments) manual hit: directly strike the hitter motor(s)
        if self.is_positioned_instrument(command):
            state = self._positioned_instruments.get(command, {})
            pairs = state.get("pairs", {})
            if not pairs:
                print(f"Cannot send '{command}': no active pairs available")
                return False

            defaults = state.get("defaults", {})
            eff_hit_degrees = defaults.get("hit_degrees", 90) if degrees is None else degrees
            eff_hit_speed = defaults.get("hit_speed", 50) if speed == 50 else speed
            eff_return_degrees = eff_hit_degrees if return_degrees is None else return_degrees

            # Select target pair(s)
            pair_list = list(pairs.values())
            if key is not None and 0 <= key < len(pair_list):
                target_pairs = [pair_list[key]]
            else:
                target_pairs = pair_list

            for p in target_pairs:
                hitter, hitter_mac = p["hitter"]
                h_lock = self._motor_locks.get(id(hitter))
                h_dir_str = p.get("hitter_direction", "clockwise")
                h_mult = 1 if h_dir_str == "clockwise" else -1

                def _run_hitter(h=hitter, mac=hitter_mac, lk=h_lock, mult=h_mult):
                    try:
                        with lk:
                            h.start_move_by(
                                eff_hit_degrees * mult,
                                speed=eff_hit_speed,
                                brake=True,
                            )
                            h_time = max(0.04, abs(eff_hit_degrees) / (max(10, eff_hit_speed) * 8.0))
                            time.sleep(h_time)
                            h.start_move_by(
                                -eff_return_degrees * mult,
                                speed=eff_hit_speed,
                                brake=True,
                            )
                            ret_time = max(0.04, abs(eff_return_degrees) / (max(10, eff_hit_speed) * 8.0))
                            time.sleep(ret_time)
                    except Exception as e:
                        print(f"  {command} hitter error on {mac}: {e}")

                q = self._brick_queues.get(hitter_mac)
                if q is not None:
                    q.put(_run_hitter)
                else:
                    threading.Thread(target=_run_hitter, daemon=True).start()

            print(f"Sent manual strike: {command} ({len(target_pairs)} hitter(s))")
            return True

        # Standard instruments (Gong, Gendang, Gamelan, etc.)
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
                with motor_lock:
                    if degrees is None:
                        motor.start_move_for(
                            duration=duration,
                            speed=speed,
                            direction=motor_direction,
                        )
                        time.sleep(duration)
                    else:
                        motor.start_move_by(
                            movement_degrees,
                            speed=speed,
                            brake=True,
                        )
                        eff_speed = max(10, speed)
                        move_time = max(0.04, abs(movement_degrees) / (eff_speed * 8.0))
                        time.sleep(move_time)
                        motor.start_move_by(
                            return_movement_degrees,
                            speed=speed,
                            brake=True,
                        )
                        ret_time = max(0.04, abs(return_movement_degrees) / (eff_speed * 8.0))
                        time.sleep(ret_time)
            except Exception as e:
                print(f"  {command}: motor command failed on brick {mac} - {e}")
                self._brick_status[mac] = False
                self._status[command] = False

        for motor, mac in target_motors:
            motor_lock = self._motor_locks.get(id(motor))
            if motor_lock is None:
                print(f"Cannot send '{command}': motor lock unavailable")
                return False
            def _enqueue(m=motor, a=mac, lk=motor_lock):
                _run_motor(m, a, lk)
            q = self._brick_queues.get(mac)
            if q is not None:
                q.put(_enqueue)
            else:
                threading.Thread(target=_enqueue, daemon=True).start()

        label = f"{command}[{key}]" if key is not None else command
        if degrees is not None:
            label += f" ({degrees} degrees out, {return_degrees} degrees back, {direction})"
        print(f"Sent command: {label} ({len(target_motors)} motor(s))")
        return True

    def get_battery_levels(self):
        """
        Returns a dict of {mac: percentage} for each currently connected brick.
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
        Actively checks every brick currently marked as connected.
        """
        for mac, brick in self._bricks.items():
            if not self._brick_status.get(mac, False):
                continue
            try:
                _ = brick.battery
            except Exception as e:
                print(f"  Health check: brick {mac} is no longer responding - {e}")
                self._brick_status[mac] = False
                for instrument in self._instruments_by_mac.get(mac, []):
                    self._status[instrument] = False
