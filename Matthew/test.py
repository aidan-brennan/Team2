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

diver_image = pygame.image.load(
    join("images", "walking_jerry1.png")
).convert_alpha()

pirate_image = pygame.image.load(
    join("images", "pirate.png")
).convert_alpha()

diver_image = pygame.transform.scale(diver_image, (95, 120))
pirate_image = pygame.transform.scale(pirate_image, (150, 120))


# ---------------- PLAYER CLASS ----------------

class Player:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 85
        self.height = 110

        self.speed = 5

        self.image = diver_image

        # Sword attack
        self.attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 0

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


    def attack(self):

        # Player can only attack when cooldown is finished
        if self.attack_cooldown == 0:

            self.attacking = True

            # How long the sword is active
            self.attack_timer = 10

            # How long before player can attack again
            self.attack_cooldown = 25


    def update_attack(self):

        if self.attack_timer > 0:

            self.attack_timer -= 1

        else:

            self.attacking = False


        if self.attack_cooldown > 0:

            self.attack_cooldown -= 1


    def draw(self):

        screen.blit(self.image, (self.x, self.y))

        # Draw sword hitbox while attacking
        if self.attacking:

            sword_rect = self.get_sword_rect()

            pygame.draw.rect(
                screen,
                (255, 255, 0),
                sword_rect
            )


    def get_rect(self):

        return pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )


    def get_sword_rect(self):

        if self.attacking:

            return pygame.Rect(
                self.x + self.width - 10,
                self.y + 25,
                80,
                60
            )

        return pygame.Rect(0, 0, 0, 0)


# ---------------- PIRATE CLASS ----------------

class Pirate:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 150
        self.height = 120

        self.speed = 2

        self.image = pirate_image


    def move_towards_player(self, player):

        # Find difference between pirate and player
        dx = player.x - self.x
        dy = player.y - self.y

        # Move horizontally towards player
        if dx > 0:

            self.x += self.speed

        elif dx < 0:

            self.x -= self.speed


        # Move vertically towards player
        if dy > 0:

            self.y += self.speed

        elif dy < 0:

            self.y -= self.speed


    def draw(self):

        screen.blit(
            self.image,
            (self.x, self.y)
        )


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

invincibility_timer = 0


# ---------------- PIRATES ----------------

pirates = []


# ---------------- GAME VARIABLES ----------------

score = 0

running = True


# ---------------- WAVE ----------------

wave = 1

pirate_in_wave = 3

pirate_spawned = 0

spawn_timer = 0

spawn_delay = 120


# ---------------- GAME LOOP ----------------

while running:

    clock.tick(60)


    # ---------------- EVENTS ----------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False


        # Spacebar attack
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:

                player.attack()


    # ---------------- PLAYER ----------------

    player.move()

    player.update_attack()


    # ---------------- PIRATE SPAWNING ----------------

    spawn_timer += 1


    # Spawn a new pirate
    if spawn_timer >= spawn_delay and pirate_spawned < pirate_in_wave:

        spawn_timer = 0

        # Random height
        pirate_y = random.randint(
            100,
            HEIGHT - 150
        )

        # Spawn on right side
        new_pirate = Pirate(
            WIDTH,
            pirate_y
        )

        pirates.append(new_pirate)

        pirate_spawned += 1


    # ---------------- PIRATE MOVEMENT ----------------

    for pirate_enemy in pirates:

        pirate_enemy.move_towards_player(player)


    # ---------------- SWORD COLLISION ----------------

    sword_rect = player.get_sword_rect()


    for pirate_enemy in pirates[:]:

        if sword_rect.colliderect(
            pirate_enemy.get_rect()
        ):

            # Pirate has been hit
            pirates.remove(pirate_enemy)


    # ---------------- REMOVE PIRATES ----------------

    for pirate_enemy in pirates[:]:

        if pirate_enemy.x < -200:

            pirates.remove(pirate_enemy)


    # ---------------- NEXT WAVE ----------------

    if pirate_spawned == pirate_in_wave and len(pirates) == 0:

        wave += 1

        pirate_in_wave += 1

        pirate_spawned = 0

        spawn_timer = 0


    # ---------------- PIRATE COLLISION ----------------

    if invincibility_timer > 0:

        invincibility_timer -= 1


    for pirate_enemy in pirates[:]:

        if player.get_rect().colliderect(
            pirate_enemy.get_rect()
        ):

            if invincibility_timer == 0:

                lives -= 1

                # 2 seconds of invincibility
                invincibility_timer = 120

                # Remove pirate after hitting player
                pirates.remove(pirate_enemy)

                if lives <= 0:

                    running = False


    # ---------------- DRAW ----------------

    screen.blit(
        background,
        (0, 0)
    )


    # Draw pirates
    for pirate_enemy in pirates:

        pirate_enemy.draw()


    # Draw player
    player.draw()


    # ---------------- SCORE ----------------

    score += 1


    font = pygame.font.SysFont(
        None,
        40
    )


    # Distance
    text = font.render(
        "Distance: " + str(score // 10),
        True,
        (255, 255, 255)
    )

    screen.blit(
        text,
        (20, 20)
    )


    # Lives
    lives_text = font.render(
        "Lives: " + str(lives),
        True,
        (255, 255, 255)
    )

    screen.blit(
        lives_text,
        (20, 60)
    )


    # Wave
    wave_text = font.render(
        "Wave: " + str(wave),
        True,
        (255, 255, 255)
    )

    screen.blit(
        wave_text,
        (20, 100)
    )


    pygame.display.flip()


pygame.quit()