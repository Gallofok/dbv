import tkinter.filedialog
import cv2 as cv
import tkinter as tk
import klo2 as ko
import numpy as np
from PIL import Image
import rtfun
import cartoon
import openCVTools as cvt
import graffiti

root = tk.Tk()
# defined the size of the frame window
root.geometry("1080x720")
var1 = tk.DoubleVar()
var2 = tk.DoubleVar()
wid = 960
hei = 540
camsize = tk.StringVar()
sped = tk.IntVar()
strsped = tk.StringVar()
savecon = tk.BooleanVar()
strboo = tk.StringVar()


def spedset(spe):
    sped.set(spe)
    strsped.set("current video speed is " + str(sped.get()))


def savesta(cmd):
    savecon.set(cmd)
    strboo.set("backforecombination save statue is " + str(savecon.get()))


def getforground():
    forground = tk.filedialog.askopenfilename(title="choosetheforground")
    if forground != '':
        ko.cropthematerial(forground)
    else:
        ko.cropthematerial(forground)


def forbackcombination():
    background = tk.filedialog.askopenfilename(title="choosethebackground")
    if background != '':
        ko.setmaterbg(background, speed=sped.get(), save=savecon.get())
    else:
        ko.setmaterbg()


# this function will crop the human face and save the cropped picture
def cropandsavepic():
    image = ko.croptheface(tk.filedialog.askopenfilename(title="open pic"),
                           fliter=tk.filedialog.askopenfilename(title="datechooser"))
    image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    PIL_image = Image.fromarray(np.uint8(image_rgb))
    file = tk.filedialog.asksaveasfile(mode='w', defaultextension=".jpg")
    if file:
        PIL_image.save(file)
        # saves the image to the input file name.


# find a video and detect the human face on this video
def rtfacedetection():
    a = tk.filedialog.askopenfilename(title="choosethevideo")
    b = tk.filedialog.askopenfilename(title="choosefliter")
    if a == '':
        ko.facedet(0, b, widt=wid, hei=hei)
    else:
        ko.facedet(a, b)


# color transfer of an video
def rtcolortransfer():
    a = tk.filedialog.askopenfilename(title="choosethevideo")
    b = tk.filedialog.askopenfilename(title="choosecolor")
    if a == '':
        ko.realtimecolortransfer(0, b, widt=wid, hei=hei)


# two videos combination
def twovideocombination():
    source = tk.filedialog.askopenfilename(title="backgroundvideo")
    if source == '':
        ko.twovideocombination(0,
                               target=tk.filedialog.askopenfilename(title="foregroundvideo"), widt=wid, hei=hei,
                               save=savecon.get())
    else:
        ko.twovideocombination(source,
                               target=tk.filedialog.askopenfilename(title="foregroundvideo"))


# video and picture combinatiuon
def facereplace():
    a = tk.filedialog.askopenfilename(title="choosethevideo")
    b = tk.filedialog.askopenfilename(title="choosepic")
    if a == '':
        ko.facereplace(0, b, widt=wid, hei=hei)
    else:
        ko.facereplace(a, b)


# video painter
def paint():
    hand = rtfun.Handdetector()
    hand.painter(widt=wid, hei=hei)


def getthesize():
    global hei, wid

    wid = int(var1.get())
    hei = int(var2.get())
    camsize.set("camera width is set to %d, and camera height is set to %d" % (wid, hei))


def cartonon():
    a = tk.filedialog.askopenfilename(title="choosetheimage")
    if a != '':
        img = cv.imread(a)

        carton = cartoon.cartoonify(img)
        cvt.showImage(carton)


def garttif():
    a = tk.filedialog.askopenfilename(title="choosetheimage1")
    b = tk.filedialog.askopenfilename(title="choosetheimage2")
    if a != '':
        x1 = 0,
        y1 = 0
        img = cv.imread(a)
        img2 = cv.imread(b)
        gra = graffiti.graffiti(img, img2, x1, y1)
        cv.imshow('result', gra)
        cv.waitKey()
        cv.destroyAllWindows()


