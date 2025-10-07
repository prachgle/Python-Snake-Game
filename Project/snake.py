import pygame
import random
import sys
import os
import time
from main import load_config

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

FONT_PATH = os.path.join(BASE_PATH, "resources", "Daydream.ttf")
CONFIG_PATH = os.path.join(BASE_PATH, "resources", "config.json")
SOUND_PATH = os.path.join(BASE_PATH, "resources", "sounds", "fruit.wav")

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
        self.move_timer = 0
        self.paused = False

    def should_move(self, base_speed, game_speed):
        self.move_timer += 1
        frames_per_move = int(60 / (base_speed * self.speed_modifier * game_speed))

        if self.move_timer >= frames_per_move:
            self.move_timer = 0
            return True
        return False

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
            if self.paused:
                return True
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

    def handle_keys(self, keys, events, shift_sound=None):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == keys["pause"]:
                    self.paused = not self.paused
                elif event.key == pygame.K_BACKSPACE:
                    return False
                elif event.key == keys["move_up"]:
                    self.turn(UP)
                elif event.key == keys["move_down"]:
                    self.turn(DOWN)
                elif event.key == keys["move_left"]:
                    self.turn(LEFT)
                elif event.key == keys["move_right"]:
                    self.turn(RIGHT)
                elif event.key == keys["sprint"]:
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
        snake.speed_modifier = 0.7
        snake.effect_timer = 18    
    def draw(self, surface):
        r = pygame.Rect((self.position[0], self.position[1]), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, (93, 216, 228), r, 1)

def get_random_food():
    food_classes = [Blueberry(), Apple(), Watermelon(), SpeedBoost(), SpeedDebuff()]
    return random.choices(food_classes, weights = [8, 6, 4, 5, 4], k = 14)[0]


def adjust_food_count(foods, score):
    desired_count = 1

    if 200 <= score < 1000:
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

def pause(screen, snake, keys, background, grid_surface, myfont):
    while snake.paused:
        screen.blit(background, (0,0))
        screen.blit(grid_surface, (0,0))
        pause_text = myfont.render("Game Paused", True, TEXT_COLOR)
        resume_text = myfont.render("Press R to resume or BACKSPACE to EXIT", True, TEXT_COLOR)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 60))
        screen.blit(resume_text, (SCREEN_WIDTH // 2 - 380, SCREEN_HEIGHT // 2 - 25))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    snake.paused = False
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    return False
            
    

def game_over_screen(screen, snake, background, grid_surface, myfont, score, multiplayer=False):
    while True:
        screen.blit(background, (0,0))
        screen.blit(grid_surface, (0,0))

        game_over_text = myfont.render("Game Over", True, TEXT_COLOR)
        restart_text = myfont.render("Press R to restart or ESC to EXIT", True, TEXT_COLOR)
        if multiplayer:
            score_text1 = myfont.render(f"Player1 Score: {score[0]}", True, TEXT_COLOR)
            score_text2 = myfont.render(f"Player2 Score: {score[1]}", True, TEXT_COLOR)
        else:
            score_text = myfont.render(f"Final Score: {score}", True, TEXT_COLOR)

        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 60))
        if not multiplayer:
            screen.blit(score_text, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 25))
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - 295, SCREEN_HEIGHT // 2 + 10))
        else:
            screen.blit(score_text1, (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 25))
            screen.blit(score_text2, (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 10))
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - 295, SCREEN_HEIGHT // 2 + 45))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                    return False
                elif event.key == pygame.K_r:
                    snake.reset()
                    return True

class BaseSnakeGame:
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

        self.font = pygame.font.Font(FONT_PATH, 20)
        self.base_speed = 10
        self.foods = [get_random_food()]

        self.settings = load_config()

        try:
            pygame.mixer.music.load("resources/music.mp3")
            pygame.mixer.music.set_volume(self.settings["music_volume"])
            pygame.mixer.music.play(-1)

            self.death_sound = pygame.mixer.Sound("resources/sounds/death.wav")
            self.shift_sound = pygame.mixer.Sound("resources/sounds/shift.wav")
            self.eat_sound = pygame.mixer.Sound("resources/sounds/fruit.wav")
            self.speed_buff_sound = pygame.mixer.Sound("resources/sounds/buff.wav")
            self.speed_debuff_sound = pygame.mixer.Sound("resources/sounds/debuff.wav")

            for snd in [self.death_sound, self.shift_sound, self.eat_sound, self.speed_buff_sound, self.speed_debuff_sound]:
                snd.set_volume(self.settings["sound_effects_volume"])
        except pygame.error as e:
            print("Failed to load sound:", e)


