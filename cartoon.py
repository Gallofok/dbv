#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 16:11:57 2022

@author: dell
"""
import cv2 as cv
import numpy as np
import openCVTools as cvt
def cartoonify(img):
    
    """
    gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)

    gray = cv.medianBlur(gray,3)

    edges = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 9, 9)

    color = cv.bilateralFilter(img,5,50,5)

    cartoon = cv.bitwise_and(color, color,mask=edges)

    cv.namedWindow('cartoon')
    cv.imshow("cartoon",cartoon)

    cv.waitKey()
    cv.destoryAllWindows()

    """

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    gray_blur = cv.medianBlur(gray, 3)

    edges = cv.adaptiveThreshold(gray_blur, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 9, 9)

    color = cv.detailEnhance(img,sigma_s=5, sigma_r=0.5)

    cartoon = cv.bitwise_and(color,color, mask=edges)
    
    return cartoon

# img = cv.imread("images/lingerie-g6be70f972_1280.jpg")
# cvt.showImage('g',cartoonify(img))
#
