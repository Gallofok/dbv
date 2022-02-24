# -*- coding: utf-8 -*-
"""
Created on Sun Feb  6 17:41:09 2022

@author: dell
"""

import cv2 as cv
import numpy as np
import openCVTools as cvt


def graffiti(img1,img2,x1,y1):
    x2=x1+img2.shape[1]
    y2=y1+img2.shape[0]
    
    
    if img1.shape[2]==3:
        b_channel,g_channel,r_channel=cv.split(img1)
        alpha_channel = np.ones(b_channel.shape,dtype=b_channel.dtype)*255
        img1=cv.merge((b_channel,g_channel,r_channel,alpha_channel))
        
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
        
    alpha_img2=img2[0:yy2,0:xx2,2]/255.0
    alpha_img1=1-alpha_img2
    
    for c in range(0,3):
        img1[y1:y2,x1:x2,c]=((alpha_img1*img1[y1:y2,x1:x2,c])+(alpha_img2*img2[yy1:yy2,xx1:xx2,c]))
        
    return img1

# img = cv.imread("images/sparrow-g4224d919e_1280.jpg",cv.IMREAD_UNCHANGED)
# img2 = cv.imread("images/feet.png",cv.IMREAD_UNCHANGED)
#
# cv.imshow('g',graffiti(img,img2,0,0))
# cv.waitKey()
# cv.destroyAllWindows()
#
        
        