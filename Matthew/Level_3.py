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
pirate_image = pygame.image.load(join("images", "pirate.png")).convert_alpha()

diver_image = pygame.transform.scale(diver_image, (85, 110))
pirate_image = pygame.transform.scale(pirate_image, (150, 120))


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

        self.image = pirate_image

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
pirates = []

pirate_x = 20
pirate_y = 270


# ---------------- GAME VARIABLES ----------------

score = 0

running = True

#-----------------WAVE-----------------------
wave = 1
wave = 1
pirate_in_wave = 3
pirate_spawned = 0

spawn_timer = 0
spawn_delay = 120
# ---------------- GAME LOOP ----------------

while running:

    clock.tick(60)

    # Events
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False


    # Player movement
    player.move()


    # pirate slowly moves across the screen
    spawn_timer += 1

    # Spawn a new pirate
    if spawn_timer >= spawn_delay and pirate_spawned < pirate_in_wave:

        spawn_timer = 0

        # Random height for shark
        pirate_y = random.randint(100, HEIGHT - 150)

        new_pirate = Pirate(WIDTH, pirate_y)

        pirates.append(new_pirate)

        pirate_spawned += 1


    # Move all pirtaes
    for pirate_enemy in pirates:
        pirate_enemy.move()


    # Remove pirates that have gone off screen
    for pirate_enemy in pirates[:]:

        if pirate_enemy.x < -100:
            pirates.remove(pirate_enemy)


    # Start next wave when all sharks are gone
    if pirate_spawned == pirate_in_wave and len(pirates) == 0:

        wave += 1

        pirate_in_wave += 1

        pirate_spawned = 0

        spawn_timer = 0

    #---------pirate collision---------
    if invincibility_timer > 0:
        invincibility_timer -= 1


    for pirate_enemy in pirates[:]:

        if player.get_rect().colliderect(pirate_enemy.get_rect()):

            if invincibility_timer == 0:

                lives -= 1
                invincibility_timer = 120

                pirates.remove(pirate_enemy)

                if lives <= 0:
                    running = False



    # ---------------- DRAW ----------------

    screen.blit(background, (0, 0))

    for pirate_enemy in pirates:
        pirate_enemy.draw()

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

    lives_text = font.render(
        "Lives: " + str(lives),
        True,
        (255, 255, 255)
    )

    screen.blit(lives_text, (20, 60))

    wave_text = font.render(
        "Wave: " + str(wave),
        True,
        (255, 255, 255)
    )

    screen.blit(wave_text, (20, 100))


    pygame.display.flip()


pygame.quit()