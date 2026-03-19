import math
from array import array
from typing import Optional
import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.font.init()

# -----------------------------
# Fonts & I18N
# -----------------------------
FONT = pygame.font.SysFont(None, 24)
FONT_MED = pygame.font.SysFont(None, 28)
FONT_BIG = pygame.font.SysFont(None, 42)

I18N = {
    "title": "PET",
    "subtitle": "Goal: learn and train animals",
    "inventory": "Animal Inventory",
    "locked": "Locked",
    "unlocked": "Unlocked",
    "stage": "Stage {cur}/{total}",
    "animal": "Animal: {name}",
    "training_steps": "Training steps:",
    "feed": "Feed",
    "pet": "Pet",
    "info": "Info",
    "home": "Home",
    "back": "Go Back",
    "prev": "Prev",
    "next": "Next",
    "fed_done": "Feed: Done",
    "fed_not": "Feed: Not yet",
    "pet_done": "Pet:  Done",
    "pet_not": "Pet:  Not yet",
    "unlock_hint": "Complete both steps to unlock the next animal.",
    "trained_next": "Trained. Next animal unlocked!",
    "trained_all": "All animals trained. Great job!",
    "tip": "Tip: I=Info, ESC=Back/Quit",
    "info_title": "{name} — Facts",
    "close_anywhere": "Click anywhere to close",
    "hover_hint": "Hover over animal for actions",
}


def tr(key: str, **kwargs) -> str:
    s = I18N.get(key, key)
    return s.format(**kwargs) if kwargs else s


# -----------------------------
# Audio
# -----------------------------
def make_tone(freq_hz: float, duration_s: float, volume: float = 0.25) -> pygame.mixer.Sound:
    sample_rate = 44100
    n = max(1, int(sample_rate * duration_s))
    buf = array("h")
    fade = int(sample_rate * min(0.02, duration_s / 4))
    for i in range(n):
        t = i / sample_rate
        s = math.sin(2 * math.pi * freq_hz * t)
        amp = volume
        if i < fade: amp *= i / fade
        if n - i - 1 < fade: amp *= (n - i - 1) / fade
        buf.append(int(32767 * amp * s))
    return pygame.mixer.Sound(buffer=buf.tobytes())


SND_FEED = make_tone(660, 0.10, 0.22)
SND_PET = make_tone(880, 0.08, 0.18)
SND_UNLOCK = make_tone(523.25, 0.10, 0.22)
SND_UI = make_tone(740, 0.05, 0.10)
SND_BITE = make_tone(330, 0.06, 0.18)
SND_CRUNCH = make_tone(220, 0.08, 0.14)


# -----------------------------
# Rendering Helpers
# -----------------------------
def rtl_x(rect: pygame.Rect, text_surface: pygame.Surface, pad: int = 0) -> int:
    return rect.right - pad - text_surface.get_width()


def draw_text(surface, text, pos, font=FONT, color=(20, 20, 20)):
    img = font.render(text, True, color)
    surface.blit(img, pos)
    return img


def draw_text_in_rect(surface, text, rect: pygame.Rect, y: int, font=FONT, color=(20, 20, 20), align="left", pad=14):
    img = font.render(text, True, color)
    x = rtl_x(rect, img, pad) if align == "right" else rect.x + pad
    surface.blit(img, (x, y))
    return img


def draw_soft_shadow(surface, rect, amount=10):
    for i in range(amount):
        shadow_rect = rect.inflate(i * 2, i * 2)
        alpha = int(15 - (i * (15 / amount)))
        if alpha <= 0: continue
        s = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, alpha), (0, 0, shadow_rect.width, shadow_rect.height), border_radius=18 + i)
        surface.blit(s, shadow_rect.topleft)


def draw_card_like_panel(surface, rect: pygame.Rect):
    draw_soft_shadow(surface, rect)
    pygame.draw.rect(surface, (255, 255, 255), rect, border_radius=18)
    pygame.draw.rect(surface, (235, 235, 240), rect, 2, border_radius=18)


