# Each instrument maps to a specific EV3 brick (by Bluetooth MAC address)
# and the motor port on that brick.
#
# Fill in real MAC addresses as you pair each brick (Settings > Brick Info > ID on the EV3).

INSTRUMENTS = {
    "GONG":  {"mac": "00:16:53:46:be:aa", "port": "A"},
    "SARON": {"mac": "00:16:53:41:95:2e", "port": "A"},
    "SARON": {"mac": "00:16:53:41:95:2e", "port": "C"},
    "DRUM":  {"mac": "00:16:53:43:d6:4a", "port": "A"},
    # Add more instruments here as needed, e.g.:
    # "KENONG": {"mac": "00:16:53:XX:XX:XX", "port": "B"},
}