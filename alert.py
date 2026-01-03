import cv2
import mediapipe as mp
from playsound import playsound
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Email Configuration ---
SENDER_EMAIL = "vishnuwilsont@gmail.com"         # change this
APP_PASSWORD = "maduraiveeran#1"    # use Gmail App Password
RECEIVER_EMAIL ="230801241@rajalakshmi.edu.in"        # change this

# --- Mediapipe Setup ---
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

alert_playing = False
email_sent = False   # To avoid sending multiple emails while the hand stays raised

# --- Function to play alert sound ---
def play_alert():
    threading.Thread(target=playsound, args=("alert.mp3",), daemon=True).start()

# --- Function to send email ---
def send_email_alert():
    subject = "⚠️ Elder Alert: Hand Raised Detected!"
    body = "The elder person has raised their hand. Please check immediately."

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print("❌ Error sending email:", e)

# --- Open Camera ---
cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty frame.")
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = hands.process(image_rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                wrist_y = hand_landmarks.landmark[0].y
                finger_tip_y = hand_landmarks.landmark[12].y

                # Hand raised condition
                if finger_tip_y < wrist_y - 0.2:
                    cv2.putText(image, "HAND RAISED - ALERT!", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    if not alert_playing:
                        play_alert()
                        alert_playing = True

                    if not email_sent:
                        threading.Thread(target=send_email_alert, daemon=True).start()
                        email_sent = True
                else:
                    cv2.putText(image, "No Alert", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    alert_playing = False
                    email_sent = False
        else:
            cv2.putText(image, "No Hand Detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            alert_playing = False
            email_sent = False

        cv2.imshow('Elder Gesture Alert System', image)

        if cv2.waitKey(5) & 0xFF == 27:  # press ESC to exit
            break

cap.release()
cv2.destroyAllWindows()
