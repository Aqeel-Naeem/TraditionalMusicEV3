# Traditional Music EV3 Controller

This is an app that lets you control LEGO EV3 robots from your computer to
play traditional musical instruments (like a gong, saron, and drum) -
either by clicking buttons, playing a full song automatically, using your
voice, or using hand gestures.

This guide assumes you've never used VS Code or written code before, so it
explains every step in detail.

---

## Before you start: what you need

- A Windows computer
- One or more LEGO EV3 bricks (using their normal, original LEGO software -
  do not install any special robot software on them)
- Motors plugged into the EV3 bricks
- Bluetooth on your computer
- A webcam (for gesture control) and a microphone (for voice control) -
  both optional, only needed if you want to use those features

---

## Step 1: Install VS Code

VS Code is the program you'll use to open and run this project.

1. Go to https://code.visualstudio.com
2. Click the big **Download** button for Windows
3. Open the downloaded file and click through the installer (default
   options are fine)

---

## Step 2: Install Python

1. Go to https://www.python.org/downloads/
2. Click **Download Python** (get the latest version)
3. Run the installer
4. **Important:** on the first installer screen, check the box that says
   **"Add python.exe to PATH"** before clicking Install

---

## Step 3: Download this project

If you were given a link to this project on GitHub:

1. Open the project's page in your web browser
2. Click the green **Code** button
3. Click **Download ZIP**
4. Find the downloaded ZIP file (usually in your Downloads folder) and
   right-click it, then choose **Extract All**
5. Choose a location you'll remember (e.g. your Desktop) and click Extract

You should now have a folder called something like `TraditionalMusicEV3`.

---

## Step 4: Open the project in VS Code

1. Open VS Code
2. Click **File > Open Folder**
3. Select the `TraditionalMusicEV3` folder you extracted
4. Click **Select Folder**

You should now see a list of files on the left side of VS Code (like
`main.py`, `gui.py`, `config.py`, etc.)

---

## Step 5: Open a terminal inside VS Code

A terminal is where you type commands to set things up.

1. In VS Code, click **Terminal** in the top menu bar
2. Click **New Terminal**
3. A panel will open at the bottom of the screen - this is where you'll
   type the commands in the next steps

---

## Step 6: Set up a Python environment

This creates a clean, separate space for this project's software so it
doesn't interfere with anything else on your computer.

In the terminal, type this and press Enter:
```
python -m venv .venv
```

Then type this and press Enter:
```
.venv\Scripts\activate
```

If you see an error mentioning "running scripts is disabled," type this
and press Enter instead:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Type `Y` and press Enter if it asks for confirmation, then try the
`.venv\Scripts\activate` command again.

You'll know it worked if you see `(.venv)` appear at the start of the line
in your terminal.

---

## Step 7: Install the required software packages

With `(.venv)` showing in your terminal, type this and press Enter:
```
pip install -r requirements.txt
```

This reads a list of everything the project needs and installs it all
automatically. It may take a minute or two.

*(If you're setting up this project for the very first time and there's no
`requirements.txt` file yet, type this instead:)*
```
pip install customtkinter ev3_dc SpeechRecognition pyaudio mediapipe==0.10.9 opencv-python
```
*(If `pyaudio` gives an error during install, try this instead:)*
```
pip install pipwin
pipwin install pyaudio
```
*(Then, to create that list file for next time, type:)*
```
pip freeze > requirements.txt
```

---

## Step 8: Connect your EV3 brick(s) to your computer via Bluetooth

