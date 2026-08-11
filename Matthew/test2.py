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

background = pygame.image.load(
    join("images", "shipwreck.png")
).convert()

background = pygame.transform.scale(
    background,
    (WIDTH, HEIGHT)
)

diver_image = pygame.image.load(
    join("images", "walking_jerry1.png")
).convert_alpha()

pirate_image = pygame.image.load(
    join("images", "pirate.png")
).convert_alpha()

harpoon_image = pygame.image.load(
    join("images", "harpoon.png")
).convert_alpha()


diver_image = pygame.transform.scale(
    diver_image,
    (85, 110)
)

pirate_image = pygame.transform.scale(
    pirate_image,
    (150, 120)
)

harpoon_image = pygame.transform.scale(
    harpoon_image,
    (150, 50)
)


# =========================================================
#                    GAME SETTINGS
# =========================================================

# CHANGE THIS TO MATCH THE TOP OF YOUR PLAYABLE AREA
TOP_BARRIER = 150

# Harpoon cooldown
# 60 = 1 second
# 120 = 2 seconds
# 180 = 3 seconds
SHOOT_COOLDOWN = 120


# =========================================================
#                    PLAYER CLASS
# =========================================================

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

        # Arrow keys
        if keys[pygame.K_LEFT]:
            self.x -= self.speed

        if keys[pygame.K_RIGHT]:
            self.x += self.speed

        if keys[pygame.K_UP]:
            self.y -= self.speed

        if keys[pygame.K_DOWN]:
            self.y += self.speed


        # ---------------- SCREEN BARRIERS ----------------

        # Left wall
        if self.x < 0:
            self.x = 0

        # Right wall
        if self.x > WIDTH - self.width:
            self.x = WIDTH - self.width

        # Top wall
        if self.y < TOP_BARRIER:
            self.y = TOP_BARRIER

        # Bottom wall
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height


    # ---------------- SWORD ATTACK ----------------

    def attack(self):

        if self.attack_cooldown == 0:

            self.attacking = True

            self.attack_timer = 10

            self.attack_cooldown = 25


    def update_attack(self):

        if self.attack_timer > 0:

            self.attack_timer -= 1

        else:

            self.attacking = False


        if self.attack_cooldown > 0:

            self.attack_cooldown -= 1


    def get_sword_rect(self):

        if self.attacking:

            return pygame.Rect(
                self.x + self.width - 10,
                self.y + 25,
                80,
                60
            )

        return pygame.Rect(0, 0, 0, 0)


    def draw(self):

        screen.blit(
            self.image,
            (self.x, self.y)
        )

        # Temporary yellow sword hitbox
        # Remove this later when you add the sword image
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


# =========================================================
#                    PIRATE CLASS
# =========================================================

class Pirate:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 150
        self.height = 120

        self.speed = 2

        self.image = pirate_image


    def move_towards_player(self, player):

        # Find horizontal difference
        dx = player.x - self.x

        if dx > 0:
            self.x += self.speed

        elif dx < 0:
            self.x -= self.speed


        # Find vertical difference
        dy = player.y - self.y

        if dy > 0:
            self.y += self.speed

        elif dy < 0:
            self.y -= self.speed


        # Stop pirate going through top wall
        if self.y < TOP_BARRIER:
            self.y = TOP_BARRIER

        # Stop pirate going through bottom wall
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height


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


# =========================================================
#                    HARPOON CLASS
# =========================================================

class Bullet:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 50
        self.height = 20

        self.speed = 10


    def move(self):

        self.x += self.speed


    def draw(self):

        # Draw the harpoon PNG
        screen.blit(
            harpoon_image,
            (self.x, self.y)
        )


    def get_rect(self):

        return pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )


# =========================================================
#                    CREATE PLAYER
# =========================================================

player = Player(
    250,
    250
)

lives = 3

invincibility_timer = 0


# =========================================================
#                    PIRATES
# =========================================================

pirates = []


# =========================================================
#                    HARPOONS
# =========================================================

bullets = []

shoot_cooldown = 0


# =========================================================
#                    GAME VARIABLES
# =========================================================

score = 0

running = True


# =========================================================
#                    WAVES
# =========================================================

wave = 1

pirate_in_wave = 3

pirate_spawned = 0

spawn_timer = 0

spawn_delay = 120


# =========================================================
#                    GAME LOOP
# =========================================================

