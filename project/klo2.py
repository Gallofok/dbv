"""
by wenchen refrence from OpenCVT
"""
import numpy as np
import time
import openCVTools as cvt
import cv2 as cv
import rtfun
import imutils
import os
import cartoon
import graffiti

#set the working path，this code only used when you want to run klo2 directly
# workingpath = os.getcwd()
# path_parent = os.path.dirname(workingpath)
# new_workingpath = os.chdir(path_parent)

# rect must cover the excavated object this value can be set according to different situations.
def applyGrabCut(img, rect = (30, 30, 550, 300), itera=5):
    mask = np.zeros(img.shape[:2], dtype=np.uint8)

    # setup the GMM for fore and background
    fgmodel = np.zeros((1, 65), dtype=np.float64)
    bgmodel = np.zeros((1, 65), dtype=np.float64)

    # apply GrabCut using the previously defined BBox (rect)
    start = time.perf_counter()
    (mask, bgmodel, fgmodel) = cv.grabCut(img, mask, rect, bgmodel, fgmodel, iterCount=itera, mode=cv.GC_INIT_WITH_RECT)
    duration = time.perf_counter() - start
    print(f"GrabCut took {duration:.2f} seconds.")

    # the output mask has four possible output values, marking each pixel
    # in the mask as definite background, definite foreground,
    # probable background, or probable foreground
    values = (("Definite Background", cv.GC_BGD),
              ("Probable Background", cv.GC_PR_BGD),
              ("Definite Foreground", cv.GC_FGD),
              ("Probable Foreground", cv.GC_PR_FGD))
    # create the resulting mask by setting everything that's background or probable background to black and
    # everything else to white
    outputmask = np.where((mask == cv.GC_BGD) | (mask == cv.GC_PR_BGD), 0, 255).astype(np.uint8)
    # show the resulting mask along with each of the individual GrabCut mask labels ((probable) foreground/background)
    imglist = [("Output Mask", outputmask, (1, 2))]
    for label, value in values:
        valueMask = (mask == value)
        imglist.append((label, valueMask))
    # _, _, masksFig = cvt.showImageList("Masks", imglist, 3, width_ratios = (2, 1, 1), show_window_now = False)
    # masksFig.set_facecolor("gray")
    # generate final output image by bitwise AND between image and mask
    output = cv.bitwise_and(img, img, mask=outputmask)
    return output

# this method be used to crop the forground image from a video
def cropthematerial(material='resources/videoplayback 9s.mp4'):
    vc = cv.VideoCapture(material)
    fourcc = cv.VideoWriter_fourcc(*'XVID')
    frame_width = int(vc.get(3))
    frame_height = int(vc.get(4))
    #fourcc = cv.VideoWriter_fourcc('M','J','P','G')
    out = cv.VideoWriter('resources/material.mp4', fourcc, 20.0, (frame_width, frame_height))  # the output video
    while vc.isOpened():
        ret, frame = vc.read()
        # this is very specific and important values , you should set a proprate rect for a pic
        #rec = (287, 30, 566, 470)#wolf
        #rec = (253,280,350,280)#eve
        rec = (100, 80, 680, 340) #dinosaur
        frame = applyGrabCut(frame, rect=rec)
        cv.imshow('j', frame)
        out.write(frame)
        if cv.waitKey(1) == ord('q'):
            break
    vc.release()
    out.release()
    cv.destroyAllWindows()


# this method get the position where the mouse click
def locatedthegraff(event, x, y, flags, param):
    global posx, posy
    if event == cv.EVENT_LBUTTONDOWN:
        posx, posy = x, y


