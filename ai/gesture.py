import threading
import time
import cv2
import mediapipe as mp

# Landmark indices for fingertips and their corresponding lower joints
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]


class GestureController:
    """
    Uses the webcam + MediaPipe Hands to detect:
    - Finger count (0-5) -> passed to on_finger_count(count)
    - Fist (0 fingers held briefly)  -> on_stop()
    - Thumbs up                       -> on_next()
    - Thumbs down                     -> on_previous()

    Runs in its own thread with its own OpenCV window, so it doesn't
    block the CustomTkinter GUI thread.
    """

    def __init__(self, on_finger_count=None, on_stop=None, on_next=None, on_previous=None):
        self.on_finger_count = on_finger_count
        self.on_stop = on_stop
        self.on_next = on_next
        self.on_previous = on_previous

        self._running = False
        self._thread = None

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        # Debounce so a single gesture doesn't fire the same command 30x/sec
        self._last_action = None
        self._last_action_time = 0
        self._debounce_seconds = 1.5

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
            max_num_hands=1,
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

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                landmarks = hand_landmarks.landmark
                finger_states = self._get_finger_states(landmarks)
                count = sum(finger_states)

                gesture = self._classify_gesture(finger_states, landmarks)
                self._trigger(gesture, count)

                cv2.putText(frame, f"Fingers: {count}", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if gesture:
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)

            cv2.imshow("Gesture Control - press Q to close", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        self._running = False

    def _get_finger_states(self, landmarks):
        """Returns a list of 5 booleans: [thumb, index, middle, ring, pinky] extended or not."""
        states = []

        # Thumb: compare x-position (works for a right hand facing the camera)
        states.append(landmarks[FINGER_TIPS[0]].x < landmarks[FINGER_PIPS[0]].x)

        # Other 4 fingers: tip above pip joint (lower y = higher on screen) means extended
        for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
            states.append(landmarks[tip].y < landmarks[pip].y)

        return states

    def _classify_gesture(self, finger_states, landmarks):
        thumb, index, middle, ring, pinky = finger_states

        # Fist: all fingers closed
        if not any(finger_states):
            return "stop"

        # Thumbs up: only thumb extended, and thumb tip is above the wrist
        if thumb and not any([index, middle, ring, pinky]):
            if landmarks[4].y < landmarks[0].y:
                return "next"
            else:
                return "previous"

        return None  # otherwise, treat as a plain finger-count gesture

    def _trigger(self, gesture, count):
        now = time.time()

        action_key = gesture if gesture else f"count_{count}"
        if action_key == self._last_action and (now - self._last_action_time) < self._debounce_seconds:
            return  # debounce: same gesture held, don't refire yet

        self._last_action = action_key
        self._last_action_time = now

        if gesture == "stop" and self.on_stop:
            self.on_stop()
        elif gesture == "next" and self.on_next:
            self.on_next()
        elif gesture == "previous" and self.on_previous:
            self.on_previous()
        elif gesture is None and count > 0 and self.on_finger_count:
            self.on_finger_count(count)