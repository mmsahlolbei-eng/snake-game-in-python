"""
Enhanced Snake Game implemented with Pygame.
Features:
- Difficulty selection (Easy, Medium, Hard)
- High score persistence
- Sound effects (eat, game over)
- Special foods (bonus score, speed up/down, shrink)
- Obstacles (walls)
- Two-player mode on one screen
- Themes (color palettes)
- Save/Load game state
"""

import sys
import os
import json
import random
import pygame

# Initialize pygame
pygame.init()  # pylint: disable=no-member

# ---------- Constants ----------
# Screen
DIS_WIDTH = 1240
DIS_HEIGHT = 600

# Grid
GRID_SIZE = 10

# Files
HIGH_SCORE_FILE = "high_score.json"
SAVE_FILE = "snake_save.json"

# Colors (themes)
THEMES = {
    "classic": {
        "bg": (50, 153, 213),
        "snake1": (0, 0, 0),
        "snake2": (0, 100, 0),
        "food": (0, 255, 0),
        "text": (255, 255, 102),
        "obstacle": (120, 120, 120),
        "bonus": (255, 165, 0),
        "speed_up": (255, 0, 0),
        "speed_down": (0, 0, 255),
        "shrink": (128, 0, 128),
    },
    "dark": {
        "bg": (20, 20, 20),
        "snake1": (200, 200, 200),
        "snake2": (150, 255, 150),
        "food": (100, 255, 100),
        "text": (200, 200, 50),
        "obstacle": (70, 70, 70),
        "bonus": (255, 140, 0),
        "speed_up": (255, 80, 80),
        "speed_down": (80, 80, 255),
        "shrink": (180, 80, 180),
    },
    "neon": {
        "bg": (10, 10, 30),
        "snake1": (0, 255, 255),
        "snake2": (255, 0, 255),
        "food": (0, 255, 0),
        "text": (255, 255, 0),
        "obstacle": (0, 120, 255),
        "bonus": (255, 255, 255),
        "speed_up": (255, 50, 50),
        "speed_down": (50, 50, 255),
        "shrink": (255, 0, 255),
    },
}

# Difficulty presets
DIFFICULTIES = {
    "easy": {"speed": 10, "obstacles": 10},
    "medium": {"speed": 15, "obstacles": 20},
    "hard": {"speed": 20, "obstacles": 35},
}

# Special foods
SPECIAL_TYPES = ["bonus", "speed_up", "speed_down", "shrink"]
SPECIAL_EFFECT_DURATION = 3000  # ms

# ---------- Setup ----------
dis = pygame.display.set_mode((DIS_WIDTH, DIS_HEIGHT))
pygame.display.set_caption("Snake Game - Enhanced")

clock = pygame.time.Clock()
font_ui = pygame.font.SysFont("bahnschrift", 26)
font_title = pygame.font.SysFont("comicsansms", 44)

# Sound (optional: wrap in try to avoid errors if mixer fails)
try:
    pygame.mixer.init()  # pylint: disable=no-member
    SOUND_EAT = pygame.mixer.Sound(file=None)  # placeholder if you don't have files
    SOUND_GAME_OVER = pygame.mixer.Sound(file=None)
    # If you have sound files, replace above lines:
    # SOUND_EAT = pygame.mixer.Sound("eat.wav")
    # SOUND_GAME_OVER = pygame.mixer.Sound("game_over.wav")
except Exception:
    SOUND_EAT = None
    SOUND_GAME_OVER = None


# ---------- Utilities ----------
def play_sound(snd):
    """Play a sound if available."""
    if snd is not None:
        try:
            snd.play()  # pylint: disable=no-member
        except Exception:
            pass


def draw_text(surface, text, color, pos):
    """Render text on surface."""
    surf = font_ui.render(text, True, color)
    surface.blit(surf, pos)


def load_high_score():
    """Load high score from file."""
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return int(data.get("high_score", 0))
        except Exception:
            return 0
    return 0


