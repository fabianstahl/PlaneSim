import cv2
import numpy as np



base_color  = (0, 0, 1, 0)


image = cv2.imread("assets/plane.png", cv2.IMREAD_UNCHANGED)

print(image.shape)

image = image + 255 * np.array(base_color) 

print(image.shape, image.dtype, np.max(image))

image       = np.clip(image, 0, 255)
image       = image.astype(np.uint8)

print(image.shape)

cv2.imwrite("assets/enemy.png", image)