import pygame
import random
import sys
import os
import json


FONT_PATH = "resources/Daydream.ttf"
TEXT_COLOR = (255, 255, 255)

BACKGROUND_START = (48, 25, 52)
BACKGROUND_END = (16, 8, 32)

BUTTON_COLOR = (80, 40, 100)
BUTTON_HOVER_COLOR = (120, 80, 100)

# Load and save settings config
def load_config():
    if not os.path.exists("resources/config.json"):
        raise FileNotFoundError("Config file not found.")
    with open("resources/config.json", "r") as file:
        config = json.load(file)
    
    for player in config["key_bindings"]:
        for action, key in config["key_bindings"][player].items():
            if isinstance(key, str) and key.startswith("K_"):
                config["key_bindings"][player][action] = getattr(pygame, key, None)
    return config
    
def save_config(settings):
    # settings_copy = json.loads(json.dumps(settings))  # Create a deep copy
    # for player in settings_copy["key_bindings"]:
    #     for action, key in settings_copy["key_bindings"][player].items():
    #         if isinstance(key, int):
    #             settings_copy["key_bindings"][player][action] = pygame.key.name(key)
    # with open("resources/config.json", "w") as file:
    #     json.dump(settings_copy, file, indent=4)
    def serialize_key_bindings(bindings):
        if isinstance(bindings, dict) and "key_bindings" in bindings:
            kb = bindings["key_bindings"]
            for player in kb:
                for action in kb[player]:
                    key = kb[player][action]
                    if isinstance(key, int):
                        kb[player][action] = f"K_{pygame.key.name(key).upper()}"
        return bindings
    
    with open("resources/config.json", "w") as file:
        json.dump(serialize_key_bindings(settings), file, indent=4)
        

