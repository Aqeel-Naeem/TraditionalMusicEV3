"""
Maps each downloaded EV3 program to the brick(s) it should run on, so the
GUI can trigger it by name.

Two separate dictionaries, matching the two GUI sections:
  - PROGRAMS: full songs, shown in "Song Selection"
  - INSTRUMENT_PROGRAMS: individual instrument test/trigger programs,
    shown in "Instrument Control"

Both use the exact same structure - { brick_mac: remote_rbf_path } per
entry - and both are triggered the same way (play_downloaded_program()).
The only difference is which GUI section they show up in.

Fill in each entry once you know:
  - which brick(s) (MAC address) it needs to run on
  - the exact path of the downloaded .rbf on that brick

Use test/list_ev3_files.py <mac> [path] to find the exact remote path -
EV3 Classroom's own naming is case-sensitive, don't guess it.

An entry that uses multiple bricks just lists every brick it needs -
ev3_program_runner.py's play_programs() starts all of them together,
skipping any brick that isn't currently connected.
"""

PROGRAMS = {
    # "Song Display Name": {
    #     "<brick mac>": "<remote .rbf path on that brick>",
    #     "<another brick mac>": "<its own .rbf path>",
    # },

    # Single master brick, no motor needed on the PC side - this brick's
    # own program handles relaying to the other 7 "servant" bricks
    # itself. Confirmed via list_ev3_files.py.
    "Rasa Sayang": {
        "00:16:53:41:90:6e": "/home/root/lms2012/prjs/Bonang/Rasa Sayang.rbf",
    },

    # If you already added "Gamelan Stop" here as a song entry, move it
    # down into INSTRUMENT_PROGRAMS below instead (or leave it here if
    # you'd rather it stay accessible from Song Selection - either
    # section works identically, this is purely about which button
    # group it shows up in).
}


# Individual instrument test/trigger programs - shown in "Instrument
# Control" instead of "Song Selection". Same structure, same trigger
# mechanism (play_downloaded_program()) - just a different section.
INSTRUMENT_PROGRAMS = {
    # "GONG": {
    #     "<brick mac>": "<remote .rbf path>",
    # },
    # "CHIME": {
    #     "<brick mac>": "<remote .rbf path>",
    # },
    # "GENDANG": {
    #     "<brick mac>": "<remote .rbf path>",
    # },
    # "GAMELAN": {
    #     "<brick mac>": "<remote .rbf path>",
    # },
    # "SARON": {
    #     "<brick mac>": "<remote .rbf path>",
    # },
}


# "Digitized instrument" note layouts - shown as a shaped grid of
# individual note buttons (e.g. Gamelan's real 5x2 rectangular layout,
# circular note shapes matching the real pots) instead of one generic
# button per instrument. Each instrument maps to {"columns": N, "notes":
# [...]}  - "columns" controls how many notes wrap per row (e.g. 5 for
# Gamelan's rectangular grid, or the full note count for an instrument
# that's really just one row, like Saron's bars). Each note has its own
# {mac, path} - triggered the same way as everything else
# (play_downloaded_program()), just laid out visually to resemble the
# real instrument.
#
# PLACEHOLDER PATHS: the individual per-note program files are still
# being built - replace "PLACEHOLDER" below with the real confirmed
# path (via list_ev3_files.py) as each note's file is ready. The MAC
# defaults to the master brick for now since that's what's connected -
# update per-note if individual notes end up on different bricks.
INSTRUMENT_NOTES = {
    # Gamelan's real physical layout: rectangular frame, 5 columns x 2
    # rows = 10 notes, each a circular hitting pot. List order matches
    # left-to-right, top-to-bottom reading order of the real instrument.
    "GAMELAN": {
        "columns": 5,
        "shape": "circle",
        "notes": [
            {"label": "6'", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 1"},
            {"label": "5'", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 2"},
            {"label": "3'", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 3"},
            {"label": "2'", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 4"},
            {"label": "1'", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 5"},
            {"label": "1", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 6"},
            {"label": "2", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 7"},
            {"label": "3", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 8"},
            {"label": "5", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 9"},
            {"label": "6", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gamelan note 10"},
        ],
    },

    # Saron is traditionally a single-row instrument (bars laid out in
    # one line, each struck individually) - unlike Gamelan's rectangular
    # grid. "columns": 6 means all 6 notes render as one row instead of
    # wrapping. Adjust if your actual physical Saron is arranged
    # differently. "shape": "bar" renders rectangular metallophone-style
    # keys (tapering length suggesting pitch) instead of circles.
    "SARON": {
        "columns": 6,
        "shape": "bar",
        "notes": [
            {"label": "1", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - saron note 1"},
            {"label": "2", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - saron note 2"},
            {"label": "3", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - saron note 3"},
            {"label": "4", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - saron note 4"},
            {"label": "5", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - saron note 5"},
            {"label": "6", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - saron note 6"},
            {"label": "7", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - saron note 7"},
        ],
    },

    # Gong is a single strike, one motor, one note - just one button.
    "GONG": {
        "columns": 1,
        "notes": [
            {"label": "1", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gong note 1"},
        ],
    },

    # Chime is one motor sweeping through all the dangling metal pieces
    # in a single continuous motion - functionally one trigger, even
    # though it produces multiple metal sounds as it sweeps. One button.
    "CHIME": {
        "columns": 1,
        "notes": [
            {"label": "1", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - chime note 1"},
        ],
    },

    # Gendang is a double-headed drum - two distinct sides, each
    # strikeable separately. Two buttons side by side.
    "GENDANG": {
        "columns": 2,
        "notes": [
            {"label": "Left", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gendang left"},
            {"label": "Right", "mac": "00:16:53:41:90:6e", "path": "PLACEHOLDER - gendang right"},
        ],
    },
}