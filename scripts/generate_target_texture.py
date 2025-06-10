import cv2
import numpy as np


size        = (200, 200, 4)

noise_level = 10

base_color  = (0, 255, 255)

max_alpha   = 0.5

image = np.zeros(size)

for y in range(size[0]):
    row_alpha   = 255 * (y / size[0] * max_alpha)
    row_col     = np.array([*base_color, row_alpha])                        # (4)
    image[y]    = np.random.random((size[1], 4)) * noise_level + row_col    # (x, 4)

image = np.clip(image, 0, 255)
image = image.astype(np.uint8)

cv2.imshow("pp", image)
cv2.waitKey()

cv2.imwrite("assets/target.png", image)