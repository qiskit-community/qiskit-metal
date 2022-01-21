import re
from pathlib import Path
"""
Given a filename and a search target, we
open that file and search
"""


def findProperty(filename, searchTarget):
    pathname = Path(filename)
    if pathname.is_file():
        filetext = pathname.read_text()
        matches = re.findall(searchTarget, filetext)
        return matches
    else:
        return None