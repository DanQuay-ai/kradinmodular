"""autotrace on the reference with its halo channels closed: Böcklin's loops pass over other strokes with a thin
white gap; closing those gaps lets the centre lines run on through the crossing as one stroke.
Usage: same arguments as autotrace.py, plus CLOSE=<radius in design units> in the environment (default 12)."""
import os, sys
import numpy as np
from scipy import ndimage
sys.path.insert(0, "/home/claude/work/gen")
import autotrace as A
R = float(os.environ.get("CLOSE", 12))
_orig = A.render
def render(face, ch, scale, pad=40):
    r = _orig(face, ch, scale, pad)
    if r is None: return r
    ink, left, top, adv = r
    S = 2 if pad >= 80 else 1
    rad = max(1, int(round(R * S)))
    yy, xx = np.ogrid[-rad:rad + 1, -rad:rad + 1]
    closed = ndimage.binary_closing(ink, structure=(xx * xx + yy * yy) <= rad * rad)
    return closed, left, top, adv
A.render = render
A.main()
