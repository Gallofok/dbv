"""
by wenchen and jing wang
"""

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
import os
root = tk.Tk()

root.title('Digital image processing')
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

frm1=tk.Frame(root)
frm2=tk.Frame(root)
frm3=tk.Frame(root)
frm4=tk.Frame(root)
frm5=tk.Frame(root)


#set the playing speed of video
def spedset(spe):
    sped.set(spe)
    strsped.set("current video speed is " + str(sped.get()))

#crop some parts of image and save it
def savesta(cmd):
    savecon.set(cmd)
    strboo.set("（Foreground video insertion with mouse click） save statue is " + str(savecon.get()))

#get the foreground video
def getforground():
    forground = tk.filedialog.askopenfilename(title="choosetheforground")
    if forground != '':
        ko.cropthematerial(forground)
    else:
        print('no video selected')

#set the foreground on background video
def forbackcombination():
    background = tk.filedialog.askopenfilename(title="choosethebackground")
    if background != '':
        ko.setmaterbg(background, speed=sped.get(), save=savecon.get())
    else:
        print('no background selected')


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
    else:
        ko.realtimecolortransfer(a, b, widt=wid, hei=hei)

# two videos combination
def videofunwithgesture():
    source = tk.filedialog.askopenfilename(title="backgroundvideo")
    if source == '':
        ko.gestureguidecombin(0,
                              target=tk.filedialog.askopenfilename(title="foregroundvideo"), widt=wid, hei=hei,
                              )
    else:
        ko.gestureguidecombin(source,
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

#show the size of camera size setting
def getthesize():
    global hei, wid

    wid = int(var1.get())
    hei = int(var2.get())
    camsize.set("camera width is set to %d, and camera height is set to %d" % (wid, hei))

#cartoon function
def cartonon():
    a = tk.filedialog.askopenfilename(title="choosetheimage")
    if a != '':
        img = cv.imread(a)

        carton = cartoon.cartoonify(img)
        cv.imshow('carton',carton)
        cv.waitKey()
        cv.destroyAllWindows()

#graffiti function
def garttif():
    global x_1,y_1
    a = tk.filedialog.askopenfilename(title="choosebigjpg")
    b = tk.filedialog.askopenfilename(title="choosesmallpng")
    if a != '':
        img = cv.imread(a)
        img2 = cv.imread(b)
        gra = graffiti.graffiti(img, img2, x_1, y_1)
        cv.imshow('result', gra)
        cv.waitKey()
        cv.destroyAllWindows()
def gracoordinate():
    global x_1,y_1
    x_1 = int(en.get())
    y_1 = int(en2.get())
    print(x_1,y_1)
def top():
    root.destroy()


frm1.config(height=1080,width=720)
frm1.place(x=350,y=200)
frm2.config(height=620,width=180,)
frm2.place(x=0,y=101)
frm3.config(height=60,width=1080,)
frm3.place(x=0,y=0)
frm4.config(height=60,width=1080)
frm4.place(x=300,y=560)
frm5.config(height=60,width=60)
frm5.place(x=460,y=460)

#add the title to the frame
tk.Label(frm3,text='Digital image processing',fg='red',font='Verdana 15 bold').place(x=400,y=20)


# load and put the button on the root frame
bgetforground = tk.Button(frm2, text="getforgroundvideo", font="Arial,14", bg="Tan",height=2,width=18,command=getforground)
bgetforground.pack()
bforebackcombination = tk.Button(frm2, text="ViedoIns(mouse)", font="Arial,14", bg="Tan", height=2, width=18, command=forbackcombination)
bforebackcombination.pack()
bfindvideo = tk.Button(frm2, text="cropandsavepic", font="Arial,14", bg="Tan", height=2, width=18, command=cropandsavepic)
bfindvideo.pack()
brealtimedet = tk.Button(frm2, text="realtimedet", font="Arial,14", bg="Tan", height=2, width=18, command=rtfacedetection)
brealtimedet.pack()
bcolortransfer = tk.Button(frm2, text="colortransfer", font="Arial,14", bg="Tan", height=2, width=18, command=rtcolortransfer)
bcolortransfer.pack()
bvideocomb = tk.Button(frm2, text="video(gesture)", font="Arial,14", bg="Tan", height=2, width=18, command=videofunwithgesture)
bvideocomb.pack()
bvideocomb = tk.Button(frm2, text="facereplace", font="Arial,14", bg="Tan", height=2, width=18, command=facereplace)
bvideocomb.pack()
bgesture = tk.Button(frm2, text="videopainter", font="Arial,14", bg="Tan", height=2, width=18, command=paint)
bgesture.pack()
bcarton = tk.Button(frm2, text="carton", font="Arial,14", bg="Tan", height=2, width=18, command=cartonon)
bcarton.pack()
bgra = tk.Button(frm2, text="graffiti", font="Arial,14", bg="Tan", height=2, width=18, command=garttif)
bgra.pack()
bstop = tk.Button(frm2, text="close", font="Arial,14", bg="Tan", height=2, width=18, command=top)
bstop.pack()




scale = tk.Scale(frm1, orient=tk.HORIZONTAL, from_=960, to=1920, length=400, variable=var1)
scale.pack()
label1 = tk.Label(frm1, text='camera wide')
label1.pack()
scale2 = tk.Scale(frm1, orient=tk.HORIZONTAL, from_=540, to=1080, length=400, variable=var2)
scale2.pack()
label2 = tk.Label(frm1, text='camera height')
label2.pack()
bconfirm = tk.Button(frm1, text='confirm', command=getthesize)
bconfirm.pack()

workingpath = os.getcwd()
path_parent = os.path.dirname(workingpath)
new_workingpath = os.chdir(path_parent)

emoji1 = tk.PhotoImage(file=r"resources/feet.png")
emoji2 = tk.PhotoImage(file=r"resources/car.png")
emoji3 = tk.PhotoImage(file=r"resources/plane.png")
emoji4 = tk.PhotoImage(file=r"resources/rocket.png")
emoji5 = tk.PhotoImage(file=r"resources/save.png")
emoji6 = tk.PhotoImage(file=r"resources/nosave.png")

b1 = tk.Button(frm1, image=emoji1, command=lambda spe=4: spedset(spe=spe))
b1.pack(side='left')
b2 = tk.Button(frm1, image=emoji2, command=lambda spe=40: spedset(spe=spe))
b2.pack(side='left')
b3 = tk.Button(frm1, image=emoji3, command=lambda spe=250: spedset(spe=spe))
b3.pack(side='left')
b4 = tk.Button(frm1, image=emoji4, command=lambda spe=500: spedset(spe=spe))
b4.pack(side='left')
b5 = tk.Button(frm1, image=emoji5, command=lambda cmd=True: savesta(cmd))
b5.pack(side='right')
b6 = tk.Button(frm1, image=emoji6, command=lambda cmd=False: savesta(cmd))
b6.pack(side='right')

en=tk.Entry(frm5)
en.pack()
en2=tk.Entry(frm5)
en2.pack()
bu2 = tk.Button(frm5,text='x and y for graffiti confirm',command=gracoordinate)
bu2.pack()



label3 = tk.Label(frm4, textvariable=camsize, font=('arial bold', 18), fg="blue")
label3.pack(side='top')
label4 = tk.Label(frm4, textvariable=strsped, font=('arial bold', 18), fg="green")
label4.pack(side='top')
label5 = tk.Label(frm4, textvariable=strboo, font=('arial bold', 18), fg="red")
label5.pack(side='top')
root.mainloop()
