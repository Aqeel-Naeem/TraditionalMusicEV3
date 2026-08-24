You are working on my existing TraditionalMusicEV3 project.

IMPORTANT: This is an existing university internship / robotics competition project. The current system already works, so reliability and minimal changes are more important than architectural perfection.

I have attached a project roadmap/handoff document. Treat it as the project's agreed direction and constraints.

Your job is to help me implement the roadmap incrementally WITHOUT unnecessarily rewriting the existing project.

==================================================
CORE PRINCIPLE
==================================================

One shared controller, multiple interfaces.

Existing:
- CustomTkinter desktop GUI
- EV3 control
- Multiple EV3 bricks
- Bluetooth connections
- Song playback
- Voice control
- Gesture control
- Connection/health monitoring

Future:
- Local phone/tablet web controller
- QR code for joining the web controller
- Optional activity feed
- Optional multi-phone support
- Experimental EV3 Wi-Fi
- Remote Internet control is currently OUT OF SCOPE

==================================================
CRITICAL RULES
==================================================

1. DO NOT rewrite the project architecture unless there is a concrete technical reason.

2. DO NOT replace Bluetooth merely because Wi-Fi or another approach may be theoretically better.

3. DO NOT switch to Pybricks or ev3dev.

4. The EV3 bricks currently use STOCK LEGO FIRMWARE.

5. Do not modify working functionality unless the requested feature requires it.

6. Before modifying a file, inspect only the relevant parts of the repository.

7. Do not repeatedly reread the entire repository after you already understand the relevant files.

8. Prefer small, isolated changes.

9. Do not add dependencies unless they are actually required.

10. Do not implement future/optional features early.

11. Do not refactor just for "clean code" if the current code works.

12. Preserve existing song timing, EV3 connection behavior, health checking, voice control, gesture control, and GUI behavior unless the current task specifically concerns them.

13. Before making a significant change, explain briefly:
   - what you found
   - what you plan to change
   - which files will change
   - why the change is necessary

14. Do not make changes outside the requested scope.

15. If you discover a potentially useful improvement that is outside scope, mention it briefly at the end instead of implementing it.

==================================================
CURRENT PRIORITY
==================================================

The current priority is to stabilize EV3 control before adding the phone controller.

I recently discovered that controlling 5–7 EV3 bricks over Bluetooth can introduce enough command delay to make synchronized song playback unreliable.

Therefore:

FIRST:
Investigate and solve the EV3 timing/communication problem.

DO NOT start implementing the phone controller until the existing EV3 musical timing is sufficiently reliable.

==================================================
LOCAL EV3 EXECUTION EXPERIMENT
==================================================

We are investigating whether a song can be converted into per-EV3 timelines and executed locally by the stock EV3 firmware.

Concept:

Laptop
  ↓
Send prepared timeline/program
  ↓
EV3
  ↓
EV3 executes timing locally
  ↓
Motors

The goal is to reduce the need for the laptop to continuously send time-sensitive commands over Bluetooth.

IMPORTANT:
This is experimental.

Do NOT modify the production song system yet.

Use a separate proof-of-concept file for experiments.

Do NOT send experimental bytecode to all 7 EV3s until the single-EV3 experiment is proven safe and correct.

If an experiment behaves unexpectedly, stop and diagnose it rather than repeatedly trying random bytecode variations.

Verify the exact ev3_dc API/documentation/source before relying on low-level bytecode behavior.

==================================================
7-EV3 CONFIGURATION
==================================================

The intended project configuration contains 7 physical EV3 bricks.

Do not artificially redesign the configuration around 5 bricks.

However, testing should progress safely:

1 EV3
→ multiple motors / more complex timeline
→ 2–3 EV3s
→ full 7 EV3 system

The final goal is reliable operation with all 7 configured bricks.

==================================================
EXISTING EV3 IMPLEMENTATION
==================================================

The project currently uses:
- Python
- CustomTkinter
- ev3_dc
- stock LEGO EV3 firmware
- Bluetooth
- per-brick worker/queue architecture
- song scheduling
- voice recognition
- gesture recognition

Inspect the actual repository before making assumptions about implementation details.