def save_high_score(value):
    """Save high score to file."""
    try:
        with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"high_score": int(value)}, f)
    except Exception:
        pass


def save_state(state):
    """Save current game state to file."""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def load_state():
    """Load game state from file."""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def grid_pos_random(max_w, max_h):
    """Get random grid-aligned position."""
    x = round(random.randrange(0, max_w - GRID_SIZE) / float(GRID_SIZE)) * GRID_SIZE
    y = round(random.randrange(0, max_h - GRID_SIZE) / float(GRID_SIZE)) * GRID_SIZE
    return x, y


# ---------- Game Entities ----------
class Snake:
    """Snake entity with position, direction and growth."""

    def __init__(self, color, start_pos, controls, initial_len=3):
        self.color = color
        self.body = [start_pos]
        self.dir = (GRID_SIZE, 0)  # moving right initially
        self.pending_dir = self.dir
        self.controls = controls
        self.grow = initial_len - 1
        self.alive = True
        self.score = 0
        self.speed_effect = 0  # positive or negative adjustments
        self.last_effect_time = 0

    def handle_event(self, event):
        """Update intended direction based on control keys."""
        if event.type == pygame.KEYDOWN:  # pylint: disable=no-member
            if event.key == self.controls["left"]:  # pylint: disable=no-member
                self.pending_dir = (-GRID_SIZE, 0)
            elif event.key == self.controls["right"]:  # pylint: disable=no-member
                self.pending_dir = (GRID_SIZE, 0)
            elif event.key == self.controls["up"]:  # pylint: disable=no-member
                self.pending_dir = (0, -GRID_SIZE)
            elif event.key == self.controls["down"]:  # pylint: disable=no-member
                self.pending_dir = (0, GRID_SIZE)

    def update(self):
        """Advance the snake by one step and apply pending direction (no reverse into self)."""
        if len(self.body) >= 2:
            head = self.body[-1]
            neck = self.body[-2]
            current_dir = (head[0] - neck[0], head[1] - neck[1])
        else:
            current_dir = self.dir

        # Prevent 180-degree reversal
        if (self.pending_dir[0] == -current_dir[0] and self.pending_dir[1] == -current_dir[1]) or (
            self.pending_dir == (0, 0)
        ):
            self.dir = current_dir
        else:
            self.dir = self.pending_dir

        new_head = (self.body[-1][0] + self.dir[0], self.body[-1][1] + self.dir[1])
        self.body.append(new_head)
        if self.grow > 0:
            self.grow -= 1
        else:
            del self.body[0]

    def draw(self, surface):
        """Draw snake body segments."""
        for x, y in self.body:
            pygame.draw.rect(surface, self.color, (x, y, GRID_SIZE, GRID_SIZE))


class Food:
    """Food entity: normal or special with type and color."""

    def __init__(self, pos, kind="normal", color=(0, 255, 0)):
        self.pos = pos
        self.kind = kind
        self.color = color

    def draw(self, surface):
        """Draw food as a rectangle with distinctive color."""
        pygame.draw.rect(surface, self.color, (self.pos[0], self.pos[1], GRID_SIZE, GRID_SIZE))


def create_obstacles(count, exclude_positions):
    """Create non-overlapping obstacles."""
    obstacles = []
    attempts = 0
    while len(obstacles) < count and attempts < 5000:
        pos = grid_pos_random(DIS_WIDTH, DIS_HEIGHT)
        if pos in exclude_positions:
            attempts += 1
            continue
        if pos not in obstacles:
            obstacles.append(pos)
        attempts += 1
    return obstacles