# def setmaterbg(background='kongfu.mp4'):
#     global posx,posy
#     posx,posy = 0,0
#     material = 'material.mp4'
#     vc = cv.VideoCapture(background)
#     vd = cv.VideoCapture(material)
#     while vc.isOpened():
#         ret, frame = vc.read()
#         rowgrenz,colgrenz ,_ = frame.shape
#         if vd.isOpened():
#             ret2, frame2 = vd.read()
#             rows, cols, channels = frame2.shape
#             # frame2 = frame2[0:int(0.9*rows),int(0.3*cols):int(0.7*cols)] #resiz the frame .this size should at least cover the foreground object
#             # rows, cols, channels = frame2.shape
#             img2gray = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
#             gra_col = posx+cols
#             gra_row = posy+rows
#             if gra_col >= colgrenz:
#                 img2gray = img2gray[0:rows, 0:colgrenz - posx]
#                 gra_col = colgrenz
#                 frame2 = frame2[0:rows, 0:colgrenz - posx]
#             if gra_row >= rowgrenz:
#                 img2gray = img2gray[0:rowgrenz - posy, 0:cols]
#                 gra_row = rowgrenz
#                 frame2 = frame2[0:rowgrenz - posy, 0:cols]
#             _, mask = cv.threshold(img2gray, 10, 255, cv.THRESH_BINARY)
#             mask_inv = cv.bitwise_not(mask)
#             frame_fg = cv.bitwise_and(frame2, frame2, mask=mask)
#             cv.namedWindow('output')
#             cv.setMouseCallback('output', locatedthegraff)
#             #frame_bg = cv.bitwise_and(frame[0:rows, 0:cols], frame[0:rows, 0:cols], mask=mask_inv)
#             print(gra_col, gra_row)
#             frame_bg = cv.bitwise_and(frame[posy:gra_row, posx:gra_col],
#                                       frame[posy:gra_row, posx:gra_col], mask=mask_inv)
#             dst = cv.add(frame_bg, frame_fg)
#             #frame[0:rows, 0:cols] = dst
#             frame[posy:gra_row, posx:gra_col] = dst
#         cv.imshow('output', frame)
#         if cv.waitKey(25) == ord('q'):#here you can set the playing speed of the video
#             break
#     vc.release()

