import cv2
import mediapipe as mp
import requests
import time

# ==========================
# Home Assistant Configuration
# ==========================
HA_URL = "ur HA URL "
TOKEN = "UR TOKEN"
ENTITY_ID = "UR ENTITY ID "

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# ==========================
# Light State
# ==========================
light_state = False
last_action_time = 0
CLICK_DELAY = 1.0  # seconds

# ==========================
# Home Assistant Functions
# ==========================
def turn_on():
    global light_state
    try:
        response = requests.post(
            f"{HA_URL}/api/services/switch/turn_on",
            headers=HEADERS,
            json={"entity_id": ENTITY_ID},
            timeout=5,
        )
        if response.status_code == 200:
            light_state = True
            print("Light ON")
        else:
            print("ON failed:", response.status_code, response.text)
    except Exception as e:
        print("Error ON:", e)

def turn_off():
    global light_state
    try:
        response = requests.post(
            f"{HA_URL}/api/services/switch/turn_off",
            headers=HEADERS,
            json={"entity_id": ENTITY_ID},
            timeout=5,
        )
        if response.status_code == 200:
            light_state = False
            print("Light OFF")
        else:
            print("OFF failed:", response.status_code, response.text)
    except Exception as e:
        print("Error OFF:", e)

# ==========================
# MediaPipe
# ==========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# ==========================
# Buttons
# ==========================
ON_BTN = (20, 400, 170, 470)
OFF_BTN = (220, 400, 370, 470)

def point_in_rect(point, rect):
    x, y = point
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2

# ==========================
# Main Loop
# ==========================
while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    finger_point = None

    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        index_tip = hand.landmark[8]  # INDEX_FINGER_TIP
        cx = int(index_tip.x * w)
        cy = int(index_tip.y * h)
        finger_point = (cx, cy)

        cv2.circle(frame, finger_point, 10, (255, 0, 255), -1)

        now = time.time()
        if now - last_action_time > CLICK_DELAY:
            if point_in_rect(finger_point, ON_BTN):
                turn_on()
                last_action_time = now
            elif point_in_rect(finger_point, OFF_BTN):
                turn_off()
                last_action_time = now

    # Button colors
    if light_state:
        on_color = (0, 255, 0)
        off_color = (60, 60, 60)
    else:
        on_color = (60, 60, 60)
        off_color = (0, 0, 255)

    # Draw buttons
    cv2.rectangle(frame, (ON_BTN[0], ON_BTN[1]), (ON_BTN[2], ON_BTN[3]), on_color, -1)
    cv2.rectangle(frame, (OFF_BTN[0], OFF_BTN[1]), (OFF_BTN[2], OFF_BTN[3]), off_color, -1)

    cv2.putText(frame, "LIGHT ON", (35, 440),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.putText(frame, "LIGHT OFF", (230, 440),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("Hand Tracking", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()