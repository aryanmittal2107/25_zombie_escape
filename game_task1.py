import pygame
import random
import math
import time

WIDTH, HEIGHT = 800, 560
FPS = 60
BG = (30,35,25)


class Zombie:
    SPEED = 1.5

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.color = (60,140,60)
        self.hp = 3
        self.wobble = random.uniform(0, 6.28)
        self.frame = 0
    def update(self, player_pos):
        px, py = player_pos
        cx, cy = self.rect.center
        dx, dy = px-cx, py-cy
        dist = (dx**2+dy**2)**0.5
        if dist:
            self.rect.x += int(dx/dist*self.SPEED)
            self.rect.y += int(dy/dist*self.SPEED)
        self.frame += 1

    def hit(self):
        self.hp -= 1
        return self.hp <= 0
    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.2)*3)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=5)
        for ex in [draw_rect.x+6, draw_rect.x+18]:
            pygame.draw.circle(screen, (200,40,40), (ex, draw_rect.y+10), 4)

class FastZombie(Zombie):
    SPEED = 3.0

    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect = pygame.Rect(x, y, 20, 20)
        self.hp = 1
        self.color = (220, 170, 40)

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.25)*2)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=6)
        pygame.draw.circle(screen, (255,240,100), draw_rect.center, 3)
        pygame.draw.line(
            screen, (120,80,20),
            (draw_rect.x + 4, draw_rect.bottom - 4),
            (draw_rect.right - 4, draw_rect.y + 4), 2
        )


class TankZombie(Zombie):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = 6
        self.color = (120, 70, 160)

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.15)*2)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect.inflate(6, 6), border_radius=6)
        pygame.draw.rect(screen, (70,35,90), draw_rect, 2, border_radius=5)
        for ex in [draw_rect.x + 7, draw_rect.right - 7]:
            pygame.draw.circle(screen, (255,80,180), (ex, draw_rect.y + 10), 4)
        pygame.draw.line(
            screen, (210,170,230),
            (draw_rect.x + 5, draw_rect.bottom - 5),
            (draw_rect.right - 5, draw_rect.y + 5), 3
        )


def spawn_zombie(width, height, player_rect, margin=120, zombie_type="normal"):
    while True:
        x = random.randint(0, width-30)
        y = random.randint(0, height-30)
        rect = pygame.Rect(x, y, 30, 30)
        if not rect.colliderect(player_rect.inflate(margin, margin)):
            if zombie_type == "fast":
                return FastZombie(x, y)
            if zombie_type == "tank":
                return TankZombie(x, y)
            return Zombie(x, y)


class Barrel:
    SIZE = 24

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.exploded = False

    def draw(self, screen):
        pygame.draw.rect(screen, (150,80,35), self.rect, border_radius=4)
        pygame.draw.rect(screen, (80,45,20), self.rect, 2, border_radius=4)
        pygame.draw.line(
            screen, (220,180,80),
            (self.rect.x + 5, self.rect.centery),
            (self.rect.right - 5, self.rect.centery), 3
        )