def top():
    root.destroy()


# load and put the button on the root frame
bgetforground = tk.Button(root, text="getforgroundvideo", font="Arial,14", bg="Tan", command=getforground)
bgetforground.pack(fill='x')
bforebackcombination = tk.Button(root, text="backforecombina", font="Arial,14", bg="Tan", command=forbackcombination)
bforebackcombination.pack(fill='x')
bfindvideo = tk.Button(root, text="cropandsavepic", font="Arial,14", bg="Tan", command=cropandsavepic)
bfindvideo.pack(fill='x')
brealtimedet = tk.Button(root, text="realtimedet", font="Arial,14", bg="Tan", command=rtfacedetection)
brealtimedet.pack(fill='x')
bcolortransfer = tk.Button(root, text="colortransfer", font="Arial,14", bg="Tan", command=rtcolortransfer)
bcolortransfer.pack(fill='x')
bvideocomb = tk.Button(root, text="videocontrolwithgesture", font="Arial,14", bg="Tan", command=twovideocombination)
bvideocomb.pack(fill='x')
bvideocomb = tk.Button(root, text="facereplace", font="Arial,14", bg="Tan", command=facereplace)
bvideocomb.pack(fill='x')
bgesture = tk.Button(root, text="videopainter", font="Arial,14", bg="Tan", command=paint)
bgesture.pack(fill='x')
bcarton = tk.Button(root, text="carton", font="Arial,14", bg="Tan", command=cartonon)
bcarton.pack(fill='x')
bgra = tk.Button(root, text="graffiti", font="Arial,14", bg="Tan", command=garttif)
bgra.pack(fill='x')
bstop = tk.Button(root, text="close", font="Arial,14", bg="Tan", command=top)
bstop.pack(fill='x')
lah = tk.LabelFrame(root)
lah.pack()

scale = tk.Scale(lah, orient=tk.HORIZONTAL, from_=960, to=1920, length=400, variable=var1)
scale.pack()
label1 = tk.Label(lah, text='camera wid')
label1.pack()
scale2 = tk.Scale(lah, orient=tk.HORIZONTAL, from_=540, to=1080, length=400, variable=var2)
scale2.pack()
label2 = tk.Label(lah, text='camera hei')
label2.pack()
bconfirm = tk.Button(lah, text='width height conf', command=getthesize)
bconfirm.pack()

emoji1 = tk.PhotoImage(file=r"images/feet.png")
emoji2 = tk.PhotoImage(file=r"images/car.png")
emoji3 = tk.PhotoImage(file=r"images/plane.png")
emoji4 = tk.PhotoImage(file=r"images/rocket.png")
emoji5 = tk.PhotoImage(file=r"images/save.png")
emoji6 = tk.PhotoImage(file=r"images/nosave.png")

b1 = tk.Button(lah, image=emoji1, command=lambda spe=4: spedset(spe=spe))
b1.pack(side='left')
b2 = tk.Button(lah, image=emoji2, command=lambda spe=40: spedset(spe=spe))
b2.pack(side='left')
b3 = tk.Button(lah, image=emoji3, command=lambda spe=250: spedset(spe=spe))
b3.pack(side='left')
b4 = tk.Button(lah, image=emoji4, command=lambda spe=500: spedset(spe=spe))
b4.pack(side='left')
b5 = tk.Button(lah, image=emoji5, command=lambda cmd=True: savesta(cmd))
b5.pack(side='right')
b6 = tk.Button(lah, image=emoji6, command=lambda cmd=False: savesta(cmd))
b6.pack(side='right')

label3 = tk.Label(root, textvariable=camsize, font=('arial bold', 18), fg="blue")
label3.pack()
label4 = tk.Label(root, textvariable=strsped, font=('arial bold', 18), fg="green")
label4.pack()
label5 = tk.Label(root, textvariable=strboo, font=('arial bold', 18), fg="red")
label5.pack()
root.mainloop()
