#!/usr/bin/env python
"""
@author: phdenzel

Scanner transform for images of rectangular shapes
"""
# # Module imports
import sys
import os
import cv2
import numpy as np
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
# verbosity
if VERBOSE:
    print("Image dimensions:\t{}x{} in {} channels".format(
        width, height, channels))

# Resize image
# adjust dimensions if important content is lost
image = cv2.resize(image, (int(800*aspr), 800))
# verbosity
if VERBOSE:
    print("Resizing to {}x{}...".format(int(800*aspr), 800))

# Original
orig = image.copy()

# Some transforms
contrast = primary_transf(image, roundup=177, rounddown=77)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
filtered = cv2.bilateralFilter(gray, 1, 10, 120)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
dilated = cv2.dilate(gray, kernel)

# blurred = cv2.GaussianBlur(gray, (5, 5), 0)
blurred = cv2.medianBlur(gray, 15)
# verbosity
if VERBOSE:
    print("Grayscaling...")

# Canny Edge Detection
edged = cv2.Canny(dilated, 10, 250)
edged_orig = edged.copy()
# verbosity
if VERBOSE:
    print("Running Canny edge detection...")


# Contours in edged image
_, contours, _ = cv2.findContours(edged.copy(),
                                  cv2.RETR_LIST,
                                  cv2.CHAIN_APPROX_NONE)
# _, contours, _ = cv2.findContours(dilated.copy(),
#                                   cv2.RETR_LIST,
#                                   cv2.CHAIN_APPROX_SIMPLE)
contours = sorted(contours, key=cv2.contourArea, reverse=True)

# Approximate contour
for c in contours:
    p = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02*p, True)
    r = cv2.boundingRect(c)
    
    if len(approx) == 4:
        break
# target = rect.angle(target)
# verbosity
if VERBOSE:
    print("Filtering edge contours...")

# Mapping target points to 800x800 quadrilateral
approx = rect.ify(target)
pts2 = np.float32([[0, 0], [800, 0], [800, 800], [0, 800]])

M = cv2.getPerspectiveTransform(approx, pts2)
dst = cv2.warpPerspective(orig, M, (800, 800))
# verbosity
if VERBOSE:
    print("Transforming perspective...")

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
cv2.imwrite(root+"tmp/Original.jpg", orig)
cv2.imwrite(root+"tmp/Original Gray.jpg", gray)
cv2.imwrite(root+"tmp/Original Blurred.jpg", blurred)
cv2.imwrite(root+"tmp/Original Edged.jpg", edged_orig)
cv2.imwrite(root+"tmp/Outline.jpg", image)
cv2.imwrite(root+"tmp/Dilated.jpg", dilated)
cv2.imwrite(root+"tmp/Primary.jpg", contrast)
cv2.imwrite(root+"tmp/Thresh Binary.jpg", th1)
cv2.imwrite(root+"tmp/Thresh mean.jpg", th2)
cv2.imwrite(root+"tmp/Thresh gauss.jpg", th3)
cv2.imwrite(root+"tmp/Otsu's.jpg", th4)
cv2.imwrite(root+"tmp/dst.jpg", dst)
# verbosity
if VERBOSE:
    print("Saving transforms in tmp/ directory...")

# # Other thresholding methods
ret, thresh1 = cv2.threshold(dst, 127, 255, cv2.THRESH_BINARY)
ret, thresh2 = cv2.threshold(dst, 127, 255, cv2.THRESH_BINARY_INV)
ret, thresh3 = cv2.threshold(dst, 127, 255, cv2.THRESH_TRUNC)
ret, thresh4 = cv2.threshold(dst, 127, 255, cv2.THRESH_TOZERO)
ret, thresh5 = cv2.threshold(dst, 127, 255, cv2.THRESH_TOZERO_INV)

cv2.imwrite(root+"tmp/Thresh Binary.jpg", thresh1)
cv2.imwrite(root+"tmp/Thresh Binary_INV.jpg", thresh2)
cv2.imwrite(root+"tmp/Thresh Trunch.jpg", thresh3)
cv2.imwrite(root+"tmp/Thresh TOZERO.jpg", thresh4)
cv2.imwrite(root+"tmp/Thresh TOZERO_INV.jpg", thresh5)
