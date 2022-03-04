# -*- coding: utf-8 -*-

import cv2 as cv
import numpy as np
import openCVTools as cvt
import os

def graffiti(img1,img2,x1,y1):
    x2=x1+img2.shape[1]
    y2=y1+img2.shape[0]
    
    #define image whether four path
    if img1.shape[2]==3:
        b_channel,g_channel,r_channel=cv.split(img1)
        alpha_channel = np.ones(b_channel.shape,dtype=b_channel.dtype)*255
        img1=cv.merge((b_channel,g_channel,r_channel,alpha_channel))
    
    #set the range of the image
    yy1=0
    yy2=img2.shape[0]
    xx1=0
    xx2=img2.shape[1]
    
    if x1<0:
        xx1=-x1
        x1=0
        
    if y1<0:
        yy1=-y1
        y1=0
        
    if x2>img1.shape[1]:
        xx2=img2.shape[1]-(x2-img1.shape[1])
        x2=img1.shape[1]
        
    if y2>img1.shape[0]:
        yy2=img2.shape[0]-(y2-img1.shape[0])
        y2=img1.shape[0]
     
    #get the value of alpha and keep it between 0-1
    alpha_img2=img2[0:yy2,0:xx2,2]/255.0
    alpha_img1=1-alpha_img2
    
    #merge the image
    for c in range(0,3):
        img1[y1:y2,x1:x2,c]=((alpha_img1*img1[y1:y2,x1:x2,c])+(alpha_img2*img2[yy1:yy2,xx1:xx2,c]))
        
    return img1

# workingpath = os.getcwd()
# path_parent = os.path.dirname(workingpath)
# new_workingpath = os.chdir(path_parent)
# img = cv.imread("resources/sparrow-g4224d919e_1280.jpg",cv.IMREAD_UNCHANGED)
# img2 = cv.imread("resources/feet.png",cv.IMREAD_UNCHANGED)
#
# cv.imshow('g',graffiti(img,img2,0,0))
# cv.waitKey()
# cv.destroyAllWindows()

        
        