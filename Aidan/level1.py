import pygame
from random import randint, uniform
from os.path import join

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load('images/jerryharpoon.png')
        self.rect = self.image.get_frect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.Vector2()
        self.mask = pygame.mask.from_surface(self.image)

        self.normal_surf = self.image.copy()
        self.speed = 600
        self.rotation_speed = randint(40,800)
        self.rotation = 0

        self.can_shoot = True
        self.harpoon_shoot_time = 0
        self.cooldown_duration = 200

        self.flash_surf = self.mask.to_surface(unsetcolor=(0, 0, 0, 0), setcolor=(255, 255 ,255 ,255))
        self.is_flashing = False
        self.flash_time = 0
        self.flash_duration = 150
        self.health = 3

    def harpoon_timer(self):
        if not self.can_shoot:
            currrent_time = pygame.time.get_ticks()
            if currrent_time - self.harpoon_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt

        if self.direction.x > 0:
            self.image = pygame.transform.flip(self.normal_surf, True, False)

        elif self.direction.x < 0:
            self.image = pygame.transform.flip(self.normal_surf, False, False)

        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        direction = mouse_pos - self.rect.center

        recent_mouse = pygame.mouse.get_just_pressed()
        if recent_mouse[0] and self.can_shoot:
            direction = pygame.Vector2(mouse_pos) - self.rect.center

            if direction:
                direction = direction.normalize()
                
                gun_pos = self.rect.center + direction * 60
                Harpoon(harpoon_surf, self.rect.center,direction, (all_sprites, harpoon_sprites))
            
            self.harpoon_shoot_time = pygame.time.get_ticks()

class Harpoon(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom = pos)
        self.direction = direction

        angle = self.direction.angle_to(pygame.Vector2(-1, 0))
        self.image = pygame.transform.rotate(self.image, angle)
    def update(self, dt):
        self.rect.center += self.direction * 300 * dt
        if not display_surface.get_rect().colliderect(self.rect):
            self.kill()

pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
background = pygame.image.load("images/background.jpeg")
running = True
clock = pygame.time.Clock()

harpoon_surf=pygame.image.load("images/harpoon.png")
all_sprites = pygame.sprite.Group()
harpoon_sprites = pygame.sprite.Group()
player = Player(all_sprites)

while running:

    dt = clock.tick()/1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    all_sprites.update(dt)

    display_surface.blit(background, (0, 0))
    all_sprites.draw(display_surface)

    pygame.display.update()

pygame.quit()