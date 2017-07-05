#!/usr/bin/env python
"""
@author: phdenzel

Scanner transform for images of rectangular shapes
"""
# # Module imports
import sys
import os
import numpy as np
import math
import cv2
import rect
from mkpath import mkdir_p
VERBOSE = True

# # File import
# Get image to work with
filename = sys.argv[1]
if os.getcwd() in filename:
    filepath = filename
else:
    filepath = os.getcwd()+'/'+filename
# just making sure...
try:
    # Python 3
    FileNotFoundError
except NameError:
    # Python 2
    FileNotFoundError = IOError
try:
    file(filepath)
except FileNotFoundError:
    print("No such file found...")
    sys.exit(1)
# get path of repository
root = "/".join(os.path.realpath(__file__).split("/")[:-1])+"/"
# verbosity
if VERBOSE:
    print("Repository in:\t\t{}".format(root))
    print("Image file:\t\t{}".format(filepath.split("/")[-1]))


# #  Image manipulations
def primary_transf(rgba, roundup=127, rounddown=127):
    """
    Pronounce pictures with primary colors
    """
    width, height, channels = rgba.shape
    primary = rgba*1
    primary[np.greater_equal(primary, roundup)] = 255
    primary[np.less(primary, rounddown)] = 0
    return primary


# Import image
image = cv2.imread(filename)
width, height, channels = image.shape
aspr = float(width)/height
_width, _height = int(800*aspr), 800
# verbosity
if VERBOSE:
    print("Image dimensions:\t{}x{} in {} channels".format(
        width, height, channels))

# Resize image
# adjust dimensions if important content is lost
image = cv2.resize(image, (_width, _height))
# verbosity
if VERBOSE:
    print("Resizing to {}x{}...".format(_width, _height))

# Original
orig = image.copy()

# Some transforms
contrast = primary_transf(image, roundup=177, rounddown=77)
if VERBOSE:
    print("Grayscaling...")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
if VERBOSE:
    print("Blurring...")
blurred = cv2.bilateralFilter(gray, 1, 10, 120)
# blurred = cv2.GaussianBlur(gray, (5, 5), 0)
# blurred = cv2.medianBlur(gray, 15)
if VERBOSE:
    print("Running Canny edge detection...")
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
dilated = cv2.dilate(gray, kernel)
edged = cv2.Canny(dilated, 10, 250)
edged_orig = edged.copy()
closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)


# Contours in edged image
if VERBOSE:
    print("Finding contours...")
_, contours, h = cv2.findContours(
    closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
# _, contours, _ = cv2.findContours(
#     dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
contours = sorted(contours, key=cv2.contourArea, reverse=True)
# approximate contour
if VERBOSE:
    print("Filtering edge contours...")
for c in contours:
    p = cv2.arcLength(c, True)
    # rec = 
    # box = 
    approx = cv2.approxPolyDP(c, 0.1*p, True)
    if len(approx) == 4:
        target = approx
        break

# Mapping target points to 800x800 quadrilateral
approx = rect.ify(target)
if VERBOSE:
    print("Transforming perspective...")
# Zoom 500%
dstw = 500 * int(math.ceil(0.005*(approx[1][0]+approx[2][0]
                                  - approx[0][0]-approx[3][0])))
dsth = 500 * int(math.ceil(0.005*(approx[2][1]+approx[3][1]
                                  - approx[1][1]-approx[0][1])))
pts2 = np.float32([[0, 0], [dstw, 0], [dstw, dsth], [0, dsth]])
M = cv2.getPerspectiveTransform(approx, pts2)
dst = cv2.warpPerspective(orig, M, (dstw, dsth))

cv2.drawContours(image, [target], -1, (0, 255, 0), 2)
dst = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)


# Threshold warped image
ret, th1 = cv2.threshold(dst, 127, 255, cv2.THRESH_BINARY)
th2 = cv2.adaptiveThreshold(dst, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                            cv2.THRESH_BINARY, 11, 2)
th3 = cv2.adaptiveThreshold(dst, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY, 11, 2)
ret2, th4 = cv2.threshold(dst, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
# verbosity
if VERBOSE:
    print("Thresholding warped images..")

mkdir_p(root+"tmp/")
cv2.imwrite(root+"tmp/_dst.jpg", dst)
cv2.imwrite(root+"tmp/Blurred.jpg", blurred)
cv2.imwrite(root+"tmp/Dilated.jpg", dilated)
cv2.imwrite(root+"tmp/Edged.jpg", edged_orig)
cv2.imwrite(root+"tmp/Gray.jpg", gray)
cv2.imwrite(root+"tmp/Original.jpg", orig)
cv2.imwrite(root+"tmp/Outline.jpg", image)
cv2.imwrite(root+"tmp/Primary.jpg", contrast)
cv2.imwrite(root+"tmp/Thresh Binary.jpg", th1)
cv2.imwrite(root+"tmp/Thresh Mean.jpg", th2)
cv2.imwrite(root+"tmp/Thresh Gauss.jpg", th3)
cv2.imwrite(root+"tmp/Otsu.jpg", th4)
# verbosity
if VERBOSE:
    print("Saving transforms in tmp/ directory...")

# # Other thresholding methods
# ret, thresh1 = cv2.threshold(dst, 127, 255, cv2.THRESH_BINARY)
# ret, thresh2 = cv2.threshold(dst, 127, 255, cv2.THRESH_BINARY_INV)
# ret, thresh3 = cv2.threshold(dst, 127, 255, cv2.THRESH_TRUNC)
# ret, thresh4 = cv2.threshold(dst, 127, 255, cv2.THRESH_TOZERO)
# ret, thresh5 = cv2.threshold(dst, 127, 255, cv2.THRESH_TOZERO_INV)
# cv2.imwrite(root+"tmp/Thresh Binary.jpg", thresh1)
# cv2.imwrite(root+"tmp/Thresh Binary_INV.jpg", thresh2)
# cv2.imwrite(root+"tmp/Thresh Trunch.jpg", thresh3)
# cv2.imwrite(root+"tmp/Thresh TOZERO.jpg", thresh4)
# cv2.imwrite(root+"tmp/Thresh TOZERO_INV.jpg", thresh5)
