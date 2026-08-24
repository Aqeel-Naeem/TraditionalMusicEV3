"""
Maps each EV3 Classroom program to the brick(s) it should run on, so the
GUI can trigger already-downloaded programs by name.

Fill in PROGRAMS once you know, for each program:
  - which brick(s) (MAC address) it needs to run on
  - the exact path of the downloaded .rbf on that brick

Use test/list_ev3_files.py <mac> [path] to find the exact remote path -
EV3 Classroom's own naming is case-sensitive, don't guess it.

Each song/program entry maps { brick_mac: remote_rbf_path }. A song that
uses multiple bricks (e.g. all 7 instruments playing together) just lists
every brick it needs - ev3_program_runner.py's play_programs() starts all
of them together, skipping any brick that isn't currently connected.
"""

PROGRAMS = {
    # "Program Display Name": {
    #     "<brick mac>": "<remote .rbf path on that brick>",
    #     "<another brick mac>": "<its own .rbf path>",
    # },

    "Top Spinner": {
        "00:16:53:41:90:6e": "/home/root/lms2012/prjs/top spinner/top spinner.rbf",
    },

    # Example of a full-ensemble song using all 7 bricks - fill in each
    # path as you confirm it with list_ev3_files.py:
    # "Rasa Sayang": {
    #     "00:16:53:46:be:aa": "/home/root/lms2012/prjs/RasaSayangGongChime/RasaSayangGongChime.rbf",
    #     "00:16:53:43:d6:4a": "/home/root/lms2012/prjs/RasaSayangGendang/RasaSayangGendang.rbf",
    #     "00:16:53:41:90:6e": "/home/root/lms2012/prjs/RasaSayangGamelan1/RasaSayangGamelan1.rbf",
    #     "00:16:53:4b:b2:e0": "/home/root/lms2012/prjs/RasaSayangGamelan2/RasaSayangGamelan2.rbf",
    #     "00:16:53:48:9b:39": "/home/root/lms2012/prjs/RasaSayangGamelan3/RasaSayangGamelan3.rbf",
    #     "00:16:53:41:95:2e": "/home/root/lms2012/prjs/RasaSayangSaronLeft/RasaSayangSaronLeft.rbf",
    #     "00:16:53:4d:46:72": "/home/root/lms2012/prjs/RasaSayangSaronRight/RasaSayangSaronRight.rbf",
    # },

    # A song using only a subset of instruments works the same way -
    # just list the bricks it actually needs:
    # "Test Motors": {
    #     "00:16:53:46:be:aa": "/home/root/lms2012/prjs/TestGongChime/TestGongChime.rbf",
    #     "00:16:53:43:d6:4a": "/home/root/lms2012/prjs/TestGendang/TestGendang.rbf",
    # },
}