#!/usr/bin/env python
"""
Induce a dictionary into an object

@author: phdenzel

"""


class objectify(object):
    def __init__(self, dictionary):
        self.__dict__ = dictionary
