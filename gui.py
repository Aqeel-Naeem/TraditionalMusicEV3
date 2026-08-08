import customtkinter as ctk
from ev3 import EV3
import threading
import difflib
from ai.voice import VoiceController
from ai.gesture import GestureController
from songs import get_song, play_song, list_songs
from config import INSTRUMENTS

class EV3App(ctk.CTk):

    SONG_LIST = ["Rasa Sayang", "Test Motors"]  # extend as you add more songs

    def __init__(self):
        super().__init__()

        self.ev3 = EV3()
        self.title("Traditional Music EV3 Controller")
        self.geometry("900x800")

        self.stop_event = threading.Event()
        self.song_list = list_songs()
        self.current_song_index = 0
        self._health_check_running = False
        self.song_playing = False

        self.voice = VoiceController(on_command=self.handle_voice_command)
        self.gesture = GestureController(
            on_finger_count=self.handle_finger_count,
            on_stop=self.stop_song,
            on_next=self.next_song,
            on_previous=self.previous_song,
        )

        self.create_widgets()  # <- this must come AFTER self.voice/self.gesture are created
        self.refresh_instrument_status()
        self.background_health_check()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        if self.ev3.connected:
            self.ev3.disconnect()
        self.destroy()

    def connect_ev3(self):
        self.connect_button.configure(state="disabled")  # prevent double-clicks
        try:
            self.ev3.connect()
            self.status_label.configure(text="EV3 Status: Connected", text_color="#22c55e")
            self.connect_button.configure(text="Connected")
        except Exception as e:
            self.status_label.configure(text="EV3 Status: Failed to connect", text_color="#ef4444")
            self.connect_button.configure(state="normal")  # re-enable so they can retry
            print(f"Connection error: {e}")

    def disconnect_ev3(self):
        self.disconnect_button.configure(state="disabled")
        self.ev3.disconnect()
        self.status_label.configure(text="EV3 Status: Disconnected", text_color="#ef4444")
        self.connect_button.configure(text="Connect EV3", state="normal")
        self.disconnect_button.configure(state="normal")

    def play_gong(self):
        self.ev3.send_command("GONG")

    def play_saron(self):
        self.ev3.send_command("SARON")

    def play_drum(self):
        self.ev3.send_command("DRUM")

    def play_selected_song(self, song_name):
        song_notes = get_song(song_name)
        if song_notes is None:
            print(f"Song not found: {song_name}")
            return

        self.stop_event.clear()  # reset in case a previous song was stopped

        def _play_wrapper():
            self.song_playing = True
            play_song(self.ev3, song_notes, stop_event=self.stop_event)
            self.song_playing = False

        threading.Thread(target=_play_wrapper, daemon=True).start()

    def create_widgets(self):
        # Main title
        title = ctk.CTkLabel(
            self,
            text="🎵 Traditional Music EV3 Controller",
            font=("Arial", 30)
        )
        title.pack(pady=20)

        #Instrument status
        status_grid_frame = ctk.CTkFrame(self)
        status_grid_frame.pack(padx=20, pady=10, fill="x")
        self.create_status_grid(status_grid_frame)

        # EV3 Section
        ev3_frame = ctk.CTkFrame(self)
        ev3_frame.pack(padx=20, pady=10, fill="x")

        self.status_label = ctk.CTkLabel(
            ev3_frame,
            text="EV3 Status: Disconnected", text_color="#ef4444",
            font=("Arial", 18)
        )
        self.status_label.pack(pady=10)

        self.connect_button = ctk.CTkButton(
            ev3_frame,
            text="Connect EV3",
            command=self.connect_ev3
        )
        self.connect_button.pack(pady=10)

        self.disconnect_button = ctk.CTkButton(
            ev3_frame,
            text="Disconnect EV3",
            command=self.disconnect_ev3
        )
        self.disconnect_button.pack(pady=10)

        battery_button = ctk.CTkButton(
            ev3_frame, text="Check Battery", command=self.check_battery
        )
        battery_button.pack(pady=10)

        # Song Section
        song_frame = ctk.CTkFrame(self)
        song_frame.pack(padx=20, pady=10, fill="x")

        song_title = ctk.CTkLabel(
            song_frame,
            text="🎼 Song Selection",
            font=("Arial", 18)
        )
        song_title.pack(pady=10)

        song_button = ctk.CTkButton(
            song_frame,
            text="Rasa Sayang",
            command=lambda: self.play_selected_song("Rasa Sayang")
        )
        song_button.pack(pady=10)

        song_button = ctk.CTkButton(
            song_frame,
            text="Test Motors",
            command=lambda: self.play_selected_song("Test Motors")
        )
        song_button.pack(pady=10)

        # Instrument Control Section
        instrument_frame = ctk.CTkFrame(self)
        instrument_frame.pack(padx=20, pady=10, fill="x")
        instrument_frame.grid_columnconfigure((0, 1, 2), weight=1)

        instrument_title = ctk.CTkLabel(
            instrument_frame,
            text="🥁 Instrument Control",
            font=("Arial", 18)
        )
        instrument_title.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=3)

        gong_button = ctk.CTkButton(instrument_frame, text="Gong", command=self.play_gong)
        gong_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        saron_button = ctk.CTkButton(instrument_frame, text="Saron", command=self.play_saron)
        saron_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        drum_button = ctk.CTkButton(instrument_frame, text="Drum", command=self.play_drum)
        drum_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

        # AI Section
        ai_frame = ctk.CTkFrame(self)
        ai_frame.pack(padx=20, pady=10, fill="x")

        ai_title = ctk.CTkLabel(
            ai_frame, text="🤖 AI Mode", font=("Arial", 18)
        )
        ai_title.pack(pady=10)

        voice_button = ctk.CTkButton(
            ai_frame, text="Voice Recognition", command=self.voice.start
        )
        voice_button.pack(pady=10)

        gesture_button = ctk.CTkButton(
            ai_frame, text="Gesture Recognition", command=self.gesture.start
        )
        gesture_button.pack(pady=10)

    def create_status_grid(self, parent_frame):
        self.instrument_status_labels = {}

        parent_frame.grid_columnconfigure(tuple(range(len(INSTRUMENTS))), weight=1)

        for i, instrument in enumerate(INSTRUMENTS.keys()):
            label = ctk.CTkLabel(
                parent_frame,
                text=f"{instrument}: Unknown",
                text_color="#888888",
                anchor="center"
            )
            label.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
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

        self.after(5000, self.background_health_check)  # checks every 5 seconds

    def _health_check_worker(self):
        self.ev3.health_check()
        self._health_check_running = False

    def handle_voice_command(self, command):
        # Build a list of everything the command could mean: instrument names + song names
        known_targets = list(INSTRUMENTS.keys()) + self.song_list  # e.g. ["GONG", "SARON", "DRUM", "Rasa Sayang", "Test Motors"]

        matches = difflib.get_close_matches(command, known_targets, n=1, cutoff=0.3)

        if not matches:
            # Try matching word-by-word too, in case the whole phrase doesn't match well
            # but one word in it does (e.g. "play roses i am" -> "am" alone won't help,
            # but this catches simpler cases like "gong" hidden inside a longer phrase)
            for word in command.split():
                word_matches = difflib.get_close_matches(word, known_targets, n=1, cutoff=0.5)
                if word_matches:
                    matches = word_matches
                    break

        if not matches:
            print(f"Could not match voice command to anything known: '{command}'")
            return

        target = matches[0]
        print(f"Matched '{command}' -> '{target}'")

        if target in INSTRUMENTS:
            self.ev3.send_command(target)
        else:
            self.play_selected_song(target)

    def handle_finger_count(self, count):
        mapping = {1: "GONG", 2: "SARON", 3: "DRUM"}
        if count in mapping:
            self.ev3.send_command(mapping[count])

    def stop_song(self):
        self.stop_event.set()
        print("Stop requested.")

    def next_song(self):
        self.current_song_index = (self.current_song_index + 1) % len(self.song_list)
        name = self.song_list[self.current_song_index]
        print(f"Next song: {name}")
        self.play_selected_song(name)

    def previous_song(self):
        self.current_song_index = (self.current_song_index - 1) % len(self.song_list)
        name = self.song_list[self.current_song_index]
        print(f"Previous song: {name}")
        self.play_selected_song(name)