Do not assume that an architecture described in this prompt exactly matches the current code.

The repository is the source of truth for implementation details.

==================================================
PHONE CONTROLLER — AFTER EV3 STABILITY
==================================================

Once EV3 control is reliable, implement the local phone controller.

Preferred architecture:

Desktop CustomTkinter
        +
      Flask
        ↓
Shared existing controller/state
        ↓
      EV3 bricks

The laptop remains the device responsible for EV3 connections.

The phone should NOT directly connect to the EV3.

Initial phone interface:
- connection status
- current song
- instrument controls
- song controls
- stop
- battery/status information

Use:
- Flask
- HTML
- CSS
- JavaScript
- fetch()

Do NOT introduce React, TypeScript, WebSockets, or a frontend build system unless there is a demonstrated need.

Start with simple HTTP endpoints and approximately 2-second status polling.

Be careful with Tkinter threading:
- Flask runs separately
- Do not manipulate Tkinter widgets directly from Flask's background thread
- Use the existing application's safe GUI update mechanism where necessary

Before implementation, inspect the actual threading behavior of the current repository.

==================================================
QR CODE — LATER
==================================================

After the phone controller works:

Add a "Show QR Code" / "Generate QR" feature.

The QR should point to the laptop's local Flask URL, for example:

http://192.168.x.x:5000

The QR is only a convenience for opening the browser.

It does NOT connect the phone directly to the EV3.

==================================================
MULTIPLE PHONES — LATER
==================================================

Multiple phones may be able to open the web interface.

However, do NOT immediately build:
- complex command queues
- user roles
- permissions
- conflict-resolution systems
- authentication infrastructure

Start simple.

Only add multi-user synchronization/locking if actual testing shows it is necessary.

==================================================
ACTIVITY FEED — OPTIONAL
==================================================

The terminal currently provides detailed technical information.

Eventually, add a simple user-facing Activity feed.

Terminal:
- detailed developer/debug information

Activity:
- meaningful user actions

Examples:
- Phone A started a song
- Desktop triggered Gong
- EV3 #2 connected
- Song stopped
- Voice command recognized

Do not expose every low-level motor packet in the user-facing Activity feed.

A lightweight in-memory recent-event list is sufficient initially.

==================================================
WI-FI
==================================================

EV3 Wi-Fi is experimental and NOT a current priority.

The EV3 stock firmware requires supported Wi-Fi hardware.

If Wi-Fi is tested:
- use one EV3 first
- use a controlled network
- time-box the experiment
- compare reliability against Bluetooth

Do not let Wi-Fi experimentation delay the phone controller or destabilize Bluetooth.

==================================================
REMOTE INTERNET CONTROL
==================================================

OUT OF SCOPE.

Do not implement Internet-based remote EV3 control unless I explicitly request it later.

==================================================
WORKFLOW
==================================================

For each task:

1. Inspect only the relevant code.
2. Explain what you found briefly.
3. Propose the smallest safe change.
4. Wait for my approval if the change is significant.
5. Implement the change.
6. Run/describe the relevant test.
7. Report exactly:
   - files changed
   - what changed
   - how to test
   - expected result
   - any remaining issue

Do not automatically proceed into the next phase after completing a task.

==================================================
IMPORTANT USER PREFERENCE
==================================================

I am relatively new to some of the deeper software architecture involved in this project.

Therefore, when giving instructions:
- Be concise.
- Give exact commands.
- Tell me exactly what file to modify.
- If code needs to change, provide the complete replacement code when practical.
- Clearly label whether I should RUN or WAIT.
- Do not assume I will infer the next step from a long explanation.

At the end of every response, include:

WHAT YOU DO NEXT
1. ...
2. ...
3. ...

And make it unambiguous whether I should run something now or wait.

==================================================
FINAL GOAL
==================================================

The final project should be:

- reliable
- competition-friendly
- maintainable
- simple to operate
- capable of controlling the configured 7 EV3 bricks
- able to play songs with reliable timing
- controllable from the existing desktop GUI
- eventually controllable from phones on the same local network

Most importantly:

DO NOT sacrifice a currently working feature just to create a theoretically cleaner architecture.

Build the smallest reliable solution that solves the actual problem.