# Handoff Note: Master Brick Connection - Ready for the Relay Program

## What's done (my part)

The PC app can connect to a single EV3 brick and start a program already
downloaded to it - confirmed working end-to-end, no motor required on
the PC side at all.

**Test it yourself:** run `python main.py`, click Connect, then click
"Rasa Sayang" or "Top Spinner" in Song Selection - both are real,
working examples right now.

## The one thing you need to know: `PROGRAM_ONLY_BRICKS`

In `config.py`, there's now a list specifically for bricks with no
motors attached - just for running a downloaded program:

```python
PROGRAM_ONLY_BRICKS = [
    "00:16:53:41:90:6e",  # master coordinator brick (Rasa Sayang relay)
]
```

This is separate from `INSTRUMENTS`/`POSITIONED_INSTRUMENTS` (which are
for bricks with actual motors). The app connects to any brick listed
here without trying to set up any motor for it - exactly what you need
for the master brick.

## What you need to do

1. Build your relay program (the one that runs on the master brick and
   talks to the other 7 "servant" bricks over its own Bluetooth) and
   download it to the master brick.
2. Find its exact file path:
   ```
   python test/list_ev3_files.py <master_brick_mac>
   ```
   then again with the folder shown, to see the exact file inside.
   **Names are case-sensitive** - always confirm this way, never guess.
3. Update the "Rasa Sayang" entry in `ev3_program_config.py` to point at
   your real file instead of the placeholder one currently there:
   ```python
   PROGRAMS = {
       "Rasa Sayang": {
           "00:16:53:41:90:6e": "<your real file's exact path>",
       },
   }
   ```
   If your relay program has a different name, rename the key too - the
   Song Selection button generates itself automatically from whatever's
   in `PROGRAMS`, no other code changes needed.
4. That's it - run the app, click Connect, click the button. The
   Activity Panel (left side of the window) will show you exactly
   what's happening at each step if anything goes wrong.

## Other things worth knowing

- **`SHOW_INSTRUMENT_SECTIONS = False`** in `gui.py` currently hides the
  instrument status grid and manual instrument buttons, since no
  instruments are configured right now. If your relay setup means the
  PC never needs to know about individual instruments/motors at all,
  you can leave this as-is permanently. If you want that UI back later
  for some other reason, just flip it to `True`.
- **Switching songs mid-play now correctly stops the old one first** -
  clicking a different Song Selection button while one is running sends
  a stop command before starting the new one, so they don't conflict.
- **The Stop button and voice/gesture stop commands** (fist gesture,
  saying "EV3, stop") all work against whatever's currently running,
  including your relay program once it's wired in.
- Full technical details (architecture history, why things are built
  this way) are in `DOCUMENTATION.md` if you want the deeper context.
