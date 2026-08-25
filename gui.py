import customtkinter as ctk
from ev3 import EV3
import threading
import queue
import sys
import re
import time
import difflib
from ai.voice import VoiceController
from ai.gesture import GestureController
from songs import get_song, play_song, list_songs
from config import INSTRUMENTS, POSITIONED_INSTRUMENTS
from ev3_program_runner import play_programs
from ev3_program_config import PROGRAMS

# Color palette - used by ROLE, not uniformly, so buttons signal their
# importance instead of all looking the same weight.
COLOR_ACCENT = "#d97706"        # primary/demo-facing actions (amber - fits the traditional-instrument theme)
COLOR_ACCENT_HOVER = "#b45309"
COLOR_SUCCESS = "#22c55e"       # connected/success state only
COLOR_DANGER = "#ef4444"        # stop/danger only
COLOR_DANGER_HOVER = "#dc2626"
COLOR_MUTED = "#52525b"         # secondary/calibration/testing controls
COLOR_MUTED_HOVER = "#3f3f46"
COLOR_AI = "#0891b2"            # voice - a distinct "featured" highlight
COLOR_AI_HOVER = "#0e7490"
COLOR_GESTURE = "#a855f7"       # gesture events - distinct from voice's teal
COLOR_LOG_MUTED = "#71717a"     # unrecognized/minor log lines - present but quiet

# Set to False to hide the legacy Architecture 2 test-song section from the
# GUI entirely (e.g. for a demo) without deleting any code. Flip back to
# True whenever you want it visible again.
SHOW_LEGACY_ARCHITECTURE_2 = False

# Set to False to hide the instrument status grid and Instrument Control
# section - relevant when no instruments are configured yet (e.g. testing
# a motor-less master coordinator brick only). Flip back to True once
# instruments are added to config.py again.
SHOW_INSTRUMENT_SECTIONS = False

# GAMELAN plays its notes low-to-high in sequence when triggered (button,
# gesture, or voice), instead of firing all motors at once - this is the
# demo instrument. It's a single combined instrument spanning all 3
# physical units (see config.py) - the sequence chains through all 9
# notes in order: unit 1, then unit 2, then unit 3.
GAMELAN_INSTRUMENTS = {"GAMELAN"}
GAMELAN_NOTE_DELAY = 0.4  # seconds between each note in the sequence


class _StdoutTee:
    """
    Wraps the real stdout: every print() (from ANY thread - voice,
    gesture, brick workers, song playback, etc.) still goes to the real
    terminal as before, AND also gets pushed onto a thread-safe queue
    that the GUI polls to fill the Activity Panel. This means every
    existing print() statement across the whole project automatically
    shows up in the panel too, with no changes needed to those files.
    """
    def __init__(self, real_stdout, line_queue):
        self._real_stdout = real_stdout
        self._queue = line_queue

    def write(self, text):
        self._real_stdout.write(text)
        if text.strip():  # skip pushing bare newlines from print()'s own \n
            self._queue.put(text)

    def flush(self):
        self._real_stdout.flush()

