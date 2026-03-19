import pygame
import sys
import time
import os
import math

# --- CRITICAL: Initialize Mixer ---
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

from animals import ANIMALS
from world_scene import WorldScene
from player_drawer import draw_realistic_player_complex
from ui import SND_FEED, SND_PET, SND_UI, SND_UNLOCK
from house_scene import HouseScene
from barn_scene import BarnScene

# --- Dynamic Path Handling ---
def get_base_path():
    if getattr(sys, 'frozen', False):
        # The application is frozen (compiled into an EXE)
        return sys._MEIPASS
    else:
        # The application is running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()
ASSETS_PATH = os.path.join(BASE_PATH, "assets", "sounds")
BGM_PATH = os.path.join(ASSETS_PATH, "farm_theme.mp3")
SND_PATH_TRACTOR = os.path.join(ASSETS_PATH, "tractor.wav")
SND_PATH_CHICKEN = os.path.join(ASSETS_PATH, "chicken_eat.wav")

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Virtual Farm")
clock = pygame.time.Clock()

# --- Global State ---
xp, unlocked_max, game_mode = 0, 0, "home"
selected_character, xp_enabled = "boy", True
master_volume, sfx_volume = 0.3, 0.2
is_dragging_master = is_dragging_sfx = False
last_barn_visit_time = 0
is_paused = False


# --- Asset Loader Helper ---
def safe_load_sound(path, fallback):
    if os.path.exists(path):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(sfx_volume)
            return s
        except:
            return fallback
    return fallback


snd_tractor = safe_load_sound(SND_PATH_TRACTOR, SND_UI)
snd_chicken = safe_load_sound(SND_PATH_CHICKEN, None)

# --- UI Assets ---
UI_FONT = pygame.font.SysFont("Arial", 24, bold=True)
TITLE_FONT = pygame.font.SysFont("Arial", 64, bold=True)
STAT_FONT = pygame.font.SysFont("Arial", 16, bold=True)
GOLD, WHITE, GREEN, RED, BLUE = (255, 215, 0), (255, 255, 255), (76, 175, 80), (229, 57, 53), (33, 150, 243)

# --- Audio Setup ---
if os.path.exists(BGM_PATH):
    try:
        pygame.mixer.music.load(BGM_PATH)
        pygame.mixer.music.set_volume(master_volume)
        pygame.mixer.music.play(-1)
    except:
        pass


def update_audio_levels():
    pygame.mixer.music.set_volume(master_volume)
    for s in [SND_FEED, SND_PET, SND_UI, SND_UNLOCK, snd_tractor, snd_chicken]:
        if s and hasattr(s, 'set_volume'): s.set_volume(sfx_volume)


update_audio_levels()


# --- UI Helpers ---
def draw_custom_slider(surface, x, y, val, label, color=BLUE):
    width, height = 150, 10
    slider_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (60, 60, 70), slider_rect, border_radius=5)
    pygame.draw.rect(surface, color, (x, y, int(width * val), height), border_radius=5)
    handle_x = x + int(width * val)
    handle_rect = pygame.Rect(handle_x - 15, y - 10, 30, 30)
    pygame.draw.circle(surface, WHITE, (handle_x, y + 5), 12)
    txt = STAT_FONT.render(f"{label}: {int(val * 100)}%", True, WHITE)
    surface.blit(txt, (x + width + 15, y - 5))
    return slider_rect, handle_rect


