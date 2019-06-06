import cv2
import numpy as np

from music import play_thread, freq


class Channel:
    def __init__(self, channel, color=(0, 0, 0)):
        self.channel = channel
        self.color = color
        self.thread = play_thread(440, 0.0, channel)


def check_color(image, num):
    py = len(image) // 2
    px = len(image[0]) // 2
    color = image[py][px]
    color = (int(color[0]), int(color[1]), int(color[2]))

    cv2.circle(image, (px, py), 0, (0, 0, 0), 2)
    cv2.circle(image, (px, py), 10, (0, 0, 0), 7)
    cv2.circle(image, (px, py), 10, color, 5)

    font = cv2.FONT_HERSHEY_SIMPLEX
    text = 'ch: {}; rgb: {}'.format(num, color)
    cv2.putText(image, text, (px + 20, py + 5), font, 0.5, (0, 255, 0), 1)

    return color


def get_mask(image, color):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV_FULL)

    color = [[color]]
    color = np.array(color, dtype="uint8")
    color = cv2.cvtColor(color, cv2.COLOR_RGB2HSV_FULL)[0][0]
    c0, c1, c2 = color
    lower = [c0 - 15, c1 - 50 if c1 - 50 > 10 else 10, c2 - 80 if c2 - 80 > 10 else 10]
    upper = [c0 + 15, c1 + 50 if c1 + 50 < 245 else 245, c2 + 80 if c2 + 80 < 245 else 245]

    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")

    mask = cv2.inRange(hsv_image, lower, upper)
    return mask


def find_contours(image, color):
    def marker_fun(img):
        pass

    mask = get_mask(image, color)
    _, thresh = cv2.threshold(mask, 70, 255, 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pitch = 0

    if len(contours) != 0:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        px = x + w // 2
        py = y + h // 2

        def marker_fun(img):
            cv2.circle(img, (px, py), 5, (0, 255, 0), 3)

        pitch = get_pitch((px, py), (len(image[0]), len(image)))

    return marker_fun, pitch


def add_grid(image, hor=(), ver=(), color=(0, 0, 0)):
    x_max = len(image[0])
    y_max = len(image)

    num_hor = len(hor)
    num_ver = len(ver)

    if num_hor > 0:
        w = x_max / num_hor
        for i, label in enumerate(hor):
            x = i * w
            x1 = int(x)
            x2 = int(x + w)
            cv2.rectangle(image, (x1, 0), (x2, y_max - 1), color, 1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(image, label, (x1 + 20, 10), font, 0.4, color, 1)

    if num_ver > 0:
        h = y_max / num_ver
        for i, label in enumerate(ver):
            y = i * h
            y1 = int(y)
            y2 = int(y + h)
            cv2.rectangle(image, (0, y1), (x_max - 1, y2), color, 1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(image, label, (0, y1 + 30), font, 0.4, color, 1)


def get_pitch(cur, max):
    x = cur[0] / max[0]
    y = cur[1] / max[1]
    octave = int(x * 12)
    note = int(y * 12)
    pitch = octave * 12 + note - 69
    return pitch


def step(img, mode, t, color):
    return img, mode, t, color


def show_webcam(mirror=False, primitive_channels=(1, 2)):
    mode = 'check'
    check_counter = 0

    channels = []
    for ch in primitive_channels:
        channel = Channel(ch)
        channels.append(channel)

    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while True:
        ret_val, img = cam.read()
        if mirror:
            img = cv2.flip(img, 1)

        if mode == 'check':
            color = check_color(img, check_counter)
            channels[check_counter].color = color

        if mode == 'play':
            for ch in channels:
                marker_fun, pitch = find_contours(img, ch.color)
                ch.marker_fun = marker_fun
                ch.pitch = pitch

            ver = ('a', 'a#', 'b', 'c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#')
            hor = ('-1', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10')
            add_grid(img, ver=ver, hor=hor, color=(0, 255, 0))
            for ch in channels:
                ch.marker_fun(img)
                print(ch.thread)
                if not ch.thread.is_alive():
                    print(ch.thread)
                    ch.thread.join()
                    ch.thread = play_thread(freq(ch.pitch), 0.5, ch.channel)

        cv2.imshow('cam', img)
        if cv2.waitKey(1) == 13:  # enter
            check_counter += 1
            if check_counter >= len(channels):
                mode = 'play'
        if cv2.waitKey(1) == 27:  # esc
            for ch in channels:
                ch.thread.join()
            break
    cv2.destroyAllWindows()


if __name__ == '__main__':
    show_webcam(mirror=True)