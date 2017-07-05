#!/usr/bin/env python
"""
@authot: phdenzel

Rectify image contours
"""
import numpy as np


def ify(h):
    """
    rect.ify - Rectify
    """
    h = h.reshape((4, 2))
    hrect = np.zeros((4, 2), dtype=np.float32)

    add = h.sum(1)
    hrect[0] = h[np.argmin(add)]
    hrect[2] = h[np.argmax(add)]

    diff = np.diff(h, axis=1)
    hrect[1] = h[np.argmin(diff)]
    hrect[3] = h[np.argmax(diff)]

    return hrect


def angle(h):
    """
    rect.angle - Transform a polygon close to a rectangle into a rectangle
    """
    hrect = np.zeros((4, 1, 2))
    hrect[0] = h[np.argmin(h[:, :, 0])]
    hrect[1] = h[np.argmax(h[:, :, 0])]
    hrect[2] = h[np.argmax(h[:, :, 1])]
    hrect[3] = h[np.argmin(h[:, :, 1])]
    return hrect