# ---------- Game Core ----------
class SnakeGame:
    """Main game class handling state, rendering, input and progression."""

    def __init__(self, difficulty="medium", theme_name="classic", two_player=False):
        self.theme = THEMES[theme_name]
        self.base_speed = DIFFICULTIES[difficulty]["speed"]
        self.obstacle_count = DIFFICULTIES[difficulty]["obstacles"]
        self.two_player = two_player

        # Initialize snakes
        self.snake1 = Snake(
            color=self.theme["snake1"],
            start_pos=(DIS_WIDTH // 4, DIS_HEIGHT // 2),
            controls={
                "left": pygame.K_LEFT,  # pylint: disable=no-member
                "right": pygame.K_RIGHT,  # pylint: disable=no-member
                "up": pygame.K_UP,  # pylint: disable=no-member
                "down": pygame.K_DOWN,  # pylint: disable=no-member
            },
            initial_len=3,
        )
        self.snake2 = None
        if two_player:
            self.snake2 = Snake(
                color=self.theme["snake2"],
                start_pos=(3 * DIS_WIDTH // 4, DIS_HEIGHT // 2),
                controls={
                    "left": pygame.K_a,  # pylint: disable=no-member
                    "right": pygame.K_d,  # pylint: disable=no-member
                    "up": pygame.K_w,  # pylint: disable=no-member
                    "down": pygame.K_s,  # pylint: disable=no-member
                },
                initial_len=3,
            )

        self.high_score = load_high_score()
        self.obstacles = create_obstacles(
            self.obstacle_count,
            exclude_positions=set(self.snake1.body + ([self.snake2.body[0]] if self.snake2 else [])),
        )
        self.foods = []
        self.spawn_foods()

        self.running = True
        self.paused = False
        self.last_update = pygame.time.get_ticks()  # pylint: disable=no-member
        self.update_interval = self.compute_interval()
        self.special_effects = {}

    def compute_interval(self):
        """Compute update interval in ms based on speed and effects."""
        speed_mod = 0
        if self.snake1:
            speed_mod += self.snake1.speed_effect
        if self.snake2:
            speed_mod += self.snake2.speed_effect
        speed = max(5, self.base_speed + speed_mod)
        return int(1000 / float(speed))

    def spawn_foods(self):
        """Spawn one normal food and occasionally a special food."""
        # Normal food
        pos = self.find_free_pos()
        self.foods.append(Food(pos=pos, kind="normal", color=self.theme["food"]))

        # Maybe special food
        if random.random() < 0.35:
            kind = random.choice(SPECIAL_TYPES)
            color = self.theme[kind]
            pos = self.find_free_pos()
            self.foods.append(Food(pos=pos, kind=kind, color=color))

    def find_free_pos(self):
        """Find a position that is not occupied by snakes, obstacles or foods."""
        occupied = set(self.obstacles)
        occupied.update(self.snake1.body)
        if self.snake2:
            occupied.update(self.snake2.body)
        occupied.update([f.pos for f in self.foods])

        attempts = 0
        while attempts < 5000:
            pos = grid_pos_random(DIS_WIDTH, DIS_HEIGHT)
            if pos not in occupied:
                return pos
            attempts += 1
        # Fallback
        return (GRID_SIZE, GRID_SIZE)

    def handle_events(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # pylint: disable=no-member
                self.running = False
            elif event.type == pygame.KEYDOWN:  # pylint: disable=no-member
                if event.key == pygame.K_q:  # pylint: disable=no-member
                    self.running = False
                elif event.key == pygame.K_p:  # pylint: disable=no-member
                    self.paused = not self.paused
                elif event.key == pygame.K_t:  # pylint: disable=no-member
                    # Cycle theme
                    names = list(THEMES.keys())
                    current_index = names.index(self.get_theme_name())
                    next_name = names[(current_index + 1) % len(names)]
                    self.set_theme(next_name)
                elif event.key == pygame.K_l:  # pylint: disable=no-member
                    self.load_game()
                elif event.key == pygame.K_s:  # pylint: disable=no-member
                    self.save_game()

                # Delegate controls
                self.snake1.handle_event(event)
                if self.snake2:
                    self.snake2.handle_event(event)

    def update(self):
        """Update game state based on timing."""
        now = pygame.time.get_ticks()  # pylint: disable=no-member
        if self.paused:
            self.last_update = now
            return

        interval = self.compute_interval()
        if now - self.last_update >= interval:
            self.snake1.update()
            if self.snake2:
                self.snake2.update()
            self.check_collisions()
            self.last_update = now

        # Expire special effects
        for key in list(self.special_effects.keys()):
            if now - self.special_effects[key] >= SPECIAL_EFFECT_DURATION:
                if key == "speed_up":
                    self.snake1.speed_effect -= 2
                    if self.snake2:
                        self.snake2.speed_effect -= 2
                elif key == "speed_down":
                    self.snake1.speed_effect += 2
                    if self.snake2:
                        self.snake2.speed_effect += 2
                del self.special_effects[key]

    def check_collisions(self):
        """Check boundary, obstacle, self and food collisions."""
        snakes = [self.snake1] + ([self.snake2] if self.snake2 else [])
        for snake in snakes:
            head = snake.body[-1]

            # Wall collision
            if head[0] < 0 or head[0] >= DIS_WIDTH or head[1] < 0 or head[1] >= DIS_HEIGHT:
                snake.alive = False

            # Obstacle collision
            if head in self.obstacles:
                snake.alive = False

            # Self collision
            if head in snake.body[:-1]:
                snake.alive = False

            # Other snake collision
            for other in snakes:
                if other is not snake:
                    if head in other.body:
                        snake.alive = False

        # Food collisions
        for snake in snakes:
            head = snake.body[-1]
            eaten = []
            for food in self.foods:
                if head == food.pos:
                    eaten.append(food)
                    self.apply_food_effect(snake, food)
            for f in eaten:
                try:
                    self.foods.remove(f)
                except ValueError:
                    pass
            if eaten:
                self.spawn_foods()

        # Game over if all snakes dead
        if all(not s.alive for s in snakes):
            play_sound(SOUND_GAME_OVER)
            self.handle_game_over()

    def apply_food_effect(self, snake, food):
        """Apply effect of eaten food and scoring."""
        play_sound(SOUND_EAT)
        if food.kind == "normal":
            snake.grow += 1
            snake.score += 1
        elif food.kind == "bonus":
            snake.grow += 2
            snake.score += 5
        elif food.kind == "speed_up":
            snake.score += 2
            snake.speed_effect += 2
            self.special_effects["speed_up"] = pygame.time.get_ticks()  # pylint: disable=no-member
        elif food.kind == "speed_down":
            snake.score += 2
            snake.speed_effect -= 2
            self.special_effects["speed_down"] = pygame.time.get_ticks()  # pylint: disable=no-member
        elif food.kind == "shrink":
            snake.score += 3
            if len(snake.body) > 3:
                # Shrink by removing middle segment
                mid = len(snake.body) // 2
                del snake.body[: mid - 1]
                snake.grow = 0

    def handle_game_over(self):
        """Update high score and show game over screen."""
        total_score = self.snake1.score + (self.snake2.score if self.snake2 else 0)
        if total_score > self.high_score:
            self.high_score = total_score
            save_high_score(self.high_score)

        # Simple game over prompt
        self.draw()  # draw final frame
        draw_text(
            dis,
            "Game Over! Press P to play again, Q to quit, or L to load last save.",
            self.theme["text"],
            (DIS_WIDTH // 10, DIS_HEIGHT // 2 - 20),
        )
        pygame.display.update()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # pylint: disable=no-member
                    self.running = False
                    waiting = False
                elif event.type == pygame.KEYDOWN:  # pylint: disable=no-member
                    if event.key == pygame.K_q:  # pylint: disable=no-member
                        self.running = False
                        waiting = False
                    elif event.key == pygame.K_p:  # pylint: disable=no-member
                        # Restart
                        self.__init__(
                            difficulty=self.get_difficulty_name(),
                            theme_name=self.get_theme_name(),
                            two_player=self.two_player,
                        )
                        waiting = False
                    elif event.key == pygame.K_l:  # pylint: disable=no-member
                        self.load_game()
                        waiting = False

    def draw(self):
        """Render the full scene."""
        dis.fill(self.theme["bg"])
        # Obstacles
        for ox, oy in self.obstacles:
            pygame.draw.rect(dis, self.theme["obstacle"], (ox, oy, GRID_SIZE, GRID_SIZE))

        # Foods
        for food in self.foods:
            food.draw(dis)

        # Snakes
        if self.snake1.alive:
            self.snake1.draw(dis)
        if self.snake2 and self.snake2.alive:
            self.snake2.draw(dis)

        # UI
        total_score = self.snake1.score + (self.snake2.score if self.snake2 else 0)
        draw_text(dis, f"Score: {total_score}  High: {self.high_score}", self.theme["text"], (10, 10))
        draw_text(
            dis,
            f"Difficulty: {self.get_difficulty_name().title()}  Theme: {self.get_theme_name().title()}",
            self.theme["text"],
            (10, 40),
        )
        draw_text(dis, "P: Pause  T: Theme  S: Save  L: Load  Q: Quit", self.theme["text"], (10, 70))
        if self.paused:
            draw_text(dis, "Paused", self.theme["text"], (DIS_WIDTH // 2 - 40, 10))

        pygame.display.update()

    def get_theme_name(self):
        """Get current theme name."""
        for name, palette in THEMES.items():
            if palette is self.theme:
                return name
        return "classic"

    def set_theme(self, name):
        """Set theme by name."""
        if name in THEMES:
            self.theme = THEMES[name]

    def get_difficulty_name(self):
        """Infer difficulty name from base speed and obstacle count."""
        for name, cfg in DIFFICULTIES.items():
            if cfg["speed"] == self.base_speed and cfg["obstacles"] == self.obstacle_count:
                return name
        return "custom"

    def save_game(self):
        """Persist current game state."""
        state = {
            "difficulty": self.get_difficulty_name(),
            "theme": self.get_theme_name(),
            "two_player": self.two_player,
            "snake1": {
                "body": self.snake1.body,
                "dir": self.snake1.dir,
                "pending_dir": self.snake1.pending_dir,
                "grow": self.snake1.grow,
                "alive": self.snake1.alive,
                "score": self.snake1.score,
                "speed_effect": self.snake1.speed_effect,
            },
            "snake2": None,
            "obstacles": self.obstacles,
            "foods": [{"pos": f.pos, "kind": f.kind} for f in self.foods],
            "high_score": self.high_score,
        }
        if self.snake2:
            state["snake2"] = {
                "body": self.snake2.body,
                "dir": self.snake2.dir,
                "pending_dir": self.snake2.pending_dir,
                "grow": self.snake2.grow,
                "alive": self.snake2.alive,
                "score": self.snake2.score,
                "speed_effect": self.snake2.speed_effect,
            }
        save_state(state)

    def load_game(self):
        """Restore game state if available."""
        state = load_state()
        if not state:
            return
        self.theme = THEMES.get(state.get("theme", "classic"), THEMES["classic"])
        self.base_speed = DIFFICULTIES.get(state.get("difficulty", "medium"), DIFFICULTIES["medium"])["speed"]
        self.obstacle_count = DIFFICULTIES.get(state.get("difficulty", "medium"), DIFFICULTIES["medium"])["obstacles"]
        self.two_player = state.get("two_player", False)

        s1 = state["snake1"]
        self.snake1 = Snake(color=self.theme["snake1"], start_pos=(0, 0), controls=self.snake1.controls)
        self.snake1.body = [tuple(p) for p in s1["body"]]
        self.snake1.dir = tuple(s1["dir"])
        self.snake1.pending_dir = tuple(s1["pending_dir"])
        self.snake1.grow = int(s1["grow"])
        self.snake1.alive = bool(s1["alive"])
        self.snake1.score = int(s1["score"])
        self.snake1.speed_effect = int(s1.get("speed_effect", 0))

        if state.get("snake2"):
            s2 = state["snake2"]
            self.snake2 = Snake(color=self.theme["snake2"], start_pos=(0, 0), controls=self.snake2.controls)
            self.snake2.body = [tuple(p) for p in s2["body"]]
            self.snake2.dir = tuple(s2["dir"])
            self.snake2.pending_dir = tuple(s2["pending_dir"])
            self.snake2.grow = int(s2["grow"])
            self.snake2.alive = bool(s2["alive"])
            self.snake2.score = int(s2["score"])
            self.snake2.speed_effect = int(s2.get("speed_effect", 0))
        else:
            self.snake2 = None

        self.obstacles = [tuple(p) for p in state.get("obstacles", [])]
        self.foods = []
        for f in state.get("foods", []):
            kind = f.get("kind", "normal")
            color = self.theme.get(kind, self.theme["food"])
            self.foods.append(Food(pos=tuple(f["pos"]), kind=kind, color=color))
        self.high_score = int(state.get("high_score", self.high_score))
        self.last_update = pygame.time.get_ticks()  # pylint: disable=no-member

    def main_loop(self):
        """Run the main loop until exit."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)


# ---------- Menu ----------
def main_menu():
    """Menu to choose difficulty, theme, single/two-player, and start game."""
    selected_diff = "medium"
    selected_theme = "classic"
    two_player = False

    running = True
    while running:
        dis.fill((30, 30, 50))
        title = font_title.render("Snake Game - Enhanced", True, (220, 220, 220))
        dis.blit(title, (DIS_WIDTH // 2 - title.get_width() // 2, 40))

        # Options
        draw_text(dis, f"Difficulty [1/2/3]: Easy/Medium/Hard (Current: {selected_diff.title()})", (220, 220, 220), (60, 140))
        draw_text(dis, f"Theme [T]: {selected_theme.title()} (Cycle)", (220, 220, 220), (60, 180))
        draw_text(dis, f"Mode [M]: {'Two-Player' if two_player else 'Single-Player'} (Toggle)", (220, 220, 220), (60, 220))
        draw_text(dis, "Start [Enter]  Load Save [L]  Quit [Q]", (220, 220, 220), (60, 260))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # pylint: disable=no-member
                pygame.quit()  # pylint: disable=no-member
                sys.exit()
            elif event.type == pygame.KEYDOWN:  # pylint: disable=no-member
                if event.key == pygame.K_q:  # pylint: disable=no-member
                    pygame.quit()  # pylint: disable=no-member
                    sys.exit()
                elif event.key == pygame.K_1:  # pylint: disable=no-member
                    selected_diff = "easy"
                elif event.key == pygame.K_2:  # pylint: disable=no-member
                    selected_diff = "medium"
                elif event.key == pygame.K_3:  # pylint: disable=no-member
                    selected_diff = "hard"
                elif event.key == pygame.K_t:  # pylint: disable=no-member
                    names = list(THEMES.keys())
                    idx = names.index(selected_theme)
                    selected_theme = names[(idx + 1) % len(names)]
                elif event.key == pygame.K_m:  # pylint: disable=no-member
                    two_player = not two_player
                elif event.key == pygame.K_l:  # pylint: disable=no-member
                    state = load_state()
                    if state:
                        game = SnakeGame(
                            difficulty=state.get("difficulty", "medium"),
                            theme_name=state.get("theme", "classic"),
                            two_player=state.get("two_player", False),
                        )
                        game.load_game()
                        game.main_loop()
                elif event.key == pygame.K_RETURN:  # pylint: disable=no-member
                    game = SnakeGame(difficulty=selected_diff, theme_name=selected_theme, two_player=two_player)
                    game.main_loop()


# ---------- Entry Point ----------
if __name__ == "__main__":
    main_menu()
