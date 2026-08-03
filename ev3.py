import ev3_dc as ev3

EV3_MAC = '00:16:53:43:7F:21'

# Map your instrument commands to physical ports
INSTRUMENT_PORTS = {
    "GONG": ev3.PORT_A,
    "SARON": ev3.PORT_B,
    "DRUM": ev3.PORT_C,
}


class EV3:

    def __init__(self):
        self.connected = False
        self._ev3 = None
        self._motors = {}

    def connect(self):
        print("Connecting to EV3...")
        self._ev3 = ev3.EV3(protocol=ev3.BLUETOOTH, host=EV3_MAC)

        for name, port in INSTRUMENT_PORTS.items():
            try:
                self._motors[name] = ev3.Motor(port, ev3_obj=self._ev3)
            except Exception as e:
                print(f"Could not initialize motor for {name} on {port}: {e}")

        self.connected = True
        print("EV3 Connected")

    def disconnect(self):
        print("Disconnecting EV3...")
        if self._ev3:
            self._ev3.__del__()  # closes the Bluetooth connection
        self.connected = False
        print("EV3 Disconnected")

    def send_command(self, command):
        if not self.connected:
            print("EV3 is not connected")
            return False

        motor = self._motors.get(command)
        if motor is None:
            print(f"Unknown command: {command}")
            return False

        motor.start_move_for(duration=0.3, speed=50)  # tune duration/speed per instrument later
        print(f"Sending command: {command}")
        return True