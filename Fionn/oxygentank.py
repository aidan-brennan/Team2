

import pygame
import random
import math 


class OxygenTank:
    

    BOB_AMPLITUDE = 5      # pixels up/down
    BOB_SPEED     = 0.009  # radians per millisecond

    def __init__(self, x, y, image, refill_amount):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.base_y = y                          # stable Y for collision
        self.time_offset = random.uniform(0, 2 * math.pi)  # random phase
        self.refill_amount = refill_amount
        self.collected = False

    def update(self, speed):
        """Move the tank left at the given scroll speed."""
        self.rect.x -= speed

    def offscreen(self):
        return self.rect.right < 0

    def draw(self, surface):
        if not self.collected:
            now = pygame.time.get_ticks()
            bob = math.sin(now * self.BOB_SPEED + self.time_offset) * self.BOB_AMPLITUDE
            draw_rect = self.rect.move(0, int(bob))
            surface.blit(self.image, draw_rect)

    def check_collect(self, player_rect):
        if not self.collected and self.rect.colliderect(player_rect):
            self.collected = True
            return True
        return False


class OxygenSystem:
  

    def __init__(
        self,
        screen_width,
        screen_height,
        image_path,
        tank_size=(60, 60),
        max_oxygen=100,
        drain_per_second=5,
        refill_amount=35,
        max_tanks_on_screen=2,
        respawn_delay_ms=(4000, 6000),
        margin=40,
        
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tank_size = tank_size

        self.max_oxygen = max_oxygen
        self.oxygen = max_oxygen
        self.drain_per_second = drain_per_second
        self.refill_amount = refill_amount
        self.angle = 0
        self.rotation_speed = 2  

        self.max_tanks_on_screen = max_tanks_on_screen
        self.respawn_delay_ms = respawn_delay_ms
        self.margin = margin

        raw_image = pygame.image.load("images/o2 tank.png").convert_alpha()
        self.image = pygame.transform.smoothscale(raw_image, tank_size)

        self.tanks = []
        self.next_spawn_time = 0
        self._queue_next_spawn(immediate=True)

    def update(self):
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, frame_count):
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        bob_offset = math.sin(frame_count * 0.1) * 5
        self.rect = self.image.get_rect(center=(self.base_x, self.base_y + bob_offset))

    def _queue_next_spawn(self, immediate=False):
        delay = 0 if immediate else random.randint(*self.respawn_delay_ms)
        self.next_spawn_time = pygame.time.get_ticks() + delay

    def _spawn_tank(self):
        # Spawn just off the right edge so the tank scrolls in like tentacles
        x = self.screen_width + self.margin
        y = random.randint(self.margin, self.screen_height - self.margin - self.tank_size[1])
        self.tanks.append(OxygenTank(x, y, self.image, self.refill_amount))

    # -- public API ---------------------------------------------------

    def reset(self):
        """Call this whenever your game resets/restarts."""
        self.oxygen = self.max_oxygen
        self.tanks = []
        self._queue_next_spawn(immediate=True)

    def add_oxygen(self, amount):
        self.oxygen = min(self.max_oxygen, self.oxygen + amount)

    def update(self, dt, player_rect, scroll_speed=3):
      
        # deplete oxygen over time
        self.oxygen -= self.drain_per_second * dt
        self.oxygen = max(0, self.oxygen)

        # spawn new tanks up to the max, on a random delay
        now = pygame.time.get_ticks()
        if len(self.tanks) < self.max_tanks_on_screen and now >= self.next_spawn_time:
            self._spawn_tank()
            self._queue_next_spawn()

        # scroll tanks left (same speed as tentacles)
        for tank in self.tanks:
            tank.update(scroll_speed)

        # check collection
        for tank in self.tanks:
            if tank.check_collect(player_rect):
                self.add_oxygen(tank.refill_amount)

        # remove tanks that were collected or have scrolled off screen
        self.tanks = [t for t in self.tanks if not t.collected and not t.offscreen()]

        return self.oxygen <= 0

    def draw(self, surface):
        for tank in self.tanks:
            tank.draw(surface)

    def draw_bar(self, surface, x=10, y=10, width=200, height=20):
        pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))
        fill_width = width * (self.oxygen / self.max_oxygen)
        color = (0, 200, 255) if self.oxygen > 30 else (255, 60, 60)
        pygame.draw.rect(surface, color, (x, y, fill_width, height))
        pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)

        # percentage label just below the bar
        pct = int(self.oxygen / self.max_oxygen * 100)
        font = pygame.font.SysFont(None, 24)
        label = font.render(f"{pct}%", True, (255, 255, 255))
        surface.blit(label, (x, y + height + 4))
        


if __name__ == "__main__":
    pygame.init()

    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Oxygen System Demo")
    clock = pygame.time.Clock()
    FPS = 60

    player = pygame.Rect(WIDTH // 2, HEIGHT // 2, 32, 32)
    player_speed = 250  # pixels per second

    system = OxygenSystem(WIDTH, HEIGHT, image_path="images/o2 tank.png")

    font = pygame.font.SysFont(None, 32)
    running = True
    game_over = False

    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
                system.reset()
                player.center = (WIDTH // 2, HEIGHT // 2)
                game_over = False

        if not game_over:
            keys = pygame.key.get_pressed()
            move = player_speed * dt
            if keys[pygame.K_LEFT]:
                player.x -= move
            if keys[pygame.K_RIGHT]:
                player.x += move
            if keys[pygame.K_UP]:
                player.y -= move
            if keys[pygame.K_DOWN]:
                player.y += move
            player.clamp_ip(screen.get_rect())

            if system.update(dt, player, scroll_speed=3):
                game_over = True

        screen.fill((10, 10, 30))
        pygame.draw.rect(screen, (255, 255, 255), player)
        system.draw(screen)
        system.draw_bar(screen)

        if game_over:
            text = font.render("Out of oxygen! Press R to restart", True, (255, 80, 80))
            screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        pygame.display.flip()

    pygame.quit()
