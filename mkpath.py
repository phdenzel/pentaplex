#!/usr/bin/env python
"""
@authot: phdenzel

Make a directory path from string
"""

def mkdir_p(pathname):
    """
    Create a directory as if using 'mkdir -p' on the command line
    """
    from os import makedirs, path
    from errno import EEXIST

    try:
        makedirs(pathname)
    except OSError as exc:  # Python > 2.5
        if exc.errno == EEXIST and path.isdir(pathname):
            pass
        else:
            raise
