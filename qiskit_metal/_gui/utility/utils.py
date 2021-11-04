import re
"""
Given a filename and a search target, we
open that file and search
"""


def findProperty(filename, searchTarget):
    try:
        with open(filename, 'r') as readfile:
            filetext = readfile.read()
            readfile.close()
            matches = re.findall(searchTarget, filetext)
            return matches
    except IOError:
        return None
