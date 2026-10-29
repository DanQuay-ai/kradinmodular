"""body height of Kɔradin Eyes: Kɔradin's 0..700 body, stretched up (EYES_H) to give stacked parts room;
contrast: the heavy master is drawn with an elliptical nib, horizontals a little lighter than verticals
(Thin is monoline). contrast(W) = horizontal thickness / vertical thickness."""
import os
H = float(os.environ.get("EYES_H", 700))
C_BLACK = float(os.environ.get("EYES_CONTRAST", 0.82))
def contrast(W, W0=40.0, W1=140.0):
    W = float(W)
    if W <= W0: return 1.0
    return 1.0 - (1.0 - C_BLACK) * min(1.0, (W - W0) / (W1 - W0))