# this method be used to set the forground img to the background video
# the position of the foreground can be moved with the movement of mouse click
# size of background video should bigger than the foreground video
def setmaterbg(background='resources/kongfu.mp4', speed=10,save = False):
    global posx, posy
    posx, posy = 0, 0
    material = 'resources/material.mp4'
    vc = cv.VideoCapture(background)
    vd = cv.VideoCapture(material)
    if save:
        fourcc = cv.VideoWriter_fourcc(*'XVID')
        #fourcc = cv.VideoWriter_fourcc(*'X264')
        frame_width = int(vc.get(3))
        frame_height = int(vc.get(4))
        # fourcc = cv.VideoWriter_fourcc('M','J','P','G')
        out = cv.VideoWriter('resources/insertforeground.mp4', fourcc, 20.0, (frame_width, frame_height))  # the output video
    while vc.isOpened():
        ret, frame = vc.read()
        rowgrenz, colgrenz, _ = frame.shape
        if vd.isOpened():
            ret2, frame2 = vd.read()
            rows, cols, channels = frame2.shape
            # frame2 = frame2[0:int(0.9*rows),int(0.3*cols):int(0.7*cols)]
            # #resiz the frame .this size should at least cover the foreground object
            # rows, cols, channels = frame2.shape #but it is not necessary to use this tow lines of code
            img2gray = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
            gra_col = posx + cols
            gra_row = posy + rows
            # The following code is used to separate the foreground according to different situations
            # normal situation the foreground don t exceed the background
            if gra_col <= colgrenz and gra_row <= rowgrenz:
                _, mask = cv.threshold(img2gray, 10, 255, cv.THRESH_BINARY)
                mask_inv = cv.bitwise_not(mask)
                frame_fg = cv.bitwise_and(frame2, frame2, mask=mask)
                cv.namedWindow('output')
                cv.setMouseCallback('output', locatedthegraff)
                # frame_bg = cv.bitwise_and(frame[0:rows, 0:cols], frame[0:rows, 0:cols], mask=mask_inv)
                print(gra_col, gra_row)
                frame_bg = cv.bitwise_and(frame[posy:gra_row, posx:gra_col],
                                          frame[posy:gra_row, posx:gra_col], mask=mask_inv)
                dst = cv.add(frame_bg, frame_fg)
                # frame[0:rows, 0:cols] = dst
                frame[posy:gra_row, posx:gra_col] = dst
            # situation 1 foreground from left to right exceed the background
            if gra_col > colgrenz and gra_row < rowgrenz:
                gray1 = img2gray[0:rows, 0:colgrenz - posx]
                gray2 = img2gray[0:rows, colgrenz - posx:cols]

                _, mask1 = cv.threshold(gray1, 10, 255, cv.THRESH_BINARY)
                mask_inv1 = cv.bitwise_not(mask1)
                frame_fg1 = cv.bitwise_and(frame2[0:rows, 0:colgrenz - posx], frame2[0:rows, 0:colgrenz - posx],
                                           mask=mask1)

                frame_bg1 = cv.bitwise_and(frame[posy:gra_row, posx:colgrenz],
                                           frame[posy:gra_row, posx:colgrenz], mask=mask_inv1)
                dst1 = cv.add(frame_bg1, frame_fg1)

                frame[posy:gra_row, posx:colgrenz] = dst1
                _, mask2 = cv.threshold(gray2, 10, 255, cv.THRESH_BINARY)
                mask_inv2 = cv.bitwise_not(mask2)
                frame_fg2 = cv.bitwise_and(frame2[0:rows, colgrenz - posx:cols], frame2[0:rows, colgrenz - posx:cols],
                                           mask=mask2)

                frame_bg2 = cv.bitwise_and(frame[posy:gra_row, 0:gra_col - colgrenz],
                                           frame[posy:gra_row, 0:gra_col - colgrenz], mask=mask_inv2)
                dst2 = cv.add(frame_bg2, frame_fg2)
                frame[posy:gra_row, 0:gra_col - colgrenz] = dst2
            # situation2 from top to bottom
            if gra_row > rowgrenz and gra_col < colgrenz:
                gray3 = img2gray[0:rowgrenz - posy, 0:cols]
                gray4 = img2gray[rowgrenz - posy:rows, 0:cols]
                _, mask3 = cv.threshold(gray3, 10, 255, cv.THRESH_BINARY)
                mask_inv3 = cv.bitwise_not(mask3)
                frame_fg3 = cv.bitwise_and(frame2[0:rowgrenz - posy, 0:cols], frame2[0:rowgrenz - posy, 0:cols],
                                           mask=mask3)
                frame_bg3 = cv.bitwise_and(frame[posy:rowgrenz, posx:gra_col],
                                           frame[posy:rowgrenz, posx:gra_col], mask=mask_inv3)
                dst3 = cv.add(frame_bg3, frame_fg3)
                frame[posy:rowgrenz, posx:gra_col] = dst3

                _, mask4 = cv.threshold(gray4, 10, 255, cv.THRESH_BINARY)
                mask_inv4 = cv.bitwise_not(mask4)
                frame_fg4 = cv.bitwise_and(frame2[rowgrenz - posy:rows, 0:cols], frame2[rowgrenz - posy:rows, 0:cols],
                                           mask=mask4)
                frame_bg4 = cv.bitwise_and(frame[0:gra_row - rowgrenz, 0:cols],
                                           frame[0:gra_row - rowgrenz, 0:cols], mask=mask_inv4)
                dst4 = cv.add(frame_bg4, frame_fg4)
                frame[0:gra_row - rowgrenz, 0:cols] = dst4
            # situation3 from lowerright to upperleft
            if gra_row > rowgrenz and gra_col > colgrenz:
                gray5 = img2gray[0:rowgrenz - posy, 0:colgrenz - posx]
                gray6 = img2gray[rowgrenz - posy:rows, colgrenz - posx:cols]
                _, mask5 = cv.threshold(gray5, 10, 255, cv.THRESH_BINARY)
                mask_inv5 = cv.bitwise_not(mask5)
                frame_fg5 = cv.bitwise_and(frame2[0:rowgrenz - posy, 0:colgrenz - posx],
                                           frame2[0:rowgrenz - posy, 0:colgrenz - posx], mask=mask5)
                frame_bg5 = cv.bitwise_and(frame[posy:rowgrenz, posx:colgrenz],
                                           frame[posy:rowgrenz, posx:colgrenz], mask=mask_inv5)
                dst5 = cv.add(frame_bg5, frame_fg5)
                frame[posy:rowgrenz, posx:colgrenz] = dst5
                _, mask6 = cv.threshold(gray6, 10, 255, cv.THRESH_BINARY)
                mask_inv6 = cv.bitwise_not(mask6)
                frame_fg6 = cv.bitwise_and(frame2[rowgrenz - posy:rows, colgrenz - posx:cols],
                                           frame2[rowgrenz - posy:rows, colgrenz - posx:cols], mask=mask6)
                frame_bg6 = cv.bitwise_and(frame[0:gra_row - rowgrenz, 0:gra_col - colgrenz],
                                           frame[0:gra_row - rowgrenz, 0:gra_col - colgrenz], mask=mask_inv6)
                dst6 = cv.add(frame_bg6, frame_fg6)
                frame[0:gra_row - rowgrenz, 0:gra_col - colgrenz] = dst6
        frame = cartoon.cartoonify(frame)
        cv.imshow('output', frame)
        if save:
            out.write(frame)
        if cv.waitKey(1000 // speed) == ord('q'):  # here you can set the playing speed of the video
            break
    if save:
        out.release()
    vc.release()
# pt = "testgui/control_xy.png"
# img = cv.imread(pt)
# hei,wid,col = img.shape
# img2gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
# _, mask1 = cv.threshold(img2gray[0:hei,200:300], 10, 255, cv.THRESH_BINARY)
# _, mask2 = cv.threshold(img2gray[0:hei,200:wid], 10, 255, cv.THRESH_BINARY)
# x=img[:,0:300]
#
# cvt.showImage('zx',img)


# pts_corner is the left top positon on the img ,where the Graffiti should be
def applyGraffiti(img, graffiti, pts_corner=(300, 300), totalcover=True):
    # use graffiti corners as point correspondances
    h, w = graffiti.shape[:2]
    pts_src = ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))

    # pts_dst include four corner points (lefttop,righttop,leftbottom,rightbottom)
    pts_dst = ((pts_corner[0], pts_corner[1]), (pts_corner[0] + w // 4, pts_corner[1]),
               (pts_corner[0], pts_corner[1] + h // 4), (pts_corner[0] + w // 4, pts_corner[1] + h // 4))

    # warp graffiti accordingly
    gwarped = cvt.warpPerspective(graffiti, pts_src, pts_dst, img.shape)

    # create a mask to only merge the warped graffity area
    mask = gwarped.copy()
    mask[mask != (0, 0, 0)] = 1
    # multiply resources (in the masked area) to get details of both
    if totalcover:
        img_with_graffit = (1 - mask) * img + mask * gwarped
    else:
        img_with_graffit = img * mask * gwarped + (1 - mask) * img
    return img_with_graffit


# color transfer function
def colorTransfer(source, target):
    source_Lab = cv.cvtColor(source, cv.COLOR_BGR2Lab)
    target_Lab = cv.cvtColor(target, cv.COLOR_BGR2Lab)

    source_mean = np.mean(source_Lab, axis=(0, 1))
    target_mean = np.mean(target_Lab, axis=(0, 1))
    source_std = np.std(source_Lab, axis=(0, 1))
    target_std = np.std(target_Lab, axis=(0, 1))

    source_Lab -= source_mean
    source_Lab /= source_std
    source_Lab *= target_std
    source_Lab += target_mean

    return cv.cvtColor(source_Lab, cv.COLOR_Lab2BGR)


# face detection and mark it
def facedet(input='resources/do.mp4', fliter='resources/haarcascades/haarcascade_frontalface_default.xml', widt=960, hei=540,
            speed=10):
    output = 'resources/face'
    timeF = 5
    c = 1
    vc = cv.VideoCapture(input)
    # in order to recognize the object,a classifier is requiered
    cascade_classifier = cv.CascadeClassifier(fliter)
    while vc.isOpened():
        ret, frame = vc.read()
        frame = imutils.resize(frame, width=widt, height=hei)
        gray = cv.cvtColor(frame, 0)
        detections = cascade_classifier.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        if len(detections) > 0:
            (x, y, w, h) = detections[0]
            frame = cv.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0),
                                 2)  # use rectangel to cover the detectd face
            # if c % timeF == 0:
            #     cv.imwrite(output + str(int(c / timeF)) + '.jpg', frame[y:y+h, x:x+w])
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        # write the flipped frame
        cv.imshow('frame', frame)
        c += 1
        if cv.waitKey(1000 // speed) == ord('q'):
            break
    vc.release()
    cv.destroyAllWindows()


# crop a single image
def croptheface(path="resources/test.jpg", fliter='resources/haarcascades/haarcascade_frontalface_default.xml'):
    img = cvt.safeLoad(path)
    gray = cv.cvtColor(img, 0)
    cascade_classifier = cv.CascadeClassifier(fliter)
    detections = cascade_classifier.detectMultiScale(gray, minSize=(20, 20))
    if len(detections) > 0:
        (x, y, w, h) = detections[0]
        frame = cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        return frame[y:y + h, x:x + w]


# video color transfer
def realtimecolortransfer(source='resources/do.mp4', target='resources/sky-g29f24e740_640.jpg', widt=960, hei=540):
    vc = cv.VideoCapture(source)
    tar = cvt.safeLoad(target, datatype=np.float32, divisor=255)
    while vc.isOpened():
        ret, frame = vc.read()
        frame = imutils.resize(frame, width=widt, height=hei)
        frame = frame.astype(dtype=np.float32) / 255
        frame = colorTransfer(frame, tar)
        cv.imshow('frame', frame)
        if cv.waitKey(1) == ord('q'):
            break
    # Release everything if job is finished
    vc.release()
    cv.destroyAllWindows()

# video and picture combination the picture will stay in a fix positon
def facereplace(source='resources/do.mp4', target='nn.jpg', widt=960, hei=540):
    fliter = 'resources/haarcascades/haarcascade_frontalface_default.xml'
    vc = cv.VideoCapture(source)
    grapic = cv.imread(target)
    cascade_classifier = cv.CascadeClassifier(fliter)
    while vc.isOpened():
        ret, frame = vc.read()
        frame = imutils.resize(frame, width=widt, height=hei)
        gray = cv.cvtColor(frame, 0)
        detections = cascade_classifier.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        frame = frame.astype(dtype=np.float32) / 255
        graffiti = grapic.astype(dtype=np.float32) / 255
        if len(detections) > 0:
            (x, y, w, h) = detections[0]

            resized = cv.resize(graffiti, (w * 4, h * 4))
            print(w, h)

            frame = applyGraffiti(frame, resized, (x, y))
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        cv.imshow('frame', frame)
        if cv.waitKey(25) == ord('q'):
            break
    # Release everything if job is finished
    vc.release()
    cv.destroyAllWindows()


# two videos combination the video,the second video will followed the finger
def gestureguidecombin(source='rescources/kongfu.mp4', target='resources/do.mp4', widt=960, hei=540, speed=10):
    vc = cv.VideoCapture(source)
    # the hand muss be detected first
    det = rtfun.Handdetector()
    vd = cv.VideoCapture(target)
    while vc.isOpened():
        ret, frame = vc.read()
        frame = imutils.resize(frame, width=widt, height=hei)
        det.findhands(frame, draw=False)
        # find the every key positions of hand
        gelenk = det.findpos(frame, draw=False)
        frame = frame.astype(dtype=np.float32) / 255
        frame1 = frame
        print(vc.get(cv.CAP_PROP_FPS))
        print(vc.get(cv.CAP_PROP_FRAME_WIDTH))
        if len(gelenk) != 0:
            # find the index finger
            a, b = det.forefinger(gelenk, frame)
            if vd.isOpened():
                ret2, frame2 = vd.read()
                graffiti = frame2.astype(dtype=np.float32) / 255
                frame1 = applyGraffiti(frame, graffiti, (a, b))
                # if the defined gesture detected then the video will be splited
                h, w = graffiti.shape[:2]
                if det.gesturedet(gelenk, frame) == 1:
                    frame = applyGraffiti(frame, graffiti[0:h, 0:w // 2], (a - 150, b))
                    frame = applyGraffiti(frame, graffiti[0:h, w // 2:w], (a + 150, b))
                    frame1 = frame

                if det.gesturedet(gelenk, frame) == 2:
                    frame = applyGraffiti(frame, graffiti[0:h // 2, 0:w], (a, b - 100))
                    frame = applyGraffiti(frame, graffiti[h // 2:h, 0:w], (a, b + 100))
                    frame1 = frame

            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

        cv.imshow('frame', frame1)
        if cv.waitKey(1000 // speed) == ord('q'):
            break
    # Release everything if job is finished
    vc.release()
    cv.destroyAllWindows()
