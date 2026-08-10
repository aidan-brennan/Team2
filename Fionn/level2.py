import pygame
import random
from os.path import join
 
pygame.init()
 
WIDTH = 1000
HEIGHT = 600
 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape the Kraken")
 
clock = pygame.time.Clock()
 
# Images
background = pygame.image.load(join("images", "background.jpeg")).convert()
background = pygame.transform.scale(background,(WIDTH,HEIGHT))
 
diver = pygame.image.load(join("images", "jerryharpoon-r.png")).convert_alpha()

 
diver = pygame.transform.scale(diver,(80,120))

 
# Positions
diver_x = 250
diver_y = 250
 

velocity = 0
gravity = 0.6
jump = -10
 
score = 0
 
running = True
 
list1=[]
#for a in range(3):
    #list1.append()
 
while running:
 
    clock.tick(60)
 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
 
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                velocity = jump
 
    velocity += gravity
    diver_y += velocity
 
    if diver_y < 0:
        diver_y = 0
 
    if diver_y > HEIGHT-120:
        diver_y = HEIGHT-120
 

    diver_rect = pygame.Rect(diver_x,diver_y,70,110)
   
 
    
    score += 1
 
    font = pygame.font.SysFont(None,40)
    text = font.render("Distance: "+str(score//10),True,(255,255,255))
    screen.blit(text,(20,20))
 
    pygame.display.flip()
 
pygame.quit()