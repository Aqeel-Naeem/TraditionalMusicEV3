import time
import threading
import ev3_dc as ev3
from config import INSTRUMENTS, POSITIONED_INSTRUMENTS

PORT_MAP = {
    "A": ev3.PORT_A,
    "B": ev3.PORT_B,
    "C": ev3.PORT_C,
    "D": ev3.PORT_D,
}

SONGS = {
    "Test Motors": [
        # ============================================================
        # COMPREHENSIVE MOTOR & ENSEMBLE DIAGNOSTIC TEST
        #
        # Tests every configured motor individually in sequence,
        # followed by a simultaneous ensemble strike across all bricks
        # to visually and audibly verify on-brick local timing.
        # ============================================================

        # --- 1. SARON: Left Pair (Notes 1 to 4) ---
        {"instrument": "SARON", "note": "Saron 1", "beat": 0.0, "hit_degrees": 90, "hit_speed": 60},
        {"instrument": "SARON", "note": "Saron 2", "beat": 1.5, "hit_degrees": 90, "hit_speed": 60},
        {"instrument": "SARON", "note": "Saron 3", "beat": 3.0, "hit_degrees": 90, "hit_speed": 60},
        {"instrument": "SARON", "note": "Saron 4", "beat": 4.5, "hit_degrees": 90, "hit_speed": 60},

        # --- 2. SARON: Right Pair (Notes 5 to 8) ---
        {"instrument": "SARON", "note": "Saron 5", "beat": 6.0, "hit_degrees": 90, "hit_speed": 60},
        {"instrument": "SARON", "note": "Saron 6", "beat": 7.5, "hit_degrees": 90, "hit_speed": 60},
        {"instrument": "SARON", "note": "Saron 7", "beat": 9.0, "hit_degrees": 90, "hit_speed": 60},
        {"instrument": "SARON", "note": "Saron 8", "beat": 10.5, "hit_degrees": 90, "hit_speed": 60},

        # --- 3. GENDANG: Individual Keys ---
        {"instrument": "GENDANG", "key": 0, "beat": 12.0, "degrees": 90, "speed": 60},
        {"instrument": "GENDANG", "key": 1, "beat": 13.5, "degrees": 90, "speed": 60},

        # --- 4. GONG: Individual Keys ---
        {"instrument": "GONG", "key": 0, "beat": 15.0, "degrees": 90, "speed": 60},
        {"instrument": "GONG", "key": 1, "beat": 16.5, "degrees": 90, "speed": 60},

        # --- 5. GAMELAN 1: Ports A, B, C ---
        {"instrument": "GAMELAN 1", "key": 0, "beat": 18.0, "degrees": 90, "speed": 60},
        {"instrument": "GAMELAN 1", "key": 1, "beat": 19.5, "degrees": 90, "speed": 60},
        {"instrument": "GAMELAN 1", "key": 2, "beat": 21.0, "degrees": 90, "speed": 60},

        # --- 6. GAMELAN 2: Ports A, B, C ---
        {"instrument": "GAMELAN 2", "key": 0, "beat": 22.5, "degrees": 90, "speed": 60},
        {"instrument": "GAMELAN 2", "key": 1, "beat": 24.0, "degrees": 90, "speed": 60},
        {"instrument": "GAMELAN 2", "key": 2, "beat": 25.5, "degrees": 90, "speed": 60},

        # --- 7. GAMELAN 3: Ports A, B, C ---
        {"instrument": "GAMELAN 3", "key": 0, "beat": 27.0, "degrees": 90, "speed": 60},
        {"instrument": "GAMELAN 3", "key": 1, "beat": 28.5, "degrees": 90, "speed": 60},
        {"instrument": "GAMELAN 3", "key": 2, "beat": 30.0, "degrees": 90, "speed": 60},

        # --- 8. SIMULTANEOUS ENSEMBLE HIT (Sync Test) ---
        {"instrument": "SARON", "note": "Saron 3", "beat": 32.0, "hit_degrees": 90, "hit_speed": 70},
        {"instrument": "GENDANG", "key": 0, "beat": 32.0, "degrees": 90, "speed": 70},
        {"instrument": "GONG", "key": 0, "beat": 32.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 1", "key": 0, "beat": 32.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 0, "beat": 32.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 3", "key": 0, "beat": 32.0, "degrees": 90, "speed": 70},
    ],

    "Rasa Sayang (10s Demo)": [
        # ============================================================
        # RASA SAYANG - 10 SECOND ENSEMBLE DEMO
        # ============================================================

        # ------------------------------------------------------------
        # INTRO - Chime
        # ------------------------------------------------------------
        {"instrument": "CHIME", "key": 0, "beat": 0.0, "duration": 0.4},

        # ------------------------------------------------------------
        # PHRASE 1 - "Rasa sayange..."
        # ------------------------------------------------------------
        {"instrument": "SARON", "note": "Saron 3", "beat": 1.0},
        {"instrument": "SARON", "note": "Saron 4", "beat": 1.5},
        {"instrument": "SARON", "note": "Saron 5", "beat": 2.0},
        {"instrument": "SARON", "note": "Saron 5", "beat": 2.5},

        {"instrument": "SARON", "note": "Saron 8", "beat": 3.25, "hit_speed": 65},
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
}


def get_song(name):
    """Return the note sequence for a song, or None if not found."""
    return SONGS.get(name)


def list_songs():
    """Return all available song names."""
    return list(SONGS.keys())


def compile_song_timelines(song_notes, tempo=1.0):
    """
    Compiles a song's note sequence into EV3 Bytecode Direct Commands
    per unique EV3 brick MAC address.

    Each brick receives a standalone bytecode timeline containing its
    exact motor commands and hardware timer waits (opTimer_Wait & opTimer_Ready).
    This executes on the EV3's ARM processor with microsecond precision,
    eliminating Bluetooth latency during song playback.
    """
    brick_events = {}

    for note in song_notes:
        inst = note.get("instrument")
        beat = note.get("beat", 0.0)
        time_ms = int(beat * tempo * 1000)

        # 1. Positioned instruments (e.g. SARON with controller + hitter)
        if inst in POSITIONED_INSTRUMENTS:
            p_def = POSITIONED_INSTRUMENTS[inst]
            note_key = note.get("note")
            note_cfg = p_def.get("notes", {}).get(note_key)
            if not note_cfg:
                continue
            pair_cfg = p_def.get("pairs", {}).get(note_cfg.get("pair"))
            if not pair_cfg:
                continue
            c_mac = pair_cfg["controller"].get("mac")
            c_port_str = pair_cfg["controller"].get("port")
            h_port_str = pair_cfg["hitter"].get("port")
            if not c_mac or not c_port_str or not h_port_str:
                continue
            c_port = PORT_MAP.get(c_port_str)
            h_port = PORT_MAP.get(h_port_str)
            defaults = p_def.get("defaults", {})

            hit_deg = note.get("hit_degrees", defaults.get("hit_degrees", 90))
            hit_spd = note.get("hit_speed", defaults.get("hit_speed", 50))
            ret_deg = note.get("return_degrees", hit_deg)
            h_dir = 1 if pair_cfg.get("hitter_direction", "clockwise") == "clockwise" else -1

            evt = {
                "type": "positioned",
                "time_ms": time_ms,
                "controller_port": c_port,
                "controller_angle": note_cfg["angle"],
                "controller_speed": defaults.get("position_speed", 50),
                "hitter_port": h_port,
                "hit_degrees": hit_deg,
                "hit_speed": hit_spd,
                "return_degrees": ret_deg,
                "hitter_dir": h_dir,
            }
            brick_events.setdefault(c_mac, []).append(evt)

        # 2. Standard direct instruments (Gamelan, Gong, Gendang, etc.)
        elif inst in INSTRUMENTS:
            locs = INSTRUMENTS[inst]
            key = note.get("key")
            if key is not None and 0 <= key < len(locs):
                target_locs = [locs[key]]
            else:
                target_locs = locs

            for loc in target_locs:
                mac = loc.get("mac")
                port_str = loc.get("port")
                if not mac or not port_str:
                    continue
                port_mask = PORT_MAP.get(port_str)
                if not port_mask:
                    continue

                direction = note.get("direction", "clockwise")
                dir_mult = 1 if direction == "clockwise" else -1
                speed = note.get("speed", 50)
                degrees = note.get("degrees") if note.get("degrees") is not None else note.get("degree")
                duration = note.get("duration", 0.3)

                evt = {
                    "type": "standard",
                    "time_ms": time_ms,
                    "port_mask": port_mask,
                    "degrees": degrees,
                    "return_degrees": note.get("return_degrees", degrees),
                    "duration": duration,
                    "speed": speed,
                    "dir_mult": dir_mult,
                }
                brick_events.setdefault(mac, []).append(evt)

    # Build binary direct command bytecode for each brick
    bytecodes = {}
    for mac, evts in brick_events.items():
        ops = []
        last_time_ms = 0

        for evt in sorted(evts, key=lambda x: x["time_ms"]):
            gap_ms = evt["time_ms"] - last_time_ms
            if gap_ms > 0:
                ops.extend((
                    ev3.opTimer_Wait,
                    ev3.LCX(gap_ms),
                    ev3.LVX(0),
                    ev3.opTimer_Ready,
                    ev3.LVX(0),
                ))
                last_time_ms = evt["time_ms"]

            if evt["type"] == "positioned":
                # Step 1: position controller
                ops.extend((
                    ev3.opOutput_Step_Speed,
                    ev3.LCX(0),
                    ev3.LCX(evt["controller_port"]),
                    ev3.LCX(evt["controller_speed"]),
                    ev3.LCX(0),
                    ev3.LCX(evt["controller_angle"]),
                    ev3.LCX(0),
                    ev3.LCX(1),  # Brake
                    ev3.opOutput_Start,
                    ev3.LCX(0),
                    ev3.LCX(evt["controller_port"]),
                    ev3.opOutput_Ready,
                    ev3.LCX(0),
                    ev3.LCX(evt["controller_port"]),
                    # Step 2: strike hitter
                    ev3.opOutput_Step_Speed,
                    ev3.LCX(0),
                    ev3.LCX(evt["hitter_port"]),
                    ev3.LCX(evt["hitter_dir"] * evt["hit_speed"]),
                    ev3.LCX(0),
                    ev3.LCX(evt["hit_degrees"]),
                    ev3.LCX(0),
                    ev3.LCX(1),
                    ev3.opOutput_Start,
                    ev3.LCX(0),
                    ev3.LCX(evt["hitter_port"]),
                    ev3.opOutput_Ready,
                    ev3.LCX(0),
                    ev3.LCX(evt["hitter_port"]),
                    # Step 3: return hitter
                    ev3.opOutput_Step_Speed,
                    ev3.LCX(0),
                    ev3.LCX(evt["hitter_port"]),
                    ev3.LCX(-evt["hitter_dir"] * evt["hit_speed"]),
                    ev3.LCX(0),
                    ev3.LCX(evt["return_degrees"]),
                    ev3.LCX(0),
                    ev3.LCX(1),
                    ev3.opOutput_Start,
                    ev3.LCX(0),
                    ev3.LCX(evt["hitter_port"]),
                    ev3.opOutput_Ready,
                    ev3.LCX(0),
                    ev3.LCX(evt["hitter_port"]),
                ))
            elif evt["type"] == "standard":
                if evt["degrees"] is not None:
                    # Degree-based outward strike & automatic return
                    ops.extend((
                        ev3.opOutput_Step_Speed,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                        ev3.LCX(evt["dir_mult"] * evt["speed"]),
                        ev3.LCX(0),
                        ev3.LCX(evt["degrees"]),
                        ev3.LCX(0),
                        ev3.LCX(1),
                        ev3.opOutput_Start,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                        ev3.opOutput_Ready,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                        # Return stroke
                        ev3.opOutput_Step_Speed,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                        ev3.LCX(-evt["dir_mult"] * evt["speed"]),
                        ev3.LCX(0),
                        ev3.LCX(evt["return_degrees"]),
                        ev3.LCX(0),
                        ev3.LCX(1),
                        ev3.opOutput_Start,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                        ev3.opOutput_Ready,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                    ))
                else:
                    # Duration-based spin/strike
                    dur_ms = int(evt["duration"] * 1000)
                    ops.extend((
                        ev3.opOutput_Time_Speed,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                        ev3.LCX(evt["dir_mult"] * evt["speed"]),
                        ev3.LCX(0),
                        ev3.LCX(dur_ms),
                        ev3.LCX(0),
                        ev3.LCX(0),
                        ev3.opOutput_Start,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                        ev3.opOutput_Ready,
                        ev3.LCX(0),
                        ev3.LCX(evt["port_mask"]),
                    ))

        # Final safety stop at end of song
        ops.extend((
            ev3.opOutput_Stop,
            ev3.LCX(0),
            ev3.LCX(15),
            ev3.LCX(0),
        ))
        bytecodes[mac] = b"".join(ops)

    return bytecodes


def play_song(ev3, song_notes, tempo=1.0, stop_event=None):
    """
    Plays a song across multiple EV3 bricks using on-brick local timelines.

    The complete timeline bytecode is compiled and sent to all active EV3
    bricks simultaneously, executing in hardware with microsecond timing.
    """
    print(f"Compiling song timeline ({len(song_notes)} notes, tempo {tempo})...")
    timelines = compile_song_timelines(song_notes, tempo)

    if not timelines:
        print("No active EV3 timelines generated for this song.")
        return

    # Launch timeline execution concurrently across all active bricks
    threads = []
    for mac, bytecode in timelines.items():
        if not ev3._brick_status.get(mac, False):
            print(f"Skipping brick {mac}: not connected")
            continue

        t = threading.Thread(
            target=ev3.play_timeline,
            args=(mac, bytecode),
            daemon=True,
            name=f"timeline-{mac}",
        )
        threads.append(t)

    print(f"Starting synchronized playback across {len(threads)} EV3 brick(s)...")
    for t in threads:
        t.start()

    # Calculate expected total song duration
    song_duration = max(note.get("beat", 0.0) for note in song_notes) * tempo + 3.0
    start_time = time.perf_counter()

    # Monitor playback and handle interrupt/stop events
    while time.perf_counter() - start_time < song_duration:
        if stop_event is not None and stop_event.is_set():
            print("Stop event received - stopping all EV3 brick timelines.")
            ev3.stop_all_motors()
            return
        time.sleep(0.05)

    print("Playback complete.")