while running:

    clock.tick(60)


    # =====================================================
    #                    EVENTS
    # =====================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False


        if event.type == pygame.KEYDOWN:

            # ---------------- SPACE = SWORD ----------------

            if event.key == pygame.K_SPACE:

                player.attack()


            # ---------------- X = HARPOON ----------------

            if event.key == pygame.K_x:

                if shoot_cooldown == 0:

                    # Spawn harpoon in front of Jerry
                    new_bullet = Bullet(
                        player.x + player.width,
                        player.y + 45
                    )

                    bullets.append(
                        new_bullet
                    )

                    # Start cooldown
                    shoot_cooldown = SHOOT_COOLDOWN


    # =====================================================
    #                    PLAYER
    # =====================================================

    player.move()

    player.update_attack()


    # =====================================================
    #                    HARPOON COOLDOWN
    # =====================================================

    if shoot_cooldown > 0:

        shoot_cooldown -= 1


    # =====================================================
    #                    PIRATE SPAWNING
    # =====================================================

    spawn_timer += 1


    if (
        spawn_timer >= spawn_delay
        and pirate_spawned < pirate_in_wave
    ):

        spawn_timer = 0

        # Spawn pirate between the barriers
        pirate_y = random.randint(
            TOP_BARRIER,
            HEIGHT - 150
        )

        new_pirate = Pirate(
            WIDTH,
            pirate_y
        )

        pirates.append(
            new_pirate
        )

        pirate_spawned += 1


    # =====================================================
    #                    PIRATE MOVEMENT
    # =====================================================

    for pirate_enemy in pirates:

        pirate_enemy.move_towards_player(
            player
        )


    # =====================================================
    #                    HARPOON MOVEMENT
    # =====================================================

    for bullet in bullets:

        bullet.move()


    # =====================================================
    #             HARPOON / PIRATE COLLISION
    # =====================================================

    for bullet in bullets[:]:

        for pirate_enemy in pirates[:]:

            if bullet.get_rect().colliderect(
                pirate_enemy.get_rect()
            ):

                # Kill pirate
                pirates.remove(
                    pirate_enemy
                )

                # Remove harpoon
                if bullet in bullets:

                    bullets.remove(
                        bullet
                    )

                break


    # =====================================================
    #              REMOVE HARPOONS OFF SCREEN
    # =====================================================

    for bullet in bullets[:]:

        if bullet.x > WIDTH:

            bullets.remove(
                bullet
            )


    # =====================================================
    #              REMOVE PIRATES
    # =====================================================

    for pirate_enemy in pirates[:]:

        if pirate_enemy.x < -200:

            pirates.remove(
                pirate_enemy
            )


    # =====================================================
    #                    NEXT WAVE
    # =====================================================

    if (
        pirate_spawned == pirate_in_wave
        and len(pirates) == 0
    ):

        wave += 1

        pirate_in_wave += 1

        pirate_spawned = 0

        spawn_timer = 0


    # =====================================================
    #                SWORD COLLISION
    # =====================================================

    sword_rect = player.get_sword_rect()


    for pirate_enemy in pirates[:]:

        if sword_rect.colliderect(
            pirate_enemy.get_rect()
        ):

            pirates.remove(
                pirate_enemy
            )


    # =====================================================
    #                PIRATE COLLISION
    # =====================================================

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

                pirates.remove(
                    pirate_enemy
                )

                if lives <= 0:

                    running = False


    # =====================================================
    #                    DRAW
    # =====================================================

    screen.blit(
        background,
        (0, 0)
    )


    # Draw pirates
    for pirate_enemy in pirates:

        pirate_enemy.draw()


    # Draw harpoons
    for bullet in bullets:

        bullet.draw()


    # Draw player
    player.draw()


    # =====================================================
    #                    SCORE
    # =====================================================

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


    # =====================================================
    #                HARPOON COOLDOWN
    # =====================================================

    if shoot_cooldown == 0:

        shoot_text = font.render(
            "Harpoon: READY",
            True,
            (255, 255, 255)
        )

    else:

        seconds = shoot_cooldown / 60

        shoot_text = font.render(
            "Harpoon: " + str(round(seconds, 1)) + "s",
            True,
            (255, 255, 255)
        )

    screen.blit(
        shoot_text,
        (20, 140)
    )


    pygame.display.flip()


pygame.quit()