import threading
import speech_recognition as sr

WAKE_WORD = "hey robot"
MIC_INDEX = 1  # confirmed working device: "Microphone Array (Intel Smart Sound)"


class VoiceController:
    """
    Listens continuously in the background for a wake word ("Hey Robot"),
    then captures the next phrase as a command and passes it to a
    callback function (e.g. to trigger EV3 instrument/song commands).
    """

    def __init__(self, on_command):
        """
        on_command: function that takes a single string argument,
        e.g. "gong", "saron", "drum", "rasa sayang"
        """
        self.on_command = on_command
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(device_index=MIC_INDEX)
        self._listening = False
        self._thread = None

        # Reduce sensitivity to background noise once at startup
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def start(self):
        if self._listening:
            return
        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("Voice recognition started. Say 'Hey Robot' followed by a command.")

    def stop(self):
        self._listening = False
        print("Voice recognition stopped.")

    def _listen_loop(self):
        while self._listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=4)

                text = self.recognizer.recognize_google(audio).lower()
                print(f"Heard: {text}")

                if WAKE_WORD in text:
                    command = text.replace(WAKE_WORD, "").strip()
                    if command:
                        print(f"Command detected: {command}")
                        self.on_command(command)
                    else:
                        print("Wake word detected, but no command followed.")

            except sr.WaitTimeoutError:
                continue  # no speech detected in the timeout window, keep listening
            except sr.UnknownValueError:
                continue  # speech was unintelligible, keep listening
            except sr.RequestError as e:
                print(f"Speech recognition service error: {e}")
                break