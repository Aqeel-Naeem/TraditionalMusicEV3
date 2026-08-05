# Each instrument maps to a LIST of one or more (brick MAC, port) pairs.
# Most instruments will have just one motor - but an instrument like SARON
# can have multiple motors (possibly across multiple bricks) that fire
# together whenever that instrument is triggered.
#
# Fill in real MAC addresses as you pair each brick (Settings > Brick Info > ID on the EV3).

INSTRUMENTS = {
    "GONG": [
        {"mac": "00:16:53:46:be:aa", "port": "A"},
    ],
    "SARON": [
        {"mac": "00:16:53:41:95:2e", "port": "A"},
        {"mac": "00:16:53:41:95:2e", "port": "D"},
    ],
    "DRUM": [
        {"mac": "00:16:53:43:d6:4a", "port": "A"},
    ],
    # Add more instruments here as needed, e.g.:
    # "KENONG": [{"mac": "00:16:53:XX:XX:XX", "port": "B"}],
}