import pygame
import random
import time

# Initialize PyGame
pygame.init()

# Set up the game window
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 300
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Turret Defense")

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Define grid settings
GRID_ROWS = 5
GRID_COLS = 10
CELL_SIZE = 60

# Calculate grid offset to center it on the screen
GRID_OFFSET_X = (WINDOW_WIDTH - GRID_COLS * CELL_SIZE) // 2
GRID_OFFSET_Y = (WINDOW_HEIGHT - GRID_ROWS * CELL_SIZE) // 2

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
        """
        Attack enemies based on turret type and range.
        - Basic turret: Attacks enemies in its own cell.
        - Advanced turret: Attacks the first enemy in its row.
        """
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
                        self.last_shot = current_time
                        return
            elif self.range == "row":
                for enemy in sorted(enemies, key=lambda e: e.x):
                    if enemy.row == self.row:
                        enemy.health -= self.damage
                        self.last_shot = current_time
                        return

    def upgrade(self):
        """Upgrade the turret to increase damage and decrease fire rate."""
        self.level += 1
        self.damage += 1
        self.fire_rate = max(0.2, self.fire_rate - 0.2)

# Enemy class to handle enemy properties and movement
class Enemy:
    def __init__(self, row):
        self.row = row
        self.x = WINDOW_WIDTH - 1  # Start from the right edge
        self.health = 10
        self.speed = 1  # pixels per frame

    def move(self):
        """Move the enemy leftward across the screen."""
        self.x -= self.speed

    def is_dead(self):
        """Check if the enemy is dead."""
        return self.health <= 0

    def reached_end(self):
        """Check if the enemy has reached the left end."""
        return self.x <= 0

# Game state variables
coins = 200  # Starting coins
turrets = []  # List of placed turrets
enemies = []  # List of active enemies
selected_turret_type = None  # Currently selected turret type
wave_timer = 0  # Timer for spawning enemies

# Drawing functions
def draw_grid():
    """Draw the grid on the screen."""
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
    """Draw all turrets on the grid with their levels."""
    for turret in turrets:
        rect = pygame.Rect(
            GRID_OFFSET_X + turret.col * CELL_SIZE,
            GRID_OFFSET_Y + turret.row * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        color = BLUE if turret.type == "basic" else GREEN
        pygame.draw.circle(screen, color, rect.center, CELL_SIZE // 4)
        # Draw level
        font = pygame.font.Font(None, 24)
        text = font.render(str(turret.level), True, WHITE)
        screen.blit(text, (rect.centerx - 5, rect.centery - 5))

def draw_enemies():
    """Draw all enemies on the screen."""
    for enemy in enemies:
        rect = pygame.Rect(
            enemy.x,
            GRID_OFFSET_Y + enemy.row * CELL_SIZE,
            CELL_SIZE // 2,
            CELL_SIZE // 2,
        )
        pygame.draw.rect(screen, RED, rect)

def draw_coins():
    """Display the player's current coin count."""
    font = pygame.font.Font(None, 36)
    text = font.render(f"Coins: {coins}", True, BLACK)
    screen.blit(text, (10, 10))

# Main game loop
def main():
    global coins, selected_turret_type, wave_timer

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
            enemies.append(Enemy(row))
            wave_timer = 0

        for enemy in enemies[:]:
            enemy.move()
            if enemy.reached_end():
                print("Enemy reached the end! Game Over.")
                running = False
            if enemy.is_dead():
                enemies.remove(enemy)
                coins += 10  # Earn coins for killing enemy

        for turret in turrets:
            turret.attack(enemies)

        # Render
        screen.fill(WHITE)
        draw_grid()
        draw_turrets()
        draw_enemies()
        draw_coins()
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()