import cv2
import numpy as np
import math

# Classic black stick-figure hero animation
W, H = 720, 720
FPS, SECONDS = 30, 6
OUT = "stick_figure_hero.mp4"

def point(cx, cy, length, angle):
    return (int(cx + length * math.cos(angle)), int(cy + length * math.sin(angle)))

def draw_line(img, a, b, width=9):
    cv2.line(img, a, b, (15, 15, 15), width, cv2.LINE_AA)

def draw_hero(img, x, y, t):
    # A gentle run-in-place followed by a heroic raised-fist pose
    phase = t * 2 * math.pi * 1.6
    running = t < 3.8
    bob = 9 * math.sin(phase * 2) if running else 0
    head = (int(x), int(y - 190 + bob))
    cv2.circle(img, head, 37, (15, 15, 15), 8, cv2.LINE_AA)

    shoulder = (int(x), int(y - 145 + bob))
    hip = (int(x), int(y - 35 + bob))
    draw_line(img, shoulder, hip, 10)

    if running:
        arm_swing = 0.85 * math.sin(phase)
        left_elbow = point(*shoulder, 66, math.pi/2 + arm_swing)
        left_hand = point(*left_elbow, 58, math.pi/2 - arm_swing)
        right_elbow = point(*shoulder, 66, math.pi/2 - arm_swing + math.pi)
        right_hand = point(*right_elbow, 58, math.pi/2 + arm_swing + math.pi)
        leg_swing = 0.8 * math.sin(phase)
        left_knee = point(*hip, 76, math.pi/2 + leg_swing)
        left_foot = point(*left_knee, 75, math.pi/2 - leg_swing*0.7)
        right_knee = point(*hip, 76, math.pi/2 + math.pi - leg_swing)
        right_foot = point(*right_knee, 75, math.pi/2 + math.pi + leg_swing*0.7)
    else:
        # Hero pose: one fist raised, the other hand on the hip
        left_elbow = (x - 68, y - 190)
        left_hand = (x - 102, y - 235)
        right_elbow = (x + 62, y - 75)
        right_hand = (x + 105, y - 95)
        left_knee, left_foot = (x - 45, y + 45), (x - 72, y + 125)
        right_knee, right_foot = (x + 45, y + 45), (x + 70, y + 125)

    draw_line(img, shoulder, left_elbow)
    draw_line(img, left_elbow, left_hand)
    draw_line(img, shoulder, right_elbow)
    draw_line(img, right_elbow, right_hand)
    draw_line(img, hip, left_knee)
    draw_line(img, left_knee, left_foot)
    draw_line(img, hip, right_knee)
    draw_line(img, right_knee, right_foot)

    # Small fist circles and a simple heroic chest badge
    cv2.circle(img, left_hand, 10, (15, 15, 15), -1, cv2.LINE_AA)
    cv2.circle(img, right_hand, 10, (15, 15, 15), -1, cv2.LINE_AA)
    cv2.circle(img, (x, y - 110 + int(bob)), 12, (15, 15, 15), 3, cv2.LINE_AA)

def main():
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUT, fourcc, FPS, (W, H))
    if not writer.isOpened():
        raise RuntimeError("Could not open MP4 writer. Check that OpenCV video codecs are installed.")

    total = FPS * SECONDS
    for i in range(total):
        t = i / FPS
        frame = np.full((H, W, 3), 255, dtype=np.uint8)

        # Ground line and subtle motion marks
        cv2.line(frame, (70, 590), (650, 590), (210, 210, 210), 2, cv2.LINE_AA)
        if t < 3.8:
            for j in range(3):
                sx = int(225 + ((i * 13 + j * 85) % 260))
                cv2.line(frame, (sx, 490 + j*12), (sx-28, 490 + j*12),
                         (190, 190, 190), 3, cv2.LINE_AA)

        draw_hero(frame, 360, 420, t)

        title = "THE STICK HERO" if t >= 3.8 else "A HERO IS RISING..."
        cv2.putText(frame, title, (130, 90), cv2.FONT_HERSHEY_SIMPLEX,
                    1.15, (20, 20, 20), 3, cv2.LINE_AA)
        if t >= 3.8:
            cv2.putText(frame, "READY FOR ACTION!", (190, 650),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (40, 40, 40), 2, cv2.LINE_AA)

        writer.write(frame)

    writer.release()
    print(f"Created: {OUT}")

if __name__ == "__main__":
    main()