class SinglePlayerGame(BaseSnakeGame):
    def __init__(self, screen):
        super().__init__(screen)
        self.snake = Snake()

    def run(self):
        print("Single Player Game start")
        while True:
            self.clock.tick(self.base_speed * self.snake.speed_modifier * self.settings["game_speed"])
            events = pygame.event.get()

            if not self.snake.handle_keys(self.settings["key_bindings"]["player1"], events, shift_sound=self.shift_sound):
                break

            adjust_food_count(self.foods, self.snake.score)

            self.surface.blit(self.background, (0, 0))
            self.surface.blit(self.grid_surface, (0, 0))

            if self.snake.paused:
                ret = pause(self.screen, self.snake, self.settings["key_bindings"]["player1"], self.background, self.grid_surface, self.font)
                if not ret:
                    break

            alive = self.snake.move()
            if not alive:
                self.death_sound.play()
                ret = game_over_screen(self.screen, self.snake, self.background, self.grid_surface, self.font, self.snake.score)
                if not ret:
                    break

            head_pos = self.snake.get_head_position()
            for food in self.foods[:]:
                if head_pos == food.position:
                    self.snake.length += 1
                    self.snake.score += food.points
                    if isinstance(food, SpeedBoost):
                        self.speed_buff_sound.play()
                        food.apply_effect(self.snake)
                    elif isinstance(food, SpeedDebuff):
                        self.speed_debuff_sound.play()
                        food.apply_effect(self.snake)
                    else:
                        self.eat_sound.play()
                    self.foods.remove(food)
                    self.foods.append(get_random_food())
                food.draw(self.surface)

            self.snake.draw(self.surface)
            self.screen.blit(self.surface, (0, 0))
            self.surface.blit(self.grid_surface, (0, 0))

            score_text = self.font.render(f"Score {self.snake.score}", True, TEXT_COLOR)
            self.screen.blit(score_text, (5, 10))
            pygame.display.update()


class MultiPlayerGame(BaseSnakeGame):
    def __init__(self, screen):
        super().__init__(screen)
        self.snakes = [Snake(), Snake()]
        self.snakes[1].color = (abs(255 - self.snakes[1].color[0]), 
                                abs(155 - self.snakes[1].color[1]), 
                                abs(55 - self.snakes[1].color[2]))  # Different color for player 2

    def run(self):
        print("Multiplayer Game start")
        while True:
            game_speed = self.settings["game_speed"]
 
            self.clock.tick(60)
            events = pygame.event.get()

            keys_p1 = self.settings["key_bindings"]["player1"]
            keys_p2 = self.settings["key_bindings"]["player2"]

            if not self.snakes[0].handle_keys(keys_p1, events, shift_sound=self.shift_sound):
                break 
            if not self.snakes[1].handle_keys(keys_p2, events, shift_sound=self.shift_sound):
                break

            self.surface.blit(self.background, (0, 0))
            self.surface.blit(self.grid_surface, (0, 0))

            for i, snake in enumerate(self.snakes):
                if snake.should_move(self.base_speed, game_speed):
                    alive = snake.move()

                    # Self-collision is already handled in move(), but we check for collision with the *other* snake here
                    other_snake = self.snakes[1 - i]
                    if snake.get_head_position() in other_snake.position:
                        alive = False

                    if snake.paused:
                        ret = pause(self.screen, snake, self.settings["key_bindings"]["player1"], self.background, self.grid_surface, self.font)
                        if not ret:
                            return

                    if not alive:
                        self.death_sound.play()

                        # Show game over screen with both scores
                        score_text = f"P1 Score: {self.snakes[0].score}  |  P2 Score: {self.snakes[1].score}"
                        ret = game_over_screen(self.screen, 
                                               snake, 
                                               self.background, 
                                               self.grid_surface, 
                                               self.font, 
                                               (self.snakes[0].score, self.snakes[1].score),
                                               True)

                        if not ret:
                            return


            # Handle food consumption
            for snake in self.snakes:
                head_pos = snake.get_head_position()
                for food in self.foods[:]:
                    if head_pos == food.position:
                        snake.length += 1
                        snake.score += food.points
                        if isinstance(food, SpeedBoost):
                            self.speed_buff_sound.play()
                            food.apply_effect(snake)
                        elif isinstance(food, SpeedDebuff):
                            self.speed_debuff_sound.play()
                            food.apply_effect(snake)
                        else:
                            self.eat_sound.play()
                        self.foods.remove(food)
                        self.foods.append(get_random_food())
                        break  # Prevent double-eating
            adjust_food_count(self.foods, max(s.score for s in self.snakes))

            for food in self.foods:
                food.draw(self.surface)

            for i, snake in enumerate(self.snakes):
                snake.draw(self.surface)
                score_text = self.font.render(f"P{i+1} Score: {snake.score}", True, TEXT_COLOR)
                self.screen.blit(score_text, (5, 10 + i * 30))

            self.screen.blit(self.surface, (0, 0))
            pygame.display.update()
