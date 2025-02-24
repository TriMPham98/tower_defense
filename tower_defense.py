import pygame
import random
import time

# Initialize PyGame
pygame.init()

# Set up the game window
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400  # Increased height to accommodate UI
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Turret Defense")

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

# Define grid settings
GRID_ROWS = 5
GRID_COLS = 10
CELL_SIZE = 60

# Calculate grid offset to center it on the screen
GRID_OFFSET_X = (WINDOW_WIDTH - GRID_COLS * CELL_SIZE) // 2
GRID_OFFSET_Y = (WINDOW_HEIGHT - GRID_ROWS * CELL_SIZE - 60) // 2  # Adjusted for UI space

# Initialize grid (None represents empty cells)
grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

# Turret class to handle turret properties and behavior
class Turret:
    def __init__(self, type_, row, col):
        self.type = type_
        self.row = row
        self.col = col
        self.level = 1
        if type_ == "basic":
            self.damage = 1
            self.fire_rate = 1.0  # seconds between shots
            self.range = "cell"
        elif type_ == "advanced":
            self.damage = 2
            self.fire_rate = 1.5
            self.range = "row"
        self.last_shot = time.time()

    def attack(self, enemies):
        current_time = time.time()
        if current_time - self.last_shot >= self.fire_rate:
            if self.range == "cell":
                cell_rect = pygame.Rect(
                    GRID_OFFSET_X + self.col * CELL_SIZE,
                    GRID_OFFSET_Y + self.row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                for enemy in enemies:
                    enemy_rect = pygame.Rect(
                        enemy.x,
                        GRID_OFFSET_Y + enemy.row * CELL_SIZE,
                        CELL_SIZE // 2,
                        CELL_SIZE // 2,
                    )
                    if cell_rect.colliderect(enemy_rect):
                        enemy.health -= self.damage
                        enemy.hit_time = current_time  # Set hit time for flash effect
                        self.last_shot = current_time
                        return
            elif self.range == "row":
                for enemy in sorted(enemies, key=lambda e: e.x):
                    if enemy.row == self.row:
                        enemy.health -= self.damage
                        enemy.hit_time = current_time  # Set hit time for flash effect
                        self.last_shot = current_time
                        return

    def upgrade(self):
        self.level += 1
        self.damage += 1
        self.fire_rate = max(0.2, self.fire_rate - 0.2)

# Enemy class to handle enemy properties and movement
class Enemy:
    def __init__(self, row, health=10, speed=1):
        self.row = row
        self.x = WINDOW_WIDTH + CELL_SIZE  # Start off-screen
        self.health = health
        self.speed = speed
        self.hit_time = 0  # Time when last hit for flash effect

    def move(self):
        self.x -= self.speed

    def is_dead(self):
        return self.health <= 0

    def reached_end(self):
        return self.x <= 0

# Game state variables
coins = 200  # Starting coins
turrets = []  # List of placed turrets
enemies = []  # List of active enemies
selected_turret_type = None  # Currently selected turret type
wave_timer = 0  # Timer for spawning enemies
enemies_killed = 0  # Track enemies killed for difficulty scaling
base_health = 10  # Base health
base_enemy_health = 10  # Initial enemy health
base_enemy_speed = 1  # Initial enemy speed
health_increment = 2  # Health increase per difficulty step
speed_increment = 0.1  # Speed increase per difficulty step

# Drawing functions
def draw_grid():
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            rect = pygame.Rect(
                GRID_OFFSET_X + col * CELL_SIZE,
                GRID_OFFSET_Y + row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(screen, BLACK, rect, 1)

def draw_turrets():
    for turret in turrets:
        rect = pygame.Rect(
            GRID_OFFSET_X + turret.col * CELL_SIZE,
            GRID_OFFSET_Y + turret.row * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        color = BLUE if turret.type == "basic" else GREEN
        pygame.draw.circle(screen, color, rect.center, CELL_SIZE // 4)
        font = pygame.font.Font(None, 24)
        text = font.render(str(turret.level), True, WHITE)
        screen.blit(text, (rect.centerx - 5, rect.centery - 5))

def draw_enemies():
    current_time = time.time()
    for enemy in enemies:
        rect = pygame.Rect(
            enemy.x,
            GRID_OFFSET_Y + enemy.row * CELL_SIZE,
            CELL_SIZE // 2,
            CELL_SIZE // 2,
        )
        if current_time - enemy.hit_time < 0.1:  # Flash white for 0.1s when hit
            color = WHITE
        else:
            color = RED
        pygame.draw.rect(screen, color, rect)

def draw_base():
    base_rect = pygame.Rect(0, 0, 20, WINDOW_HEIGHT)
    pygame.draw.rect(screen, GRAY, base_rect)

def draw_coins():
    font = pygame.font.Font(None, 36)
    text = font.render(f"Coins: {coins}", True, BLACK)
    screen.blit(text, (10, 10))

def draw_base_health():
    font = pygame.font.Font(None, 36)
    text = font.render(f"Base Health: {base_health}", True, BLACK)
    screen.blit(text, (WINDOW_WIDTH - 200, 10))

def draw_ui():
    font = pygame.font.Font(None, 24)
    if selected_turret_type:
        text = f"Selected: {selected_turret_type} (Cost: {50 if selected_turret_type == 'basic' else 100})"
    else:
        text = "Select a turret type: 1 for basic, 2 for advanced"
    screen.blit(font.render(text, True, BLACK), (10, WINDOW_HEIGHT - 30))
    screen.blit(font.render("Left click to place, right click to upgrade (100 coins)", True, BLACK), (10, WINDOW_HEIGHT - 60))

# Main game loop
def main():
    global coins, selected_turret_type, wave_timer, enemies_killed, base_health

    clock = pygame.time.Clock()
    running = True

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_turret_type = "basic"
                elif event.key == pygame.K_2:
                    selected_turret_type = "advanced"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                grid_x = (mouse_x - GRID_OFFSET_X) // CELL_SIZE
                grid_y = (mouse_y - GRID_OFFSET_Y) // CELL_SIZE
                if 0 <= grid_x < GRID_COLS and 0 <= grid_y < GRID_ROWS:
                    if event.button == 1:  # Left click to place turret
                        if grid[grid_y][grid_x] is None and selected_turret_type:
                            cost = 50 if selected_turret_type == "basic" else 100
                            if coins >= cost:
                                turret = Turret(selected_turret_type, grid_y, grid_x)
                                turrets.append(turret)
                                grid[grid_y][grid_x] = turret
                                coins -= cost
                    elif event.button == 3:  # Right click to upgrade
                        turret = grid[grid_y][grid_x]
                        if turret and coins >= 100:
                            turret.upgrade()
                            coins -= 100

        # Update game state
        wave_timer += 1
        if wave_timer >= 100:  # Spawn enemy every 100 frames
            row = random.randint(0, GRID_ROWS - 1)
            health = base_enemy_health + (enemies_killed // 10) * health_increment
            speed = base_enemy_speed + (enemies_killed // 10) * speed_increment
            enemies.append(Enemy(row, health, speed))
            wave_timer = 0

        for enemy in enemies[:]:
            enemy.move()
            if enemy.reached_end():
                base_health -= 1
                enemies.remove(enemy)
                if base_health <= 0:
                    print("Base destroyed! Game Over.")
                    running = False
            elif enemy.is_dead():
                enemies.remove(enemy)
                coins += 10
                enemies_killed += 1

        for turret in turrets:
            turret.attack(enemies)

        # Render
        screen.fill(WHITE)
        draw_base()
        draw_grid()
        draw_turrets()
        draw_enemies()
        draw_coins()
        draw_base_health()
        draw_ui()
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()