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
    # Positioned instruments such as SARON are configured below. Keeping the
    # name here lets the GUI continue to show its connection status.
    "GAMELAN": [],
    "CHIME": [],
    "GENDANG": [
        {"mac": "00:16:53:43:d6:4a", "port": "A"},
    ],
    # Add more instruments here as needed, e.g.:
    # "KENONG": [{"mac": "00:16:53:XX:XX:XX", "port": "B"}],
}


# Instruments with one or more controller + hitter pairs. The controller
# moves to a note angle in advance; the paired hitter performs the strike.
# Add another instrument here when it uses the same physical arrangement.
POSITIONED_INSTRUMENTS = {
    "SARON": {
        "pairs": {
            "left": {
                "controller": {"mac": "00:16:53:41:95:2e", "port": "A"},
                "hitter": {"mac": "00:16:53:41:95:2e", "port": "D"},
                "hitter_direction": "clockwise",
            },
            "right": {
                # PLACEHOLDER - replace with the right EV3 brick's real MAC
                # address (Settings > Brick Info > ID on that brick).
                # Ports assumed to match the left pair's layout (A/D).
                "controller": {"mac": "00:16:53:XX:XX:XX", "port": "A"},
                "hitter": {"mac": "00:16:53:XX:XX:XX", "port": "D"},
                "hitter_direction": "clockwise",
            },
        },
        # Dummy calibration layout. Replace these note labels and angles with
        # the real Saron layout after measuring each hitting plate.
        #
        # IMPORTANT: angle 0 is NOT a fixed physical point - it's wherever
        # the controller motor happens to be positioned the moment the app
        # connects (ev3_dc resets each motor's "0" reference on creation).
        # The hitting stick MUST be physically placed at the true center of
        # each side BEFORE clicking "Connect EV3", every time, or these
        # angles will be offset from the wrong starting point.
        #
        # Angles are symmetric around that center: 2 notes to the left
        # (negative) and 2 to the right (positive) of the stick's resting
        # position, matching the real mechanism.
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
            # Increased from 0.75s: a real, pro-size Saron likely needs a
            # wider controller swing between outer notes than the dummy
            # 0-90 degree range assumes, plus Bluetooth timing margin.
            # Tune this by ear once physically tested - shorten if hits
            # feel like they're waiting too long, lengthen if a hit feels
            # rushed/early relative to the controller finishing its move.
            "position_lead_seconds": 1.0,
            "hit_degrees": 90,
            "hit_speed": 50,
        },
    },
}