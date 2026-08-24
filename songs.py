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
        {"instrument": "GAMELAN 1", "key": 0, "beat": 0.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 1", "key": 1, "beat": 0.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 1", "key": 2, "beat": 1.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 1", "key": 2, "beat": 2.0, "degrees": 90, "speed": 70},

        {"instrument": "GAMELAN 2", "key": 0, "beat": 3.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 1, "beat": 4.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 2, "beat": 4.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 3", "key": 0, "beat": 5.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 3", "key": 1, "beat": 5.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 3", "key": 2, "beat": 6.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 0, "beat": 6.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 1, "beat": 7.0, "degrees": 90, "speed": 70},
    ],

    "Rasa Sayang (10s Demo)": [
        {"instrument": "GAMELAN 1", "key": 0, "beat": 0.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 1", "key": 1, "beat": 0.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 1", "key": 2, "beat": 1.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 1", "key": 2, "beat": 2.0, "degrees": 90, "speed": 70},

        {"instrument": "GAMELAN 2", "key": 0, "beat": 3.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 1, "beat": 4.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 2, "beat": 4.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 3", "key": 0, "beat": 5.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 3", "key": 1, "beat": 5.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 3", "key": 2, "beat": 6.0, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 0, "beat": 6.5, "degrees": 90, "speed": 70},
        {"instrument": "GAMELAN 2", "key": 1, "beat": 7.0, "degrees": 90, "speed": 70},
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
            if not c_mac or not c_port_str:
                continue
            c_port = PORT_MAP.get(c_port_str)

            # "hitter" may be a single location dict or a list of them
            # (e.g. SARON's 2 hit motors on the same brick). Combine every
            # hitter that shares the controller's brick into one port
            # bitmask so a single opOutput_Start/opOutput_Ready pair fires
            # and waits on all of them at once (true simultaneous strike).
            hitter_cfg = pair_cfg["hitter"]
            hitter_locations = hitter_cfg if isinstance(hitter_cfg, list) else [hitter_cfg]
            h_port = 0
            for loc in hitter_locations:
                if loc.get("mac") != c_mac:
                    continue
                loc_port = PORT_MAP.get(loc.get("port"))
                if loc_port:
                    h_port |= loc_port
            if not h_port:
                continue
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
        # Tracks each controller port's last-commanded absolute angle.
        # opOutput_Step_Speed is a RELATIVE "rotate by N degrees" command,
        # not a "move to absolute angle" command, so each controller move
        # must send the delta from its previous position - not the raw
        # note angle - or repeated notes accumulate drift every time they
        # run, eventually driving the motor into a mechanical hard stop.
        # 0 = wherever the controller physically was when the app connected.
        controller_positions = {}

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
                # Step 1: position controller (relative move = delta from
                # its last commanded position). Direction is encoded in
                # SPEED's sign, and STEP2 is an unsigned degree magnitude -
                # matching how ev3_dc's own Motor.start_move_by() builds
                # this same opcode.
                port = evt["controller_port"]
                prev_angle = controller_positions.get(port, 0)
                target_angle = evt["controller_angle"]
                delta = target_angle - prev_angle
                controller_positions[port] = target_angle

                if delta != 0:
                    c_speed = evt["controller_speed"] if delta >= 0 else -evt["controller_speed"]
                    c_angle_mag = abs(delta)
                    ops.extend((
                        ev3.opOutput_Step_Speed,
                        ev3.LCX(0),
                        ev3.LCX(port),
                        ev3.LCX(c_speed),
                        ev3.LCX(0),
                        ev3.LCX(c_angle_mag),
                        ev3.LCX(0),
                        ev3.LCX(1),  # Brake
                        ev3.opOutput_Start,
                        ev3.LCX(0),
                        ev3.LCX(port),
                        ev3.opOutput_Ready,
                        ev3.LCX(0),
                        ev3.LCX(port),
                    ))

                ops.extend((
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

        # Return every controller used in this song back to its starting
        # position (0 = wherever it physically was at connect time), so the
        # stick ends upright/centered instead of wherever the last note
        # left it, and the next run doesn't need a manual recenter.
        for port, last_angle in controller_positions.items():
            if last_angle == 0:
                continue
            return_speed = -50 if last_angle >= 0 else 50
            return_mag = abs(last_angle)
            ops.extend((
                ev3.opOutput_Step_Speed,
                ev3.LCX(0),
                ev3.LCX(port),
                ev3.LCX(return_speed),
                ev3.LCX(0),
                ev3.LCX(return_mag),
                ev3.LCX(0),
                ev3.LCX(1),  # Brake
                ev3.opOutput_Start,
                ev3.LCX(0),
                ev3.LCX(port),
                ev3.opOutput_Ready,
                ev3.LCX(0),
                ev3.LCX(port),
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

    # Calculate expected total song duration. The compiled timeline's
    # inter-note waits are based on scheduled beat times only - they don't
    # account for how long each note's actual motor movement takes, so a
    # brick can still be genuinely executing after the nominal beat-based
    # duration has elapsed. Disconnecting (which force-stops mid-movement)
    # before that happens is unsafe, so this buffer is generous and scales
    # with note count rather than using a small flat margin.
    song_duration = (
        max(note.get("beat", 0.0) for note in song_notes) * tempo
        + 5.0
        + 0.5 * len(song_notes)
    )
    start_time = time.perf_counter()

    # Monitor playback and handle interrupt/stop events
    while time.perf_counter() - start_time < song_duration:
        if stop_event is not None and stop_event.is_set():
            print("Stop event received - stopping all EV3 brick timelines.")
            ev3.stop_all_motors()
            return
        time.sleep(0.05)

    print("Playback complete.")
