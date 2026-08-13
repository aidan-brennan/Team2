import pygame
import random
import sys
import os
import math
from oxygentank import OxygenSystem
 
pygame.init()
 
WIDTH = 1000
HEIGHT = 600
 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape the Shark")
 
Gravity = 0.3
Swim_strength = -7
Max_fall_speed = 6
 
diver_x = 80
diver_radius = 16         
diver_size = (95, 75)       
 
tentacle_width = 110
tentacle_gap = 120
tentacle_speed = 4
tentacle_spawn_min = 1000
tentacle_spawn_max = 2000
tentacle_spawn_ms = random.randint(tentacle_spawn_min, tentacle_spawn_max)
 
Ground_height = 40
FPS = 60
 

TEXT_COLOR = (255, 255, 255)
 
tentacle = pygame.image.load("images/newredtentacle.png")
tentacle = pygame.transform.flip(tentacle, True, False)
tentacle_ceiling = pygame.transform.flip(tentacle, False, True)
background = pygame.image.load("images/cave.png")
background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT)) 
 
jerry = pygame.image.load('images/jerryharpoon.png')
jerry = pygame.transform.smoothscale(jerry, diver_size)  
jerry = pygame.transform.rotate(jerry, angle=270)
jerry = pygame.transform.flip(jerry, False, True)



 
clock = pygame.time.Clock()
font_big = pygame.font.SysFont(None, 64)
font_small = pygame.font.SysFont(None, 32)
 
 
class diver:
    def __init__(self):
        self.x = diver_x
        self.y = HEIGHT // 2
        self.velocity_y = 0
        self.radius = diver_radius
        self.angle = 0
 
    def swim(self):
        self.velocity_y = Swim_strength
 
    def update(self):
        self.velocity_y += Gravity
        self.velocity_y = min(self.velocity_y, Max_fall_speed)
        self.y += self.velocity_y
        self.angle = max(-5, min(100, -self.velocity_y * 4))
 
    def draw(self, surface):
        if jerry is not None:
            rotated = pygame.transform.rotate(jerry, self.angle)
            rect = rotated.get_rect(center=(self.x, int(self.y)))
            surface.blit(rotated, rect)
 
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
 
 
class Tentacle:
    SWAY_AMPLITUDE = 4
    SWAY_SPEED     = 0.004

    def __init__(self, x):
        self.x = x
        self.gap_y = random.randint(120, HEIGHT - Ground_height - 120)
        self.width = tentacle_width
        self.passed = False
        self.time_offset = random.uniform(0, 2 * math.pi)
        # cached scaled images and masks, rebuilt only when height changes
        self._last_top_h = -1
        self._last_bot_h = -1
        self._top_img = None
        self._bot_img = None
        self._top_mask = None
        self._bot_mask = None

    def update(self):
        self.x -= tentacle_speed

    def get_rects(self):
        top_rect = pygame.Rect(self.x, 0, self.width, self.gap_y - tentacle_gap // 2)
        bottom_rect = pygame.Rect(
            self.x, self.gap_y + tentacle_gap // 2,
            self.width, HEIGHT - (self.gap_y + tentacle_gap // 2) - Ground_height
        )
        return top_rect, bottom_rect

    def _get_scaled(self):
        """Return (top_img, bot_img, top_mask, bot_mask), rebuilding only when sizes change."""
        top_rect, bottom_rect = self.get_rects()
        if top_rect.height != self._last_top_h:
            self._top_img = pygame.transform.smoothscale(tentacle_ceiling, (self.width, max(1, top_rect.height)))
            self._top_mask = pygame.mask.from_surface(self._top_img)
            self._last_top_h = top_rect.height
        if bottom_rect.height != self._last_bot_h:
            self._bot_img = pygame.transform.smoothscale(tentacle, (self.width, max(1, bottom_rect.height)))
            self._bot_mask = pygame.mask.from_surface(self._bot_img)
            self._last_bot_h = bottom_rect.height
        return self._top_img, self._bot_img, self._top_mask, self._bot_mask

    def check_collision(self, player_rect):
        """Pixel-perfect collision between the player rect and both tentacles."""
        top_rect, bottom_rect = self.get_rects()
        _, _, top_mask, bot_mask = self._get_scaled()

        player_mask = pygame.mask.Mask((player_rect.width, player_rect.height), fill=True)

        # offset = tentacle_topleft - player_topleft
        for t_rect, t_mask in ((top_rect, top_mask), (bottom_rect, bot_mask)):
            offset = (t_rect.x - player_rect.x, t_rect.y - player_rect.y)
            if player_mask.overlap(t_mask, offset):
                return True
        return False

    def draw(self, surface):
        top_rect, bottom_rect = self.get_rects()
        top_img, bot_img, _, _ = self._get_scaled()

        now = pygame.time.get_ticks()
        sway = int(math.sin(now * self.SWAY_SPEED + self.time_offset) * self.SWAY_AMPLITUDE)

        surface.blit(bot_img, bottom_rect.move(sway, 0))
        surface.blit(top_img, top_rect.move(-sway, 0))

    def offscreen(self):
        return self.x + self.width < 0
 
 
class Bubble:
    """A small translucent bubble that drifts upward with a gentle sway."""

    def __init__(self, x, y):
        self.radius = random.randint(2, 6)
        self.x = float(x)
        self.y = float(y)
        self.rise_speed = random.uniform(30, 80)
        self.sway_amount = random.uniform(4, 14)
        self.sway_speed = random.uniform(1.5, 3.5)
        self.age = 0.0
        self.lifetime = random.uniform(2.5, 5.5)
        # white, mostly opaque bubble surface
        size = self.radius * 2 + 2
        self._surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self._surf, (240, 248, 255, 90),
                           (self.radius + 1, self.radius + 1), self.radius)
        pygame.draw.circle(self._surf, (255, 255, 255, 200),
                           (self.radius + 1, self.radius + 1), self.radius, 1)
        # highlight dot
        pygame.draw.circle(self._surf, (255, 255, 255, 230),
                           (self.radius - 1, self.radius - 1), max(1, self.radius // 3))

    def update(self, dt):
        self.age += dt
        self.y -= self.rise_speed * dt
        self.x -= tentacle_speed                                      # scroll left with the world
        self.x += math.sin(self.age * self.sway_speed) * self.sway_amount * dt

    def draw(self, surface):
        surface.blit(self._surf, (int(self.x) - self.radius, int(self.y) - self.radius))

    def dead(self):
        return self.age >= self.lifetime or self.y + self.radius < 0 or self.x + self.radius < 0


def draw_background(surface, bg_x):
    if background is not None:
        surface.blit(background, (bg_x, 0))
        surface.blit(background, (bg_x + WIDTH, 0))
 
def draw_text_center(surface, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(WIDTH // 2, y))
    surface.blit(rendered, rect)
 
 
def reset_game():
    Diver = diver()
    Tentacles = [Tentacle(WIDTH + 100)]
    score = 0
    bg_x = 0
    oxygen_system = OxygenSystem(WIDTH, HEIGHT, image_path="images/o2 tank.png")
    # seed a small number of ground bubbles so the screen isn't bare at start
    bubbles = [Bubble(random.randint(0, WIDTH), HEIGHT - Ground_height) for _ in range(6)]
    return Diver, Tentacles, score, oxygen_system, bg_x, bubbles

def main():
    global tentacle_spawn_ms
    Diver, Tentacles, score, oxygen_system, bg_x, bubbles = reset_game()
    game_over = False
    level_complete = False
    started = False

    last_tentacle_time = pygame.time.get_ticks()

    running = True

    while running:
        dt = clock.tick(FPS) / 1000   # seconds elapsed this frame
        swim_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    swim_pressed = True
                if event.key == pygame.K_r and game_over:
                    Diver, Tentacles, score, oxygen_system, bg_x, bubbles = reset_game()
                    last_tentacle_time = pygame.time.get_ticks()
                    game_over = False
                    level_complete = False
                    started = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                swim_pressed = True

        if swim_pressed and not game_over and not level_complete:
            if not started:
                last_tentacle_time = pygame.time.get_ticks()
            started = True
            Diver.swim()

        if not game_over and not level_complete and started:
            Diver.update()

            # scroll background
            bg_x -= tentacle_speed
            if bg_x <= -WIDTH:
                bg_x = 0

            # update bubbles and remove dead ones
            for b in bubbles:
                b.update(dt)
            bubbles = [b for b in bubbles if not b.dead()]

            # trail behind the diver: ~3 bubbles/sec from just behind the player
            if random.random() < 3 * dt:
                trail_x = Diver.x + random.randint(-20, 5)
                trail_y = Diver.y + random.randint(-8, 8)
                bubbles.append(Bubble(trail_x, trail_y))

            # ground bubbles: ~1 bubble/sec from a random point along the floor
            if random.random() < 1 * dt:
                ground_x = random.randint(0, WIDTH)
                bubbles.append(Bubble(ground_x, HEIGHT - Ground_height))

            now = pygame.time.get_ticks()
            if now - last_tentacle_time > tentacle_spawn_ms:
                Tentacles.append(Tentacle(WIDTH + 20))
                last_tentacle_time = now
                tentacle_spawn_ms = random.randint(tentacle_spawn_min, tentacle_spawn_max)

            for t in Tentacles:
                t.update()

            Tentacles[:] = [t for t in Tentacles if not t.offscreen()]

            for t in Tentacles:
                if not t.passed and t.x + t.width < Diver.x:
                    t.passed = True
                    score += 1
                    if score >= 30:
                        level_complete = True

            Diver_rect = Diver.get_rect()
            if Diver.y - Diver.radius <= 0 or Diver.y + Diver.radius >= HEIGHT - Ground_height:
                game_over = True
            for t in Tentacles:
                if t.check_collision(Diver_rect):
                    game_over = True

            # oxygen system: update and check for out-of-oxygen
            if oxygen_system.update(dt, Diver.get_rect(), scroll_speed=tentacle_speed):
                game_over = True

        draw_background(screen, bg_x)
        for b in bubbles:
            b.draw(screen)
        for t in Tentacles:
            t.draw(screen)
        Diver.draw(screen)
        oxygen_system.draw(screen)
        oxygen_system.draw_bar(screen)

        draw_text_center(screen, str(score), font_big, (255, 255, 255), 60)

        if not started and not game_over:
            draw_text_center(screen, "Press SPACE to start", font_small, TEXT_COLOR, HEIGHT // 2)

        if game_over:
            draw_text_center(screen, "Game Over", font_big, (200, 30, 30), HEIGHT // 2 - 30)
            draw_text_center(screen, f"Score: {score}", font_small, TEXT_COLOR, HEIGHT // 2 + 15)
            draw_text_center(screen, "Press R to restart", font_small, TEXT_COLOR, HEIGHT // 2 + 50)

        if level_complete:
            draw_text_center(screen, "Level 2 Complete!", font_big, (50, 220, 50), HEIGHT // 2 - 30)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()



