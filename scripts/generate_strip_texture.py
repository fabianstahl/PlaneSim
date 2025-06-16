import cv2
import numpy as np


size            = (200, 200, 4)

strip_width     = 5
strip_start     = 100 
strip_end       = 200
bullet_color    = (0.9, 0.9, 0.9)

max_alpha       = 0.9
min_alpha       = 0.0

centers         = (0.142, 0.3, 0.7, 0.858)

image = np.zeros(size)

for center in centers:
    c_total = center * size[0]
    for y in range(strip_start, strip_end):
        x_start = int(c_total - strip_width / 2)
        x_end   = int(c_total + strip_width / 2)
        alpha   = 1 - ((y - strip_start) / (strip_end - strip_start) * (max_alpha - min_alpha) + min_alpha)
        image[y, x_start:x_end] = np.array([*bullet_color, alpha]) * 255


image       = np.clip(image, 0, 255)
image       = image.astype(np.uint8)
cv2.imwrite("assets/strip.png", image)