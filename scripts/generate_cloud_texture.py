import cv2
import numpy as np

size        = (200, 200, 4)
noise_level = 10
min_alpha   = 0.0
max_alpha   = 0.2

cloud_base_colors   = [(1, 1, 1), (0, 0, 0)]
cloud_paths         = ["assets/cloud_white.png", "assets/cloud_black.png"]

for (base_color, path) in zip(cloud_base_colors, cloud_paths):

    base_image  = np.zeros(size) + np.array([*base_color, min_alpha]) * 255
    noise       = np.random.random(size) * (max_alpha-min_alpha) * 255 + min_alpha
    image       = base_image + noise

    image       = np.clip(image, 0, 255)
    image       = image.astype(np.uint8)
    cv2.imwrite(path, image)