class EV3App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.ev3 = EV3()
        self.title("Traditional Music EV3 Controller")
        self.geometry("1450x800")

        # Activity Panel: redirect stdout so every existing print()
        # anywhere in the project (voice, gesture, song playback, brick
        # workers, etc.) automatically shows up in the GUI panel too,
        # not just the terminal.
        self._log_queue = queue.Queue()
        sys.stdout = _StdoutTee(sys.stdout, self._log_queue)

        self.current_stop_event = None
        self.song_list = list_songs()
        self.current_song_index = 0
        self._health_check_running = False
        self.song_playing = False

        # One combined list, used everywhere (status grid, buttons, gesture,
        # voice matching) - so an instrument only needs to be added to
        # config.py once, in EITHER INSTRUMENTS or POSITIONED_INSTRUMENTS,
        # and it automatically shows up consistently across the whole app.
        self.all_instruments = list(INSTRUMENTS.keys()) + list(POSITIONED_INSTRUMENTS.keys())

        # Initialized here (not just inside create_status_grid) so
        # refresh_instrument_status's polling loop is always safe to run,
        # even when SHOW_INSTRUMENT_SECTIONS is False and the grid is
        # never actually built - it just iterates an empty dict then.
        self.instrument_status_labels = {}

        # mac -> instrument name(s), used to translate raw MAC addresses in
        # log output into friendly instrument names for the Activity Panel.
        self._mac_to_instruments = {}
        for name, locations in INSTRUMENTS.items():
            for loc in locations:
                self._mac_to_instruments.setdefault(loc["mac"], set()).add(name)
        for name, definition in POSITIONED_INSTRUMENTS.items():
            for pair in definition["pairs"].values():
                macs = {pair["controller"].get("mac")} | {h.get("mac") for h in pair["hitter"]}
                for mac in macs:
                    if mac:
                        self._mac_to_instruments.setdefault(mac, set()).add(name)

        self.voice = VoiceController(on_command=self.handle_voice_command)
        self.gesture = GestureController(
            on_instrument_finger_count=self.handle_instrument_gesture,
            on_song_finger_count=self.handle_song_gesture,
            on_stop=self.stop_song,
            hint_text=(
                "Right hand = instrument | Left hand = song | Fist = stop"
                if self.all_instruments
                else "Left hand = song | Fist = stop"
            ),
        )

        self.create_widgets()  # <- this must come AFTER self.voice/self.gesture are created
        self.refresh_instrument_status()
        self.background_health_check()
        self._drain_log_queue()
        self._sync_gesture_button()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """
        Full safe shutdown, used by both the window's X button and the
        voice "exit"/"quit"/"shutdown" commands. Order matters: motors
        need to be told to stop WHILE still connected (stop_all_motors()
        can't reach the brick after disconnect), so that happens first.
        """
        # Stop any in-progress song/Gamelan sequence and halt motors
        # cleanly, before the connection goes away.
        if self.current_stop_event is not None:
            self.current_stop_event.set()
        if self.ev3.connected:
            self.ev3.stop_all_motors()

        # Stop gesture/voice recognition so they exit their own loops
        # cleanly (releasing the webcam properly) instead of being
        # abruptly killed when the process ends.
        if self.gesture._running:
            self.gesture.stop()
        if self.voice._listening:
            self.voice.stop()

        if self.ev3.connected:
            self.ev3.disconnect()
        if isinstance(sys.stdout, _StdoutTee):
            sys.stdout = sys.stdout._real_stdout
        self.destroy()

    def connect_ev3(self):
        self.connect_button.configure(state="disabled")  # prevent double-clicks

        def _connect_wrapper():
            try:
                self.ev3.connect()
                self.after(0, lambda: (
                    self.status_label.configure(text="EV3 Status: Connected", text_color="#22c55e"),
                    self.connect_button.configure(text="Connected"),
                ))
            except Exception as e:
                print(f"Connection error: {e}")
                self.after(0, lambda: (
                    self.status_label.configure(text="EV3 Status: Failed to connect", text_color="#ef4444"),
                    self.connect_button.configure(state="normal"),  # re-enable so they can retry
                ))

        threading.Thread(target=_connect_wrapper, daemon=True).start()

    def disconnect_ev3(self):
        self.disconnect_button.configure(state="disabled")
        self.ev3.disconnect()
        self.status_label.configure(text="EV3 Status: Disconnected", text_color="#ef4444")
        self.connect_button.configure(text="Connect EV3", state="normal")
        self.disconnect_button.configure(state="normal")

    def play_selected_song(self, song_name):
        song_notes = get_song(song_name)
        if song_notes is None:
            print(f"Song not found: {song_name}")
            return

        if self.song_playing and getattr(self, "currently_playing_song", None) == song_name:
            print(f"'{song_name}' is already playing - ignoring duplicate request.")
            return

        # Stop whatever's currently playing (if anything), before starting the new one
        if self.current_stop_event is not None:
            self.current_stop_event.set()

        my_stop_event = threading.Event()
        self.current_stop_event = my_stop_event

        def _play_wrapper():
            self.song_playing = True
            self.currently_playing_song = song_name
            play_song(self.ev3, song_notes, stop_event=my_stop_event)
            # Only clear song_playing if THIS song is still the current one
            # (avoids a race where an old thread's cleanup wipes out the new song's state)
            if self.currently_playing_song == song_name:
                self.song_playing = False
                self.currently_playing_song = None

        threading.Thread(target=_play_wrapper, daemon=True).start()

    def play_instrument(self, instrument_name):
        """
        Central place instrument triggers go through, regardless of
        whether they came from a button click, gesture, or voice command -
        so all three input methods behave consistently.

        For GAMELAN units specifically (the demo instrument), plays each
        of its motors in sequence, lowest port to highest, instead of
        firing them all at once - shows every motor responding instead of
        one simultaneous clump. Every other instrument still just fires
        normally via send_command().

        Only GAMELAN participates in current_stop_event coordination here.
        Manually triggering a DIFFERENT single instrument (Gong, Saron,
        etc.) while GAMELAN's sequence is running does NOT stop it -
        they're allowed to coexist, same as any two instruments playing
        together normally. GAMELAN's sequence is only interrupted by:
        selecting a different song/program, the Stop button, or a fist
        gesture - things that mean "start a new performance," not a
        one-off manual test of another instrument.
        """
        if instrument_name in GAMELAN_INSTRUMENTS:
            if self.current_stop_event is not None:
                self.current_stop_event.set()

            my_stop_event = threading.Event()
            self.current_stop_event = my_stop_event

            threading.Thread(
                target=self._play_gamelan_sequence,
                args=(instrument_name, my_stop_event),
                daemon=True,
            ).start()
        else:
            self.ev3.send_command(instrument_name)

    def _play_gamelan_sequence(self, instrument_name, stop_event):
        num_keys = len(INSTRUMENTS.get(instrument_name, []))
        print(f"🎹 {instrument_name.title()}: playing low to high ({num_keys} notes)")
        for key in range(num_keys):
            if stop_event.is_set():
                print(f"🎹 {instrument_name.title()}: sequence stopped early")
                return
            self.ev3.send_command(instrument_name, key=key)
            time.sleep(GAMELAN_NOTE_DELAY)

    def play_downloaded_program(self, program_name):
        """
        Triggers an EV3 Classroom program that's already been downloaded
        to the brick(s) directly (not via this app) - see ev3_program_config.py
        for the mapping of program name -> {brick mac: remote .rbf path}.
        """
        brick_map = PROGRAMS.get(program_name, {})
        if not brick_map:
            print(f"No bricks configured for program '{program_name}' - "
                  "fill in ev3_program_config.py")
            return

        # Signal anything else currently playing (e.g. a GAMELAN sequence)
        # to stop, same coordination songs/instruments already use.
        if self.current_stop_event is not None:
            self.current_stop_event.set()

        # IMPORTANT: a downloaded program runs independently ON the brick
        # once started - it's not a Python-side loop, so current_stop_event
        # alone does nothing to it. stop_all_motors() is what actually
        # terminates a running on-brick program (see its docstring in
        # ev3.py) - without this, switching songs would try to start a
        # new program while the old one might still be running on the
        # same brick.
        if self.ev3.connected:
            self.ev3.stop_all_motors()

        threading.Thread(
            target=play_programs, args=(self.ev3, brick_map), daemon=True
        ).start()

    def create_widgets(self):
        # Main title
        title = ctk.CTkLabel(
            self,
            text="🎵 Traditional Music EV3 Controller",
            font=("Arial", 30)
        )
        title.pack(pady=20)

        main_row = ctk.CTkFrame(self, fg_color="transparent")
        main_row.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Activity Panel (left side) - shows every print() from anywhere
        # in the app (voice, gesture, songs, EV3 connection) in real time.
        self.create_activity_panel(main_row)

        self.content_frame = ctk.CTkScrollableFrame(main_row, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True)

        #Instrument status
        if SHOW_INSTRUMENT_SECTIONS:
            status_grid_frame = ctk.CTkFrame(self.content_frame)
            status_grid_frame.pack(padx=10, pady=12, fill="x")
            self.create_status_grid(status_grid_frame)

        # EV3 Section
        ev3_frame = ctk.CTkFrame(self.content_frame)
        ev3_frame.pack(padx=10, pady=12, fill="x")
        ev3_frame.grid_columnconfigure((0, 1), weight=1)

        self.status_label = ctk.CTkLabel(
            ev3_frame,
            text="EV3 Status: Disconnected", text_color="#ef4444",
            font=("Arial", 18)
        )
        self.status_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.connect_button = ctk.CTkButton(
            ev3_frame, text="Connect EV3", command=self.connect_ev3,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
        )
        self.connect_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.disconnect_button = ctk.CTkButton(
            ev3_frame, text="Disconnect EV3", command=self.disconnect_ev3,
            fg_color=COLOR_MUTED, hover_color=COLOR_MUTED_HOVER,
        )
        self.disconnect_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        battery_button = ctk.CTkButton(
            ev3_frame, text="Check Battery", command=self.check_battery,
            fg_color=COLOR_MUTED, hover_color=COLOR_MUTED_HOVER,
        )
        battery_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Song Section (Architecture 2 - legacy, hidden for the demo via
        # SHOW_LEGACY_ARCHITECTURE_2, but nothing here is deleted)
        if SHOW_LEGACY_ARCHITECTURE_2:
            song_frame = ctk.CTkFrame(self.content_frame)
            song_frame.pack(padx=10, pady=12, fill="x")

            song_title = ctk.CTkLabel(
                song_frame, text="🧪 Test Songs (Architecture 2 - not in use)", font=("Arial", 18)
            )
            song_title.pack(padx=10, pady=(10, 0))

            song_subtitle = ctk.CTkLabel(
                song_frame,
                text="Hand-built on-brick bytecode - being revisited later, not the current primary path",
                text_color="#888888",
                font=("Arial", 11),
            )
            song_subtitle.pack(padx=10, pady=(0, 10))

            song_buttons_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
            song_buttons_frame.pack(pady=10)

            for song_name in self.song_list:
                btn = ctk.CTkButton(
                    song_buttons_frame,
                    text=song_name,
                    command=lambda name=song_name: self.play_selected_song(name),
                    fg_color=COLOR_MUTED, hover_color=COLOR_MUTED_HOVER,
                    width=140,
                )
                btn.pack(side="left", padx=8)

            # Prominent Stop Song button
            self._legacy_stop_song_button = ctk.CTkButton(
                song_frame,
                text="⏹ Stop Song",
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=self.stop_song,
            )
            self._legacy_stop_song_button.pack(fill="x", padx=10, pady=(0, 10))

        # EV3 Classroom Programs Section (programs downloaded to the brick
        # directly, triggered by name - see ev3_program_config.py). This is
        # the current primary song-playing path (Architecture 3), so it's
        # labeled with the user-facing "Song Selection" name.
        program_frame = ctk.CTkFrame(self.content_frame)
        program_frame.pack(padx=10, pady=12, fill="x")

        program_title = ctk.CTkLabel(
            program_frame, text="🎼 Song Selection", font=("Arial", 18)
        )
        program_title.grid(row=0, column=0, columnspan=max(1, len(PROGRAMS)), padx=10, pady=10, sticky="ew")

        if PROGRAMS:
            program_frame.grid_columnconfigure(tuple(range(len(PROGRAMS))), weight=1)
            for i, program_name in enumerate(PROGRAMS):
                btn = ctk.CTkButton(
                    program_frame,
                    text=program_name,
                    command=lambda name=program_name: self.play_downloaded_program(name),
                    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                    font=("Arial", 14, "bold"),
                    height=42,
                )
                btn.grid(row=1, column=i, padx=10, pady=10, sticky="ew")
        else:
            empty_label = ctk.CTkLabel(
                program_frame,
                text="No programs configured yet - fill in ev3_program_config.py",
                text_color="#888888",
            )
            empty_label.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Prominent Stop button, right here since this is the section that
        # actually starts songs (the old Stop Song button was inside the
        # now-hidden legacy section, so nothing visible could stop a
        # currently-playing downloaded program before this).
        self.stop_song_button = ctk.CTkButton(
            program_frame,
            text="⏹ Stop",
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            font=("Arial", 14, "bold"),
            height=38,
            command=self.stop_song,
        )
        self.stop_song_button.grid(
            row=2, column=0, columnspan=max(1, len(PROGRAMS)), padx=10, pady=(0, 10), sticky="ew"
        )

        # Instrument Control Section
        if SHOW_INSTRUMENT_SECTIONS:
            instrument_frame = ctk.CTkFrame(self.content_frame)
            instrument_frame.pack(padx=10, pady=12, fill="x")

            instrument_title = ctk.CTkLabel(
                instrument_frame,
                text="🥁 Instrument Control (calibration/testing)",
                font=("Arial", 15),
                text_color="#a1a1aa",
            )
            instrument_title.pack(padx=10, pady=10)

            instrument_columns = 4
            instruments = self.all_instruments
            rows_needed = -(-len(instruments) // instrument_columns)  # ceil division

            for r in range(rows_needed):
                row_frame = ctk.CTkFrame(instrument_frame, fg_color="transparent")
                row_frame.pack(pady=4)
                chunk = instruments[r * instrument_columns:(r + 1) * instrument_columns]
                for instrument_name in chunk:
                    btn = ctk.CTkButton(
                        row_frame,
                        text=instrument_name.title(),
                        command=lambda name=instrument_name: self.play_instrument(name),
                        fg_color=COLOR_MUTED, hover_color=COLOR_MUTED_HOVER,
                        width=120, height=28,
                        font=("Arial", 12),
                    )
                    btn.pack(side="left", padx=6)

        # AI Section
        ai_frame = ctk.CTkFrame(self.content_frame)
        ai_frame.pack(padx=10, pady=12, fill="x")
        ai_frame.grid_columnconfigure((0, 1), weight=1)

        ai_title = ctk.CTkLabel(
            ai_frame, text="🤖 AI Mode", font=("Arial", 18)
        )
        ai_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.voice_button = ctk.CTkButton(
            ai_frame, text="Voice Recognition", command=self.toggle_voice,
            fg_color=COLOR_AI, hover_color=COLOR_AI_HOVER,
        )
        self.voice_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.gesture_button = ctk.CTkButton(
            ai_frame, text="Gesture Recognition", command=self.toggle_gesture,
            fg_color=COLOR_AI, hover_color=COLOR_AI_HOVER,
        )
        self.gesture_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

    def create_activity_panel(self, parent):
        """
        A live-updating log panel on the left side of the window, showing
        every print() from anywhere in the app (voice recognition, gesture
        detection, EV3 connection/health checks, song/program playback) as
        it happens - so a demo audience can see what's going on without
        needing the terminal visible.
        """
        panel = ctk.CTkFrame(parent, width=340)
        panel.pack(side="left", fill="y", padx=(0, 12))
        panel.pack_propagate(False)  # keep this width fixed regardless of content

        header_row = ctk.CTkFrame(panel, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(10, 5))

        panel_title = ctk.CTkLabel(
            header_row, text="📋 Activity Log", font=("Arial", 16, "bold")
        )
        panel_title.pack(side="left")

        clear_button = ctk.CTkButton(
            header_row, text="Clear", width=60, height=24,
            fg_color=COLOR_MUTED, hover_color=COLOR_MUTED_HOVER,
            font=("Arial", 11),
            command=self.clear_activity_log,
        )
        clear_button.pack(side="right")

        self.activity_textbox = ctk.CTkTextbox(
            panel, wrap="word", font=("Consolas", 11), activate_scrollbars=True
        )
        self.activity_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.activity_textbox.configure(state="disabled")  # read-only from the user's side

        # Color tags so different kinds of events are visually scannable
        # at a glance, matching the app's existing color roles.
        self.activity_textbox.tag_config("success", foreground=COLOR_SUCCESS)
        self.activity_textbox.tag_config("error", foreground=COLOR_DANGER)
        self.activity_textbox.tag_config("voice", foreground=COLOR_AI)
        self.activity_textbox.tag_config("gesture", foreground=COLOR_GESTURE)
        self.activity_textbox.tag_config("action", foreground=COLOR_ACCENT)
        self.activity_textbox.tag_config("info", foreground="#d4d4d8")
        self.activity_textbox.tag_config("muted", foreground=COLOR_LOG_MUTED)

    def clear_activity_log(self):
        self.activity_textbox.configure(state="normal")
        self.activity_textbox.delete("1.0", "end")
        self.activity_textbox.configure(state="disabled")

    def _friendly_instrument(self, mac):
        """Translate a raw MAC address into its instrument name(s), for display."""
        names = self._mac_to_instruments.get(mac)
        return " / ".join(sorted(names)) if names else mac

    def _format_log_line(self, raw_line):
        """
        Translates one raw print() line into (display_text, tag) for the
        Activity Panel - friendlier wording, instrument names instead of
        MAC addresses, and an icon/color per category. Returns None for
        lines that are pure internal noise not worth showing a demo
        audience (never suppresses errors/failures, only routine
        confirmations already reflected elsewhere, like the status grid).

        Anything that doesn't match a known pattern still gets shown
        (as-is, muted color) rather than silently dropped - so nothing
        useful is ever hidden, just de-prioritized visually.
        """
        line = raw_line.strip()
        if not line:
            return None

        m = re.match(r"^Brick (\S+): connected$", line)
        if m:
            return f"✅ {self._friendly_instrument(m.group(1))} connected", "success"

        m = re.match(r"^Brick (\S+): FAILED to connect - (.+)$", line)
        if m:
            return f"❌ {self._friendly_instrument(m.group(1))} failed to connect", "error"

        if re.match(r"^Brick (\S+): worker thread started$", line):
            return None  # internal detail, not demo-relevant

        if line == "EV3 connection phase complete (see above for per-instrument status).":
            return "🎉 Ready to play!", "success"

        if line == "Connecting to EV3 bricks...":
            return "🔌 Connecting to all instruments...", "info"

        if line == "Disconnecting all EV3 bricks...":
            return "🔌 Disconnecting...", "info"

        if re.match(r"^Brick (\S+): disconnected$", line):
            return None  # confirmed individually, summary is enough

        m = re.match(r"^(.+): NOT fully ready \(.+\)$", line)
        if m:
            return f"⚠️ {m.group(1)} not fully connected", "error"

        if re.match(r"^.+: ready \(.+\)$", line) or re.match(r"^.+ \w+: ready$", line):
            return None  # already reflected in the status grid, redundant here

        if re.match(r"^.+ \w+: pending configuration$", line):
            return None  # expected/normal during partial setup

        m = re.match(r"^(.+) (\w+): unavailable \(brick not connected\)$", line)
        if m:
            return f"⚠️ {m.group(1)} ({m.group(2)}) unavailable", "error"

        m = re.match(r"^(.+) (\w+): FAILED to set up - (.+)$", line)
        if m:
            return f"❌ {m.group(1)} ({m.group(2)}) setup failed", "error"

        m = re.match(r"^Sent command: (\S+?)(?:\[\d+\])? \(\d+ motor\(s\)\)", line)
        if m:
            return f"🥁 {m.group(1).title()} played", "action"

        m = re.match(r"^Sent manual strike: (\S+) \(\d+ pair\(s\)\)$", line)
        if m:
            return f"🎶 {m.group(1).title()} played", "action"

        m = re.match(r"^Cannot send '(.+)': not connected$", line)
        if m:
            return f"⚠️ Can't play {m.group(1).title()} - not connected", "error"

        m = re.match(r"^Cannot send '(.+)': (.+)$", line)
        if m:
            return f"⚠️ {m.group(1).title()}: {m.group(2)}", "error"

        if re.match(r"^Voice recognition started", line):
            return "🎤 Voice recognition ON", "voice"
        if line == "Voice recognition stopped.":
            return "🎤 Voice recognition OFF", "voice"

        m = re.match(r"^Heard: (.+)$", line)
        if m:
            return f'🎤 Heard: "{m.group(1)}"', "voice"

        if re.match(r"^Command detected:", line):
            return None  # the "Matched" line right after covers this

        if line == "Wake word detected, but no command followed.":
            return "🎤 Heard wake word, no command followed", "voice"

        m = re.match(r"^Matched '.+' -> '(.+)'$", line)
        if m:
            return f"🎤 Voice: Playing {m.group(1)}", "voice"

        m = re.match(r"^Could not match voice command to anything known: '(.+)'$", line)
        if m:
            return f'🎤 Didn\'t understand: "{m.group(1)}"', "error"

        m = re.match(r"^Right hand \d+ finger\(s\) -> (.+)$", line)
        if m:
            return f"✋ Gesture: Playing {m.group(1)}", "gesture"

        m = re.match(r"^Left hand \d+ finger\(s\) -> (.+)$", line)
        if m:
            return f"✋ Gesture: Playing {m.group(1)}", "gesture"

        if re.match(r"^No (song|program) mapped to \d+ finger", line):
            return None  # idle/no-op gesture, not worth showing

        if re.match(r"^Starting \d+ EV3 program\(s\)", line):
            return None  # redundant, per-brick "started" lines follow

        m = re.match(r"^Brick (\S+): program started \((.+)\)$", line)
        if m:
            return f"▶️ {self._friendly_instrument(m.group(1))} started", "action"

        m = re.match(r"^Brick (\S+): FAILED to start program \((.+)\) - (.+)$", line)
        if m:
            return f"❌ {self._friendly_instrument(m.group(1))} failed to start", "error"

        if line == "Stop requested.":
            return "⏹ Stopped", "action"

        m = re.match(r"^Battery (\S+): (.+)$", line)
        if m:
            return f"🔋 {self._friendly_instrument(m.group(1))}: {m.group(2)}", "info"

        if line == "Not connected - can't check battery":
            return "⚠️ Connect first to check battery", "error"

        # Fallback: show unrecognized lines as-is rather than hide them,
        # just visually quiet so they don't compete with the friendly ones.
        return line, "muted"

    def _drain_log_queue(self):
        """
        Runs on the main GUI thread via self.after() - pulls any new lines
        pushed by _StdoutTee (from print() calls on ANY thread), translates
        them into friendly text via _format_log_line, and appends them to
        the panel with a timestamp and color tag. Polling like this
        (instead of writing directly from whichever background thread
        called print) keeps all Tkinter widget updates safely on the main
        thread.
        """
        drained_any = False
        try:
            while True:
                raw_line = self._log_queue.get_nowait()
                for line in raw_line.splitlines():
                    formatted = self._format_log_line(line)
                    if formatted is None:
                        continue
                    text, tag = formatted
                    timestamp = time.strftime("%H:%M:%S")
                    self.activity_textbox.configure(state="normal")
                    self.activity_textbox.insert("end", f"[{timestamp}] ", "muted")
                    self.activity_textbox.insert("end", text + "\n", tag)
                    drained_any = True
        except queue.Empty:
            pass

        if drained_any:
            self.activity_textbox.configure(state="disabled")
            self.activity_textbox.see("end")  # auto-scroll to the newest line

        self.after(150, self._drain_log_queue)

    def create_status_grid(self, parent_frame):
        self.instrument_status_labels = {}

        columns = 4  # wrap after this many, so it scales cleanly past 4 instruments
        parent_frame.grid_columnconfigure(tuple(range(columns)), weight=1)

        for i, instrument in enumerate(self.all_instruments):
            row, col = divmod(i, columns)
            label = ctk.CTkLabel(
                parent_frame,
                text=f"{instrument}: Unknown",
                text_color="#888888",
                font=("Arial", 13),
                anchor="center"
            )
            label.grid(row=row, column=col, padx=8, pady=8, sticky="ew")
            self.instrument_status_labels[instrument] = label

    def refresh_instrument_status(self):
        for instrument, label in self.instrument_status_labels.items():
            if self.ev3.connected and self.ev3.is_instrument_connected(instrument):
                label.configure(text=f"{instrument}: Connected", text_color="#22c55e")
            else:
                label.configure(text=f"{instrument}: Disconnected", text_color="#ef4444")

        self.after(2000, self.refresh_instrument_status)

    def check_battery(self):
        if not self.ev3.connected:
            print("Not connected - can't check battery")
            return

        threading.Thread(target=self._check_battery_worker, daemon=True).start()

    def _check_battery_worker(self):
        levels = self.ev3.get_battery_levels()
        for mac, percentage in levels.items():
            text = f"{percentage}%" if percentage is not None else "Unknown"
            print(f"Battery {mac}: {text}")

    def background_health_check(self):
        if self.ev3.connected and not self.song_playing and not self._health_check_running:
            self._health_check_running = True
            threading.Thread(target=self._health_check_worker, daemon=True).start()

        self.after(15000, self.background_health_check)  # checks every 15 seconds

    def _health_check_worker(self):
        self.ev3.health_check()
        self._health_check_running = False

    def handle_voice_command(self, command):
        voice_actions = {
            "connect": self.connect_ev3,
            "disconnect": self.disconnect_ev3,
            "battery": self.check_battery,
            "check battery": self.check_battery,
            "stop listening": self.stop_voice_command,
            "stop voice": self.stop_voice_command,
            "stop": self.stop_song,
            "stop song": self.stop_song,
            "stop music": self.stop_song,
            "stop playing": self.stop_song,
            "stop all": self.stop_song,
            "pause": self.stop_song,
            "start gesture": self.start_gesture_command,
            "stop gesture": self.stop_gesture_command,
            "exit": self.voice_shutdown,
            "quit": self.voice_shutdown,
            "shut down": self.voice_shutdown,
            "shutdown": self.voice_shutdown,
            "close program": self.voice_shutdown,
            "end program": self.voice_shutdown,
        }

        # Strip common filler words that don't help matching and can throw off scoring
        filler_words = {"play", "the", "a", "please", "to"}
        cleaned = " ".join(w for w in command.split() if w.lower() not in filler_words)
        if not cleaned:
            cleaned = command

        known_targets = self.all_instruments + list(PROGRAMS.keys()) + list(voice_actions.keys())
        lower_to_real = {t.lower(): t for t in known_targets}
        lower_targets = list(lower_to_real.keys())

        matches = difflib.get_close_matches(cleaned.lower(), lower_targets, n=1, cutoff=0.4)

        if not matches:
            for word in cleaned.split():
                word_matches = difflib.get_close_matches(word.lower(), lower_targets, n=1, cutoff=0.6)
                if word_matches:
                    matches = word_matches
                    break

        if not matches:
            print(f"Could not match voice command to anything known: '{command}'")
            return

        target = lower_to_real[matches[0]]
        print(f"Matched '{command}' -> '{target}'")

        if target.lower() in voice_actions:
            voice_actions[target.lower()]()
        elif target in self.all_instruments:
            self.play_instrument(target)
        else:
            self.play_downloaded_program(target)

    def toggle_voice(self):
        if self.voice._listening:
            self.voice.stop()
            self.voice_button.configure(text="Voice Recognition", fg_color=COLOR_AI)
        else:
            self.voice.start()
            self.voice_button.configure(text="Stop Voice Recognition", fg_color="#ef4444")

    def stop_voice_command(self):
        self.voice.stop()
        # Schedule the button update on the main thread, since this runs
        # from voice recognition's background thread, not the GUI thread
        self.after(0, lambda: self.voice_button.configure(
            text="Voice Recognition", fg_color=COLOR_AI
        ))

    def voice_shutdown(self):
        """
        Safely closes the whole program by voice - reuses the exact same
        on_close() the window's X button already calls (disconnects EV3,
        restores stdout, destroys the window), just scheduled onto the
        main GUI thread via self.after(0, ...) since this runs from
        voice recognition's background thread, and self.destroy() isn't
        safe to call directly from a non-main thread.
        """
        print("👋 Shutting down...")
        self.after(0, self.on_close)

    def start_gesture_command(self):
        if not self.gesture._running:
            self.gesture.start()
            self.after(0, lambda: self.gesture_button.configure(
                text="Stop Gesture Recognition", fg_color="#ef4444"
            ))

    def stop_gesture_command(self):
        if self.gesture._running:
            self.gesture.stop()
            self.after(0, lambda: self.gesture_button.configure(
                text="Gesture Recognition", fg_color=COLOR_AI
            ))

    def handle_instrument_gesture(self, count):
        index = count - 1
        if 0 <= index < len(self.all_instruments):
            instrument = self.all_instruments[index]
            self.play_instrument(instrument)
            print(f"Right hand {count} finger(s) -> {instrument}")
        elif not self.all_instruments:
            print("✋ No instruments configured right now")

    def handle_song_gesture(self, count):
        program_names = list(PROGRAMS.keys())
        index = count - 1
        if 0 <= index < len(program_names):
            program_name = program_names[index]
            print(f"Left hand {count} finger(s) -> {program_name}")
            self.play_downloaded_program(program_name)
        else:
            print(f"No program mapped to {count} finger(s) (only {len(program_names)} program(s) available)")

    def toggle_gesture(self):
        if self.gesture._running:
            self.gesture.stop()
            self.gesture_button.configure(text="Gesture Recognition", fg_color=COLOR_AI)
        else:
            self.gesture.start()
            self.gesture_button.configure(text="Stop Gesture Recognition", fg_color="#ef4444")

    def _sync_gesture_button(self):
        """
        Runs periodically on the main GUI thread. The gesture loop can end
        on its own (pressing 'q', or closing the webcam window) without
        going through toggle_gesture()/stop_gesture_command() - when that
        happens, self.gesture._running becomes False internally, but the
        button was never told to update. This polls and corrects that
        mismatch, so the button always reflects what's actually running.
        """
        actually_running = self.gesture._running
        button_says_running = self.gesture_button.cget("text") == "Stop Gesture Recognition"

        if button_says_running and not actually_running:
            self.gesture_button.configure(text="Gesture Recognition", fg_color=COLOR_AI)
            print("Gesture recognition window closed - button synced")

        self.after(500, self._sync_gesture_button)

    def stop_song(self):
        if self.current_stop_event is not None:
            self.current_stop_event.set()
        if self.ev3.connected:
            self.ev3.stop_all_motors()
        print("Stop requested.")