# TraditionalMusicEV3

## Project

This is a Python application for controlling LEGO Mindstorms EV3 bricks and
motors that perform traditional music on instruments such as gong, saron, and
drum.

## Current architecture

- `main.py` starts the CustomTkinter application in `gui.py`.
- `gui.py` owns the user interface, application state, song threads, voice and
  gesture controllers, and periodic status/health updates.
- `ev3.py` is the hardware boundary. It uses `ev3_dc` Bluetooth connections,
  reuses one connection per unique brick MAC address, maps configured ports to
  motors, and supports multiple motors per instrument.
- `config.py` maps instrument names to EV3 brick MAC addresses and motor ports.
- `songs.py` contains song note data and beat-based playback scheduling.
- `ai/voice.py` provides wake-word speech recognition in a background thread.
- `ai/gesture.py` provides MediaPipe/OpenCV hand-gesture recognition in a
  background thread.
- `README.md` contains setup and user instructions; `DOCUMENTATION.md`
  explains implementation details and design decisions.
- `test/` contains manual, hardware-dependent diagnostic scripts rather than
  an automated unit-test suite.

## Current capabilities

- Bluetooth control of multiple EV3 bricks and motors.
- Manual instrument strikes and timed song playback.
- Per-note motor direction in `songs.py`: direction may be `"clockwise"` or
  `"counterclockwise"`; omitted direction defaults to `"clockwise"`.
- `ev3.py` translates those names to the `ev3_dc` values `1` and `-1`.
- Voice and gesture control are implemented and must remain functional.
- Cross-platform web access is not implemented yet. The approved future
  direction is a responsive local website hosted by the PC, with the PC
  retaining the EV3 Bluetooth connection. A Raspberry Pi may become a later
  deployment target, but is not currently required.

## Important rules

- Do not rewrite or remove working EV3 communication code unless necessary.
- Do not break existing CustomTkinter, voice, gesture, or song functionality.
- Do not make changes until the user approves the proposed files and approach.
- When proposing changes, explain what will change, which files will be
  modified, and how existing functionality will be preserved.
- Before changing the architecture, explain the proposed approach first.
- Prefer small, testable changes and reuse existing modules before creating
  new ones.
- Keep hardware-specific code separate from GUI and future web-interface code.
- Preserve backwards-compatible defaults. In particular, calls to
  `EV3.send_command()` without a direction must retain the default clockwise
  behavior.
- Do not commit unrelated files such as local instruction files, generated
  files, or user-specific configuration unless explicitly requested.

## Development workflow

Before making a significant change:

1. Inspect the existing implementation and repository status.
2. Explain the relevant architecture and proposed approach.
3. Identify the exact files that need modification.
4. Wait for user approval before editing.
5. Make the smallest reasonable change.
6. Run available syntax checks, tests, or hardware-safe diagnostics.
7. Review the diff for unrelated changes.
8. Explain what changed and any verification limitations.

## Future web-controller direction

The intended cross-device design is:

```text
PC browser / phone / tablet -> local web server on PC -> existing ev3.py -> EV3
```

The PC-hosted server should reuse `ev3.py` and `songs.py` rather than
duplicating Bluetooth logic. The existing desktop GUI should remain available
until the web interface has feature parity and has been tested. A standard
browser is an interface only; it should not connect directly to the EV3.


## Project phases

### Phase 1 — Demo-ready desktop controller

The current phase focuses on reliable EV3 operation through the existing
CustomTkinter desktop application, including manual instruments, songs,
voice control, gesture control, status checks, and per-note motor direction.

### Phase 2 — Phone and tablet integration

The planned next phase is a responsive local website hosted by the PC.
Phones and tablets will connect through Wi-Fi, while the PC continues to
own the existing EV3 Bluetooth connection. The desktop GUI and hardware
logic should remain functional during this transition.