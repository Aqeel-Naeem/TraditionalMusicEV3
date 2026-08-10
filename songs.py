import time
import threading

SONGS = {
    "Rasa Sayang": [
        # "key" refers to which motor within that instrument's motor list to strike.
        # Omit "key" (or set to None) to fire ALL motors for that instrument together.
        # speed defaults to 50
        {"instrument": "GONG",  "key": None, "beat": 0.0,  "duration": 0.5},
        {"instrument": "SARON", "key": 0,    "beat": 0.5,  "duration": 0.25, "speed": 100},
        {"instrument": "SARON", "key": 1,    "beat": 0.75, "duration": 0.25, "speed": 10},
        {"instrument": "DRUM",  "key": None, "beat": 1.0,  "duration": 0.5},
        {"instrument": "SARON", "key": 0,    "beat": 1.5,  "duration": 0.25},
        {"instrument": "SARON", "key": 1,    "beat": 1.75, "duration": 0.25},
        {"instrument": "GONG",  "key": None, "beat": 2.0,  "duration": 0.5},
        {"instrument": "DRUM",  "key": None, "beat": 2.5,  "duration": 0.5},
        {"instrument": "SARON", "key": 0,    "beat": 3.0,  "duration": 0.25},
        {"instrument": "SARON", "key": 1,    "beat": 3.25, "duration": 0.25},
    ],

    "Test Motors": [
        # Basic check that every instrument responds
        {"instrument": "GONG",  "key": None, "beat": 0.0, "duration": 1.0},
        {"instrument": "SARON", "key": 0,    "beat": 1.0, "duration": 1.0},
        {"instrument": "SARON", "key": 1,    "beat": 2.0, "duration": 1.0},
        {"instrument": "DRUM",  "key": None, "beat": 3.0, "duration": 1.0},
 
        # Speed demo: same instrument, same duration, only speed differs -
        # a clean side-by-side comparison for demo purposes.
        {"instrument": "DRUM", "key": None, "beat": 5.0, "duration": 1.0, "speed": 20},
        {"instrument": "DRUM", "key": None, "beat": 7.0, "duration": 1.0, "speed": 100},
    ],
}


def get_song(name):
    """Return the note sequence for a song, or None if not found."""
    return SONGS.get(name)


def list_songs():
    """Return all available song names."""
    return list(SONGS.keys())


def _group_notes_by_beat(song_notes):
    """Groups notes that share the same beat, so they can fire together."""
    groups = {}
    for note in song_notes:
        groups.setdefault(note["beat"], []).append(note)
    return sorted(groups.items())  # list of (beat, [notes]) sorted by beat


def play_song(ev3, song_notes, tempo=1.0, stop_event=None):
    """
    Plays a song across (potentially multiple) EV3 bricks and motors.
    Notes sharing the same beat fire simultaneously via separate threads,
    so multi-brick/multi-motor timing stays tight instead of drifting
    due to per-brick Bluetooth latency.

    stop_event: an optional threading.Event(). If it becomes set while
    the song is playing, playback stops before the next beat fires
    (used to let voice/gesture commands interrupt a song in progress).
    """
    grouped = _group_notes_by_beat(song_notes)
    last_beat = 0.0

    for beat, notes in grouped:
        if stop_event is not None and stop_event.is_set():
            print("Song stopped early.")
            return

        wait = (beat - last_beat) * tempo
        if wait > 0:
            time.sleep(wait)

        threads = []
        for note in notes:
            t = threading.Thread(
                target=ev3.send_command,
                kwargs={
                    "command": note["instrument"],
                    "key": note.get("key"),
                    "duration": note["duration"],
                    "speed": note.get("speed", 50),
                },
                daemon=True,
            )
            threads.append(t)
            t.start()

        # Don't block waiting for threads to finish - let them fire and move on,
        # so the next beat's timing isn't delayed by slow Bluetooth responses.

        last_beat = beat