class BackgroundSnake:
    def __init__(self, screen):
        self.screen = screen
        self.position = [random.randint(0, 800), random.randint(0, 600)]
        self.velocity = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.lenght = random.randint(5, 45)
        self.body = [self.position[:]] * self.lenght
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
        self.body = self.body[:self.lenght]  # Keep only the last 5 positions
    
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
            self.action()

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
            "win_minus": (self.decrease_window_size, False),
            "win_plus": (self.increase_window_size, True),
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
        self.static_buttons = [self.key_button, self.back_button]

        self.scroll_offset = 0
        self.scroll_speed = 40
        self.total_rows = 6
        
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

        labels = ["Window Size", "Music Volume", "Sounds Volume", "Game Speed"]
        values = [
            f"{self.settings['window_size'][0]}x{self.settings['window_size'][1]}",
            f"{int(self.settings['music_volume'] * 100)}%",
            f"{int(self.settings['sound_effects_volume'] * 100)}%",
            f"{int(self.settings['game_speed'] * 1)}"
        ]

        # for i in range(3):
        #     y = y_start + i * gap
        #     label_surface = self.font.render(labels[i], True, TEXT_COLOR)
        #     value_surface = self.font.render(values[i], True, TEXT_COLOR)

        #     screen.blit(label_surface, (cx - 100, y + label_offset))
        #     screen.blit(value_surface, value_surface.get_rect(center=(cx, y + value_offset)))

        def row_y(row_idx):
            return y_start + row_idx * gap - self.scroll_offset

        #Screen label
        #y = y_start + 0 * gap
        y = row_y(0)
        if not(y < -gap or y > height + gap):
            label_surface = self.font.render(labels[0], True, TEXT_COLOR)
            value_surface = self.font.render(values[0], True, TEXT_COLOR)

            screen.blit(label_surface, (cx - int(105 * scale), y + label_offset))
            screen.blit(value_surface, value_surface.get_rect(center=(cx, y + value_offset)))

        #Music label
        #y = y_start + 1 * gap
        y = row_y(1)
        if not(y < -gap or y > height + gap):
            label_surface = self.font.render(labels[1], True, TEXT_COLOR)
            value_surface = self.font.render(values[1], True, TEXT_COLOR)

            screen.blit(label_surface, (cx - int(115 * scale), y + label_offset))
            screen.blit(value_surface, value_surface.get_rect(center=(cx, y + value_offset)))

        #Sounds label
        #y = y_start + 2 * gap
        y = row_y(2)
        if not(y < -gap or y > height + gap):
            label_surface = self.font.render(labels[2], True, TEXT_COLOR)
            value_surface = self.font.render(values[2], True, TEXT_COLOR)

            screen.blit(label_surface, (cx - int(130 * scale), y + label_offset))
            screen.blit(value_surface, value_surface.get_rect(center=(cx, y + value_offset)))

        #Game Speed label
        #y = y_start + 3 * gap
        y = row_y(3)
        if not(y < -gap or y > height + gap):
            label_surface = self.font.render(labels[3], True, TEXT_COLOR)
            value_surface = self.font.render(values[3], True, TEXT_COLOR)

            screen.blit(label_surface, (cx - int(100 * scale), y + label_offset))
            screen.blit(value_surface, value_surface.get_rect(center=(cx, y + value_offset)))
        
        def pos(i, side):
            return (cx + int(side * 100 *scale), row_y(i) + button_offset)
        
        self.buttons["win_minus"].center = pos(0, -1)
        self.buttons["win_plus"].center = pos(0, 1)
        self.buttons["music_minus"].center = pos(1, -1)
        self.buttons["music_plus"].center = pos(1, 1)
        self.buttons["sounds_minus"].center = pos(2, -1)
        self.buttons["sounds_plus"].center = pos(2, 1)
        self.buttons["speed_minus"].center = pos(3, -1)
        self.buttons["speed_plus"].center = pos(3, 1)

        for button in self.buttons.values():
            button.rect.center = button.center
            button.rect.size = (int(40 * scale), int(40 * scale))
            button.font = self.font
            if -gap < button.center[1] < height + gap:
                button.draw(screen)
        
        # Key Bindings button
        y_key = row_y(4)
        self.key_button.rect.size = (int(220 * scale), int(50 * scale))
        self.key_button.rect.center = (cx, y_key + int(20 * scale))
        self.key_button.font = self.font
        if -gap < y_key < height + gap:
            self.key_button.draw(screen, pygame.mouse.get_pos())

        # Back button
        y_back = row_y(5)
        self.back_button.rect.size = (int(180 * scale), int(50 * scale))
        self.back_button.rect.center = (cx, y_back)
        self.back_button.font = self.font
        if -gap < y_back < height + gap:
            self.back_button.draw(screen, pygame.mouse.get_pos())

        # self.buttons["win_minus"].center = (cx - 100, y_start + 0 * gap + button_offset)
        # self.buttons["win_plus"].center = (cx + 100, y_start + 0 * gap + button_offset)
        # self.buttons["music_minus"].center = (cx - 100, y_start + 1 * gap + button_offset)
        # self.buttons["music_plus"].center = (cx + 100, y_start + 1 * gap + button_offset)
        # self.buttons["sounds_minus"].center = (cx - 100, y_start + 2 * gap + button_offset)
        # self.buttons["sounds_plus"].center = (cx + 100, y_start + 2 * gap + button_offset)
        # self.buttons["speed_minus"].center = (cx - 100, y_start + 3 * gap + button_offset)
        # self.buttons["speed_plus"].center = (cx + 100, y_start + 3 * gap + button_offset)

        # for button in self.buttons.values():
        #     button.rect.center = button.center
        #     button.draw(screen)
        
        # self.key_button.rect.center = (cx, y_start + 4 * gap + 20)
        # self.key_button.draw(screen, pygame.mouse.get_pos())

        # self.back_button.rect.center = (self.settings["window_size"][0] // 2, self.settings["window_size"][1] - 60)
        # self.back_button.draw(screen, pygame.mouse.get_pos())
    
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
    
    def decrease_music_volume(self):
        self.settings["music_volume"] = max(self.settings["music_volume"] - 0.1, 0.0)
    
    def increase_sounds_volume(self):
        self.settings["sound_effects_volume"] = min(self.settings["sound_effects_volume"] + 0.1, 1.0)
    
    def decrease_sounds_volume(self):
        self.settings["sound_effects_volume"] = max(self.settings["sound_effects_volume"] - 0.1, 0.0)

    def increase_speed(self):
        self.settings["game_speed"] = min(self.settings["game_speed"] + 1, 20.0)
    
    def decrease_speed(self):
        self.settings["game_speed"] = max(self.settings["game_speed"] - 1, 1.0)
    
    def open_key_bindings(self):
        print("Opening key bindings...")
    
    def back_to_main_menu(self):
        self.main.in_settings = False
    

class Main:
    def __init__(self):
        pygame.init()
        self.settings = load_config()
        self.screen = pygame.display.set_mode(self.settings["window_size"])
        pygame.display.set_caption("Greedy Snake")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(FONT_PATH, 20)
        self.title_font = pygame.font.Font(FONT_PATH, 32)

        self.snakes = [BackgroundSnake(self.screen) for _ in range(5)]
        self.buttons = []
        self.in_settings = False
        self.settings_menu = SettingsMenu(self)

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
        #TO.DO: Implement settings menu
        self.in_settings = True

    def start_singleplayer(self):
        print("Starting singleplayer mode...")
        # TO.DO: Implement singleplayer game logic

    def start_multiplayer(self):
        print("Starting multiplayer mode...")
        # TO.DO: Implement multiplayer game logic
    
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
            else:
                self.draw_title()

                for snake in self.snakes:
                    snake.move()
                    snake.draw()
                
                self.draw_title()

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


        