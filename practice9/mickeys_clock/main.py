# main.py
import pygame
import datetime

class MickeyClock:
    def __init__(self, center_point):
        self.center_point = center_point
        self.bg = pygame.image.load('images/mickey_no_arms.png')
        self.hand_min_img = pygame.image.load('images/mickey_right-hand.png')
        self.hand_sec_img = pygame.image.load('images/mickey_left-hand.png')

    def rotate_center(self, image, angle):
        rotated_image = pygame.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center=self.center_point)
        return rotated_image, new_rect

    def draw(self, screen):
        now = datetime.datetime.now()
        
        angle_sec = -(now.second * 6) - 32
        angle_min = -(now.minute * 6) + 120

        screen.blit(self.bg, (0, 0))

        img_min, rect_min = self.rotate_center(self.hand_min_img, angle_min)
        img_sec, rect_sec = self.rotate_center(self.hand_sec_img, angle_sec)

        screen.blit(img_min, rect_min)
        screen.blit(img_sec, rect_sec)