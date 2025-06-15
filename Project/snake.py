import pygame
import random
import sys
from main import load_config

FONT_PATH = "resources/Daydream.ttf"
TEXT_COLOR = (255, 255, 255)

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)



class Snake():
    def __init__(self):
        self.length = 1
        self.position = [((SCREEN_WIDTH/2), (SCREEN_HEIGHT/2))]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.color = (random.randint(5, 200), random.randint(5, 200), random.randint(5, 200))
        self.score = 0
        self.speed_modifier = 1
        self.effect_timer = 0

    def update_speed(self):
        if self.effect_timer > 0:
            self.effect_timer -= 1
            if self.effect_timer == 0:
                self. speed_modifier = 1

    def get_head_position(self):
        return self.position[0]

    def turn(self, point):
        if self.length > 1 and (point[0]*-1, point[1]*-1) == self.direction:
            return
        else:
            self.direction = point

    def move(self):
        self.update_speed()
        cur = self.get_head_position()
        x, y = self.direction
        new = (((cur[0]+(x*GRID_SIZE))%SCREEN_WIDTH),
            (cur[1]+(y*GRID_SIZE))%SCREEN_HEIGHT)
        if len(self.position) > 2 and new in self.position[2:]:
            return False
        else:
            self.position.insert(0, new)
            if len(self.position) > self.length:
                self.position.pop()
            return True

    def reset(self):
        self.length = 1
        self.position = [((SCREEN_WIDTH/2), (SCREEN_HEIGHT/2))]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.score = 0
        self.speed_modifier = 1

    def draw(self, surface):
        for p in self.position:
            r = pygame.Rect((p[0], p[1]), (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(surface, self.color, r)
            pygame.draw.rect(surface, (93, 216, 228), r, 1)

    def handle_keys(self, shift_sound=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False  # Signal to quit snake game loop
                elif event.key == pygame.K_UP:
                    self.turn(UP)
                elif event.key == pygame.K_DOWN:
                    self.turn(DOWN)
                elif event.key == pygame.K_LEFT:
                    self.turn(LEFT)
                elif event.key == pygame.K_RIGHT:
                    self.turn(RIGHT)
                elif event.key == pygame.K_LSHIFT:
                    shift_sound.play()
                    if self.speed_modifier == 1:
                        self.speed_modifier = 1.5
                    elif self.speed_modifier == 1.5:
                        self.speed_modifier = 1
        return True  # Continue game


class Consumable():
    def __init__(self, color=(0, 0, 225), points=10):
        self.position = (0, 0)
        self.color = color
        self.points = points
        self.randomize_position()

    def randomize_position(self):
        self.position = (
                        random.randint(0, GRID_WIDTH - 1) * GRID_SIZE, 
                        random.randint(0, GRID_HEIGHT - 1) * GRID_SIZE)
    
    def draw(self, surface):
        center = (self.position[0] + GRID_SIZE // 2, self.position[1] + GRID_SIZE // 2)
        radius = GRID_SIZE // 2 - 2
        pygame.draw.circle(surface, self.color, center, radius)
        pygame.draw.circle(surface, (93, 216, 228), center, radius, 1)
    
    def effect(self, snake):
        snake.score += self.points

class Blueberry(Consumable):
    def __init__(self):
        super().__init__(color=(0, 0, 255), points=10)

class Apple(Consumable):
    def __init__(self):
        super().__init__(color=(255, 0, 0), points=20)

class Watermelon(Consumable):
    def __init__(self):
        super().__init__(color=(0, 255, 0), points=30)

class SpeedBoost(Consumable):
    def __init__(self):
        super().__init__(color=(0, 150, 0), points=5)
    
    def apply_effect(self, snake):
        #snake.set_speed_modifier(1.75, duration=20)
        snake.speed_modifier = 1.75
        snake.effect_timer = 200
    
    def draw(self, surface):
        r = pygame.Rect((self.position[0], self.position[1]), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, (93, 216, 228), r, 1)

class SpeedDebuff(Consumable):
    def __init__(self):
        super().__init__(color=(150, 0, 0))
    
    def apply_effect(self, snake):
        #snake.set_speed_modifier(0.7, duration=10)
        snake.speed_modifier = 0.7
        snake.effect_timer = 100
    
    def draw(self, surface):
        r = pygame.Rect((self.position[0], self.position[1]), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, (93, 216, 228), r, 1)

def get_random_food():
    food_classes = [Blueberry(), Apple(), Watermelon(), SpeedBoost(), SpeedDebuff()]
    return random.choices(food_classes, weights = [8, 6, 4, 5, 4], k = 14)[0]


def adjust_food_count(foods, score):
    desired_count = 1

    if score >= 200:
        desired_count = 3
    elif score >= 1000:
        desired_count = 5

    while len(foods) < desired_count:
        foods.append(get_random_food())
    
    while len(foods) > desired_count:
        foods.pop()

def draw_grid(surface):
    surface.fill((0,0,0,0))
    line_color = (255,255,255,10)

    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(surface, line_color, (x, 0), (x, SCREEN_HEIGHT))

    # Draw horizontal lines
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(surface, line_color, (0, y), (SCREEN_WIDTH, y))

def game_over_screen(screen, snake, background, grid_surface, myfont, score):
    while True:
        screen.blit(background, (0,0))
        screen.blit(grid_surface, (0,0))

        game_over_text = myfont.render("Game Over", True, TEXT_COLOR)
        restart_text = myfont.render("Press R to restart or ESC to EXIT", True, TEXT_COLOR)
        score_text = myfont.render(f"Final Score: {score}", True, TEXT_COLOR)

        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 60))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 25))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - 295, SCREEN_HEIGHT // 2 + 10))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
                elif event.key == pygame.K_r:
                    snake.reset()
                    return True

