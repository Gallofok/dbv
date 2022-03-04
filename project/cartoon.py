#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2 as cv
import numpy as np
import openCVTools as cvt
def cartoonify(img):
    

    #convrt the image to grayscale
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    #Blur the grayscale with medianBlur
    gray_blur = cv.medianBlur(gray, 3)

    #detect edges from the image
    edges = cv.adaptiveThreshold(gray_blur, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 9, 9)

    #sharpen the image
    color = cv.detailEnhance(img,sigma_s=5, sigma_r=0.5)

    #Merge the colors of sam images using mask
    cartoon = cv.bitwise_and(color,color, mask=edges)
    
    return cartoon

# img = cv.imread("images/lingerie-g6be70f972_1280.jpg")
# cvt.showImage('g',cartoonify(img))
#
