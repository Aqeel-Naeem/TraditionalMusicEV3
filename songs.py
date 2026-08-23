import time
import threading

SONGS = {
    "Rasa Sayang (10s Demo)": [
        # ============================================================
        # RASA SAYANG - 10 SECOND ENSEMBLE DEMO
        #
        # Assumed Saron mapping:
        #   Saron 1 = scale degree 1
        #   Saron 2 = scale degree 2
        #   Saron 3 = scale degree 3
        #   Saron 4 = scale degree 4
        #   Saron 5 = scale degree 5
        #   Saron 6 = scale degree 6
        #   Saron 7 = scale degree 7
        #   Saron 8 = high 1'
        #
        # IMPORTANT:
        # The Saron pitch mapping is currently a dummy calibration
        # in config.py and must be physically verified.
        #
        # The melody is based on the commonly published refrain:
        #   3 4 5 5 | 1' 7 6 5 | 5 3 4 5
        #
        # This is an EV3 arrangement/prototype, not a verified
        # recording-accurate transcription.
        # ============================================================

        # ------------------------------------------------------------
        # INTRO - Chime
        # ------------------------------------------------------------

        {"instrument": "CHIME", "key": 0, "beat": 0.0, "duration": 0.4},

        # ------------------------------------------------------------
        # PHRASE 1 - "Rasa sayange..."
        #
        # Saron melody:
        # 3  4  5  5 | 1'  7  6  5
        # ------------------------------------------------------------

        {"instrument": "SARON", "note": "Saron 3", "beat": 1.0},
        {"instrument": "SARON", "note": "Saron 4", "beat": 1.5},
        {"instrument": "SARON", "note": "Saron 5", "beat": 2.0},
        {"instrument": "SARON", "note": "Saron 5", "beat": 2.5},

        {"instrument": "SARON", "note": "Saron 8", "beat": 3.25,
        "hit_speed": 65},
        {"instrument": "SARON", "note": "Saron 7", "beat": 3.75},
        {"instrument": "SARON", "note": "Saron 6", "beat": 4.25},
        {"instrument": "SARON", "note": "Saron 5", "beat": 4.75},

        # Gendang rhythm
        {"instrument": "GENDANG", "key": 0, "beat": 1.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 2.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 3.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 4.0, "duration": 0.25},

        # Light Bonang support
        {"instrument": "BONANG", "key": 0, "beat": 2.0, "duration": 0.2},
        {"instrument": "BONANG", "key": 0, "beat": 4.0, "duration": 0.2},

        # ------------------------------------------------------------
        # PHRASE 2 - "Rasa sayang sayange..."
        #
        # 5  3  4  5
        # ------------------------------------------------------------

        {"instrument": "SARON", "note": "Saron 5", "beat": 5.5},
        {"instrument": "SARON", "note": "Saron 3", "beat": 6.0},
        {"instrument": "SARON", "note": "Saron 4", "beat": 6.5},
        {"instrument": "SARON", "note": "Saron 5", "beat": 7.0},

        # Bonang response
        {"instrument": "BONANG", "key": 0, "beat": 5.5, "duration": 0.2},
        {"instrument": "BONANG", "key": 0, "beat": 6.5, "duration": 0.2},
        {"instrument": "BONANG", "key": 0, "beat": 7.0, "duration": 0.2},

        # Gendang continues the pulse
        {"instrument": "GENDANG", "key": 0, "beat": 5.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 6.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 7.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 8.0, "duration": 0.25},

        # Gong marks the end of the first recognizable phrase
        {"instrument": "GONG", "key": None, "beat": 8.0, "duration": 0.5},

        # ------------------------------------------------------------
        # REPEAT / RESPONSE
        #
        # Bring back the recognizable 3-4-5 motif
        # ------------------------------------------------------------

        {"instrument": "SARON", "note": "Saron 3", "beat": 9.0},
        {"instrument": "SARON", "note": "Saron 4", "beat": 9.5},
        {"instrument": "SARON", "note": "Saron 5", "beat": 10.0},
        {"instrument": "SARON", "note": "Saron 5", "beat": 10.5},

        {"instrument": "BONANG", "key": 0, "beat": 10.0, "duration": 0.2},

        # Gendang
        {"instrument": "GENDANG", "key": 0, "beat": 9.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 10.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 11.0, "duration": 0.25},

        # Chime transition
        {"instrument": "CHIME", "key": 0, "beat": 11.5, "duration": 0.4},

        # ------------------------------------------------------------
        # ENDING
        # ------------------------------------------------------------

        {"instrument": "SARON", "note": "Saron 5", "beat": 13.0},
        {"instrument": "SARON", "note": "Saron 3", "beat": 14.0},
        {"instrument": "SARON", "note": "Saron 5", "beat": 15.0},

        {"instrument": "GENDANG", "key": 0, "beat": 13.0, "duration": 0.25},
        {"instrument": "GENDANG", "key": 0, "beat": 14.0, "duration": 0.25},

        # Final gong
        {"instrument": "GONG", "key": None, "beat": 16.0, "duration": 0.5},
    ],

    "Test Motors": [
        # Degree-based strike calibration: move out, then automatically return.
        # {"instrument": "SARON", "note": "Saron 1", "beat": 0.0, "hit_degrees": 360, "hit_speed": 100},
        # {"instrument": "SARON", "note": "Saron 2", "beat": 1.0, "hit_degrees": 180, "hit_speed": 80},

        {"instrument": "SARON", "note": "Saron 1", "beat": 0.0},
        {"instrument": "SARON", "note": "Saron 2", "beat": 0.5},
        {"instrument": "SARON", "note": "Saron 3", "beat": 1.0},
        {"instrument": "SARON", "note": "Saron 4", "beat": 1.5},
        {"instrument": "SARON", "note": "Saron 5", "beat": 2.0},
        {"instrument": "SARON", "note": "Saron 6", "beat": 2.5},
        {"instrument": "SARON", "note": "Saron 7", "beat": 3.0},
        {"instrument": "SARON", "note": "Saron 8", "beat": 3.5},
        {"instrument": "GENDANG", "key": 0, "beat": 4.0, "degree": 90},
        {"instrument": "GENDANG", "key": 1, "beat": 5.0, "degree": 90},
        {"instrument": "GONG", "key": 0, "beat": 6.0, "degree": 90},
        {"instrument": "GONG", "key": 1, "beat": 7.0, "degree": 90},
        {"instrument": "GAMELAN 1", "key": 0, "beat": 8.0, "degree": 90},
        {"instrument": "GAMELAN 1", "key": 1, "beat": 9.0, "degree": 90},
        {"instrument": "GAMELAN 1", "key": 2, "beat": 10.0, "degree": 90},
        {"instrument": "GAMELAN 2", "key": 0, "beat": 11.0, "degree": 90},
        {"instrument": "GAMELAN 2", "key": 1, "beat": 12.0, "degree": 90},
        {"instrument": "GAMELAN 2", "key": 2, "beat": 13.0, "degree": 90},
        {"instrument": "GAMELAN 3", "key": 0, "beat": 14.0, "degree": 90},
        {"instrument": "GAMELAN 3", "key": 1, "beat": 15.0, "degree": 90},
        {"instrument": "GAMELAN 3", "key": 2, "beat": 16.0, "degree": 90},
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
    positioned_requests = {}
    positioned_requests_lock = threading.Lock()

    # Prepare the first note for each controller pair before the song clock
    # starts, so the first audible hit never waits for positioning.
    first_notes_by_pair = {}
    for note in song_notes:
        instrument = note["instrument"]
        if not ev3.is_positioned_instrument(instrument):
            continue
        pair = ev3.get_positioned_note_pair(instrument, note.get("note"))
        if pair is not None:
            pair_key = (instrument, pair)
            previous_note = first_notes_by_pair.get(pair_key)
            if previous_note is None or note["beat"] < previous_note["beat"]:
                first_notes_by_pair[pair_key] = note

    for note in first_notes_by_pair.values():
        request = ev3.prepare_positioned_note(
            note["instrument"],
            note["note"],
            note.get("hit_degrees"),
            note.get("hit_speed"),
            note.get("return_degrees"),
        )
        if request is not None:
            positioned_requests[id(note)] = request

    for request in positioned_requests.values():
        request["ready"].wait()

    # Every later positioned note starts controller movement ahead of its beat.
    # Its worker holds the pair until the beat triggers the hitter, preserving
    # the selected angle even when the next note is queued early.
    first_note_ids = {id(note) for note in first_notes_by_pair.values()}
    for note in song_notes:
        instrument = note["instrument"]
        if (not ev3.is_positioned_instrument(instrument)
                or id(note) in first_note_ids):
            continue

        def _prepare_later(positioned_note=note):
            lead_time = ev3.get_position_lead_seconds(positioned_note["instrument"])
            delay = (positioned_note["beat"] - lead_time) * tempo
            if delay > 0:
                time.sleep(delay)
            if stop_event is not None and stop_event.is_set():
                return
            request = ev3.prepare_positioned_note(
                positioned_note["instrument"],
                positioned_note.get("note"),
                positioned_note.get("hit_degrees"),
                positioned_note.get("hit_speed"),
                positioned_note.get("return_degrees"),
            )
            if request is not None:
                with positioned_requests_lock:
                    positioned_requests[id(positioned_note)] = request

        threading.Thread(target=_prepare_later, daemon=True).start()

    last_beat = 0.0

    for beat, notes in grouped:
        if stop_event is not None and stop_event.is_set():
            with positioned_requests_lock:
                requests_to_cancel = list(positioned_requests.values())
            for request in requests_to_cancel:
                ev3.cancel_positioned_note(request)
            print("Song stopped early.")
            return

        wait = (beat - last_beat) * tempo
        if wait > 0:
            time.sleep(wait)

        threads = []
        for note in notes:
            if ev3.is_positioned_instrument(note["instrument"]):
                with positioned_requests_lock:
                    request = positioned_requests.get(id(note))
                if request is None:
                    request = ev3.prepare_positioned_note(
                        note["instrument"],
                        note.get("note"),
                        note.get("hit_degrees"),
                        note.get("hit_speed"),
                        note.get("return_degrees"),
                    )
                ev3.trigger_positioned_note(request)
                continue

            t = threading.Thread(
                target=ev3.send_command,
                kwargs={
                    "command": note["instrument"],
                    "key": note.get("key"),
                    "duration": note.get("duration", 0.3),
                    "speed": note.get("speed", 50),
                    "direction": note.get("direction", "clockwise"),
                    "degrees": note.get("degrees"),
                    "return_degrees": note.get("return_degrees"),
                },
                daemon=True,
            )
            threads.append(t)
            t.start()

        # Don't block waiting for threads to finish - let them fire and move on,
        # so the next beat's timing isn't delayed by slow Bluetooth responses.

        last_beat = beat