class Explosion:
    DURATION = 30
    RADIUS = 90

    def __init__(self, center):
        self.center = center
        self.timer = self.DURATION

    def update(self):
        self.timer -= 1

    def draw(self, screen):
        progress = 1 - self.timer / self.DURATION
        radius = max(1, int(self.RADIUS * (0.35 + 0.65 * progress)))
        pygame.draw.circle(screen, (255,120,30), self.center, radius, 4)
        pygame.draw.circle(screen, (255,220,80), self.center, max(1, radius // 2), 3)

    @property
    def active(self):
        return self.timer > 0


SPEED = 4


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (60,160,220)
        self.bullets = []
        self.shoot_cooldown = 0
        self.hp = 3
        self.invincibility_timer = 0
        self.ammo = 12
        self.reload_timer = 0.0

    def move(self, keys, width, height):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = SPEED
        self.rect.x = max(0, min(width-self.rect.width, self.rect.x+dx))
        self.rect.y = max(0, min(height-self.rect.height, self.rect.y+dy))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

        if self.reload_timer > 0:
            self.reload_timer = max(0.0, self.reload_timer - 1.0 / FPS)
            if self.reload_timer == 0:
                self.ammo = 12

    def shoot(self, target_pos):
        if self.shoot_cooldown > 0 or self.reload_timer > 0 or self.ammo <= 0:
            return
        cx, cy = self.rect.center
        tx, ty = target_pos
        dx, dy = tx-cx, ty-cy
        dist = (dx**2+dy**2)**0.5
        if dist == 0: return
        vx, vy = dx/dist*10, dy/dist*10
        self.bullets.append(pygame.Rect(cx-4, cy-4, 8, 8))
        self.bullets.append([cx-4, cy-4, vx, vy])
        self.bullets.pop(-2)
        self.ammo -= 1
        self.shoot_cooldown = 15
        if self.ammo == 0:
            self.reload_timer = 2.0

    def update_bullets(self, width, height):
        live = []
        for b in self.bullets:
            b[0] += b[2]; b[1] += b[3]
            if 0 <= b[0] <= width and 0 <= b[1] <= height:
                live.append(b)
        self.bullets = live

    def draw(self, screen):
        if self.invincibility_timer > 0 and (self.invincibility_timer // 5) % 2 == 0:
            draw_color = (180,220,255)
        else:
            draw_color = self.color
        pygame.draw.rect(screen, draw_color, self.rect, border_radius=6)
        for b in self.bullets:
            pygame.draw.circle(screen, (255,220,60), (int(b[0]), int(b[1])), 5)


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Zombie Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH//2, HEIGHT//2)
        self.zombies = [spawn_zombie(WIDTH, HEIGHT, self.player.rect) for _ in range(4)]
        self.barrels = [
            Barrel(100, 100),
            Barrel(WIDTH - 124, 100),
            Barrel(100, HEIGHT - 124),
            Barrel(WIDTH - 124, HEIGHT - 124),
        ]
        self.explosions = []
        self.score = 0
        self.wave = 1
        self.kills = 0
        self.kills_to_next = len(self.zombies)
        self.game_over = False
        self.start_time = time.time()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                self.player.shoot(event.pos)
        return True

    def update(self):
        if self.game_over: return
        keys = pygame.key.get_pressed()
        self.player.move(keys, WIDTH, HEIGHT)
        self.player.update_bullets(WIDTH, HEIGHT)
        self.score = int(time.time() - self.start_time)

        for z in self.zombies:
            z.update(self.player.rect.center)
            if z.rect.colliderect(self.player.rect) and self.player.invincibility_timer == 0:
                self.player.hp -= 1
                self.player.invincibility_timer = 60
                if self.player.hp <= 0:
                    self.game_over = True

        for explosion in self.explosions:
            explosion.update()
        self.explosions = [e for e in self.explosions if e.active]

        for b in self.player.bullets[:]:
            bx, by = int(b[0]), int(b[1])
            for barrel in self.barrels[:]:
                if not barrel.exploded and barrel.rect.collidepoint(bx, by):
                    barrel.exploded = True
                    self.barrels.remove(barrel)
                    self.explosions.append(Explosion(barrel.rect.center))
                    if b in self.player.bullets:
                        self.player.bullets.remove(b)

                    explosion_center = barrel.rect.center
                    remaining_zombies = []
                    for z in self.zombies:
                        zx, zy = z.rect.center
                        dx = zx - explosion_center[0]
                        dy = zy - explosion_center[1]
                        if (dx * dx + dy * dy) ** 0.5 <= Explosion.RADIUS:
                            self.kills += 1
                            self.score += 10
                        else:
                            remaining_zombies.append(z)
                    self.zombies = remaining_zombies
                    break

        dead = []
        for z in self.zombies:
            for b in self.player.bullets[:]:
                bx, by = int(b[0]), int(b[1])
                if z.rect.collidepoint(bx, by):
                    if z.hit():
                        dead.append(z)
                    if b in self.player.bullets:
                        self.player.bullets.remove(b)
        for z in dead:
            if z in self.zombies:
                self.zombies.remove(z)
                self.kills += 1
                self.score += 10
        if not self.zombies:
            self.kills = 0
            self.wave += 1
            self.kills_to_next = self.wave + 3
            for i in range(self.wave + 3):
                if self.wave >= 3 and i % 5 == 0:
                    zombie_type = "tank"
                elif self.wave >= 2 and i % 3 == 0:
                    zombie_type = "fast"
                else:
                    zombie_type = "normal"
                self.zombies.append(
                    spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_type=zombie_type)
                )

    def draw(self):
        self.screen.fill(BG)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, (40,45,35), (x,0), (x,HEIGHT), 1)
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, (40,45,35), (0,y), (WIDTH,y), 1)
        for barrel in self.barrels:
            barrel.draw(self.screen)
        for z in self.zombies: z.draw(self.screen)
        for explosion in self.explosions:
            explosion.draw(self.screen)
        self.player.draw(self.screen)
        hud_bg = pygame.Rect(0, 0, WIDTH, 40)
        pygame.draw.rect(self.screen, (15,20,15), hud_bg)
        hud = self.font.render(
            f"HP: {self.player.hp}/3  Ammo: {self.player.ammo}/12"
            + (f"  RELOADING: {self.player.reload_timer:.1f}s" if self.player.reload_timer > 0 else "")
            + f"  Wave: {self.wave}  Score: {self.score}  Kills: {self.kills}/{self.kills_to_next}  |  WASD Move, Click Shoot, R Restart",
            True, (160,220,120))
        self.screen.blit(hud, (8, 8))
        if self.game_over:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov, (0,0))
            m = self.big_font.render("DEVOURED!", True, (180,40,40))
            s = self.font.render(f"Wave {self.wave} | Score {self.score} | Press R", True, (200,200,200))
            self.screen.blit(m, (WIDTH//2-m.get_width()//2, HEIGHT//2-40))
            self.screen.blit(s, (WIDTH//2-s.get_width()//2, HEIGHT//2+20))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
