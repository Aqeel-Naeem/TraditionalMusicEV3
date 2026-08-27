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
    # "GONG": [
    #     {"mac": "00:16:53:46:be:aa", "port": "A"},
    #     {"mac": "00:16:53:46:be:aa", "port": "B"},
    # ],

    # "CHIME": [
    #     {"mac": "00:16:53:46:be:aa", "port": "D"},
    # ],

    # "GONG": [
    #     {"mac": "00:16:53:3d:cc:4c", "port": "A"},
    # ],

    # "CHIME": [
    #     {"mac": "00:16:53:4f:f7:b7", "port": "A"},
    # ],

    # "GENDANG": [
    #     {"mac": "00:16:53:43:d6:4a", "port": "A"},
    #     {"mac": "00:16:53:43:d6:4a", "port": "D"},
    # ],

    # Combined into one instrument (was 3 separate GAMELAN 1/2/3 entries) -
    # this also brings total instrument count to 5, fitting within the
    # 5-finger gesture selection limit. Order matters: keys 0-2 are
    # Gamelan 1, 3-5 are Gamelan 2, 6-8 are Gamelan 3 - the low-to-high
    # sequence play (see gui.py's _play_gamelan_sequence) walks through
    # them in this exact order, chaining all 3 units into one run.
    # (Commented out for now - this brick is being used as a motor-less
    # master coordinator instead, see PROGRAM_ONLY_BRICKS below.)
    # "GAMELAN": [
    #     {"mac": "00:16:53:41:90:6e", "port": "A"},
    #     {"mac": "00:16:53:41:90:6e", "port": "B"},
    #     {"mac": "00:16:53:41:90:6e", "port": "C"},
    # ],

    # To add an 8th+ instrument later, just follow the same pattern:
    # "KENONG": [{"mac": "00:16:53:XX:XX:XX", "port": "A"}],
}

# Bricks with NO motors at all, connected purely so a downloaded program
# can be started on them - e.g. a "master" brick whose own program
# relays commands to other bricks independently, without the PC needing
# to know about any of that. These are NOT instruments - nothing in
# INSTRUMENTS/POSITIONED_INSTRUMENTS should reference them, and no
# {"mac": ..., "port": ...} entry is needed since there's no motor.
PROGRAM_ONLY_BRICKS = [
    {"mac": "00:16:53:41:90:6e", "protocol": "usb"},  # master coordinator brick (Rasa Sayang relay)
]


# Instruments with one or more controller + hitter pairs. The controller
# moves to a note angle in advance; the paired hitter performs the strike.
# Add another instrument here when it uses the same physical arrangement.
POSITIONED_INSTRUMENTS = {
    # "SARON": {
    #     "pairs": {
    #         "left": {
    #             "controller": {"mac": "00:16:53:41:95:2e", "port": "A"},
    #             "hitter": [
    #                 {"mac": "00:16:53:41:95:2e", "port": "B"},
    #                 {"mac": "00:16:53:41:95:2e", "port": "C"},
    #             ],
    #             "hitter_direction": "clockwise",
    #         },
    #         "right": {
    #             "controller": {"mac": "00:16:53:4d:46:72", "port": "A"},
    #             "hitter": [
    #                 {"mac": "00:16:53:4d:46:72", "port": "B"},
    #                 {"mac": "00:16:53:4d:46:72", "port": "C"},
    #             ],
    #             "hitter_direction": "clockwise",
    #         },
    #     },
    #     # IMPORTANT: angle 0 is NOT a fixed physical point - it's wherever
    #     # the controller motor happens to be positioned the moment the app
    #     # connects (ev3_dc resets each motor's "0" reference on creation).
    #     # The hitting stick MUST be physically placed at the true center of
    #     # each side BEFORE clicking "Connect EV3", every time.
    #     "notes": {
    #         "Saron 1": {"pair": "left", "angle": -45},
    #         "Saron 2": {"pair": "left", "angle": -15},
    #         "Saron 3": {"pair": "left", "angle": 15},
    #         "Saron 4": {"pair": "left", "angle": 45},
    #         "Saron 5": {"pair": "right", "angle": -45},
    #         "Saron 6": {"pair": "right", "angle": -15},
    #         "Saron 7": {"pair": "right", "angle": 15},
    #         "Saron 8": {"pair": "right", "angle": 45},
    #     },
    #     "defaults": {
    #         "position_speed": 50,
    #         "position_lead_seconds": 1.0,
    #         "hit_degrees": 90,
    #         "hit_speed": 50,
    #     },
    # },
}