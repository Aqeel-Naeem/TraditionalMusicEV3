# Each instrument maps to a LIST of one or more (brick MAC, port) pairs.
# Most instruments will have just one motor - but an instrument like SARON
# can have multiple motors (possibly across multiple bricks) that fire
# together whenever that instrument is triggered.
#
# All instruments are defined here at all times, even ones you don't have
# physically with you today - connect() already handles a brick that isn't
# reachable gracefully (marks it "not ready", doesn't crash anything else).
# No need to comment/uncomment based on which bricks are on hand.
#
# Fill in real MAC addresses as you pair each brick (Settings > Brick Info > ID on the EV3).

INSTRUMENTS = {
    "GONG": [
        {"mac": "00:16:53:46:be:aa", "port": "A"},
        {"mac": "00:16:53:46:be:aa", "port": "B"},
    ],

    "CHIME": [
        {"mac": "00:16:53:46:be:aa", "port": "D"},
    ],

    "GENDANG": [
        {"mac": "00:16:53:43:d6:4a", "port": "A"},
        {"mac": "00:16:53:43:d6:4a", "port": "D"},
    ],

    "GAMELAN 1": [
        {"mac": "00:16:53:41:90:6e", "port": "A"},
        # {"mac": "00:16:53:41:90:6e", "port": "B"},
        # {"mac": "00:16:53:41:90:6e", "port": "C"},
    ],

    "GAMELAN 2": [
        {"mac": "00:16:53:4b:b2:e0", "port": "A"},
        {"mac": "00:16:53:4b:b2:e0", "port": "B"},
        {"mac": "00:16:53:4b:b2:e0", "port": "C"},
    ],

    "GAMELAN 3": [
        {"mac": "00:16:53:48:9b:39", "port": "A"},
        {"mac": "00:16:53:48:9b:39", "port": "B"},
        {"mac": "00:16:53:48:9b:39", "port": "C"},
    ],

    # To add an 8th+ instrument later, just follow the same pattern:
    # "KENONG": [{"mac": "00:16:53:XX:XX:XX", "port": "A"}],
}


# Instruments with one or more controller + hitter pairs. The controller
# moves to a note angle in advance; the paired hitter performs the strike.
# Add another instrument here when it uses the same physical arrangement.
POSITIONED_INSTRUMENTS = {
    "SARON": {
        "pairs": {
            "left": {
                "controller": {"mac": "00:16:53:41:95:2e", "port": "A"},
                "hitter": [
                    {"mac": "00:16:53:41:95:2e", "port": "B"},
                    {"mac": "00:16:53:41:95:2e", "port": "C"},
                ],
                "hitter_direction": "clockwise",
            },
            "right": {
                "controller": {"mac": "00:16:53:4d:46:72", "port": "A"},
                "hitter": [
                    {"mac": "00:16:53:4d:46:72", "port": "B"},
                    {"mac": "00:16:53:4d:46:72", "port": "C"},
                ],
                "hitter_direction": "clockwise",
            },
        },
        # IMPORTANT: angle 0 is NOT a fixed physical point - it's wherever
        # the controller motor happens to be positioned the moment the app
        # connects (ev3_dc resets each motor's "0" reference on creation).
        # The hitting stick MUST be physically placed at the true center of
        # each side BEFORE clicking "Connect EV3", every time.
        "notes": {
            "Saron 1": {"pair": "left", "angle": -45},
            "Saron 2": {"pair": "left", "angle": -15},
            "Saron 3": {"pair": "left", "angle": 15},
            "Saron 4": {"pair": "left", "angle": 45},
            "Saron 5": {"pair": "right", "angle": -45},
            "Saron 6": {"pair": "right", "angle": -15},
            "Saron 7": {"pair": "right", "angle": 15},
            "Saron 8": {"pair": "right", "angle": 45},
        },
        "defaults": {
            "position_speed": 50,
            "position_lead_seconds": 1.0,
            "hit_degrees": 90,
            "hit_speed": 50,
        },
    },
}