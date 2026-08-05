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
    single Bluetooth connection instead of opening a new one each time.
    """

    def __init__(self):
        self.connected = False
        self._bricks = {}    # mac -> ev3.EV3 connection object (one per unique brick)
        self._brick_status = {}  # mac -> True/False (connected or not)
        self._motors = {}    # instrument name -> ev3.Motor object
        self._status = {}    # instrument name -> True/False (usable or not)

    def connect(self):
        print("Connecting to EV3 bricks...")
        any_success = False

        # Step 1: connect to each unique brick MAC only once
        unique_macs = {info["mac"] for info in INSTRUMENTS.values()}

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

        # Step 2: create a Motor object per instrument, using the shared brick connection
        for instrument, info in INSTRUMENTS.items():
            mac = info["mac"]

            if not self._brick_status.get(mac, False):
                self._status[instrument] = False
                print(f"  {instrument}: unavailable (brick {mac} not connected)")
                continue

            try:
                brick = self._bricks[mac]
                motor = ev3.Motor(PORT_MAP[info["port"]], ev3_obj=brick)
                self._motors[instrument] = motor
                self._status[instrument] = True
                print(f"  {instrument}: ready (brick {mac}, port {info['port']})")
            except Exception as e:
                self._status[instrument] = False
                print(f"  {instrument}: FAILED to set up motor - {e}")

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

    def send_command(self, command, duration=0.3, speed=50):
        """
        Sends a movement command to the motor for the given instrument.
        Returns True if sent, False if that instrument isn't available.
        """
        if not self._status.get(command, False):
            print(f"Cannot send '{command}': not connected")
            return False

        motor = self._motors[command]
        motor.start_move_for(duration=duration, speed=speed)
        print(f"Sent command: {command}")
        return True