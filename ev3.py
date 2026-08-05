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
    Manages connections to multiple EV3 bricks, one per instrument.
    Keeps the same public interface (connect, disconnect, send_command)
    so gui.py and songs.py don't need to change.
    """

    def __init__(self):
        self.connected = False  # True if at least one brick connected successfully
        self._bricks = {}   # instrument name -> ev3.EV3 connection object
        self._motors = {}   # instrument name -> ev3.Motor object
        self._status = {}   # instrument name -> True/False (connected or not)

    def connect(self):
        print("Connecting to EV3 bricks...")
        any_success = False

        for instrument, info in INSTRUMENTS.items():
            try:
                brick = ev3.EV3(protocol=ev3.BLUETOOTH, host=info["mac"])
                motor = ev3.Motor(PORT_MAP[info["port"]], ev3_obj=brick)

                self._bricks[instrument] = brick
                self._motors[instrument] = motor
                self._status[instrument] = True
                any_success = True
                print(f"  {instrument}: connected ({info['mac']})")

            except Exception as e:
                self._status[instrument] = False
                print(f"  {instrument}: FAILED to connect ({info['mac']}) - {e}")

        self.connected = any_success

        if any_success:
            print("EV3 connection phase complete (see above for per-brick status).")
        else:
            raise ConnectionError("No EV3 bricks connected successfully.")

    def disconnect(self):
        print("Disconnecting all EV3 bricks...")
        for instrument, brick in self._bricks.items():
            try:
                brick.__del__()
                print(f"  {instrument}: disconnected")
            except Exception as e:
                print(f"  {instrument}: error while disconnecting - {e}")

        self._bricks = {}
        self._motors = {}
        self._status = {}
        self.connected = False

    def is_instrument_connected(self, instrument):
        return self._status.get(instrument, False)

    def send_command(self, command, duration=0.3, speed=50):
        """
        Sends a movement command to the motor for the given instrument.
        Returns True if sent, False if that instrument's brick isn't connected.
        """
        if not self._status.get(command, False):
            print(f"Cannot send '{command}': brick not connected")
            return False

        motor = self._motors[command]
        motor.start_move_for(duration=duration, speed=speed)
        print(f"Sent command: {command}")
        return True