> **A note on EV3 Bluetooth reliability (from real experience building
> this project):** EV3 Bluetooth connections on Windows can be
> unpredictable - some laptops connect smoothly every time, others
> struggle no matter what you try. In practice, when one EV3 brick was
> being difficult, simply trying a *different* physical brick sometimes
> solved it immediately, even with identical setup steps. This isn't a
> guaranteed fix and the exact cause isn't fully understood, but it's
> worth trying if you're stuck.
>
> Also, in testing, the very first time you click **Connect EV3** in the
> app (with a brick that hasn't been paired to that computer before),
> Windows sometimes automatically shows an "Add a device" pop-up right
> at that moment - if that happens, just accept it and enter `1234` if
> asked for a PIN. This has only needed to happen once per brick per
> computer; after that, it connects normally through the app.

Do this once for each EV3 brick you'll use.

1. On the EV3 brick itself, use its buttons to go to **Settings**
   (looks like a wrench)
2. Go to **Bluetooth**
3. Turn Bluetooth **ON**
4. Also turn on **Visible** (sometimes called "Visibility")
5. On your computer, click the **Start Menu > Settings > Bluetooth & devices**
6. Click **Add device > Bluetooth**
7. Your EV3 should appear in the list (it may be named something like
   "EV3" or similar) - click it
8. On the EV3's screen, it will ask "Connect to this device?" - select **Yes**
9. On your computer, if it asks for a PIN, type **1234**. If it instead
   shows a screen with a number and just asks you to click Connect (with
   no PIN box), that's normal too - just click **Connect**

Repeat this for every EV3 brick you're using.

---

## Step 9: Find each EV3's ID (MAC address)

You need this so the app knows which brick is which.

1. On the EV3 brick, go to **Settings > Brick Info**
2. Look for **ID** - write down the number shown, e.g. `001653437F21`
3. Add colons every 2 characters so it looks like this:
   `00:16:53:43:7F:21`

Do this for every brick and keep a note of which ID belongs to which brick.

---

## Step 10: Tell the app which instrument uses which brick

1. In VS Code's file list (left side), click on **config.py** to open it
2. You'll see something like this:

```python
INSTRUMENTS = {
    "GONG": [
        {"mac": "00:16:53:46:be:aa", "port": "A"},
    ],
    "SARON": [
        {"mac": "00:16:53:41:95:2e", "port": "A"},
    ],
    "DRUM": [
        {"mac": "00:16:53:43:d6:4a", "port": "A"},
    ],
}
```

3. Replace each `"mac"` value with the real ID you noted down in Step 9
   for that instrument's brick
4. The `"port"` value should match which port (A, B, C, or D) the motor
   is physically plugged into on that brick
5. Save the file (**Ctrl + S**)

**If one instrument has more than one motor** (e.g. a big instrument with
motors on both sides), just add another line inside its brackets, for example:
```python
"SARON": [
    {"mac": "00:16:53:41:95:2e", "port": "A"},
    {"mac": "00:16:53:41:95:2e", "port": "C"},
],
```

---

## Step 11: Run the app

In the terminal (making sure it still shows `(.venv)` at the start), type:
```
python main.py
```

A window should open showing the app.

---

## Step 12: Using the app

- **Connect EV3** - connects to all your bricks
- **Disconnect EV3** - disconnects everything
- **Check Battery** - shows each brick's battery level (check this before
  every use!)
- The colored list shows which instruments are currently connected
  (green = working, red = not connected)
- **Song Selection buttons** - plays a full song automatically
- **Instrument Control buttons** - manually plays one instrument, useful
  for testing

---

## Step 13: Using voice and gesture control (optional)

These are extra ways to control the app besides clicking buttons.

### Voice recognition

1. Click **Voice Recognition** in the app (the button turns red and says
   "Stop Voice Recognition" while it's listening - click it again, or
   say "EV3, stop listening," to turn it off).
2. Say a word close to **"EV3"** followed by your command, e.g.
   "Hey EV3, play gong" or "EV3, play drum."
3. Requires an internet connection to work.

**Note:** you only need to say something close to "EV3" plus your
command - words like "Hey" or "please" are just for natural phrasing and
aren't actually required by the app. "EV3 drum" works exactly the same
as "Hey EV3, please play the drum."

