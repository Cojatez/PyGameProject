import pygame
import random
import math
import json
import os

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# FPS
FPS = 60

# Initialize the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Explorer")

# Clock
clock = pygame.time.Clock()

# Load assets
player_image = pygame.image.load("player.png")
asteroid_image = pygame.image.load("asteroid.png")
resource_image = pygame.image.load("resource.png")
boss_image = pygame.image.load("boss.png")
background_image = pygame.image.load("background.png")

# Scale images
player_image = pygame.transform.scale(player_image, (50, 50))
asteroid_image = pygame.transform.scale(asteroid_image, (50, 50))
resource_image = pygame.transform.scale(resource_image, (30, 30))
boss_image = pygame.transform.scale(boss_image, (100, 100))
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Sounds
shoot_sound = pygame.mixer.Sound("shoot.wav")
explosion_sound = pygame.mixer.Sound("explosion.wav")
resource_sound = pygame.mixer.Sound("resource.wav")
boss_explosion_sound = pygame.mixer.Sound("boss_explosion.wav")
phase_change_sound = pygame.mixer.Sound("phase_change.wav")

# Fonts
pygame.font.init()
def get_font(size):
    return pygame.font.SysFont("Arial", size)

# Constants for game states
STATE_MAIN_MENU = "main_menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"

# Classes
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_image
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.speed = 5
        self.shield = 100
        self.fuel = 100
        self.score = 0
        self.boost = False
        self.is_invincible = False
        self.invincibility_timer = 0

    def update(self, keys):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        # Boost mode
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if self.fuel > 0:
                self.speed = 8
                self.fuel -= 0.5
                self.boost = True
        else:
            self.speed = 5
            self.boost = False

        # Invincibility handling
        if self.is_invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.is_invincible = False

        # Keep player on screen
        self.rect.clamp_ip(screen.get_rect())

    def shoot(self):
        shoot_sound.play()
        return Projectile(self.rect.centerx, self.rect.top)

    def take_damage(self, damage):
        if not self.is_invincible:
            self.shield -= damage
            self.is_invincible = True
            self.invincibility_timer = FPS * 2  # 2 seconds of invincibility

class Asteroid(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = asteroid_image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -50)
        self.speed = random.randint(3, 7)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.y = random.randint(-150, -50)
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)

