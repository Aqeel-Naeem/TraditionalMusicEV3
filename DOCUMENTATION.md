# Code Documentation

This document explains how the code works, file by file, using simple
language. If you want setup/installation instructions instead, see
`README.md`.

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

---

## 1. Project overview

The app works like a "brain and musician" system:

```
User (clicks a button in the app)
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
│   ├── voice.py   - listens for voice commands (in progress)
│   └── gesture.py - watches your webcam for hand gestures (in progress)
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
  instrument everywhere else in the project (buttons, songs, etc.).
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
   automatically show up in the status grid, and you can now use
   `"KENONG"` in songs or add a button for it in `gui.py` (see Section 6
   below for adding a button).

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

---

## 5. `songs.py` - the actual songs

### How one note is written

```python
{"instrument": "SARON", "key": 0, "beat": 0.5, "duration": 0.25}
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
4. Add a button for it in `gui.py` (see Section 6 below) so it shows up
   in the app.

### How to remove a song

1. Open `songs.py`.
2. Delete that song's entire entry (from its name to its closing `],`).
3. Save the file.
4. Remove its button from `gui.py` if one exists.

### How to change the timing or rhythm of an existing song

Just change the `"beat"` numbers. Notes with the exact same `beat` number
will play at the same time. There's no need to touch any other file to
change timing - it's purely data inside `songs.py`.

---

## 6. `gui.py` - the window and buttons

This file builds the actual app window using a library called
CustomTkinter, and connects each button to a function that does something
(like sending a command to `ev3.py`).

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

## 8. Known limitations (things not fully finished yet)

- If a brick quietly stops working and nothing tries to send it a command,
  the app won't notice until something actually tries to use it. There's
  no automatic "check if everything's still connected" happening in the
  background yet.
- Voice recognition (`ai/voice.py`) needs an internet connection to work,
  and hasn't been fully connected to the current multi-brick setup yet.
- Gesture recognition (`ai/gesture.py`) is designed assuming a right hand;
  it hasn't been tested with a left hand.