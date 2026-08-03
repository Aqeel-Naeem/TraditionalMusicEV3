import time

SONGS = {
    "Rasa Sayang": [
        {"instrument": "GONG",  "beat": 0.0, "duration": 0.5},
        {"instrument": "SARON", "beat": 0.5, "duration": 0.25},
        {"instrument": "SARON", "beat": 0.75, "duration": 0.25},
        {"instrument": "DRUM",  "beat": 1.0, "duration": 0.5},
        {"instrument": "SARON", "beat": 1.5, "duration": 0.25},
        {"instrument": "SARON", "beat": 1.75, "duration": 0.25},
        {"instrument": "GONG",  "beat": 2.0, "duration": 0.5},
        {"instrument": "DRUM",  "beat": 2.5, "duration": 0.5},
        {"instrument": "SARON", "beat": 3.0, "duration": 0.25},
        {"instrument": "SARON", "beat": 3.25, "duration": 0.25},
    ],
}


def get_song(name):
    """Return the note sequence for a song, or None if not found."""
    return SONGS.get(name)


def list_songs():
    """Return all available song names."""
    return list(SONGS.keys())


def play_song(ev3, song_notes, tempo=1.0):
    """
    Plays a song by sending timed commands to the EV3.
    tempo: multiplier for speed (1.0 = normal, 0.5 = half speed, etc.)
    """
    last_beat = 0.0

    for note in song_notes:
        wait = (note["beat"] - last_beat) * tempo
        if wait > 0:
            time.sleep(wait)

        ev3.send_command(note["instrument"])
        last_beat = note["beat"]