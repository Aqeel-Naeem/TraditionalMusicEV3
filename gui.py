import customtkinter as ctk
from ev3 import EV3
import threading
from songs import get_song, play_song

class EV3App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.ev3 = EV3()
        self.title("Traditional Music EV3 Controller")
        self.geometry("900x600")

        self.create_widgets()

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
        self.ev3.disconnect()
        self.status_label.configure(text="EV3 Status: Disconnected", text_color="#ef4444")
        self.connect_button.configure(text="Connect EV3", state="normal")

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

        threading.Thread(
            target=play_song,
            args=(self.ev3, song_notes),
            daemon=True
        ).start()

    def create_widgets(self):
        # Main title
        title = ctk.CTkLabel(
            self,
            text="🎵 Traditional Music EV3 Controller",
            font=("Arial", 30)
        )
        title.pack(pady=20)

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
            ai_frame, text="Voice Recognition"
        )
        voice_button.pack(pady=10)