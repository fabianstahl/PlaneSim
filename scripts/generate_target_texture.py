import cv2
import numpy as np


size        = (200, 200, 4)
min_alpha   = 0.0
max_alpha   = 0.3

noise_level = 0.5
base_color  = (0, 1, 1)

"""
image = np.zeros(size)

for y in range(size[0]):
    row_alpha   = 255 * (y / size[0] * max_alpha)
    row_col     = np.array([*base_color, row_alpha])                        # (4)
    image[y]    = np.random.random((size[1], 4)) * 255 + row_col    # (x, 4)

image = np.clip(image, 0, 255)
image = image.astype(np.uint8)

cv2.imwrite("assets/target.png", image)
"""

base_image  = np.zeros((size[0], size[1], 3)) + np.array(base_color)
noise       = (np.random.random((size[0], size[1], 3)) - 0.5) * noise_level
image       = (base_image + noise) * 255

# Add alpha channel
image       = np.concat([image, np.zeros((size[0], size[1], 1))], -1) 

for y in range(size[0]):
    image[y,:,-1] = 255 * ((y / size[0]) * (max_alpha - min_alpha) + min_alpha)

image       = np.clip(image, 0, 255)
image       = image.astype(np.uint8)
cv2.imwrite("assets/target.png", image)