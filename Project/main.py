import pygame
import random
import sys
import os
import json


BASE_PATH = os.path.dirname(os.path.abspath(__file__))

FONT_PATH = os.path.join(BASE_PATH, "resources", "Daydream.ttf")
CONFIG_PATH = os.path.join(BASE_PATH, "resources", "config.json")
SOUND_PATH = os.path.join(BASE_PATH, "resources", "sounds", "fruit.wav")

TEXT_COLOR = (255, 255, 255)

BACKGROUND_START = (48, 25, 52)
BACKGROUND_END = (16, 8, 32)

BUTTON_COLOR = (80, 40, 100)
BUTTON_HOVER_COLOR = (120, 80, 100)

# Load and save settings config
def load_config():
    try:
        if not os.path.exists(CONFIG_PATH): 
            raise FileNotFoundError("Config file not found.")
        
        with open(CONFIG_PATH, "r") as file:
            config = json.load(file)

        if "key_bindings" not in config:
            raise KeyError("Key bindings not found in config.")

        for player in config["key_bindings"]:
            for action in config["key_bindings"][player]:
                key_str = config["key_bindings"][player][action]
                if isinstance(key_str, str): # Only convert if it's a string
                    try:
                        config["key_bindings"][player][action] = getattr(pygame, key_str)
                    except AttributeError:
                        raise ValueError(f"Invalid key binding: {key_str} for {player} - {action}")
        return config

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except (KeyError, ValueError) as e:
        print(f"Error in config structure: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return None
    
def save_config(settings):
    try:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError("Config file not found.")
        
        with open(CONFIG_PATH, "w") as file:
            json.dump(settings, file, indent=4)
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

class BackgroundSnake:
    def __init__(self, screen):
        self.screen = screen
        self.position = [random.randint(0, 800), random.randint(0, 600)]
        self.velocity = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.length = random.randint(5, 45)
        self.body = [self.position[:]] * self.length
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def move(self):
        self.position[0] += self.velocity[0] * 3
        self.position[1] += self.velocity[1] * 3

        width, height = self.screen.get_size()
        if self.position[0] <= 0 or self.position[0] >= width:
            self.velocity[0] *= -1
        if self.position[1] <= 0 or self.position[1] >= height:
            self.velocity[1] *= -1
        
        self.body.insert(0, list(self.position))
        self.body = self.body[:self.length]  # Keep only the last 5 positions
    
    def draw(self):
        for segment in self.body:
            pygame.draw.rect(self.screen, self.color, (*segment, 10, 10))

class Button:
    def __init__(self, text, font, x, y, width, height, callback=None):
        self.text = text
        self.font = font
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
    
    def draw(self, screen, mouse_pos):
        color = BUTTON_HOVER_COLOR if self.rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect)
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.callback:
                sound = pygame.mixer.Sound("resources/sounds/fruit.wav")
                sound.set_volume(load_config()["sound_effects_volume"])
                sound.play()
                self.callback()

class CircleButtons:
    def __init__(self, center, radius, action, is_plus=True):
        self.center = center
        self.radius = radius
        self.action = action
        self.is_plus = is_plus
        self.color = (200, 200, 200) if is_plus else (150, 150, 150)
        self.rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), self.center, self.radius, 2)
        cx, cy = self.center
        pygame.draw.line(screen, (255, 255, 255), (cx-8, cy), (cx + 8, cy), 2)
        if self.is_plus:
            pygame.draw.line(screen, (255, 255, 255), (cx, cy-8), (cx, cy + 8), 2)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            sound = pygame.mixer.Sound("resources/sounds/fruit.wav")
            sound.set_volume(load_config()["sound_effects_volume"])
            sound.play()
            self.action()

