import speech_recognition as sr

MIC_INDEX = 1  # Microphone Array (Intel Smart Sound) - your laptop's built-in mic

recognizer = sr.Recognizer()
microphone = sr.Microphone(device_index=MIC_INDEX)

with microphone as source:
    print("Adjusting for ambient noise...")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("Listening...")
    audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)

print("Recognizing...")
try:
    text = recognizer.recognize_google(audio)
    print(f"You said: {text}")
except sr.UnknownValueError:
    print("Could not understand audio")
except sr.RequestError as e:
    print(f"Could not reach speech recognition service: {e}")