import cv2
import numpy as np
import mediapipe as mp
import screen_brightness_control as sbc
from math import hypot
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import pyautogui


def main():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol, maxVol, _ = volRange

    mpHands = mp.solutions.hands
    hands = mpHands.Hands(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.75,
        min_tracking_confidence=0.75,
        max_num_hands=2)

    draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = hands.process(frameRGB)

            left_landmark_list, right_landmark_list = get_left_right_landmarks(frame, processed, draw, mpHands)
            # Change brightness using left hand (In video it would appear as right hand as we are mirroring the frame)
            if left_landmark_list:
                left_distance = get_distance(frame, left_landmark_list)
                b_level = np.interp(left_distance, [50, 220], [0, 100])
                sbc.set_brightness(int(b_level))

            # Change volume using right hand (In video it would appear as left hand as we are mirroring the frame)
            if right_landmark_list:
                right_distance = get_distance(frame, right_landmark_list)
                vol = np.interp(right_distance, [50, 220], [minVol, maxVol])
                volume.SetMasterVolumeLevel(vol, None)

            # Capture screenshot when two palms are detected and the lines intersect
            if len(left_landmark_list) >= 2 and len(right_landmark_list) >= 2:
                if lines_intersect(left_landmark_list, right_landmark_list):
                    pyautogui.screenshot("screenshot.png")

            cv2.imshow('Image', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def get_left_right_landmarks(frame, processed, draw, mpHands):
    left_landmark_list = []
    right_landmark_list = []

    if processed.multi_hand_landmarks:
        for handlm in processed.multi_hand_landmarks:
            for idx, found_landmark in enumerate(handlm.landmark):
                height, width, _ = frame.shape
                x, y = int(found_landmark.x * width), int(found_landmark.y * height)
                if idx == 4 or idx == 8:
                    landmark = [idx, x, y]
                    if handlm == processed.multi_hand_landmarks[0]:
                        left_landmark_list.append(landmark)
                    elif handlm == processed.multi_hand_landmarks[1]:
                        right_landmark_list.append(landmark)

            draw.draw_landmarks(frame, handlm, mpHands.HAND_CONNECTIONS)

    return left_landmark_list, right_landmark_list


def get_distance(frame, landmark_list):
    if len(landmark_list) < 2:
        return
    (x1, y1), (x2, y2) = (landmark_list[0][1], landmark_list[0][2]), \
                         (landmark_list[1][1], landmark_list[1][2])
    cv2.circle(frame, (x1, y1), 7, (0, 255, 0), cv2.FILLED)
    cv2.circle(frame, (x2, y2), 7, (0, 255, 0), cv2.FILLED)
    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
    L = hypot(x2 - x1, y2 - y1)

    return L


def lines_intersect(left_landmark_list, right_landmark_list):
    # Check if the lines formed by the landmarks intersect
    (x1, y1), (x2, y2) = (left_landmark_list[0][1], left_landmark_list[0][2]), \
                         (left_landmark_list[1][1], left_landmark_list[1][2])
    (x3, y3), (x4, y4) = (right_landmark_list[0][1], right_landmark_list[0][2]), \
                         (right_landmark_list[1][1], right_landmark_list[1][2])

    # Calculate the determinant to check if lines are parallel
    det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if det == 0:
        return False  # Lines are parallel, no intersection

    # Calculate intersection point
    intersect_x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / det
    intersect_y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / det

    # Check if intersection point is within the range of the two lines
    if min(x1, x2) <= intersect_x <= max(x1, x2) and min(y1, y2) <= intersect_y <= max(y1, y2) and \
            min(x3, x4) <= intersect_x <= max(x3, x4) and min(y3, y4) <= intersect_y <= max(y3, y4):
        return True

    return False


if __name__ == '__main__':
    main()
