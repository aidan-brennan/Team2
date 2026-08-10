import pygame
import random
import sys
import os
 
pygame.init()
 
WIDTH = 1000
HEIGHT = 600
 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape the Shark")
 
Gravity = 0.3
Swim_strength = -6
Max_fall_speed = 8
 
diver_x = 80
diver_radius = 16         
diver_size = (90, 70)       
 
tentacle_width = 110
tentacle_gap = 150
tentacle_speed = 3
tentacle_spawn_ms = random.randint(1500,2000)
tentacle_hitbox_inset = 70   
 
Ground_height = 40
FPS = 60
 

TEXT_COLOR = (255, 255, 255)
 
tentacle = pygame.image.load("images/Tentacle.png")
tentacle = pygame.transform.flip(tentacle, True, False)
tentacle_ceiling = pygame.image.load("images/Tentacle Upside Down.png")  
tentacle_ceiling = pygame.transform.flip(tentacle_ceiling, True, False)
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
        self.angle = max(-25, min(90, -self.velocity_y * 4))
 
    def draw(self, surface):
        if jerry is not None:
            rotated = pygame.transform.rotate(jerry, self.angle)
            rect = rotated.get_rect(center=(self.x, int(self.y)))
            surface.blit(rotated, rect)
 
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
 
 
class Tentacle:
    def __init__(self, x):
        self.x = x
        self.gap_y = random.randint(120, HEIGHT - Ground_height - 120)
        self.width = tentacle_width
        self.passed = False
 
    def update(self):
        self.x -= tentacle_speed
 
    def get_rects(self):
        """Full-size rects matching the drawn image — used for drawing."""
        top_rect = pygame.Rect(self.x, 0, self.width, self.gap_y - tentacle_gap // 2)
        bottom_rect = pygame.Rect(
            self.x, self.gap_y + tentacle_gap // 2,
            self.width, HEIGHT - (self.gap_y + tentacle_gap // 2) - Ground_height
        )
        return top_rect, bottom_rect
 
    def get_collision_rects(self):
        """Slightly smaller rects (inset from the drawn edges) — used for collision checks."""
        top_rect, bottom_rect = self.get_rects()
        return (
            top_rect.inflate(-tentacle_hitbox_inset * 2, -tentacle_hitbox_inset),
            bottom_rect.inflate(-tentacle_hitbox_inset * 2, -tentacle_hitbox_inset),
        )
 
    def draw(self, surface):
        top_rect, bottom_rect = self.get_rects()
 
        if tentacle is not None:
            bottom_img = pygame.transform.smoothscale(tentacle, (self.width, bottom_rect.height))
            surface.blit(bottom_img, bottom_rect.topleft)
 
        if tentacle_ceiling is not None:
            top_img = pygame.transform.smoothscale(tentacle_ceiling, (self.width, top_rect.height))
            surface.blit(top_img, top_rect.topleft)
 
    def offscreen(self):
        return self.x + self.width < 0
 
 
def draw_background(surface):
    if background is not None:
        surface.blit(background, (0, 0))
 
def draw_text_center(surface, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(WIDTH // 2, y))
    surface.blit(rendered, rect)
 
 
def reset_game():
    Diver = diver()
    Tentacles = [Tentacle(WIDTH + 100)]
    score = 0
    return Diver, Tentacles, score
 
 
def main():
    Diver, Tentacles, score = reset_game()
    game_over = False
    started = False
 
    last_tentacle_time = pygame.time.get_ticks()
 
    running = True
 
    while running:
        swim_pressed = False
 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    swim_pressed = True
                if event.key == pygame.K_r and game_over:
                    Diver, Tentacles, score = reset_game()
                    game_over = False
                    started = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                swim_pressed = True
 
        if swim_pressed and not game_over:
            started = True
            Diver.swim()
 
        if not game_over and started:
            Diver.update()
 
            now = pygame.time.get_ticks()
            if now - last_tentacle_time > tentacle_spawn_ms:
                Tentacles.append(Tentacle(WIDTH + 20))
                last_tentacle_time = now
 
            for t in Tentacles:
                t.update()
 
            Tentacles[:] = [t for t in Tentacles if not t.offscreen()]
 
            for t in Tentacles:
                if not t.passed and t.x + t.width < Diver.x:
                    t.passed = True
                    score += 1
 
            Diver_rect = Diver.get_rect()
            if Diver.y - Diver.radius <= 0 or Diver.y + Diver.radius >= HEIGHT - Ground_height:
                game_over = True
            for t in Tentacles:
                top_rect, bottom_rect = t.get_collision_rects()
                if Diver_rect.colliderect(top_rect) or Diver_rect.colliderect(bottom_rect):
                    game_over = True
 
       
        draw_background(screen)
        for t in Tentacles:
            t.draw(screen)
        Diver.draw(screen)
 
        draw_text_center(screen, str(score), font_big, (255, 255, 255), 60)
 
        if not started and not game_over:
            draw_text_center(screen, "Press SPACE to start", font_small, TEXT_COLOR, HEIGHT // 2)
 
        if game_over:
            draw_text_center(screen, "Game Over", font_big, (200, 30, 30), HEIGHT // 2 - 30)
            draw_text_center(screen, f"Score: {score}", font_small, TEXT_COLOR, HEIGHT // 2 + 15)
            draw_text_center(screen, "Press R to restart", font_small, TEXT_COLOR, HEIGHT // 2 + 50)
 
        pygame.display.flip()
        clock.tick(FPS)
 
    pygame.quit()
    sys.exit()
 
 
if __name__ == "__main__":
    main()
 

        


    



