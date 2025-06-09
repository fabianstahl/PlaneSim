from OpenGL.GL import *
import os
import cv2
import numpy as np

class Texture():

    def __init__(self, path, backup_path = "assets/test.png"):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        # Texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        
        try:
            if not os.path.exists(path):
                raise FileNotFoundError
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if image is None:
                raise ImportError
        except: 
            image = cv2.imread(backup_path, cv2.IMREAD_UNCHANGED)

        # Flip vertically to match OpenGL's coordinate system
        image = cv2.flip(image, 0)

        # Add full alpha channel if missing
        if image.shape[2] == 3:
            alpha = np.full((image.shape[0], image.shape[1], 1), 255, dtype=np.uint8)
            image = np.concatenate((image, alpha), axis=2)

        # Convert BGR(A) to RGB(A)
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.shape[1], image.shape[0], 0, GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def release(self):
        glDeleteTextures([self.texture])