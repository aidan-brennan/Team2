import pygame
import random
from os.path import join

pygame.init()

WIDTH = 1000
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fight the Pirate Crew")

clock = pygame.time.Clock()


# ---------------- IMAGES ----------------

background = pygame.image.load(join("images", "shipwreck.png")).convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

diver_image = pygame.image.load(join("images", "walking_jerry.png")).convert_alpha()
pirate = pygame.image.load(join("images", "pirate.png")).convert_alpha()

diver_image = pygame.transform.scale(diver_image, (85, 110))
pirate = pygame.transform.scale(pirate, (150, 120))


# ---------------- PLAYER CLASS ----------------

class Player:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.width = 80
        self.height = 120

        self.speed = 5

        self.image = diver_image

    def move(self):
        keys = pygame.key.get_pressed()

        # Arrow key movement
        if keys[pygame.K_LEFT]:
            self.x -= self.speed

        if keys[pygame.K_RIGHT]:
            self.x += self.speed

        if keys[pygame.K_UP]:
            self.y -= self.speed

        if keys[pygame.K_DOWN]:
            self.y += self.speed

        # Stop player leaving the screen
        if self.x < 0:
            self.x = 0

        if self.x > WIDTH - self.width:
            self.x = WIDTH - self.width

        if self.y < 0:
            self.y = 0

        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


#-----------------PIRATE CLASS-------------------
class Pirate:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.width = 100
        self.height = 90

        self.speed = 3

        self.image = pirate

    def move(self):
        self.x -= self.speed

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        return pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )
# ---------------- CREATE PLAYER ----------------

player = Player(250, 250)
lives = 3

#-----------------invincibility_timer
invincibility_timer = 0


# ---------------- SHARK ----------------
sharks = []

pirate_x = 20
pirate_y = 270


# ---------------- GAME VARIABLES ----------------

score = 0

running = True


# ---------------- GAME LOOP ----------------

while running:

    clock.tick(60)

    # Events
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False


    # Player movement
    player.move()


    # Shark slowly moves across the screen
    if pirate_x < WIDTH:
        pirate_x += 1

    if pirate_x >= WIDTH:
        pirate_x = 0


    # ---------------- DRAW ----------------

    screen.blit(background, (0, 0))

    screen.blit(pirate, (pirate_x, pirate_y))

    player.draw()


    # ---------------- COLLISION ----------------

    player_rect = player.get_rect()

    pirate_rect = pygame.Rect(
        pirate_x + 40,
        pirate_y + 10,
        60,
        60
    )

    if player_rect.colliderect(pirate_rect):
        running = False


    # ---------------- SCORE ----------------

    score += 1

    font = pygame.font.SysFont(None, 40)

    text = font.render(
        "Distance: " + str(score // 10),
        True,
        (255, 255, 255)
    )

    screen.blit(text, (20, 20))


    pygame.display.flip()


pygame.quit()