**Voice commands you can use:**
- Any instrument name (e.g. "gong", "saron", "drum")
- Any song name (e.g. "rasa sayang", "test motors")
- "connect" - connects to all EV3 bricks
- "disconnect" - disconnects all EV3 bricks
- "battery" or "check battery" - checks battery levels
- "stop song" or "stop music" - stops whatever song is currently playing
- "start gesture" - turns on gesture recognition
- "stop gesture" - turns off gesture recognition
- "stop listening" or "stop voice" - turns off voice recognition

**Note on response delay:** since voice commands are matched using
"fuzzy matching" (finding the closest known word to what was heard),
there's a small delay between speaking and the action happening -
usually well under a second, but noticeable. This is normal, not a bug.

**If you're setting this up on a new computer**, voice recognition may
not work correctly until you find the right microphone for that
computer. See `DOCUMENTATION.md` (Section 14) for how to do this using
the included `test_mic.py` script.

Honest warning: voice recognition is not perfectly reliable,
especially for non-English song names. It sometimes mishears words.
Gesture recognition (below) tends to work more consistently - use voice
mainly as a backup or demo feature, not something to depend on entirely.

### Gesture recognition

1. Click **Gesture Recognition** (the button turns red and says "Stop
   Gesture Recognition" while it's active - click it again, or say
   "EV3, stop gesture," to turn it off) - a webcam window will open.
2. Hold up fingers on your **right hand** to select an instrument
   (1 finger = 1st instrument, 2 fingers = 2nd, and so on, matching the
   order in `config.py`).
3. Hold up fingers on your **left hand** to select and play a song
   (1 finger = 1st song, 2 fingers = 2nd, and so on).
4. Make a **fist** with either hand to stop whatever song is playing.
5. Press **Q** with the webcam window focused to close the window (the
   app's Gesture Recognition button won't automatically update if you
   close it this way - use the button or a voice command instead for a
   cleaner stop).

If the webcam window doesn't appear but the camera light turns on, close
any other program that might be using your webcam (Zoom, Teams, browser
tabs with camera access) and try again.

Gesture recognition works best with decent, consistent lighting - very
dim or uneven lighting can make hand tracking less reliable.

---

## Things to watch out for

- **Only connect your EV3 bricks to Bluetooth using their normal LEGO
  settings.** Don't install any special software on them.
- **Check the battery before every use.** A low battery can cause the
  connection to behave strangely.
- **If reconnecting fails right after disconnecting**, wait a few seconds
  and try again - this is a normal EV3 quirk, not a mistake on your part.
- **If Bluetooth pairing keeps failing**, go to Windows Settings >
  Bluetooth & devices, remove the EV3 from the list, then pair it again
  from scratch. If it still won't cooperate, try a different physical
  brick if you have one available (see the note in Step 8).
- **Keep your EV3 bricks reasonably close to your computer.** Bluetooth
  range is limited, especially with walls or other obstacles in the way.
- **Voice and gesture recognition need their own hardware access.** Make
  sure no other app is using your microphone or webcam at the same time.

---

## If something isn't working

| Problem | What to try |
|---|---|
| "No EV3 device found" when reconnecting | Wait a few seconds after disconnecting before clicking Connect again |
| App freezes when checking battery | A brick may have disconnected - try reconnecting all bricks |
| Bluetooth pairing keeps failing | Remove the device in Windows Bluetooth settings, then pair again from scratch. Trying a different physical brick sometimes helps too |
| Motor doesn't move even though it says "Connected" | Double-check the port letter in `config.py` matches where the motor is actually plugged in |
| Gesture window doesn't open, but webcam light turns on | Close other apps using the webcam (Zoom, Teams, browser camera tabs), then try again |
| Voice recognition mishears commands often | This is a known limitation, especially for non-English song names - use gesture recognition instead for reliable control |
| Voice recognition doesn't seem to hear anything at all | You may be on a new computer - the microphone setting needs to be updated for this specific machine, see `DOCUMENTATION.md` Section 14 |