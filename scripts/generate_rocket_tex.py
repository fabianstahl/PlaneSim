import cv2
import numpy as np


size        = (200, 200, 4)

no_bullets      = 5
rocket_width    = 20
rocket_height   = 200
bullet_color    = (0.9, 0.3, 0.3)

max_alpha       = 0.9
min_alpha       = 0.0

x_step          = size[0] / no_bullets
y_start         = int(size[1] / 2 - rocket_height / 2)
y_end           = int(size[1] / 2 + rocket_height / 2)

image = np.zeros(size)

for i in range(no_bullets):
    for y in range(y_start, y_end):
        x_start = int(i * x_step - rocket_width / 2)
        x_end   = int(i * x_step + rocket_width / 2)
        alpha   = 1 - ((y - y_start) / (y_end - y_start) * (max_alpha - min_alpha) + min_alpha)
        image[y, x_start:x_end] = np.array([*bullet_color, alpha]) * 255


image       = np.clip(image, 0, 255)
image       = image.astype(np.uint8)
cv2.imwrite("assets/rocket.png", image)