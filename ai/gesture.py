import threading
import cv2
import mediapipe as mp

# Landmark indices for fingertips and their corresponding lower joints
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]


class GestureController:
    """
    Uses the webcam + MediaPipe Hands (tracking BOTH hands at once) to detect:

    - RIGHT hand finger count (1-5) -> on_instrument_finger_count(count)
      Selects an instrument directly, same idea as clicking an instrument button.

    - LEFT hand finger count (1-5)  -> on_song_finger_count(count)
      Selects/plays a song directly (not next/previous - a direct pick,
      same idea as clicking a specific song button).

    - Fist on EITHER hand -> on_stop()
      Stops whatever song is currently playing.

    A gesture only fires ONCE per "hold" - i.e. holding the same finger
    count continuously (e.g. while a song keeps playing) will NOT keep
    re-triggering it. It only fires again once something changes: a
    different gesture is shown, or the hand is taken away and a gesture
    is shown again afterward.

    Runs in its own thread with its own OpenCV window, so it doesn't
    block the CustomTkinter GUI thread.
    """

    def __init__(self, on_instrument_finger_count=None, on_song_finger_count=None, on_stop=None):
        self.on_instrument_finger_count = on_instrument_finger_count
        self.on_song_finger_count = on_song_finger_count
        self.on_stop = on_stop

        self._running = False
        self._thread = None

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        # Tracks the last action fired PER HAND, so we only re-fire when
        # something actually changes (not on every frame the gesture is held).
        self._last_left_action = None
        self._last_right_action = None

        # Smooths out landmark jitter: a gesture must be read consistently
        # for several consecutive frames before it's accepted as real,
        # instead of reacting to every single frame (which flickers due to
        # natural camera/landmark noise even when your hand isn't moving).
        self._left_candidate = None
        self._left_candidate_count = 0
        self._right_candidate = None
        self._right_candidate_count = 0
        self._stability_threshold = 5  # frames needed before a gesture "counts"

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run_loop(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DirectShow backend - more reliable on Windows than the default

        if not cap.isOpened():
            print("ERROR: Could not open webcam at all (index 0). Check that no other app is using it.")
            self._running = False
            return

        failed_reads = 0

        hands = self.mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        while self._running:
            success, frame = cap.read()
            if not success:
                failed_reads += 1
                if failed_reads == 1:
                    print("Webcam opened, but no frame could be read yet - retrying...")
                if failed_reads == 30:
                    print("ERROR: Still can't read frames after many attempts. "
                          "Try closing other apps that might be using the webcam "
                          "(e.g. Zoom, Teams, browser tabs with camera access).")
                if failed_reads > 100:
                    print("Giving up on webcam - too many failed reads.")
                    break
                continue

            failed_reads = 0  # reset once a frame successfully comes through

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            seen_left = False
            seen_right = False

            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                    # Because the frame is flipped for a natural "mirror" view,
                    # MediaPipe's own left/right label ends up matching what
                    # the PERSON would call their own left/right hand.
                    label = handedness.classification[0].label  # "Left" or "Right"

                    landmarks = hand_landmarks.landmark
                    side = "right" if label == "Right" else "left"
                    finger_states = self._get_finger_states(landmarks, side)
                    count = sum(finger_states)
                    is_fist = not any(finger_states)

                    if label == "Right":
                        seen_right = True
                        self._handle_hand("right", is_fist, count)
                        text_y = 40
                    else:
                        seen_left = True
                        self._handle_hand("left", is_fist, count)
                        text_y = 80

                    label_text = f"{label} hand: {'FIST' if is_fist else count}"
                    cv2.putText(frame, label_text, (10, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # If a hand is no longer visible, reset its "last action" so the
            # same gesture can fire again fresh next time that hand reappears.
            if not seen_left:
                self._last_left_action = None
                self._left_candidate = None
                self._left_candidate_count = 0
            if not seen_right:
                self._last_right_action = None
                self._right_candidate = None
                self._right_candidate_count = 0

            cv2.putText(frame, "Right hand = instrument | Left hand = song | Fist = stop",
                        (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow("Gesture Control - press Q to close", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        self._running = False

    def _get_finger_states(self, landmarks, side):
        """
        Returns a list of 5 booleans: [thumb, index, middle, ring, pinky] extended or not.
        side: "left" or "right" - needed because the thumb splays in opposite
        x-directions for each hand, so the same simple comparison doesn't
        work for both without flipping it.
        """
        states = []

        # Thumb: compare x-position, direction depends on which hand this is
        if side == "right":
            states.append(landmarks[FINGER_TIPS[0]].x < landmarks[FINGER_PIPS[0]].x)
        else:
            states.append(landmarks[FINGER_TIPS[0]].x > landmarks[FINGER_PIPS[0]].x)

        # Other 4 fingers: tip above pip joint (lower y = higher on screen) means extended
        for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
            states.append(landmarks[tip].y < landmarks[pip].y)

        return states

    def _handle_hand(self, side, is_fist, count):
        """
        side: "left" or "right"
        Requires the gesture to read the same way for several consecutive
        frames (see _stability_threshold) before treating it as real -
        this filters out natural frame-to-frame jitter. Once stable, it
        only fires if it's DIFFERENT from the last action that was
        actually fired for this hand (so holding steady doesn't re-fire).
        """
        action_key = "fist" if is_fist else (f"count_{count}" if count > 0 else None)

        if side == "right":
            candidate, candidate_count = self._right_candidate, self._right_candidate_count
        else:
            candidate, candidate_count = self._left_candidate, self._left_candidate_count

        if action_key == candidate:
            candidate_count += 1
        else:
            candidate = action_key
            candidate_count = 1

        if side == "right":
            self._right_candidate, self._right_candidate_count = candidate, candidate_count
        else:
            self._left_candidate, self._left_candidate_count = candidate, candidate_count

        if candidate_count < self._stability_threshold:
            return  # not stable/consistent enough yet - wait for more frames

        last_action = self._last_right_action if side == "right" else self._last_left_action

        if action_key == last_action:
            return  # already fired this exact action - don't re-fire

        if side == "right":
            self._last_right_action = action_key
        else:
            self._last_left_action = action_key

        if action_key is None:
            return  # open hand / no clear gesture - nothing to do

        if is_fist:
            if self.on_stop:
                self.on_stop()
            return

        if side == "right" and self.on_instrument_finger_count:
            self.on_instrument_finger_count(count)
        elif side == "left" and self.on_song_finger_count:
            self.on_song_finger_count(count)