class SnakeGame:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.surface = pygame.Surface(screen.get_size()).convert()

        self.background = pygame.image.load("resources/background.jpg")
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        draw_grid(self.grid_surface)

        self.surface.blit(self.background, (0, 0))
        self.surface.blit(self.grid_surface, (0, 0))

        self.snake = Snake()
        self.foods = [get_random_food()]
        self.font = pygame.font.Font(FONT_PATH, 20)
        self.base_speed = 10

    def run(self):
        print("Game start")
        pygame.mixer.init()

        settings = load_config()

        # Load music and sound
        try:
            pygame.mixer.music.load("resources/music.mp3")
            pygame.mixer.music.set_volume(settings["music_volume"])
            pygame.mixer.music.play(-1)

            death_sound = pygame.mixer.Sound("resources/sounds/death.wav")
            death_sound.set_volume(settings["sound_effects_volume"])
            shift_sound = pygame.mixer.Sound("resources/sounds/shift.wav")
            shift_sound.set_volume(settings["sound_effects_volume"])
            eat_sound = pygame.mixer.Sound("resources/sounds/fruit.wav")
            eat_sound.set_volume(settings["sound_effects_volume"])
            speed_buff_sound = pygame.mixer.Sound("resources/sounds/buff.wav")
            speed_buff_sound.set_volume(settings["sound_effects_volume"])
            speed_debuff_sound = pygame.mixer.Sound("resources/sounds/debuff.wav")
            speed_debuff_sound.set_volume(settings["sound_effects_volume"])
        except pygame.error as e:
            print("Failed to load sound:", e)

        while True:
            game_speed = settings["game_speed"]
            print("Game speed:", game_speed)
            self.clock.tick(self.base_speed * self.snake.speed_modifier * game_speed)

            if not self.snake.handle_keys(shift_sound=shift_sound):
                break  # Exit the game loop and return to menu

            adjust_food_count(self.foods, self.snake.score)

            self.surface.blit(self.background, (0, 0))
            self.surface.blit(self.grid_surface, (0, 0))

            alive = self.snake.move()
            if not alive:
                death_sound.play()
                ret = game_over_screen(self.screen, self.snake, self.background, self.grid_surface, self.font, self.snake.score)
                if not ret:
                    break  # Return to main menu after game over

            head_pos = self.snake.get_head_position()
            for food in self.foods[:]:
                if head_pos == food.position:
                    self.snake.length += 1
                    self.snake.score += food.points
                    if isinstance(food, SpeedBoost):
                        speed_buff_sound.play()
                        food.apply_effect(self.snake)
                    elif isinstance(food, SpeedDebuff):
                        speed_debuff_sound.play()
                        food.apply_effect(self.snake)
                    else:
                        eat_sound.play()
                    self.foods.remove(food)
                    self.foods.append(get_random_food())
                food.draw(self.surface)

            self.snake.draw(self.surface)
            self.screen.blit(self.surface, (0, 0))
            self.surface.blit(self.grid_surface, (0, 0))

            score_text = self.font.render(f"Score {self.snake.score}", True, TEXT_COLOR)
            self.screen.blit(score_text, (5, 10))
            pygame.display.update()