class Resource(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = resource_image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -50)
        self.speed = 4

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.y = random.randint(-150, -50)
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = -8

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = boss_image
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, 100)
        self.health = 200
        self.speed = 3
        self.direction = 1
        self.cooldown = 120  # Frames between attacks
        self.last_attack = 0
        self.phase = 1
        self.attack_pattern = 1

    def update(self):
        # Horizontal movement
        self.rect.x += self.speed * self.direction
        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
            self.direction *= -1

        # Phase-based behavior
        if self.health <= 100 and self.phase == 1:
            self.trigger_phase_change(2, 5, 80, 2, "The boss becomes faster!")
        elif self.health <= 50 and self.phase == 2:
            self.trigger_phase_change(3, 6, 60, 3, "The boss is enraged!")

    def trigger_phase_change(self, new_phase, new_speed, new_cooldown, new_pattern, message):
        phase_change_sound.play()
        self.phase = new_phase
        self.speed = new_speed
        self.cooldown = new_cooldown
        self.attack_pattern = new_pattern
        show_phase_message(message, 2)

    def attack(self):
        if pygame.time.get_ticks() - self.last_attack > self.cooldown:
            self.last_attack = pygame.time.get_ticks()
            if self.attack_pattern == 1:
                return BossProjectile(self.rect.centerx, self.rect.bottom)
            elif self.attack_pattern == 2:
                return [
                    BossProjectile(self.rect.centerx - 20, self.rect.bottom),
                    BossProjectile(self.rect.centerx + 20, self.rect.bottom)
                ]
            elif self.attack_pattern == 3:
                return [
                    BossProjectile(self.rect.centerx - 30, self.rect.bottom),
                    BossProjectile(self.rect.centerx, self.rect.bottom),
                    BossProjectile(self.rect.centerx + 30, self.rect.bottom)
                ]

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 5

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Helper functions
def show_phase_message(message, duration):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(128)
    overlay.fill(BLACK)
    font = get_font(48)
    text = font.render(message, True, ORANGE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < duration * 1000:
        screen.blit(background_image, (0, 0))
        screen.blit(overlay, (0, 0))
        screen.blit(text, text_rect)
        pygame.display.flip()
        clock.tick(FPS)

# Save and load system
def save_game(player, level, file_name="savegame.json"):
    save_data = {
        "score": player.score,
        "shield": player.shield,
        "fuel": player.fuel,
        "level": level
    }
    with open(file_name, "w") as file:
        json.dump(save_data, file)


def load_game(player, file_name="savegame.json"):
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            save_data = json.load(file)
            player.score = save_data["score"]
            player.shield = save_data["shield"]
            player.fuel = save_data["fuel"]
            return save_data["level"]
    return 1

# Main menu
def main_menu():
    running = True
    while running:
        screen.fill(BLACK)
        font = get_font(48)
        title = font.render("SPACE EXPLORER", True, WHITE)
        play_button = get_font(36).render("PLAY", True, GREEN)
        exit_button = get_font(36).render("EXIT", True, RED)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        screen.blit(play_button, (SCREEN_WIDTH // 2 - play_button.get_width() // 2, 250))
        screen.blit(exit_button, (SCREEN_WIDTH // 2 - exit_button.get_width() // 2, 350))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if 250 <= mouse_y <= 250 + play_button.get_height() and \
                   SCREEN_WIDTH // 2 - play_button.get_width() // 2 <= mouse_x <= SCREEN_WIDTH // 2 + play_button.get_width() // 2:
                    return True
                if 350 <= mouse_y <= 350 + exit_button.get_height() and \
                   SCREEN_WIDTH // 2 - exit_button.get_width() // 2 <= mouse_x <= SCREEN_WIDTH // 2 + exit_button.get_width() // 2:
                    running = False
                    return False

# Pause menu
def pause_menu():
    paused = True
    while paused:
        screen.fill(BLACK)
        font = get_font(48)
        title = font.render("PAUSED", True, WHITE)
        resume_button = get_font(36).render("RESUME", True, GREEN)
        save_button = get_font(36).render("SAVE GAME", True, ORANGE)
        exit_button = get_font(36).render("EXIT", True, RED)

        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        screen.blit(resume_button, (SCREEN_WIDTH // 2 - resume_button.get_width() // 2, 250))
        screen.blit(save_button, (SCREEN_WIDTH // 2 - save_button.get_width() // 2, 350))
        screen.blit(exit_button, (SCREEN_WIDTH // 2 - exit_button.get_width() // 2, 450))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if 250 <= mouse_y <= 250 + resume_button.get_height() and \
                   SCREEN_WIDTH // 2 - resume_button.get_width() // 2 <= mouse_x <= SCREEN_WIDTH // 2 + resume_button.get_width() // 2:
                    return True
                if 350 <= mouse_y <= 350 + save_button.get_height() and \
                   SCREEN_WIDTH // 2 - save_button.get_width() // 2 <= mouse_x <= SCREEN_WIDTH // 2 + save_button.get_width() // 2:
                    save_game(player, level)
                if 450 <= mouse_y <= 450 + exit_button.get_height() and \
                   SCREEN_WIDTH // 2 - exit_button.get_width() // 2 <= mouse_x <= SCREEN_WIDTH // 2 + exit_button.get_width() // 2:
                    return False

# Sprite groups
all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
asteroid_group = pygame.sprite.Group()
resource_group = pygame.sprite.Group()
projectile_group = pygame.sprite.Group()
boss_group = pygame.sprite.Group()
boss_projectile_group = pygame.sprite.Group()

# Player instance
player = Player()
player_group.add(player)
all_sprites.add(player)

# Generate asteroids and resources
def generate_asteroids(count):
    for _ in range(count):
        asteroid = Asteroid()
        asteroid_group.add(asteroid)
        all_sprites.add(asteroid)

def generate_resources(count):
    for _ in range(count):
        resource = Resource()
        resource_group.add(resource)
        all_sprites.add(resource)

# Generate initial objects
generate_asteroids(8)
generate_resources(3)

# Level system
level = 1

def level_up():
    global level
    level += 1
    generate_asteroids(level + 5)
    generate_resources(2)
    if level % 5 == 0:
        boss = Boss()
        boss_group.add(boss)
        all_sprites.add(boss)

# Start game
if not main_menu():
    pygame.quit()
    exit()

# Load game
level = load_game(player)

# Game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                projectile = player.shoot()
                projectile_group.add(projectile)
                all_sprites.add(projectile)
            if event.key == pygame.K_ESCAPE:
                if not pause_menu():
                    running = False

    # Key states
    keys = pygame.key.get_pressed()

    # Update
    all_sprites.update()
    player.update(keys)

    # Boss attacks
    for boss in boss_group:
        boss_attacks = boss.attack()
        if boss_attacks:
            if isinstance(boss_attacks, list):
                for attack in boss_attacks:
                    boss_projectile_group.add(attack)
                    all_sprites.add(attack)
            else:
                boss_projectile_group.add(boss_attacks)
                all_sprites.add(boss_attacks)

    # Collisions
    for asteroid in pygame.sprite.spritecollide(player, asteroid_group, True):
        explosion_sound.play()
        player.take_damage(10)
        if player.shield <= 0:
            running = False

    for resource in pygame.sprite.spritecollide(player, resource_group, True):
        resource_sound.play()
        player.fuel += 10
        player.score += 5

    for projectile in projectile_group:
        if pygame.sprite.spritecollide(projectile, asteroid_group, True):
            explosion_sound.play()
            projectile.kill()
            player.score += 10

    for boss in boss_group:
        if pygame.sprite.spritecollide(boss, projectile_group, True):
            boss_explosion_sound.play()
            boss.health -= 20
            if boss.health <= 0:
                boss.kill()
                player.score += 100

    for boss_projectile in pygame.sprite.spritecollide(player, boss_projectile_group, True):
        explosion_sound.play()
        player.take_damage(20)
        if player.shield <= 0:
            running = False

    # Level progression
    if len(asteroid_group) == 0 and len(boss_group) == 0:
        level_up()

    # Draw
    screen.blit(background_image, (0, 0))
    all_sprites.draw(screen)

    font = pygame.font.SysFont(None, 36)
    shield_text = font.render(f"Shield: {player.shield}", True, WHITE)
    fuel_text = font.render(f"Fuel: {player.fuel:.1f}", True, WHITE)
    score_text = font.render(f"Score: {player.score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    if boss_group:
        boss_health_text = font.render(f"Boss Health: {boss_group.sprites()[0].health}", True, RED)
        screen.blit(boss_health_text, (SCREEN_WIDTH - 200, 10))
    screen.blit(shield_text, (10, 10))
    screen.blit(fuel_text, (10, 50))
    screen.blit(score_text, (10, 90))
    screen.blit(level_text, (10, 130))

    # Refresh display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(FPS)

pygame.quit()