class KeyBindings:
    def __init__(self, main):
        self.main = main
        self.config = main.settings
        self.font_path = FONT_PATH
        self.screen = main.screen
        self.key_pressed = None  # (player, action)
        self.scroll_offset = 0
        self.scroll_speed = 2

        self.key_buttons = {}  # {(player, action): Button}
        self.back_button = Button("Back", None, 0, 0, 150, 50, self.back_to_settings)  # Font assigned later
        self.create_buttons()
        self.scale_ui()

    def parse_key_name(self, key_name):
        return getattr(pygame, key_name, None)

    def get_max_scroll_offset(self):
        total_height = 0
        for player in ["player1", "player2"]:
            total_height += self.box_height + int(30 * self.scale)
            total_height += len(self.config["key_bindings"][player]) * (self.box_height + self.padding)
        total_height += int(100 * self.scale)  # space for title and padding
        visible_height = self.screen_height - int(100 * self.scale)  # approx visible area
        max_scroll = max(0, total_height - visible_height)
        return max_scroll // self.scroll_speed  # adjust for scroll_speed scaling


    def create_buttons(self):
        self.key_buttons.clear()
        for player in ["player1", "player2"]:
            for action in self.config["key_bindings"][player]:
                btn = Button("...", None, 0, 0, 200, 40,
                             callback=lambda p=player, a=action: self.set_key(p, a))
                self.key_buttons[(player, action)] = btn
        
        for (player, action), button in self.key_buttons.items():
            button.text = self.format_key(self.config["key_bindings"][player][action])

    def set_key(self, player, action):
        self.key_pressed = (player, action)

    def scale_ui(self):
        self.screen_width, self.screen_height = self.config["window_size"]
        self.scale = max(0.8, min(2.0, self.screen_width / 800))
        font_size = max(16, int(20 * self.scale))
        self.font = pygame.font.Font(self.font_path, font_size)

        # Resize back button
        self.back_button.font = self.font
        self.back_button.rect.size = (int(180 * self.scale), int(50 * self.scale))
        self.back_button.rect.center = (self.screen_width // 2, self.screen_height - int(60 * self.scale))

        # Resize key buttons
        for (player, action), btn in self.key_buttons.items():
            btn.font = self.font
            btn.rect.size = (int(200 * self.scale), int(40 * self.scale))

        # Title
        title_font_size = int(30 * self.scale)
        self.title_font = pygame.font.Font(self.font_path, title_font_size)
        self.title_surface = self.title_font.render("Key Bindings", True, TEXT_COLOR)
        self.title_rect = self.title_surface.get_rect(center=(self.screen_width // 2, int(50 * self.scale)))

        self.box_height = int(40 * self.scale)
        self.padding = int(10 * self.scale)

    def handle_event(self, event):
        self.back_button.handle_event(event)
        for btn in self.key_buttons.values():
            btn.handle_event(event)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * 20
            self.scroll_offset = max(0, min(self.scroll_offset, self.get_max_scroll_offset()))

        elif event.type == pygame.KEYDOWN and self.key_pressed:
            player, action = self.key_pressed
            new_key = event.key
            self.config["key_bindings"][player][action] = new_key
            self.key_buttons[(player, action)].text = self.format_key(new_key)
            save_config(self.config)
            self.key_pressed = None

    def format_label(self, text):
        return text.replace("_", " ").title()

    def format_key(self, key_code):
        return pygame.key.name(key_code).upper()

    def draw(self):
        y_offset = int(100 * self.scale) - self.scroll_offset * self.scroll_speed

        if y_offset > int(60 * self.scale):
            self.screen.blit(self.title_surface, self.title_rect)

        mouse_pos = pygame.mouse.get_pos()

        for player in ["player1", "player2"]:
            header = self.font.render(player.capitalize(), True, TEXT_COLOR)
            header_rect = header.get_rect(topleft=(int(50 * self.scale), y_offset))
            self.screen.blit(header, header_rect)
            y_offset += self.box_height + int(30 * self.scale)

            for action, key in self.config["key_bindings"][player].items():
                label_surface = self.font.render(self.format_label(action), True, TEXT_COLOR)
                label_rect = label_surface.get_rect()
                label_rect.right = self.screen_width // 2 - int(20 * self.scale)  # leave gap before button
                label_rect.top = y_offset
                self.screen.blit(label_surface, label_rect)

                btn = self.key_buttons[(player, action)]
                btn.text = "..." if self.key_pressed == (player, action) else self.format_key(key)
                btn.rect.topleft = (self.screen_width // 2 + int(10 * self.scale), y_offset)
                btn.draw(self.screen, mouse_pos)

                y_offset += self.box_height + self.padding

        # Draw back button at the bottom
        self.back_button.rect.center = (self.screen_width // 2, y_offset + int(40 * self.scale))
        self.back_button.draw(self.screen, mouse_pos)

    def update(self, new_size):
        self.config["window_size"] = new_size
        self.scale_ui()

    def back_to_settings(self):
        self.main.in_key_bindings = False
        self.main.in_settings = True


class SettingsMenu:
    def __init__(self, main):
        self.main = main
        self.settings = main.settings
        self.font = main.font
        self.title_font = main.title_font
        self.window_sizes = [
            [640, 480],
            [800, 600],
            [1024, 768],
            [1280, 720],
            [1366, 768],
            [1600, 900],
            [1920, 1080]
        ]

        self.button_action = {
            "music_minus": (self.decrease_music_volume, False),
            "music_plus": (self.increase_music_volume, True),   
            "sounds_minus": (self.decrease_sounds_volume, False),
            "sounds_plus": (self.increase_sounds_volume, True),
            "speed_minus": (self.decrease_speed, False),
            "speed_plus": (self.increase_speed, True),
        }

        self.buttons = {name: CircleButtons((0, 0), 15, action, is_plus)
                        for name, (action, is_plus) in self.button_action.items()}
        
        self.key_button = Button("Key Bindings", self.font, 0, 0, 250, 50, self.open_key_bindings)
        self.back_button = Button("Back", self.font, 0, 0, 120, 40, self.back_to_main_menu)

        self.scroll_offset = 0
        self.scroll_speed = 40
        self.total_rows = 5
        
    def draw(self, screen):
        width, height = self.settings["window_size"]
        cx = width // 2

        scale = max(0.8, min(2, width / 800))  # Scale based on window width
        font_size = max(16, min(int(20 * scale), 28))
        title_font_size = max(20, int(32 * scale))
        self.font = pygame.font.Font(FONT_PATH, font_size)
        self.title_font = pygame.font.Font(FONT_PATH, title_font_size)

        y_start = int(150 * scale)
        gap = int(90 * scale)
        label_offset = int(-20 * scale)
        value_offset = int(35 * scale)
        button_offset = int(35 * scale)

        if self.scroll_offset == 0:
            title_surface = self.title_font.render("Settings", True, TEXT_COLOR)
            screen.blit(title_surface, title_surface.get_rect(center=(cx, int(80 * scale))))

        labels = [
                  "Music Volume", 
                  "Sounds Volume", "Game Speed"]
        values = [
            f"{int(self.settings['music_volume'] * 100)}%",
            f"{int(self.settings['sound_effects_volume'] * 100)}%",
            f"{int(self.settings['game_speed'] * 10)}"
        ]

        def row_y(row_idx):
            return y_start + row_idx * gap - self.scroll_offset

        label_offset_table = [105 * scale, 110 * scale, 110 *scale, 90 * scale]
        for i, (label, value) in enumerate(zip(labels, values)):
            y = row_y(i)
            if not(y < -gap or y > height + gap):
                label_surface = self.font.render(label, True, TEXT_COLOR)
                value_surface = self.font.render(value, True, TEXT_COLOR)
                screen.blit(label_surface, (cx - label_offset_table[i], y + label_offset ))
                screen.blit(value_surface, value_surface.get_rect(center=(cx, y + value_offset)))
        
        def pos(i, side):
            return (cx + int(side * 100 * scale), row_y(i) + button_offset)
        
        self.buttons["music_minus"].center = pos(0, -1)
        self.buttons["music_plus"].center = pos(0, 1)
        self.buttons["sounds_minus"].center = pos(1, -1)
        self.buttons["sounds_plus"].center = pos(1, 1)
        self.buttons["speed_minus"].center = pos(2, -1)
        self.buttons["speed_plus"].center = pos(2, 1)

        for button in self.buttons.values():
            button.rect.center = button.center
            button.rect.size = (int(40 * scale), int(40 * scale))
            button.font = self.font
            if -gap < button.center[1] < height + gap:
                button.draw(screen)
        
        # Key Bindings button
        y_key = row_y(3)
        self.key_button.rect.size = (int(220 * scale), int(50 * scale))
        self.key_button.rect.center = (cx, y_key + int(20 * scale))
        self.key_button.font = self.font
        if -gap < y_key < height + gap:
            self.key_button.draw(screen, pygame.mouse.get_pos())

        # Back button
        y_back = row_y(4)
        self.back_button.rect.size = (int(180 * scale), int(50 * scale))
        self.back_button.rect.center = (cx, y_back)
        self.back_button.font = self.font
        if -gap < y_back < height + gap:
            self.back_button.draw(screen, pygame.mouse.get_pos())
    
    def handle_event(self, event):
        for button in self.buttons.values():
            button.handle_event(event)
        self.key_button.handle_event(event)
        self.back_button.handle_event(event)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * self.scroll_speed
            self._clamp_scroll()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.scroll_offset -= self.scroll_speed
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.scroll_offset += self.scroll_speed
            self._clamp_scroll()
    
    def _clamp_scroll(self):
        width, height = self.settings["window_size"]
        scale = max(0.8, min(2, width / 800))
        y_start = int(150 * scale)
        gap = int(90 * scale)
        bottom_margin = int(120 * scale)
        content_height = y_start + (self.total_rows - 1) * gap + bottom_margin
        max_offset = max(0, content_height - height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))

    def get_window_index(self):
        try:
            return self.window_sizes.index(self.settings["window_size"])
        except ValueError:
            return -1

    def increase_window_size(self):
        index = self.get_window_index()
        if index < len(self.window_sizes) - 1:
            self.settings["window_size"] = self.window_sizes[index + 1]
            self.apply_window_size()
    
    def decrease_window_size(self):
        index = self.get_window_index()
        if index > 0:
            self.settings["window_size"] = self.window_sizes[index - 1]
            self.apply_window_size()
    
    def apply_window_size(self):
        self.main.screen = pygame.display.set_mode(self.settings["window_size"])
        save_config(self.settings)
    
    def increase_music_volume(self):
        self.settings["music_volume"] = min(self.settings["music_volume"] + 0.1, 1.0)
        pygame.mixer.music.set_volume(self.settings["music_volume"])
        save_config(self.settings)
    
    def decrease_music_volume(self):
        self.settings["music_volume"] = max(self.settings["music_volume"] - 0.1, 0.0)
        pygame.mixer.music.set_volume(self.settings["music_volume"])
        save_config(self.settings)
    
    def increase_sounds_volume(self):
        self.settings["sound_effects_volume"] = min(self.settings["sound_effects_volume"] + 0.1, 1.0)
        save_config(self.settings)

    def decrease_sounds_volume(self):
        self.settings["sound_effects_volume"] = max(self.settings["sound_effects_volume"] - 0.1, 0.0)
        save_config(self.settings)

    def increase_speed(self):
        self.settings["game_speed"] = min(self.settings["game_speed"] + 0.1, 4.0)
        save_config(self.settings)

    def decrease_speed(self):
        self.settings["game_speed"] = max(self.settings["game_speed"] - 0.1, 0.1)
        save_config(self.settings)

    def open_key_bindings(self):
        self.main.in_settings = False
        self.main.in_key_bindings = True
    
    def back_to_main_menu(self):
        self.main.in_settings = False

class Main:
    def __init__(self):
        pygame.init()
        self.settings = load_config()
        self.screen = pygame.display.set_mode(self.settings["window_size"], 0, 32)
        pygame.display.set_caption("Greedy Snake")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(FONT_PATH, 20)
        self.title_font = pygame.font.Font(FONT_PATH, 32)

        self.snakes = [BackgroundSnake(self.screen) for _ in range(5)]
        self.buttons = []
        self.in_settings = False
        self.in_key_bindings = False
        self.settings_menu = SettingsMenu(self)
        self.key_bindings_menu = KeyBindings(self)

        self.in_game = False
        self.game_screen = None

        pygame.mixer.init()
        self.death_sound = pygame.mixer.Sound("resources/sounds/death.wav")
        self.shift_sound = pygame.mixer.Sound("resources/sounds/shift.wav")
        self.eat_sound = pygame.mixer.Sound("resources/sounds/fruit.wav")
        self.buff_sound = pygame.mixer.Sound("resources/sounds/buff.wav")
        self.debuff_sound = pygame.mixer.Sound("resources/sounds/debuff.wav")

        try:
            pygame.mixer.music.load("resources/music.mp3")
            pygame.mixer.music.set_volume(self.settings["music_volume"])
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print("Failed to load music:", e)
        
        self.create_buttons()

    
    def create_buttons(self):
        self.buttons = []
        width, height = 200, 50
        total_button_width = width + 50
        x = (self.settings["window_size"][0]  - total_button_width) // 2
        y_start = 250
        gap = 70

        self.buttons.append(Button("Singleplayer", self.font, x, y_start, total_button_width, height, self.start_singleplayer))
        self.buttons.append(Button("Multiplayer", self.font, x, y_start + gap, total_button_width, height, self.start_multiplayer))
        self.buttons.append(Button("Settings", self.font, x, y_start + 2 * gap, total_button_width, height, self.open_settings))
        self.buttons.append(Button("Exit", self.font, x, y_start + 3 * gap, total_button_width, height, self.exit_game))

    def draw_gradient_background(self):
        width, height = self.settings["window_size"]
        for y in range(height):
            ratio = y / height
            r = int(48 * (1 - ratio) + 16 * ratio)
            g = int(25 * (1 - ratio) + 8 * ratio)
            b = int(52 * (1 - ratio) + 32 * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (width, y))
    
    def draw_title(self):
        title_surface = self.title_font.render("Greedy Snake", True, TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(self.settings["window_size"][0] // 2, 100))
        self.screen.blit(title_surface, title_rect)

    def open_settings(self):
        self.in_settings = True

    def start_singleplayer(self):
        from snake import SinglePlayerGame
        print("Starting singleplayer mode...")
        self.in_game = True
        game = SinglePlayerGame(self.screen)
        game.run()
        self.in_game = False


    def start_multiplayer(self):
        from snake import MultiPlayerGame
        print("Starting multiplayer mode...")
        self.in_game = True
        game = MultiPlayerGame(self.screen)
        game.run()
        self.in_game = False
    
    def exit_game(self):
        print("Exiting game...")
        pygame.quit()
        sys.exit()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exit_game()

            if self.in_settings:
                self.settings_menu.handle_event(event)
            elif self.in_key_bindings:
                self.key_bindings_menu.handle_event(event)
            else:
                for button in self.buttons:
                    button.handle_event(event)
    
    def update_button_positions(self):
        width, height = self.settings["window_size"]
        scale = width / 800  # Assuming 800 is the base width for button scaling
        font_size = max(16, int(20 * scale))
        self.font = pygame.font.Font(FONT_PATH, font_size)

        btn_width = int(250 * scale)
        btn_height = int(50 * scale)
        x = (width - btn_width) // 2
        y_start = int(150 * scale)
        gap = int(70 * scale)

        for i, button in enumerate(self.buttons):
            button.rect.update(x, y_start + i * gap, btn_width, btn_height)
        for button in self.buttons:
            button.font = self.font

    def run(self):
        while True:
            self.handle_events()
            self.screen.fill((0, 0, 0))
            self.draw_gradient_background()

            if self.in_settings:
                self.settings_menu.draw(self.screen)
            elif self.in_key_bindings:
                self.key_bindings_menu.draw()
            else:
                self.draw_title()

                for snake in self.snakes:
                    snake.move()
                    snake.draw()

                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons:
                    button.draw(self.screen, mouse_pos)
                self.update_button_positions()

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    try:
        main_game = Main()
        main_game.run()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        pygame.quit()
        sys.exit()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        pygame.quit()
        sys.exit()


        