def draw_bar(surface, x, y, value, color):
    w, h = 180, 16
    pygame.draw.rect(surface, (210, 210, 215), (x, y, w, h), border_radius=8)
    if value > 0:
        fill_w = int(w * (value / 100))
        pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=8)
        shine_surf = pygame.Surface((fill_w, h // 2), pygame.SRCALPHA)
        pygame.draw.rect(shine_surf, (255, 255, 255, 60), (0, 0, fill_w, h // 2), border_radius=8)
        surface.blit(shine_surf, (x, y))


def draw_grayscale_overlay(surface, rect):
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((120, 120, 120, 160))
    surface.blit(overlay, rect.topleft)


# -----------------------------
# Buttons
# -----------------------------
class Button:
    def __init__(self, rect: pygame.Rect, label_key: Optional[str] = None, label_text: Optional[str] = None):
        self.rect = rect
        self.label_key = label_key
        self.label_text = label_text

    def text(self) -> str:
        if self.label_text is not None: return self.label_text
        if self.label_key is not None: return tr(self.label_key)
        return ""

    def draw(self, surface, enabled: bool = True, primary: bool = False, alpha: int = 255):
        if alpha > 200: draw_soft_shadow(surface, self.rect, amount=6)
        btn_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        if primary:
            bg = (70, 120, 210, alpha) if enabled else (180, 190, 210, alpha)
            fg = (255, 255, 255, alpha) if enabled else (120, 120, 120, alpha)
            border = (45, 70, 140, alpha) if enabled else (140, 140, 140, alpha)
        else:
            bg = (240, 240, 240, alpha) if enabled else (220, 220, 220, alpha)
            fg = (25, 25, 25, alpha) if enabled else (120, 120, 120, alpha)
            border = (70, 70, 70, alpha) if enabled else (140, 140, 140, alpha)

        pygame.draw.rect(btn_surface, bg, (0, 0, self.rect.width, self.rect.height), border_radius=12)
        pygame.draw.rect(btn_surface, border, (0, 0, self.rect.width, self.rect.height), 2, border_radius=12)

        txt = FONT_MED.render(self.text(), True, fg[:3])
        txt.set_alpha(alpha)
        btn_surface.blit(txt,
                         (self.rect.width // 2 - txt.get_width() // 2, self.rect.height // 2 - txt.get_height() // 2))
        surface.blit(btn_surface, self.rect.topleft)

    def hit(self, mx, my) -> bool:
        return self.rect.collidepoint(mx, my)


class FloatingButton:
    def __init__(self, icon: str, label: str, offset_x: int, offset_y: int, color_scheme: str = "blue"):
        self.icon, self.label, self.offset_x, self.offset_y = icon, label, offset_x, offset_y
        self.rect = pygame.Rect(0, 0, 80, 80)
        self.hover = False
        self.color_scheme = color_scheme
        self.pulse = 0.0

    def update_position(self, animal_cx: int, animal_cy: int):
        self.rect.centerx, self.rect.centery = animal_cx + self.offset_x, animal_cy + self.offset_y

    def update(self, dt: float):
        self.pulse += dt * 3.0

    def draw(self, surface, alpha: int = 255, enabled: bool = True):
        schemes = {
            "green": {"bg": (80, 200, 120), "bg_hover": (100, 220, 140), "border": (50, 150, 90),
                      "glow": (120, 255, 160), "disabled": (160, 160, 160)},
            "pink": {"bg": (255, 100, 150), "bg_hover": (255, 130, 170), "border": (200, 60, 110),
                     "glow": (255, 150, 200), "disabled": (160, 160, 160)},
            "purple": {"bg": (150, 100, 255), "bg_hover": (170, 130, 255), "border": (110, 60, 200),
                       "glow": (200, 150, 255), "disabled": (160, 160, 160)}
        }
        scheme = schemes.get(self.color_scheme, schemes["green"])

        if enabled:
            pulse_offset = int(5 * math.sin(self.pulse))
            for i in range(3):
                glow_size = self.rect.width + 30 - i * 10 + pulse_offset
                glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                glow_alpha = int((60 - i * 20) * (alpha / 255))
                if self.hover: glow_alpha = int(glow_alpha * 1.8)
                pygame.draw.circle(glow, (*scheme["glow"], glow_alpha), (glow_size // 2, glow_size // 2),
                                   glow_size // 2)
                surface.blit(glow, (self.rect.centerx - glow_size // 2, self.rect.centery - glow_size // 2))

        btn_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        if enabled:
            base_color = scheme["bg_hover"] if self.hover else scheme["bg"]
            for i in range(3):
                layer_alpha = max(0, min(255, int(alpha - i * 20)))
                layer_radius = self.rect.width // 2 - i * 2
                r = max(0, min(255, int(base_color[0] - i * 15)))
                g = max(0, min(255, int(base_color[1] - i * 15)))
                b = max(0, min(255, int(base_color[2] - i * 15)))
                pygame.draw.circle(btn_surface, (r, g, b, layer_alpha), (self.rect.width // 2, self.rect.height // 2),
                                   layer_radius)

            shine = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.circle(shine, (255, 255, 255, int(40 * (alpha / 255))),
                               (self.rect.width // 2 - 8, self.rect.height // 2 - 8), self.rect.width // 3)
            btn_surface.blit(shine, (0, 0))
            pygame.draw.circle(btn_surface, (*scheme["border"], alpha), (self.rect.width // 2, self.rect.height // 2),
                               self.rect.width // 2, 4)
        else:
            pygame.draw.circle(btn_surface, (*scheme["disabled"], alpha), (self.rect.width // 2, self.rect.height // 2),
                               self.rect.width // 2)
            pygame.draw.circle(btn_surface, (100, 100, 100, alpha), (self.rect.width // 2, self.rect.height // 2),
                               self.rect.width // 2, 3)

        icon_font = pygame.font.SysFont(None, 44)
        icon_surf = icon_font.render(self.icon, True, (255, 255, 255))
        icon_surf.set_alpha(alpha)
        shadow_surf = icon_font.render(self.icon, True, (0, 0, 0))
        shadow_surf.set_alpha(int(60 * (alpha / 255)))
        btn_surface.blit(shadow_surf, (self.rect.width // 2 - icon_surf.get_width() // 2 + 2,
                                       self.rect.height // 2 - icon_surf.get_height() // 2 + 2))
        btn_surface.blit(icon_surf, (self.rect.width // 2 - icon_surf.get_width() // 2,
                                     self.rect.height // 2 - icon_surf.get_height() // 2))
        surface.blit(btn_surface, self.rect.topleft)

        if self.hover and enabled and alpha > 200:
            label_font = pygame.font.SysFont(None, 26)
            label_surf = label_font.render(self.label, True, (255, 255, 255))
            label_bg = pygame.Surface((label_surf.get_width() + 20, label_surf.get_height() + 10), pygame.SRCALPHA)
            for i in range(label_bg.get_height()):
                a = int(220 - (i / label_bg.get_height()) * 40)
                pygame.draw.line(label_bg, (40, 40, 50, a), (6, i), (label_bg.get_width() - 6, i))
            pygame.draw.rect(label_bg, (80, 80, 90, 180), (0, 0, label_bg.get_width(), label_bg.get_height()),
                             border_radius=8)
            label_bg.blit(label_surf, (10, 5))
            surface.blit(label_bg, (self.rect.centerx - label_bg.get_width() // 2, self.rect.bottom + 12))

    def hit(self, mx: int, my: int) -> bool:
        dx, dy = mx - self.rect.centerx, my - self.rect.centery
        return (dx * dx + dy * dy) <= (self.rect.width // 2) ** 2