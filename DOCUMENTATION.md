# Code Documentation

Explains how the code works and *why* it's built this way - including
the false starts, since understanding what didn't work matters as much
as what did. For setup instructions, see `README.md`.

---

## Table of Contents

0. [Glossary](#0-glossary)
1. [Project overview](#1-project-overview)
2. [Architecture history - why we're on our 3rd approach](#2-architecture-history---why-were-on-our-3rd-approach)
3. [File structure](#3-file-structure)
4. [`config.py` - instrument mapping](#4-configpy---instrument-mapping)
5. [`ev3.py` - the hardware layer](#5-ev3py---the-hardware-layer)
6. [SARON - the positioned-instrument system](#6-saron---the-positioned-instrument-system)
7. [The Bluetooth 7-device limit and brick consolidation](#7-the-bluetooth-7-device-limit-and-brick-consolidation)
8. [Architecture 3 - EV3 Classroom downloaded programs](#8-architecture-3---ev3-classroom-downloaded-programs)
9. [The disconnect/stop crash, and how it was actually fixed](#9-the-disconnectstop-crash-and-how-it-was-actually-fixed)
10. [GAMELAN - combined instrument + sequence play](#10-gamelan---combined-instrument--sequence-play)
11. [`gui.py` - interface layer](#11-guipy---interface-layer)
12. [The Activity Panel](#12-the-activity-panel)
13. [Voice recognition](#13-voice-recognition)
14. [Gesture recognition](#14-gesture-recognition)
15. [Safe shutdown](#15-safe-shutdown)
16. [Known limitations](#16-known-limitations)

---

## 0. Glossary

- **Function/Method** - a named block of code you run by calling its name.
- **Class** - a blueprint for an object holding data + the functions that
  work on it. `EV3` is a class representing "a connection manager."
- **Thread** - code running in the background, at the same time as the
  rest of the program, instead of making everything wait for it.
- **MAC address** - a unique ID every Bluetooth device has.
- **Direct Command / byte-code** - the EV3's own low-level instruction
  format, sent directly to its onboard processor. Powerful but
  unforgiving - a wrong field can cause real, unpredictable behavior.
- **Piconet** - the Bluetooth network one device (your laptop) forms
  with the devices it's actively connected to; hard-capped at 7.
- **`.rbf` file** - a compiled EV3 Classroom program, ready to run
  directly on the brick.

---

## 1. Project overview

```
User (button / voice / gesture)
            |
        gui.py
            |
        ev3.py  <- the only place that talks Bluetooth
            |
    One or more EV3 bricks (stock, unmodified LEGO firmware)
            |
        Motors -> instruments
```

The Python app is the "brain," each EV3 brick is a "musician." The
bricks never need custom firmware or software installed on them.

---

## 2. Architecture history - why we're on our 3rd approach

This matters a lot for understanding the current code, since remnants
of all three approaches still exist in the project.

### Architecture 1 - live, per-command control
Every action (a button click, a song note) sent a command over
Bluetooth immediately, using `ev3_dc`'s own tested, high-level Python
methods (`motor.start_move_by()`, etc.). **This never crashed.** Its
problem: Bluetooth has real, variable latency, especially once several
bricks are connected - meaning song timing could drift or fire notes
out of order relative to what the code intended.

### Architecture 2 - compiled on-brick timelines
To remove Bluetooth latency from song *timing*, the whole song got
compiled into raw EV3 byte-code (hand-built `opOutput_Step_Speed` /
`opTimer_Wait` / etc. sequences) and uploaded once; the brick then ran
the entire timed sequence on its own processor, with no further
Bluetooth traffic needed mid-song. This is a legitimately clever fix for
the latency problem - but building byte-code by hand, without a
validated reference for every operation used, turned out to
**intermittently crash the brick**. The `songs.py`/`ev3.py` code for
this still exists (`compile_song_timelines()`, `play_timeline()`) and
is intentionally kept, not deleted - it's meant to be revisited later,
once each operation it uses can be validated the way we eventually
validated `opProgram_Stop` (see Section 9). It's currently hidden from
the GUI by default (`SHOW_LEGACY_ARCHITECTURE_2 = False` in `gui.py`).

### Architecture 3 - EV3 Classroom downloaded programs (current)
Instead of hand-building byte-code in Python, each song's motor timing
is built visually in **EV3 Classroom** (LEGO's own official app),
compiled by LEGO's own tested compiler into a `.rbf` file, and just
*uploaded and started* from Python using `ev3_dc`'s already-tested
`FileSystem` API (`ev3_program_runner.py`). This gets Architecture 2's
benefit (the brick runs everything itself, no Bluetooth latency during
playback) **without** the hand-rolled byte-code risk - the only custom
byte-code left is the small, carefully-validated "start this program" /
"stop everything" commands (see Section 9), not entire song logic.

**This is why the GUI's "Song Selection" section is Architecture 3**
(triggering downloaded programs), while the old Architecture 2 song
data sits hidden but intact for later.

---

## 3. File structure

```
TraditionalMusicEV3/
├── main.py                  - entry point
├── gui.py                   - CustomTkinter interface
├── ev3.py                   - Bluetooth connection + command dispatch
├── config.py                - instrument -> brick/port mapping
├── songs.py                 - Architecture 2 (legacy, hidden by default)
├── ev3_program_runner.py    - Architecture 3: upload/start .rbf programs
├── ev3_program_config.py    - Architecture 3: song name -> program paths
├── ai/
│   ├── voice.py              - wake-word voice control
│   └── gesture.py            - two-hand gesture control
├── test/                     - manual hardware diagnostic scripts
└── requirements.txt
```

---

## 4. `config.py` - instrument mapping

Two dictionaries:

**`INSTRUMENTS`** - simple instruments, each a list of `{mac, port}`
motor locations:
```python
INSTRUMENTS = {
    "GONG": [{"mac": "...", "port": "A"}],
    "GAMELAN": [  # 9 motors across 3 physical bricks, one combined instrument
        {"mac": "brick1", "port": "A"}, ...
    ],
}
```
An instrument can span multiple bricks, or share a brick with a totally
different instrument (`ev3.py` deduplicates connections by MAC
automatically, regardless of how many instruments reference it).

**`POSITIONED_INSTRUMENTS`** - for instruments needing a "controller"
motor (pre-positions to an angle) plus "hitter" motor(s) (strikes) - see
Section 6, this is currently only SARON.

---

## 5. `ev3.py` - the hardware layer

The only file that talks Bluetooth. Key design points:

- **One connection per unique brick MAC**, never per-instrument - fixes
  a real early bug where two instruments sharing a brick tried to open
  two separate connections to it.
- **Per-brick failure isolation** - each brick connects inside its own
  try/except; one brick failing doesn't take down the others.
- **A persistent worker thread + queue per brick** for live commands -
  serializes commands *per brick* in submission order, while different
  bricks still run fully concurrently.
- **`is_instrument_connected()`, `get_battery_levels()`,
  `health_check()`** - status/monitoring, used by the GUI's status grid
  and background health polling.
- **`stop_all_motors()`** - see Section 9, this method's history is a
  good case study in validating byte-code before trusting it.

---

## 6. SARON - the positioned-instrument system

SARON has "pairs" (left/right), each with a **controller** motor
(rotates to a specific angle before a strike) and one or more **hitter**
motor(s) (perform the actual strike).

### Why angle 0 isn't a fixed physical point
`ev3_dc` resets a motor's position reference to wherever it physically
is the moment its `Motor` object is created (i.e., at `connect()` time) -
not a fixed mechanical zero. **The hitting stick must be physically
centered before every connect**, or the configured angles (`-45, -15,
15, 45` - symmetric around center, matching the stick resting in the
middle of each side) will be offset from the wrong starting point.

### Why hitter is sometimes a LIST of motors
One pair's hitter can be **two mechanically gear-linked motors**
providing combined torque for a heavy striking stick. Since they're
rigidly linked, sending them as two separate sequential commands (even
queued on the same brick) risked desync/gear strain. The fix: combine
their ports into a single mask (e.g. `PORT_B + PORT_C`) and issue **one**
low-level command that starts both motors at the exact same instant -
same technique validated for `stop_all_motors()` (see a real, documented
reference example: `opOutput_Speed` set per port individually, then one
`opOutput_Start` using the *summed* port values). All hitter motors in
one pair must be on the same physical brick for this to work.

### `hitter_direction` - a physical calibration value, not a bug
Which direction counts as "the hit" vs "the return" depends on how the
motor is mounted - can't be known from code alone. It was determined by
physically testing (triggering one hit, watching the direction, flipping
the config value if backwards) - already confirmed correct
(`"clockwise"` for both pairs on this build) but is inherently a
hardware-specific setting that would need re-checking on a different
physical build.

---

## 7. The Bluetooth 7-device limit and brick consolidation

Classic Bluetooth's piconet architecture hard-caps one master device
(your laptop) at 7 simultaneous active connections - a real protocol
limit (a 3-bit address field), not a setting anyone can raise.

**Symptom this caused:** noticeable, *variable* command delay - even for
a single instrument, single command - once the project reached 7
separate bricks. Confirmed via a controlled isolation test: connecting
just 1 brick made the same command consistently fast, proving the delay
was connection-count-related, not a code bug.

**Fixes applied, in order:**
1. Reduced background health-check polling interval (less idle traffic)
2. Consolidated GONG + GENDANG onto one shared brick (exact 2+2 port fit)
3. Merged GAMELAN 1/2/3 into a single combined `GAMELAN` instrument
   spanning all 3 physical units - this was **also** necessary to fit
   gesture recognition's 5-finger selection limit (7 instruments would
   leave 2 permanently unreachable by gesture; 5 fits exactly)

**Deliberately NOT done:** merging SARON's left+right pairs onto one
brick. Even though cable length wasn't the blocker, doing so would force
both sides through a single Bluetooth connection instead of two
parallel ones - reintroducing exactly the kind of timing risk this
consolidation work was meant to reduce, for an instrument whose design
specifically depends on tight left/right coordination.

**A hard ceiling worth knowing for the future:** if the project ever
needs more than 7 active bricks even after consolidating everything
possible, that's a genuine architectural wall requiring a different
approach (a second Bluetooth adapter, or similar) - not something more
code optimization can solve.

---

## 8. Architecture 3 - EV3 Classroom downloaded programs

`ev3_program_runner.py` has two jobs:

- **`upload_program()`** - uses `ev3_dc`'s own tested `FileSystem` API
  to copy a `.rbf` file to a brick. No custom byte-code involved.
- **`start_program()`** - a small, deliberately minimal direct command
  (load the file into brick memory, then `opProgram_Start`) sourced from
  a documented EV3 direct-commands reference, not invented from
  scratch.
- **`play_programs()`** - starts a program on multiple bricks from
  separate threads launched together, for as-close-as-possible
  simultaneous starts (true byte-level simultaneity isn't physically
  possible over one shared Bluetooth radio - see the note on ASYNC mode
  below for the actual mitigation).

`ev3_program_config.py`'s `PROGRAMS` dict maps a song's display name to
`{brick_mac: remote_path}` - a song using multiple bricks just lists
every brick it needs.

**Program paths are case-sensitive** (the brick's filesystem is
Linux-based) - always confirmed via `test/list_ev3_files.py`, never
guessed, after an early mismatch ("Top Spinner" vs "top spinner") wasted
real debugging time.

**Multi-brick start timing:** starting several bricks' programs
"simultaneously" is still bounded by one shared Bluetooth radio only
being able to transmit to one device at a time. Switching
`start_program()`'s `sync_mode` to `ASYNC` (fire-and-don't-wait-for-ack)
rather than `SYNC` (wait for a full round-trip before moving to the
next brick) meaningfully tightens this window, since 7 "go" signals can
be sent back-to-back instead of each one waiting out a full
acknowledgment first.

---

## 9. The disconnect/stop crash, and how it was actually fixed

A genuinely important case study, since the fix method (find a *verified*
reference, don't hand-guess byte-code) is the template for validating
anything similar later.

**Symptom:** the brick would crash specifically after disconnecting,
once Architecture 3 was in active use.

**Root cause found:** `disconnect()` was calling `stop_all_motors()`
automatically every time, and that method sent unvalidated raw
byte-code (`opProgram_Stop` called three times, targeting slots 0, 1,
and 2) trying to kill the running program - a command that had likely
never been tested against a brick with a *real* uploaded program
actively running, since that situation didn't really exist before
Architecture 3.

**First fix (safe, partial):** removed the `opProgram_Stop` calls
entirely from `stop_all_motors()`, keeping only `opOutput_Stop` (halts
motor *output* directly, a pattern independently matched against a
verified reference example). This stopped the crash, but meant Stop
only halted motors - the program itself kept running in the background
for a few harmless seconds until it finished on its own.

**Second fix (found the actual correct reference):** located a real,
confirmed-working example showing `opProgram_Stop` correctly takes
**one** argument - `LC0(USER_SLOT)` - not three separate calls to
different slots. The original crash was very likely caused specifically
by targeting slots that shouldn't have been touched (possibly reserved
for the brick's own system/menu). `stop_all_motors()` now correctly
sends `opProgram_Stop` targeting only `USER_SLOT` - the same slot
`ev3_program_runner.py` already starts programs in - stopping both the
motors *and* the program cleanly, enabling immediate song-switching
after a stop.

**One implementation detail worth remembering:** `ev3.USER_SLOT` is
already pre-encoded bytes in `ev3_dc`, not a raw Python int - it must be
used directly, *not* wrapped in `LCX()` (which expects to encode a raw
int itself and raises an `AssertionError` otherwise).

---

## 10. GAMELAN - combined instrument + sequence play

### Why it's one combined instrument, not three
See Section 7 - solves both the Bluetooth connection-count concern and
the gesture 5-finger selection limit at once.

### The low-to-high sequence
`play_instrument()` special-cases `GAMELAN`: instead of firing all 9
motors at once, it plays them in order (`key=0` through `key=8`, ~0.4s
apart) via `_play_gamelan_sequence()` - demonstrating every motor
responds, rather than one simultaneous clump. The 9-motor order in
`config.py` directly determines playback order (unit 1's 3 ports, then
unit 2's, then unit 3's) - no separate sequencing logic needed beyond
config ordering.

### Stop coordination - a deliberately narrow design
GAMELAN's sequence shares the same `current_stop_event` mechanism songs
already used, but **only** in these directions:
- Starting a song/program stops an in-progress GAMELAN sequence
- The Stop button or a fist gesture stops it
- Starting GAMELAN again while already running restarts it fresh

**Playing a different single instrument does NOT stop it** - this was a
deliberate correction after an initial overly-broad version made *any*
instrument trigger cancel GAMELAN, which turned out to be wrong: a
manual one-off test of another instrument should be able to coexist
with an in-progress sequence, since that's not really "starting a
conflicting new performance" the way selecting a different song is.

Stopping uses two layers together: `current_stop_event.set()` (tells the
Python loop not to send more notes) and `stop_all_motors()` (immediately
halts whatever's physically moving *right now*, closing the gap between
"loop notices the stop" and "motor actually stops," which could
otherwise be up to ~0.4s).

---

## 11. `gui.py` - interface layer

### Color palette, applied by role
```
COLOR_ACCENT  - primary/demo actions (Connect, Song Selection)
COLOR_SUCCESS - connected/success state only
COLOR_DANGER  - stop/danger only
COLOR_MUTED   - secondary/calibration controls (Instrument Control, legacy songs)
COLOR_AI      - voice recognition (a "featured" highlight)
COLOR_GESTURE - gesture recognition (distinct from voice)
```
Not every button should carry equal visual weight - this was a
deliberate fix after an early version where everything used the same
default blue, making the interface feel undifferentiated/overwhelming
for a demo audience.

### Layout: scrollable, not fixed
`self.content_frame` is a `CTkScrollableFrame`, not a plain frame - so
adding more instruments, songs, or programs later can never cause
content to be cut off again; it just scrolls.

### Button clustering, not column-stretching
Small groups of secondary buttons (legacy songs, Instrument Control) are
packed together in their own tight sub-frame and centered, rather than
each button being fixed-width-but-centered-in-a-wide-grid-column - the
latter created large, unintentional-looking gaps once the window got
wide enough to have many columns.

### `play_instrument()` - the single path all triggers go through
Button clicks, gesture detections, and voice commands all call this one
method rather than `ev3.send_command()` directly - this is what let the
GAMELAN sequence special-case, and its stop coordination, apply
consistently regardless of *how* an instrument was triggered.

---

## 12. The Activity Panel

A live log panel on the left side of the window, built by **redirecting
`sys.stdout`** rather than manually adding GUI-logging calls to every
`print()` scattered across `ev3.py`, `ai/voice.py`, `ai/gesture.py`, etc.
`_StdoutTee` wraps the real stdout: every print still reaches the
terminal as before, *and* gets pushed onto a thread-safe queue the GUI
polls (`self.after(150, ...)`) - keeping all Tkinter widget updates
safely on the main thread regardless of which background thread
actually called `print()`.

### Friendly formatting layer
`_format_log_line()` translates known raw message patterns into
readable text with icons and color tags (success/error/voice/gesture/
action/muted), and replaces raw MAC addresses with instrument names via
a reverse lookup built from `config.py`. Purely internal noise (worker
thread startup, redundant per-instrument "ready" confirmations already
shown in the status grid) is filtered out - but **errors and failures
are never suppressed**, and anything genuinely unrecognized still shows
up, just visually quiet rather than hidden - the design principle being
"never hide something that might matter," not "only show what's
pre-approved."

---

## 13. Voice recognition

`ai/voice.py` - wake word "EV3" (`WAKE_TRIGGER`), fuzzy-matched via
`difflib.SequenceMatcher` at a 60% similarity threshold against every
word in what was heard - not an exact match requirement, since "EV3"
consistently gets mis-transcribed in different ways. `SPEECH_LANGUAGE =
"en-MY"` tunes Google's recognizer for a Malaysian accent.
`WAKE_TRIGGER` (checked) and `WAKE_WORD` (display text only, e.g. "hey
ev3") are intentionally separate - "hey" is never actually required, it
just reads naturally in the on-screen instructions.

`MIC_INDEX` is specific to the computer it was configured on (Windows
lists many duplicate entries for one physical microphone across
different driver types) - `test_mic.py` finds the correct one for a new
machine.

Commands (instruments, songs, "connect"/"disconnect"/"battery"/"stop"
variants/"start gesture"/"stop gesture"/"exit"/"quit"/"shutdown") are
matched the same fuzzy way in `gui.py`'s `handle_voice_command()`,
comparing everything in lowercase (an early bug matched against
uppercase instrument names like `"GONG"` against lowercase heard text
and silently failed) with common filler words ("play", "the", "a")
stripped first.

---

## 14. Gesture recognition

`ai/gesture.py` uses MediaPipe to track **both hands at once**: right
hand's finger count selects an instrument, left hand's selects a
song/program, a fist (either hand) stops playback.

### Stability buffering
A gesture must read consistently for several consecutive frames
(`_stability_threshold`) before it's accepted - filters out natural
frame-to-frame landmark jitter that otherwise caused occasional
flickering/repeated triggering even when a hand wasn't moving.

### Change-based firing, not time-based
A gesture only fires once per distinct state - holding the same count
steady (even for a long time, even while something plays) doesn't
re-trigger it. It fires again only when the gesture changes, or the hand
leaves frame and reappears.

### The thumb-direction bug
Thumb-extended detection compares x-position against a lower joint -
correct for a right hand, backwards for a left hand (the thumb splays
the opposite way). This caused a genuine closed left-hand fist to
misread as "1 finger." Fixed by flipping the comparison direction
specifically for the left hand.

### Closing the window properly
OpenCV's native window X button doesn't stop a running capture loop on
its own - clicking it just hides/destroys the window handle while
`cv2.imshow()` keeps getting called on it. Fixed by checking
`cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1` each
frame alongside the existing 'q' key check - the standard, documented
way to detect an X-button close.

### GUI button state sync
Since the loop can end on its own (via 'q', or the window closing) -
not just via the app's explicit stop button/voice command - `gui.py`
polls every 500ms (`_sync_gesture_button`) and corrects the button's
displayed state if it doesn't match what's actually running, rather
than requiring every possible stop path to remember to update the
button itself.

---

## 15. Safe shutdown

`on_close()` (called by both the window's X button and voice
"exit"/"quit"/"shutdown") does, in order:
1. Signal any playing song/GAMELAN sequence to stop
2. `stop_all_motors()` - **while still connected**, since this command
   can't reach a brick after disconnecting
3. Stop gesture recognition if running (releases the webcam cleanly)
4. Stop voice recognition if running
5. Disconnect EV3
6. Restore the real `sys.stdout`
7. Destroy the window

Voice-triggered shutdown (`voice_shutdown()`) reuses this exact method
via `self.after(0, self.on_close)`, rather than a separate close path -
ensuring both ways of closing the app are identically safe, and
schedules it onto the main thread since `self.destroy()` isn't safe to
call directly from voice recognition's background thread.

---

## 16. Known limitations

- Voice recognition remains less reliable than gesture, especially for
  non-English words - treat it as a backup/demo feature
- Gesture-based selection supports up to 5 instruments and 5
  songs/programs (one hand's finger count each) - currently exactly
  fits (GONG, CHIME, GENDANG, GAMELAN, SARON = 5 instruments)
- Architecture 2 (`songs.py`'s compiled timelines) remains hidden and
  unvalidated beyond `opProgram_Stop` - each operation it uses
  (`opOutput_Step_Speed`, `opTimer_Wait`, etc.) would need the same
  verified-reference treatment before being trusted again
- Port mismatches (wrong port in `config.py`, or a motor plugged into
  the wrong port) are only caught when a command is sent and does
  nothing - no live diagnostic tool for this (a "live port checking"
  feature was attempted and scrapped: `ev3_dc`'s port-detection only
  scans once at connect time, not continuously, and forcing a live
  re-scan would mean risky repeated reconnects)
- True byte-level simultaneous start across many bricks isn't physically
  possible over one shared Bluetooth radio - ASYNC mode narrows the gap
  but can't eliminate it entirely