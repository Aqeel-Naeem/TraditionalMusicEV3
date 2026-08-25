# Traditional Music EV3 Controller

An app that lets you control LEGO EV3 robots from your computer to play
traditional musical instruments (gong, chime, gendang, gamelan, saron) -
by clicking buttons, using your voice, or using hand gestures.

This guide assumes you've never used VS Code or written code before.

---

## Before you start: what you need

- A Windows computer
- LEGO EV3 bricks (using their normal, original LEGO software - do not
  install any special robot software on them)
- Motors plugged into the EV3 bricks
- Bluetooth on your computer
- A webcam (for gesture control) and a microphone (for voice control) -
  both optional

---

## Step 1: Install VS Code
1. Go to https://code.visualstudio.com
2. Click **Download** for Windows, run the installer (default options fine)

## Step 2: Install Python
1. Go to https://www.python.org/downloads/
2. Download and run the installer
3. **Important:** check **"Add python.exe to PATH"** on the first screen

## Step 3: Download this project
1. Open the project's GitHub page, click **Code > Download ZIP**
2. Extract it somewhere you'll remember (e.g. Desktop)

## Step 4: Open it in VS Code
**File > Open Folder**, select the extracted folder.

## Step 5: Open a terminal
**Terminal > New Terminal** in VS Code's top menu.

## Step 6: Set up a Python environment
```
python -m venv .venv
.venv\Scripts\activate
```
If you see a "running scripts is disabled" error:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
then try activating again. You'll know it worked when you see `(.venv)`
at the start of your terminal line.

## Step 7: Install required packages
```
pip install -r requirements.txt
```
First time, no requirements.txt yet:
```
pip install customtkinter ev3_dc SpeechRecognition pyaudio mediapipe==0.10.9 opencv-python
```
If `pyaudio` fails:
```
pip install pipwin
pipwin install pyaudio
```
Then create the file for next time:
```
pip freeze > requirements.txt
```

---

## Step 8: Connect your EV3 brick(s) via Bluetooth

> **A note on EV3 Bluetooth reliability:** it can be unpredictable on
> Windows - some laptops connect smoothly, others struggle. If one brick
> is being difficult, trying a *different* physical brick sometimes fixes
> it immediately, for reasons we never fully pinned down. Also: the very
> first time you click "Connect EV3" with a new brick, Windows sometimes
> pops up its own "Add a device" prompt right then - just accept it and
> enter `1234` if asked for a PIN. This only needs to happen once per
> brick per computer.
>
> **A hard limit worth knowing:** classic Bluetooth can only actively
> connect to 7 devices at once from one computer (a real protocol limit,
> not a setting). If you have many bricks, consolidating instruments onto
> shared bricks (see Step 10) helps avoid ever hitting that ceiling.

For each brick:
1. On the EV3: **Settings > Bluetooth**, turn ON, enable **Visible**
2. On Windows: **Settings > Bluetooth & devices > Add device > Bluetooth**
3. Click the EV3 when it appears, accept on the brick (**Yes**)
4. If asked for a PIN, type **1234**; if it just shows a number with a
   Connect button (no PIN box), that's normal too - just click Connect

## Step 9: Find each EV3's ID (MAC address)
**Settings > Brick Info** on the brick, look for **ID**, e.g.
`001653437F21` - add colons every 2 characters: `00:16:53:43:7F:21`.

## Step 10: Set up your brick(s)

### The current setup: one master brick (no motors needed)

