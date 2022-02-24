import cv2
import cv2 as cv
import imutils
import mediapipe as mp
import time
import numpy as np


# this is the module for hand detcter and its setting
class Handdetector():
    def __init__(self, mode=False, maxhands=2, complexity=1, detconfi=0.5, trackconfi=0.5):
        self.mode = mode
        self.maxhands = maxhands
        self.complexity = complexity
        self.detconfi = detconfi
        self.trackconfi = trackconfi
        self.mphands = mp.solutions.hands
        self.hands = self.mphands.Hands(self.mode, self.maxhands, self.complexity,
                                        self.detconfi, self.trackconfi)
        self.mydraw = mp.solutions.drawing_utils

    # this function used to find the hands
    def findhands(self, img, draw=True):
        imgrgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.results = self.hands.process(imgrgb)
        if self.results.multi_hand_landmarks:
            for hand in self.results.multi_hand_landmarks:
                if draw:
                    self.mydraw.draw_landmarks(img, hand, self.mphands.HAND_CONNECTIONS)
        return img

    # this function gather the x,y informations of the key components of hands
    def findpos(self, img, handno=0, draw=True):
        lmlist = []
        if self.results.multi_hand_landmarks:
            hand = self.results.multi_hand_landmarks[handno]
            for id, lm in enumerate(hand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmlist.append([id, cx, cy])
                if draw:
                    cv.circle(img, (cx, cy), 5, (255, 0, 255), cv.FILLED)
        return lmlist

    # this function find the location of index finger
    def forefinger(self, gelenke, img):
        for top in gelenke:
            if top[0] == 8:
                cv.circle(img, (top[1], top[2]), 5, (0, 255, 255), cv.FILLED)
                return (top[1], top[2])
    # it used to detect the defined gestures
    def gesturedet(self, gelenke, img):
        c = 4
        # gesture used to gather the key componets of hands i need to be the gesture
        gesture = []

        for top in gelenke:
            if top[0] % c == 0 and top[0] != 0:  # this is actually the fingertips
                gesture.append((top[1], top[2]))
                cv.circle(img, (top[1], top[2]), 5, (0, 255, 255), cv.FILLED)
        # two gestures defined :gesture[1] is index finger and gesture[2] is middle finger
        if np.abs(gesture[1][1] - gesture[2][1]) <= 15:#when the distance between two finger tips less than 15 pixel then
            cv.putText(img, "split horizon", (90, 90), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 0), 3)
            center_X, center_y = (gesture[1][0] + gesture[2][0]) // 2, (gesture[1][1] + gesture[2][1]) // 2
            cv.circle(img, (center_X, center_y), 5, (255, 255, 0), cv.FILLED)
            return 1
        if np.abs(gesture[1][0] - gesture[2][0]) <= 15:
            cv.putText(img, "split vertical", (90, 90), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 0), 3)
            center_X, center_y = (gesture[1][0] + gesture[2][0]) // 2, (gesture[1][1] + gesture[2][1]) // 2
            cv.circle(img, (center_X, center_y), 5, (255, 255, 0), cv.FILLED)
            return 2
    # here is the painter
    def paint(self, gelenke, img, pen):
        for top in gelenke:
            if top[0] == 8:
                pen.append([top[1], top[2]]) #location of index finger
        if len(pen) >= 2:  # the color can change with the movement of finger ,These three values can be modified by the user
            for i in range(len(pen)):
                thick = i % 8 + 1
                col1 = i % 255
                col2 = (i + 50) % 255
                col3 = (i + 100) % 255
                if i > 0:
                    cv.line(img, pen[i - 1], pen[i], (col1, col2, col3), thick)
        return pen


# default main function is finger painter
    def painter(self,widt = 960,hei = 540):
        ptime = 0
        cap = cv.VideoCapture(0)
        det = Handdetector()
        pen = []
        while True:
            sucess, img = cap.read()
            img = imutils.resize(img, width=widt, height=hei)
            det.findhands(img, draw=False)
            gelenke = det.findpos(img, draw=False)
            det.paint(gelenke, img, pen)

    #record the fps of video
            ctime = time.time()
            fps = 1 / (ctime - ptime)
            ptime = ctime
            cv.putText(img, str(int(fps)), (37, 37), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
            cv.imshow("img", img)
            cv.waitKey(1)


if __name__ == "__main__":
    Hand = Handdetector()
    Hand.painter()
