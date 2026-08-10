# Code Documentation

This document explains how the code works, file by file, using simple
language. If you want setup/installation instructions instead, see
`README.md`.

---

## Table of Contents

0. [Glossary](#0-glossary-words-used-in-this-document)
1. [Project overview](#1-project-overview)
2. [File structure](#2-file-structure)
3. [`config.py` - which motor plays which instrument](#3-configpy---which-motor-plays-which-instrument)
4. [`ev3.py` - the `EV3` class](#4-ev3py---the-ev3-class-talks-to-the-bricks)
5. [`songs.py` - song data and playback](#5-songspy---song-data-and-playback-scheduling)
6. [`gui.py` - the window and buttons](#6-guipy---the-window-and-buttons)
7. [Why some choices were made](#7-why-some-choices-were-made-background-context)
8. [Detecting a brick that silently disconnects](#8-detecting-a-brick-that-silently-disconnects)
9. [Why port verification was not added](#9-why-port-verification-checking-whats-actually-plugged-into-each-port-was-not-added)
10. [`ai/voice.py` - voice recognition](#10-aivoicepy---voice-recognition)
11. [`ai/gesture.py` - gesture recognition](#11-aigesturepy---gesture-recognition)
12. [Switching songs safely (stopping the previous one)](#12-switching-songs-safely-stopping-the-previous-one)
13. [Known limitations](#13-known-limitations-things-not-fully-finished-yet)
14. [Changing voice commands, the wake word, and gesture settings](#14-changing-voice-commands-the-wake-word-and-gesture-settings)
15. [Turning voice and gesture recognition on/off](#15-turning-voice-and-gesture-recognition-onoff)
16. [Layout structure (`gui.py`)](#16-layout-structure-guipy)

---

## 0. Glossary (words used in this document)

- **Function / Method** - a named block of code that does one specific
  job. You "call" it (run it) by writing its name followed by `()`.
  A "method" is just a function that belongs to a class.
- **Class** - a blueprint for creating an object that holds both data and
  the functions that work on that data. In this project, `EV3` is a class
  that represents "one connection manager that knows how to talk to your
  bricks."
- **Object / Instance** - an actual thing created from a class. If `EV3`
  is the blueprint, `self.ev3 = EV3()` creates one real object from it.
- **Dictionary (`dict`)** - a way to store data as `key: value` pairs, like
  a real dictionary where you look up a word (`key`) to find its meaning
  (`value`). Example: `{"GONG": "loud", "SARON": "metallic"}`.
- **List** - an ordered collection of items, written with square brackets,
  e.g. `["GONG", "SARON", "DRUM"]`.
- **Thread** - a way to run a piece of code "in the background," at the
  same time as the rest of your program, instead of making everything
  wait for it to finish first.
- **MAC address** - a unique ID number every Bluetooth device has, used to
  identify exactly which physical device you want to connect to.
- **Bluetooth port** - on the EV3 brick, this refers to one of the 4
  physical sockets (A, B, C, D) that a motor can be plugged into.
- **Instance variable (`self.something`)** - a piece of data that belongs
  to one specific object, and can be used by any method inside that
  object's class.
- **Fuzzy matching** - comparing two pieces of text to see how *similar*
  they are, instead of requiring them to match exactly. Used in this
  project so voice commands still work even when speech recognition
  mishears a word slightly.

---

## 1. Project overview

The app works like a "brain and musician" system:

```
User (clicks a button, speaks, or shows a gesture)
            |
        gui.py  (the window you see and interact with)
            |
        ev3.py  (decides which brick/motor to talk to)
            |
      Bluetooth (the wireless connection)
            |
    One or more EV3 bricks
            |
        Motors -> hit the real instruments
```

Your **Python app is the "brain"** - it decides what to play and when. Each
**EV3 brick is the "musician"** - it just receives a simple instruction
("move now") and does it. The EV3 bricks never need any special software
installed on them - they use LEGO's normal, original software.

---

## 2. File structure

```
TraditionalMusicEV3/
├── main.py       - starts the app
├── gui.py        - the window/buttons you see and click
├── ev3.py        - handles talking to the EV3 bricks over Bluetooth
├── config.py     - a list of which motor plays which instrument
├── songs.py      - the songs themselves (which notes play, and when)
├── ai/
│   ├── voice.py   - listens for voice commands
│   └── gesture.py - watches your webcam for hand gestures
└── requirements.txt
```

---

## 3. `config.py` - which motor plays which instrument

This file is just a list (a dictionary) that says: "this instrument uses
these motors, on these bricks." It's kept separate from the rest of the
code on purpose - so if you change your hardware setup, you only ever need
to edit this one file, not touch any actual logic/code.

```python
INSTRUMENTS = {
    "GONG": [
        {"mac": "00:16:53:46:be:aa", "port": "A"},
    ],
    "SARON": [
        {"mac": "00:16:53:41:95:2e", "port": "A"},
        {"mac": "00:16:53:41:95:2e", "port": "C"},
    ],
}
```

- Each **name in quotes** (`"GONG"`, `"SARON"`) is what you'll call that
  instrument everywhere else in the project (buttons, songs, voice
  commands, gesture selection, etc.).
- Each instrument points to a **list** of motors - usually just one, but
  it can be more than one if a big instrument needs several motors.
- `"mac"` = which physical brick (its unique ID number).
- `"port"` = which of that brick's 4 sockets (A/B/C/D) the motor is
  plugged into.

### How to add a new EV3 brick / instrument

1. Physically connect the motor to a port on the brick.
2. Pair that brick with your computer over Bluetooth (see `README.md`
   Step 8 if you haven't done this yet).
3. Find the brick's MAC address (`README.md` Step 9).
4. Open `config.py` in VS Code.
5. Add a new line following the same pattern, for example:
   ```python
   "KENONG": [
       {"mac": "00:16:53:XX:XX:XX", "port": "A"},
   ],
   ```
6. Save the file (**Ctrl + S**).
7. That's it - no other file needs to change. The new instrument will
   automatically show up in the status grid, become selectable by voice
   ("play kenong"), become selectable by gesture (right hand finger
   count), and you can add a manual button for it in `gui.py` if you want
   (see Section 6 below).

### How to remove an EV3 brick / instrument

1. Open `config.py`.
2. Delete that instrument's entire block (from its name to its closing
   `],`).
3. Save the file.
4. **Important:** if any song in `songs.py` still uses that instrument's
   name, remove those notes too, or the song will try to use an
   instrument that no longer exists and print an error instead of playing.
5. If there's a button for it in `gui.py`, you can remove that button too
   (optional - it just won't do anything useful if left in).

### How to give one instrument multiple motors

Just add more lines inside that instrument's list:
```python
"SARON": [
    {"mac": "00:16:53:41:95:2e", "port": "A"},
    {"mac": "00:16:53:41:95:2e", "port": "C"},  # 2nd motor, same brick
],
```
Motors can be on the same brick (different ports) or on completely
different bricks - both work the same way.

---

## 4. `ev3.py` - the `EV3` class (talks to the bricks)

This file contains one class, `EV3`, which manages every Bluetooth
connection and knows how to send movement commands. The rest of the app
never talks to Bluetooth directly - it always goes through this class, so
if the underlying connection method ever changes, only this one file needs
updating.

### Why one connection per brick, not per instrument?

Early on, this code tried to open a new connection for every instrument.
That broke when two instruments shared the same physical brick (just
different ports), because it tried to connect to the same brick twice at
once, which isn't allowed. The fix: `connect()` first works out the list
of *unique* bricks used across `config.py`, connects to each one exactly
once, then creates the individual motor objects afterward, all pointing
back to that one shared connection.

### Why does one brick failing not break everything?

Each brick connects inside its own "try this, and if it fails, just note
that down and keep going" block (called `try/except` in Python). This
means if 1 out of 5 bricks isn't working, the other 4 still connect fine
and the app keeps running.

### Why do commands run in background threads?

If one instrument has 2 motors, or if a song wants 2 different instruments
to play at the exact same instant, sending those commands one-after-
another (instead of at the same time) would create a tiny, noticeable
delay between them, since each Bluetooth message takes a small amount of
time to travel. Running them in separate threads lets them fire at
basically the same moment instead.

### Key methods (functions) in this file

| Method | What it does, in plain terms |
|---|---|
| `connect()` | Connects to every brick listed in `config.py`, one time each, then sets up each instrument's motor(s). |
| `disconnect()` | Disconnects everything, and waits a couple of seconds afterward (EV3 bricks need a short pause before they'll accept a new connection). |
| `send_command(command, key=None, ...)` | Tells an instrument to play. `key=None` moves all of that instrument's motors together; `key=0`, `key=1`, etc. moves just one specific motor. |
| `is_instrument_connected(instrument)` | Answers yes/no: is this specific instrument currently working? Used to color the status grid green/red. |
| `get_battery_levels()` | Checks the battery percentage of every connected brick. |
| `health_check()` | Actively checks every brick that's supposed to be connected, even if nothing has tried to use it recently. Catches a brick that quietly stopped working while sitting idle. See Section 8 for details. |

---

## 5. `songs.py` - song data and playback scheduling

### How one note is written

```python
{"instrument": "SARON", "key": 0, "beat": 0.5, "duration": 0.25, "speed": 50}
```

- `"instrument"` - which instrument plays (must match a name from
  `config.py`).
- `"key"` - which specific motor to use, if that instrument has more than
  one (0 = the first motor listed for it, 1 = the second, and so on).
  Use `None` if you want *all* of that instrument's motors to move
  together.
- `"beat"` - **when** this note plays, measured in seconds *from the very
  start of the song* (not from the note before it).
- `"duration"` - how many seconds the motor should move for.
- `"speed"` - *(optional)* how fast/forcefully the motor moves, from 0 to
  100. If left out, it defaults to 50. Use a higher number for a
  stronger/faster hit (e.g. a big gong strike), and a lower number for a
  gentler one. This is separate from `"duration"` - duration is *how
  long* the motor moves, speed is *how fast* it moves while doing so.

### How to add a new song

1. Open `songs.py`.
2. Inside the `SONGS` dictionary, add a new entry with your song's name
   and its own list of notes:
   ```python
   SONGS = {
       "Rasa Sayang": [
           ...
       ],
       "Your New Song Name": [
           {"instrument": "GONG", "key": None, "beat": 0.0, "duration": 0.5},
           {"instrument": "DRUM", "key": None, "beat": 0.5, "duration": 0.3},
       ],
   }
   ```
3. Save the file.
4. That's it - the new song automatically becomes selectable by voice
   ("play your new song name"), by gesture (left hand finger count), and
   you can add a manual button for it in `gui.py` too if you want.

### How to remove a song

1. Open `songs.py`.
2. Delete that song's entire entry (from its name to its closing `],`).
3. Save the file.
4. Remove its button from `gui.py` if one exists.

### How to change the timing or rhythm of an existing song

Just change the `"beat"` numbers. Notes with the exact same `beat` number
will play at the same time. There's no need to touch any other file to
change timing - it's purely data inside `songs.py`.

### Why `play_song` groups notes by beat before playing

If two notes share the same `beat` value, they're fired together in
separate threads instead of one after another - this keeps multi-brick
timing tight instead of one instrument lagging slightly behind another
due to per-brick Bluetooth latency.

### The `stop_event` parameter

`play_song()` accepts an optional `stop_event` (a `threading.Event`).
While a song is playing, the code checks this before firing each beat -
if it's been set, playback stops early instead of continuing to the end.
This is what allows a gesture (fist) or a new song request to interrupt
a song that's currently playing. See Section 12 for how this is used
safely when switching between songs.

---

## 6. `gui.py` - the window and buttons

This file builds the actual app window using a library called
CustomTkinter, and connects each button (and each voice/gesture action)
to a function that does something (like sending a command to `ev3.py`).

### How to add a button for a new song

Find the `song_frame` section inside `create_widgets()`, and add a new
button following the same pattern as the existing one:
```python
new_song_button = ctk.CTkButton(
    song_frame,
    text="Your New Song Name",
    command=lambda: self.play_selected_song("Your New Song Name")
)
new_song_button.pack(pady=10)
```
Make sure the text inside `play_selected_song("...")` exactly matches the
song's name as written in `songs.py`.

### How to add a button for a new instrument

Find the `instrument_frame` section, and add a button similar to the
existing Gong/Saron/Drum ones:
```python
new_button = ctk.CTkButton(
    instrument_frame,
    text="Your Instrument Name",
    command=lambda: self.ev3.send_command("YOUR_INSTRUMENT_NAME")
)
new_button.grid(row=1, column=3, padx=10, pady=10, sticky="ew")
```
(Adjust the `column` number so it doesn't overlap with existing buttons,
and update `instrument_frame.grid_columnconfigure(...)` to include the
new column count.)

---

## 7. Why some choices were made (background context)

- **The EV3 bricks use their normal, original LEGO software - nothing
  special was installed on them.** An alternative approach (called
  "Pybricks") was tried first, but caused a lot of connection problems.
  Using the bricks' original software with a Python library called
  `ev3_dc` turned out to be far more reliable, and doesn't require
  changing anything on the physical bricks at all.
- **Threads, not a more advanced technique called `asyncio`.** Threads
  were simpler to add on top of the existing code without a big rewrite,
  given the project's tight deadline.
- **Multiple bricks were added partway through the project.** The code
  was originally built assuming just one brick, then restructured once it
  became clear the instruments would be spread far apart, each needing
  its own brick.

---

## 8. Detecting a brick that silently disconnects

### The problem this solves

Originally, the app only found out a brick had disconnected in one way:
by trying to actually send it a command and having that fail. If a brick
died while just sitting idle (nothing currently trying to use it), the
status grid would keep wrongly showing it as "Connected" until someone
happened to click a button that used it - which, during a real
performance, could be the worst possible moment to find out.

### How `health_check()` fixes this

Every few seconds, the app automatically sends a small, harmless request
(checking the battery level) to every brick it currently believes is
connected - a "are you still actually there?" check. If a brick doesn't
respond, it's immediately marked as disconnected (and so is every
instrument that depends on it), so the status grid turns red within
seconds, without anyone needing to click anything.

### Why it pauses while a song is playing

Sending this extra check at the same time as real movement commands could
add a small delay to the song's precise timing. So the health check is
skipped entirely while a song is actively playing, and resumes once
playback finishes.

### Why checks can't be scheduled too close together

Checking every brick takes a small but real amount of time (each one is
checked one at a time, not all instantly). If the background check were
scheduled to repeat faster than a full round actually takes, multiple
checks could start overlapping and pile up, sending duplicate Bluetooth
traffic to the same bricks at once - risking the same kind of connection
instability this feature is trying to prevent. To guard against this, a
simple flag (`self._health_check_running` in `gui.py`) makes sure a new
check can never start while a previous one is still in progress,
regardless of how short the repeat interval is set to.

---

## 9. Why port verification (checking what's actually plugged into each port) was not added

### What we tried

The idea was to compare what `config.py` *expects* to be plugged into
each port against what the brick *actually* reports - catching mistakes
like a typo in a port letter, or a motor that's come unplugged, before
it causes a silent failure during a performance.

`ev3_dc` provides a property called `sensors_as_dict` that reports what's
plugged into every port. In testing, this worked correctly *once* - right
after first connecting - matching physical reality exactly.

### Why it doesn't work as a live/ongoing check

Through direct testing, we confirmed that `sensors_as_dict` only reflects
what was plugged in **at the moment the connection was first made** - it
does not update again afterward, no matter how many times it's re-checked
on that same connection. Physically unplugging a motor and checking again
(without reconnecting) still showed the old, outdated result.

A second test confirmed that a **brand new connection** to the same brick
*does* correctly detect the change - meaning the brick only re-scans its
ports once, at connection time, not continuously.

### Why we didn't work around this by reconnecting periodically

Making this "live" would require disconnecting and fully reconnecting
every brick on a repeating timer, just to force a fresh port scan. Given
what was learned earlier in the project - that EV3 bricks need a cooldown
period between disconnecting and reconnecting, and that repeated
reconnect attempts caused real connection instability - doing this
automatically and repeatedly in the background was judged too risky. It
could end up *causing* the exact kind of dropped connections this feature
was meant to catch.

### Where this leaves things

Port verification was removed from the project entirely for now, rather
than being kept as a limited "connect-time only" tool, to keep the
codebase focused on what's actually being used. The `health_check()`
method (Section 8) remains the way the app detects a brick that's stopped
responding - it just can't identify *which specific port* failed, only
that the whole brick did.

---

## 10. `ai/voice.py` - voice recognition

### How it works

The app listens continuously in the background for a **wake word**
("EV3"). Once it hears something close to that word, it treats whatever
comes right after as a command (e.g. "play gong"), and passes that text
to `gui.py` to figure out what to do with it.

Voice recognition uses Google's free online speech-to-text service (via
the `SpeechRecognition` library), which means **it needs an internet
connection to work at all**.

### Problems we ran into, and what we learned

- **"EV3" is hard for speech recognition to get consistently right,**
  since it's not a normal English word. Different attempts got
  transcribed differently (e.g. "evie 3," or something unrelated
  entirely). Two things helped a lot: setting the recognizer's language
  to `"en-MY"` (Malaysian English) instead of the default, and using
  **fuzzy matching** (accepting close phonetic matches like "robert" for
  "robot," or "evie 3" for "EV3") instead of requiring an exact match.
- **The wrong microphone was being used by default.** Windows lists many
  duplicate entries for the same physical microphone (different driver
  types), and letting the code just use "the default" sometimes picked a
  low-quality or incorrectly-routed one. We fixed this by explicitly
  specifying which microphone index to use (`MIC_INDEX` in `voice.py`),
  found by testing with a small standalone script (`test_mic.py`) that
  lists all available microphones and lets you try each one.
- **Malay song names are still unreliable.** Even with the above fixes,
  phrases like "Rasa Sayang" occasionally get badly mis-heard (e.g. as
  "roses I am"), since Google's speech model doesn't know Malay words.
  Fuzzy matching (comparing what was heard against known song/instrument
  names to find the closest match) helps a lot but isn't perfect.
- **Matching was originally case-sensitive by accident,** comparing
  lowercase heard text against uppercase instrument names like `"GONG"` -
  since these look completely different letter-by-letter to a simple
  text comparison, single-word instrument commands like "drum" were
  failing to match at all. Fixed by comparing everything in lowercase,
  then mapping back to the correctly-cased real name afterward.
- **Filler words like "play" were sometimes throwing off the matching
  score,** especially for short instrument names. Fixed by stripping out
  common filler words ("play," "the," "a," "please," "to") before
  comparing.

### Current status

Voice recognition works and includes commands for instruments, songs,
and actions (connect/disconnect/battery - see Section 14), but it is
**not as reliable as gesture recognition** given the accent/mishearing
challenges above. It's a genuinely useful backup/demo feature, but
gesture recognition (Section 11) is the recommended input method for
anything that needs to work consistently.

---

## 11. `ai/gesture.py` - gesture recognition

### How it works

Uses your webcam plus a library called MediaPipe, which can detect a
hand and figure out the position of each knuckle/fingertip in real time.
From those positions, the code works out: how many fingers are held up,
and whether the hand is a closed fist.

**Both hands are tracked at once**, and treated differently:
- **Right hand**, finger count (1-5) -> directly selects and plays an
  **instrument** (same idea as clicking an instrument button).
- **Left hand**, finger count (1-5) -> directly selects and plays a
  **song** (same idea as clicking a song button).
- **Fist on either hand** -> stops whatever song is currently playing.

### Why this replaced the original "next/previous song" design

The first version used a thumbs-up/thumbs-down gesture to step through
songs one at a time (like pressing "next" or "previous"). In testing,
this felt confusing and easy to overshoot - you'd have to remember how
many songs you'd stepped past. Switching to **direct selection** (a
specific finger count always means a specific, particular song) is more
predictable and matches how instrument selection already worked.

### Why a gesture doesn't keep re-triggering while held

Early on, holding a gesture steady (e.g. while a song played) would
sometimes cause it to restart repeatedly, or fire many times in a row.
This was fixed with two separate mechanisms:

1. **Only fire on change.** The code remembers the last gesture that
   actually triggered an action, separately for each hand. It only fires
   again once the gesture changes to something different (or the hand
   leaves the frame and a gesture is shown again afterward) - simply
   holding the same gesture steady does nothing further.
2. **Stability buffering.** Even a hand that isn't moving still produces
   very slightly different readings from frame to frame (camera noise,
   tiny natural hand tremor). This caused occasional flickering between
   two different gesture readings, which looked like "spamming" commands.
   The fix requires a gesture to be read the *same way* for several
   consecutive frames in a row before it's accepted as real, filtering
   out that natural jitter.

### A bug worth knowing about: the thumb direction fix

Whether a thumb counts as "extended" was originally determined by
comparing its x-position to a knuckle further down the thumb - this
works for a right hand, but is backwards for a left hand (the thumb
splays toward the opposite side). This caused a real, closed left-hand
fist to be misread as "1 finger extended." The fix compares thumb
position in the opposite direction specifically for the left hand.

### Why song-switching needed its own fix

Originally, all songs shared a single "please stop" signal
(`stop_event`). Starting a new song accidentally reset this shared signal,
which meant the *previous* song never actually received the stop request
- it just kept playing at the same time as the new one, sending
conflicting commands to the same instruments. See Section 12 for the fix.

---

## 12. Switching songs safely (stopping the previous one)

### The problem

If you selected a new song (by gesture or button) while a different song
was still playing, both would play *at the same time*, since nothing was
actually telling the first one to stop.

### The fix

Each time a song starts, it gets its **own personal stop signal**
(instead of every song sharing one). Before starting a new song, the app
now explicitly tells whichever song is currently playing to stop first,
using that specific song's own signal - so switching songs cleanly stops
the old one before starting the new one, instead of them overlapping.

This also means a fist (stop gesture) reliably stops *whatever* is
currently playing, regardless of which song it is.

---

## 13. Known limitations (things not fully finished yet)

- Port mismatches (e.g. a typo in `config.py`, or a motor plugged into
  the wrong port) are only caught when a command is actually sent to that
  port and does nothing - there's currently no diagnostic tool for this
  (see Section 9 for why).
- Voice recognition works, but is not reliable enough to depend on for a
  real performance - see Section 10 for details. Gesture recognition is
  the more dependable AI input method.
- Gesture recognition currently supports up to 5 instruments and 5 songs
  (one per finger count on one hand each). Going beyond that would need
  an additional gesture (e.g. a "mode switch") to select further down a
  longer list.
- Gesture stability buffering (Section 11) adds a small delay (a
  fraction of a second) before a gesture is accepted, to filter out
  jitter. This is a deliberate trade-off between responsiveness and
  reliability.
- The microphone index used by voice recognition (`MIC_INDEX` in
  `ai/voice.py`) is specific to the computer it was set up on. Moving to
  a different computer requires finding and setting the correct index
  again (see Section 14).

---

## 14. Changing voice commands, the wake word, and gesture settings

### Changing the wake word

In `ai/voice.py`, near the top:
```python
WAKE_WORD = "hey ev3"
WAKE_TRIGGER = "ev3"
```
`WAKE_TRIGGER` is the word that's actually checked for (using fuzzy
matching, so close mishearings still count). `WAKE_WORD` is just
decorative display text shown in messages - changing it alone does
nothing; you must change `WAKE_TRIGGER` to actually change what's
detected.

**Important, from real testing:** saying the wake word alone is enough -
words like "hey" or "please" are NOT required by the code, they're just
natural-sounding filler. Saying "EV3, drum" works exactly the same as
"Hey EV3, please play the drum."

### Changing the microphone used

In `ai/voice.py`:
```python
MIC_INDEX = 1
```
This number is specific to the laptop it was set up on. On a different
computer, this index will likely be wrong, and voice recognition will
fail silently or mishear everything. To find the correct number on a new
machine:

1. Create a file called `test_mic.py` with this content:
   ```python
   import speech_recognition as sr

   print("Available microphones:")
   for i, name in enumerate(sr.Microphone.list_microphone_names()):
       print(f"  {i}: {name}")

   recognizer = sr.Recognizer()
   microphone = sr.Microphone()

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
   ```
2. Run it, note which microphone number sounds like your actual laptop
   microphone (usually something like "Microphone Array"), then try
   changing `device_index=` in that script to test a few numbers until
   one reliably transcribes what you say correctly.
3. Update `MIC_INDEX` in `ai/voice.py` to that confirmed working number.

### Adding or removing voice commands (beyond instruments/songs)

In `gui.py`, inside `handle_voice_command()`:
```python
voice_actions = {
    "connect": self.connect_ev3,
    "disconnect": self.disconnect_ev3,
    "battery": self.check_battery,
    "check battery": self.check_battery,
}
```
Add a new line following the same pattern to add a new voice-triggered
action, pointing it at any existing method in `gui.py`. Remove a line to
take that command away. Instrument and song commands don't need to be
added here at all - they're picked up automatically from `config.py` and
`songs.py`.

### Changing the accent/language hint

In `ai/voice.py`:
```python
SPEECH_LANGUAGE = "en-MY"
```
This tells Google's speech recognizer which accent to expect. Change
this if voice recognition is being used by someone with a different
accent - e.g. `"en-US"`, `"en-GB"`, `"en-AU"`, etc. are all valid options.

### Changing gesture settings

In `ai/gesture.py`:
- **Which hand controls what:** currently right hand = instruments, left
  hand = songs. This is set inside `_handle_hand()` - swap the `if side
  == "right"` / `"left"` logic to reverse it.
- **How many frames a gesture needs to be held before it counts:**
  ```python
  self._stability_threshold = 5
  ```
  Raise this number for steadier/more deliberate detection (but slower
  to respond), lower it for a snappier response (but more prone to
  jitter/false triggers).

---

## 15. Turning voice and gesture recognition on/off

### Why they need an explicit stop, not just "always on"

Both features run continuously once started, listening/watching in the
background for the rest of the app session unless stopped. Since the
voice wake word is "EV3" - a word that naturally comes up constantly
while explaining or discussing the project - leaving it always-on risks
accidental triggers from ordinary conversation. Both AI features are
therefore designed to be turned on only when actually needed, and off
again afterward.

### How the buttons work

Both the Voice Recognition and Gesture Recognition buttons act as
on/off switches (not just "start" buttons) - clicking again while
active stops that feature, and the button's text/color changes to make
the current state clear at a glance.

### Voice commands to control both features

Since these are also available as voice commands (see Section 14's
`voice_actions` dictionary): "stop listening" or "stop voice" turns off
voice recognition (spoken through itself, so it takes effect right after
that phrase is processed). "Start gesture" and "stop gesture" control
gesture recognition the same way, but using dedicated start/stop actions
rather than a toggle - this is deliberate, so the command always does
exactly what it says regardless of the current state, rather than
risking the opposite effect if a toggle command were misheard.

### A note on response delay

Because voice commands are matched using fuzzy comparison against known
instrument/song/action names (rather than an instant exact-match check),
there's a brief, normal processing delay between finishing a spoken
command and the action actually happening - this is expected behavior,
not a performance bug.

---

## 16. Layout structure (`gui.py`)

### Why sections are wrapped in a `content_frame`

Originally, each section (EV3 controls, song selection, instruments, AI
mode) was packed directly onto the main window and stretched to its full
width. On a wide window, this made buttons very wide relative to their
text, giving the app a stretched, uneven look rather than a deliberately
designed one.

The fix: a `content_frame` with a fixed maximum width sits inside the
main window and is centered; every section is placed inside
`content_frame` instead of directly on the window. This keeps the
interface a comfortable, consistent width no matter how large the window
is resized.

### Why song buttons are generated in a loop, not written one-by-one

As more songs get added to `songs.py`, manually adding a matching button
for each one in `gui.py` would be easy to forget and error-prone. Song
buttons are instead generated automatically from `self.song_list` (which
comes from `list_songs()` in `songs.py`), so adding a new song
automatically gets it a button with zero changes needed in `gui.py`.

One technical detail worth knowing: the button's click handler uses
`lambda name=song_name: self.play_selected_song(name)`, specifically
capturing `song_name` as a default argument. Without this, every
generated button would end up playing the *last* song in the list
instead of its own - a common Python pitfall when creating functions
inside a loop, where the loop variable itself is looked up at the time
the button is clicked (by which point the loop has already finished),
not at the time the button was created.