Right now, the app is set up to connect to **one coordinator brick**
that has no motors attached - that brick runs its own program which
handles talking to all the other instrument bricks on its own, outside
this app entirely. This is simpler to set up on the PC side, and was
adopted specifically to reduce Bluetooth command delay (see
`DOCUMENTATION.md`'s Architecture History, Architecture 4).

In `config.py`:
```python
PROGRAM_ONLY_BRICKS = [
    "00:16:53:41:90:6e",  # your master brick's MAC
]
```
That's the only config needed for this brick - no ports, no motors.
See Step 13 for how to tell the app which program to run on it.

### The older approach: one brick per instrument (still works, currently unused)

If you're *not* using a master-relay setup, instruments can instead be
configured directly - open `config.py`'s `INSTRUMENTS` dict:
```python
INSTRUMENTS = {
    "GONG": [
        {"mac": "00:16:53:46:be:aa", "port": "A"},
    ],
}
```
**An instrument can span multiple bricks or share a brick with another
instrument** - just list every `{mac, port}` it needs. Two instruments
can even sit on the *same* brick, using different ports.

Complex instruments with a "controller" motor (positions to an angle)
and a "hitter" motor (strikes) go in `POSITIONED_INSTRUMENTS` instead -
see `DOCUMENTATION.md`.

If you switch to this approach, also set `SHOW_INSTRUMENT_SECTIONS =
True` in `gui.py` to bring back the status grid and manual instrument
buttons (currently hidden since they're not relevant to a master-brick
only setup).

## Step 11: Run the app
```
python main.py
```

---

## Step 12: Using the app

- **Connect EV3 / Disconnect EV3 / Check Battery** - self-explanatory;
  check battery before every use, low battery can cause odd behavior
- **Activity Panel** (left side) - shows everything happening in plain
  language: connections, commands sent, voice/gesture events, errors -
  color-coded, with timestamps
- **Song Selection** - your actual songs/programs, downloaded to the EV3
  brick(s) directly and triggered by name (see Step 13)
- **Status grid / Instrument Control** - only shown if you're using the
  older per-instrument setup (`SHOW_INSTRUMENT_SECTIONS = True`)
- **Test Songs (Architecture 2)** - hidden by default (see
  `DOCUMENTATION.md`), an older approach kept for future development

## Step 13: Setting up songs/programs

Songs are built as small programs in **EV3 Classroom** (LEGO's own
official app), downloaded directly onto a brick, and triggered by name
from this app - not written as Python code.

1. Build the program (in EV3 Classroom, or whatever tool was used to
   build your master brick's relay program) and download it
2. Find its exact file path:
   ```
   python test/list_ev3_files.py <brick_mac>
   ```
   then again with a folder path shown in the output, to see the actual
   file inside. **Names are case-sensitive** - always confirm the real
   path this way rather than guessing.
3. Add an entry to `ev3_program_config.py`'s `PROGRAMS` dict:
   ```python
   PROGRAMS = {
       "Your Song Name": {
           "<brick mac>": "<exact remote .rbf path>",
       },
   }
   ```
   For the master-relay setup, this is just **one** brick (the master).
   For the older per-instrument approach, list every brick the song
   needs, same as before.
4. Restart the app - a button for your song appears automatically

## Step 14: Using voice and gesture control

### Voice recognition
1. Click **Voice Recognition** (button turns red while listening; click
   again, or say "EV3, stop listening," to turn it off)
2. Say something close to **"EV3"** followed by your command - e.g.
   "Hey EV3, play gamelan" or just "EV3, play gamelan." Words like "Hey"
   or "please" are just natural phrasing, not actually required.
3. Needs an internet connection.

**Available commands:** any instrument name, any song name, "connect",
"disconnect", "battery", "stop"/"stop song"/"pause", "start gesture",
"stop gesture", "exit"/"quit"/"shutdown" (safely closes the whole app).

**Honest limitation:** voice recognition is not perfectly reliable,
especially for non-English words. Gesture control is more consistent -
treat voice as a backup/demo feature.

**Setting up on a new computer:** the microphone index is specific to
the machine it was configured on. Run `test_mic.py` to find the correct
one for a new computer, then update `MIC_INDEX` in `ai/voice.py`.

### Gesture recognition
1. Click **Gesture Recognition** - a webcam window opens (closeable by
   pressing **Q** or clicking its **X** button - both work correctly)
2. **Right hand** finger count (1-5) selects an instrument directly
3. **Left hand** finger count (1-5) selects and plays a song/program
4. **Fist** (either hand) stops whatever's currently playing
5. Playing a different single instrument manually does **not** stop an
   in-progress instrument sequence (like Gamelan's note run) - only
   selecting a new song, the Stop button, or a fist gesture does

Works best with decent, consistent lighting.

---

## Things to watch out for

- Only connect EV3 bricks via their normal LEGO settings - no special
  software on the bricks themselves
- Check battery before every use
- If reconnecting fails right after disconnecting, wait a few seconds -
  normal EV3 quirk
- If Bluetooth pairing keeps failing, remove the device in Windows
  Bluetooth settings and pair again from scratch; try a different
  physical brick if available
- Keep bricks reasonably close to your computer - Bluetooth range is
  limited
- Voice and gesture need their own hardware access - make sure nothing
  else is using your mic/webcam at the same time
- Closing the app (X button, or saying "EV3, exit") safely stops any
  playing song, halts all motors, stops gesture/voice, and disconnects
  everything in the right order before actually closing

## If something isn't working

| Problem | What to try |
|---|---|
| "No EV3 device found" when reconnecting | Wait a few seconds, try again |
| App freezes when checking battery | A brick may have disconnected - reconnect all |
| Bluetooth pairing keeps failing | Remove and re-pair from scratch; try a different brick |
| Motor doesn't move despite "Connected" | Double-check the port letter in `config.py` |
| Gesture window doesn't open, webcam light is on | Close other apps using the webcam |
| Voice mishears commands often | Known limitation, especially non-English words - use gesture instead |
| Voice hears nothing at all | New computer - update `MIC_INDEX` in `ai/voice.py`, see Step 14 |
| A downloaded program's path fails | Re-confirm the exact case-sensitive path with `list_ev3_files.py` |
| Connecting many bricks feels laggy | You may be near the 7-device Bluetooth limit - consolidate instruments onto shared bricks |