def draw_hud(surface):
    draw_custom_slider(surface, 30, 30, master_volume, "MUSIC")
    draw_custom_slider(surface, 30, 70, sfx_volume, "SFX", (200, 100, 200))

    if xp_enabled:
        bx, by, bw = WIDTH - 240, 20, 220
        pygame.draw.rect(surface, (40, 40, 50), (bx, by, bw, 25), border_radius=12)
        pygame.draw.rect(surface, GOLD, (bx, by, int(bw * ((xp % 50) / 50)), 25), border_radius=12)
        pygame.draw.rect(surface, WHITE, (bx, by, bw, 25), 2, border_radius=12)
        txt = STAT_FONT.render(f"XP: {xp % 50}/50 (Lvl {unlocked_max + 1})", True, WHITE)
        surface.blit(txt, (bx + bw // 2 - txt.get_width() // 2, by + 3))

    pause_rect = pygame.Rect(WIDTH - 130, 60, 110, 35)
    quit_rect = pygame.Rect(WIDTH - 250, 60, 110, 35)

    p_color = (200, 150, 50) if is_paused else (100, 150, 200)
    pygame.draw.rect(surface, p_color, pause_rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, pause_rect, 2, border_radius=8)
    p_txt = STAT_FONT.render("RESUME" if is_paused else "PAUSE", True, WHITE)
    surface.blit(p_txt, (pause_rect.centerx - p_txt.get_width() // 2, pause_rect.centery - p_txt.get_height() // 2))

    pygame.draw.rect(surface, RED, quit_rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, quit_rect, 2, border_radius=8)
    q_txt = STAT_FONT.render("QUIT", True, WHITE)
    surface.blit(q_txt, (quit_rect.centerx - q_txt.get_width() // 2, quit_rect.centery - q_txt.get_height() // 2))


def add_xp(amount):
    global xp, unlocked_max
    if xp_enabled:
        xp += amount
        new_val = min(len(ANIMALS) - 1, xp // 50)
        if new_val > unlocked_max:
            unlocked_max = new_val
            SND_UNLOCK.play()


class FloatingButton:
    def __init__(self, id, text, x, y, color):
        self.id, self.text, self.x_off, self.y_off = id, text, x, y
        self.rect = pygame.Rect(0, 0, 110, 40)
        self.color = GREEN if color == "green" else (233, 30, 99) if color == "pink" else (156, 39, 176)

    def update_position(self, cx, cy): self.rect.center = (cx + self.x_off, cy + self.y_off)

    def draw(self, surf, alpha):
        s = pygame.Surface((110, 40), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.color, alpha), (0, 0, 110, 40), border_radius=10)
        surf.blit(s, self.rect.topleft)
        t = UI_FONT.render(self.text, True, WHITE)
        t.set_alpha(alpha)
        surf.blit(t, (self.rect.centerx - t.get_width() // 2, self.rect.centery - t.get_height() // 2))

    def hit(self, mx, my): return self.rect.collidepoint(mx, my)


world = WorldScene(ANIMALS, add_xp, lambda: None, lambda i: None, lambda: selected_character, None, None,
                   FloatingButton)
house = HouseScene(lambda: selected_character)


def main():
    global game_mode, selected_character, xp_enabled, unlocked_max, xp
    global master_volume, sfx_volume, is_dragging_master, is_dragging_sfx
    global last_barn_visit_time, is_paused

    barn = BarnScene(lambda: selected_character)

    boy_r = pygame.Rect(WIDTH // 2 - 250, 200, 200, 250)
    girl_r = pygame.Rect(WIDTH // 2 + 50, 200, 200, 250)
    xp_btn = pygame.Rect(WIDTH // 2 - 150, 480, 300, 50)
    start_btn = pygame.Rect(WIDTH // 2 - 100, 600, 200, 60)

    while True:
        dt = clock.tick(60) / 1000.0
        mx, my = pygame.mouse.get_pos()
        current_time = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pause_rect = pygame.Rect(WIDTH - 130, 60, 110, 35)
                quit_rect = pygame.Rect(WIDTH - 250, 60, 110, 35)

                if quit_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

                if pause_rect.collidepoint(mx, my):
                    is_paused = not is_paused
                    SND_UI.play()
                    continue

                m_s, m_h = draw_custom_slider(screen, 30, 30, master_volume, "BGM")
                if m_s.collidepoint(mx, my) or m_h.collidepoint(mx, my): is_dragging_master = True
                s_s, s_h = draw_custom_slider(screen, 30, 70, sfx_volume, "SFX", (200, 100, 200))
                if s_s.collidepoint(mx, my) or s_h.collidepoint(mx, my): is_dragging_sfx = True

                if not is_paused:
                    if game_mode == "home":
                        if boy_r.collidepoint(mx, my):
                            selected_character = "boy"
                            SND_UI.play()
                        elif girl_r.collidepoint(mx, my):
                            selected_character = "girl"
                            SND_UI.play()
                        elif xp_btn.collidepoint(mx, my):
                            xp_enabled = not xp_enabled
                            SND_UI.play()
                            unlocked_max = len(ANIMALS) - 1 if not xp_enabled else min(len(ANIMALS) - 1, xp // 50)
                        elif start_btn.collidepoint(mx, my):
                            game_mode = "world"
                            SND_UI.play()

                    elif game_mode == "world":
                        res = world.handle_click((mx, my))
                        if res == "enter_house":
                            game_mode = "house"
                            house.player_x, house.player_y = 640, 500
                            SND_UI.play()
                        elif res == "enter_barn":
                            game_mode = "barn"
                            barn.player_x, barn.player_y = 640, 400
                            SND_UI.play()
                        elif res in ["feed", "pet"]:
                            (SND_FEED if res == "feed" else SND_PET).play()

                    elif game_mode == "house":
                        res_h = house.handle_click(event.pos)
                        if res_h == "exit_house":
                            game_mode = "world"
                            world.player_y += 120

                            if hasattr(world, 'solids'):
                                feet = pygame.Rect(world.player_x - 15, world.player_y + 155, 30, 10)
                                for solid in world.solids:
                                    if feet.colliderect(solid):
                                        world.player_y = solid.bottom - 145

                            SND_UI.play()
                        elif res_h == "toggle_lamp":
                            SND_UI.play()
                        elif res_h == "feed_fish":
                            SND_FEED.play()

                    elif game_mode == "barn":
                        res_b = barn.handle_click(event.pos)
                        if res_b == "exit_barn":
                            game_mode = "world"
                            world.player_y += 120

                            if hasattr(world, 'solids'):
                                feet = pygame.Rect(world.player_x - 15, world.player_y + 155, 30, 10)
                                for solid in world.solids:
                                    if feet.colliderect(solid):
                                        world.player_y = solid.bottom - 145

                            last_barn_visit_time = time.time()
                            SND_UI.play()
                        elif res_b == "feed_chicken_xp":
                            add_xp(1)
                            SND_FEED.play()

            if event.type == pygame.MOUSEBUTTONUP:
                is_dragging_master = is_dragging_sfx = False

        if is_dragging_master:
            master_volume = max(0, min(1, (mx - 30) / 150))
            update_audio_levels()
        if is_dragging_sfx:
            sfx_volume = max(0, min(1, (mx - 30) / 150))
            update_audio_levels()

        if not is_paused:
            if game_mode == "world":
                update_res = world.update(dt, pygame.key.get_pressed())
                if update_res == "hit_tractor": snd_tractor.play()
                for i in range(unlocked_max + 1): ANIMALS[i].update(dt)
            elif game_mode == "house":
                house.update(dt, pygame.key.get_pressed())
            elif game_mode == "barn":
                update_res = barn.update(dt, pygame.key.get_pressed(), current_time, last_barn_visit_time)
                if update_res == "chicken_eat_sound" and snd_chicken:
                    snd_chicken.play()

        if game_mode == "home":
            screen.fill((50, 50, 60))
            screen.blit(TITLE_FONT.render("VIRTUAL FARM", True, WHITE), (WIDTH // 2 - 200, 50))
            pygame.draw.rect(screen, GREEN if selected_character == "boy" else (80, 80, 90), boy_r, border_radius=15)
            pygame.draw.rect(screen, GREEN if selected_character == "girl" else (80, 80, 90), girl_r, border_radius=15)
            draw_realistic_player_complex(screen, boy_r.centerx, boy_r.centery + 40, "boy", time.time() * 2, False,
                                          True)
            draw_realistic_player_complex(screen, girl_r.centerx, girl_r.centery + 40, "girl", time.time() * 2, False,
                                          True)
            pygame.draw.rect(screen, BLUE if xp_enabled else (120, 120, 130), xp_btn, border_radius=10)
            mode_txt = UI_FONT.render(f"Mode: {'Progression' if xp_enabled else 'Sandbox'}", True, WHITE)
            screen.blit(mode_txt, (xp_btn.centerx - mode_txt.get_width() // 2, xp_btn.centery - 15))
            pygame.draw.rect(screen, GREEN, start_btn, border_radius=10)
            screen.blit(UI_FONT.render("START", True, WHITE), (start_btn.centerx - 35, start_btn.centery - 15))

        elif game_mode == "world":
            world.draw(screen, unlocked_max)
        elif game_mode == "house":
            house.draw(screen)
        elif game_mode == "barn":
            barn.draw(screen)

        if is_paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            pause_text = TITLE_FONT.render("PAUSED", True, WHITE)
            screen.blit(pause_text,
                        (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

        draw_hud(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()