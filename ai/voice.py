import threading
import difflib
import speech_recognition as sr

WAKE_WORD = "hey ev3"
WAKE_TRIGGER = "ev3"  # the key word we fuzzy-match for, within the wake phrase
MIC_INDEX = 1  # confirmed working device: "Microphone Array (Intel Smart Sound)"
SPEECH_LANGUAGE = "en-MY"  # Malaysian English - helps accuracy for a Malaysian accent


class VoiceController:
    """
    Listens continuously in the background for a wake word ("Hey EV3"),
    then captures the next phrase as a command and passes it to a
    callback function (e.g. to trigger EV3 instrument/song commands).

    Wake word matching is fuzzy (not exact), since accented speech often
    gets transcribed as a similar-sounding word rather than the exact
    word said.
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
        print("Voice recognition started. Say 'Hey EV3' followed by a command.")

    def stop(self):
        self._listening = False
        print("Voice recognition stopped.")

    def _find_wake_word(self, text):
        """
        Returns the position (word index) right after the wake trigger
        word if a close match is found in the heard text, otherwise None.
        Uses fuzzy matching so accented mishearings (e.g. "robert" for
        "robot") still count.
        """
        words = text.split()
        for i, word in enumerate(words):
            similarity = difflib.SequenceMatcher(None, word, WAKE_TRIGGER).ratio()
            if similarity >= 0.6:  # lenient threshold - tune if needed
                return i
        return None

    def _listen_loop(self):
        while self._listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=4)

                text = self.recognizer.recognize_google(audio, language=SPEECH_LANGUAGE).lower()
                print(f"Heard: {text}")

                wake_index = self._find_wake_word(text)

                if wake_index is not None:
                    remaining_words = text.split()[wake_index + 1:]
                    command = " ".join(remaining_words).strip()
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