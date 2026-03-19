import pygame
import math
import random
import time
from typing import List, Dict
from ui import SND_UI

class Animal:
    def __init__(self, kind: str, name_en: str, name_he: str, facts_en: List[str], facts_he: List[str]):
        self.kind = kind
        self.name_en = name_en
        self.name_he = name_he
        self.facts_en = facts_en
        self.facts_he = facts_he
        self.next_decay_timer = 0.0

        self.fed = False
        self.petted = False
        self.critical_time = 0.0
        self.dead = False

        self.hunger = 100.0
        self.affection = 100.0
        self.hunger_decay = 4.0
        self.affection_decay = 3.0
        if self.kind == "leopard":
            self.spots = [(random.randint(-70, 70), random.randint(50, 120)) for _ in range(20)]

        self.t0 = time.time()
        self.blink_timer = 0.0
        self.is_blinking = False
        self.hearts: List[Dict[str, float]] = []
        self.alert_timer = 0.0
        self.hitbox = pygame.Rect(0, 0, 280, 360)

    def mood(self):
        if self.hunger <= 20 or self.affection <= 20: return "critical"
        elif self.hunger <= 50 or self.affection <= 50: return "warning"
        return "happy"

    def trained(self) -> bool: return self.fed and self.petted
    def name(self) -> str: return self.name_en
    def facts(self) -> List[str]: return self.facts_en

    def reset_for_new_stage(self):
        self.fed = False
        self.petted = False
        self.hunger = 100
        self.affection = 100
        self.hearts.clear()
        self.t0 = time.time()

    def update_hitbox(self, cx: int, cy: int):
        self.hitbox.centerx = cx
        self.hitbox.centery = cy

    def add_heart_burst(self, cx, cy):
        for i in range(12):
            ang = (i / 12) * math.tau
            self.hearts.append({
                "x": cx, "y": cy,
                "vx": math.cos(ang) * (32 + 10 * math.sin(i * 1.1)),
                "vy": -95 - 20 * math.cos(i * 0.7),
                "life": 0.9,
            })

    def update(self, dt: float):
        self.next_decay_timer -= dt
        if self.hunger <= 0: self.affection -= 10 * dt
        if self.affection <= 0: self.hunger -= 5 * dt

        if self.next_decay_timer <= 0:
            self.hunger -= random.uniform(2, 6)
            self.affection -= random.uniform(1, 5)
            self.next_decay_timer = random.uniform(6.0, 15.0)

        self.hunger = max(0, min(100, self.hunger))
        self.affection = max(0, min(100, self.affection))

        self.blink_timer += dt
        if not self.is_blinking and self.blink_timer > 2.1 + 1.3 * (0.5 + 0.5 * math.sin(time.time() * 0.7)):
            self.is_blinking = True
            self.blink_timer = 0.0
        elif self.is_blinking and self.blink_timer > 0.12:
            self.is_blinking = False
            self.blink_timer = 0.0

        alive = []
        for h in self.hearts:
            h["life"] -= dt
            h["x"] += h["vx"] * dt
            h["y"] += h["vy"] * dt
            h["vy"] += 120 * dt
            if h["life"] > 0: alive.append(h)
        self.hearts = alive

        if self.mood() == "critical":
            self.critical_time += dt
            if self.critical_time >= 180.0: self.dead = True
        else: self.critical_time = 0.0

        if self.mood() == "critical":
            self.alert_timer -= dt
            if self.alert_timer <= 0:
                SND_UI.play()
                self.alert_timer = 4.0
        else: self.alert_timer = 0.0

    def draw(self, surface, cx: int, cy: int):
        t = time.time() - self.t0
        bob = int(5 * math.sin(t * 2.2))
        cx2, cy2 = cx, cy + bob
        self.update_hitbox(cx2, cy2)

        pygame.draw.ellipse(surface, (205, 205, 210), (cx2 - 110, cy2 + 150, 220, 34))

        if self.kind == "squirrel": self._draw_squirrel(surface, cx2, cy2)
        elif self.kind == "cat": self._draw_cat(surface, cx2, cy2)
        elif self.kind == "rabbit": self._draw_rabbit(surface, cx2, cy2)
        elif self.kind == "dog": self._draw_dog(surface, cx2, cy2)
        elif self.kind == "parrot": self._draw_parrot(surface, cx2, cy2)
        elif self.kind == "tiger": self._draw_tiger(surface, cx2, cy2)
        elif self.kind == "snake": self._draw_snake(surface, cx2, cy2)
        elif self.kind == "leopard": self._draw_leopard(surface, cx2, cy2)
        elif self.kind == "capybara": self._draw_capybara(surface, cx2, cy2)
        else: self._draw_generic(surface, cx2, cy2)

        for h in self.hearts:
            alpha = max(0, min(255, int(255 * (h["life"] / 0.9))))
            self._draw_heart(surface, int(h["x"]), int(h["y"]), alpha)

    def _eye(self, surface, x, y, r=5):
        if self.is_blinking: pygame.draw.line(surface, (35, 35, 40), (x - r, y), (x + r, y), 3)
        else:
            pygame.draw.circle(surface, (35, 35, 40), (x, y), r)
            pygame.draw.circle(surface, (255, 255, 255), (x - 2, y - 2), max(1, r // 2))

    def _draw_heart(self, surface, x, y, alpha):
        s = pygame.Surface((28, 26), pygame.SRCALPHA)
        c = (220, 70, 90, alpha)
        pygame.draw.circle(s, c, (9, 9), 8)
        pygame.draw.circle(s, c, (19, 9), 8)
        pygame.draw.polygon(s, c, [(2, 12), (26, 12), (14, 25)])
        surface.blit(s, (x - 14, y - 13))

    def _shine(self, surface, cx, cy, w, h, alpha=110):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (255, 255, 255, alpha), (0, 0, w, h))
        surface.blit(s, (cx, cy))

    # --- 9 Animals Draw Functions ---
    def _draw_squirrel(self, surface, cx, cy):
        body, shade, belly, outline = (175, 118, 70), (150, 95, 55), (220, 175, 125), (70, 50, 35)
        t = time.time() - self.t0
        wag = int(10 * math.sin(t * 5.0))
        bob = int(3 * math.sin(t * 3.0))
        if self.mood() == "critical": bob = int(bob * 0.3)

        for i in range(3):
            offset = i * 3
            alpha_shade = tuple(max(0, c - i * 15) for c in shade)
            pygame.draw.ellipse(surface, alpha_shade, (cx + 48 - offset, cy - 44 + wag - offset, 96 + offset * 2, 128 + offset * 2))

        pygame.draw.ellipse(surface, body, (cx + 52, cy - 40 + wag, 88, 120))
        for stripe_y in range(-30, 60, 20): pygame.draw.arc(surface, shade, (cx + 55, cy - 35 + wag + stripe_y, 75, 30), 0, math.pi, 2)

        pygame.draw.ellipse(surface, outline, (cx + 48, cy - 44 + wag, 96, 128), 3)
        self._shine(surface, cx + 82, cy - 18 + wag, 30, 40, 90)

        pygame.draw.ellipse(surface, shade, (cx - 74, cy + 14 + bob, 148, 158))
        pygame.draw.ellipse(surface, body, (cx - 70, cy + 10 + bob, 140, 150))
        pygame.draw.ellipse(surface, outline, (cx - 74, cy + 14 + bob, 148, 158), 3)

        pygame.draw.ellipse(surface, belly, (cx - 40, cy + 62 + bob, 80, 92))
        pygame.draw.ellipse(surface, (230, 190, 140), (cx - 25, cy + 70 + bob, 50, 70))

        pygame.draw.circle(surface, shade, (cx, cy + 2 + bob), 58)
        pygame.draw.circle(surface, body, (cx, cy + bob), 55)
        pygame.draw.circle(surface, outline, (cx, cy + 2 + bob), 58, 3)
        self._shine(surface, cx - 30, cy - 34 + bob, 36, 28, 85)

        pygame.draw.polygon(surface, body, [(cx - 32, cy - 48 + bob), (cx - 55, cy - 8 + bob), (cx - 16, cy - 22 + bob)])
        pygame.draw.polygon(surface, (200, 150, 100), [(cx - 32, cy - 42 + bob), (cx - 48, cy - 15 + bob), (cx - 22, cy - 25 + bob)])
        pygame.draw.polygon(surface, outline, [(cx - 32, cy - 48 + bob), (cx - 55, cy - 8 + bob), (cx - 16, cy - 22 + bob)], 2)

        pygame.draw.polygon(surface, body, [(cx + 32, cy - 48 + bob), (cx + 55, cy - 8 + bob), (cx + 16, cy - 22 + bob)])
        pygame.draw.polygon(surface, (200, 150, 100), [(cx + 32, cy - 42 + bob), (cx + 48, cy - 15 + bob), (cx + 22, cy - 25 + bob)])
        pygame.draw.polygon(surface, outline, [(cx + 32, cy - 48 + bob), (cx + 55, cy - 8 + bob), (cx + 16, cy - 22 + bob)], 2)

        pygame.draw.circle(surface, (190, 135, 90), (cx - 35, cy + 10 + bob), 12)
        pygame.draw.circle(surface, (190, 135, 90), (cx + 35, cy + 10 + bob), 12)

        self._eye(surface, cx - 18, cy - 6 + bob, 6); self._eye(surface, cx + 18, cy - 6 + bob, 6)

        pygame.draw.circle(surface, (60, 40, 30), (cx, cy + 14 + bob), 6)
        pygame.draw.ellipse(surface, (80, 60, 45), (cx - 3, cy + 12 + bob, 6, 5))
        pygame.draw.arc(surface, outline, (cx - 18, cy + 10 + bob, 36, 22), math.pi * 0.1, math.pi * 0.9, 2)

        whisker_color = (90, 70, 50)
        for angle in [-0.3, -0.15, 0]:
            pygame.draw.line(surface, whisker_color, (cx - 35, cy + 5 + bob), (cx - 35 + int(30 * math.cos(math.pi + angle)), cy + 5 + bob + int(10 * math.sin(math.pi + angle))), 1)
            pygame.draw.line(surface, whisker_color, (cx + 35, cy + 5 + bob), (cx + 35 + int(30 * math.cos(angle)), cy + 5 + bob + int(10 * math.sin(angle))), 1)

        pygame.draw.ellipse(surface, belly, (cx - 58, cy + 118 + bob, 46, 26))
        for toe_x in [-50, -40, -30]: pygame.draw.circle(surface, outline, (cx + toe_x, cy + 130 + bob), 3)
        pygame.draw.ellipse(surface, belly, (cx + 12, cy + 118 + bob, 46, 26))
        for toe_x in [20, 30, 40]: pygame.draw.circle(surface, outline, (cx + toe_x, cy + 130 + bob), 3)

        pygame.draw.ellipse(surface, (160, 110, 65), (cx - 10, cy + 70 + bob, 20, 24))
        pygame.draw.circle(surface, (145, 95, 55), (cx, cy + 78 + bob), 14)
        pygame.draw.ellipse(surface, (120, 80, 45), (cx - 9, cy + 68 + bob, 18, 10))
        for i in range(3): pygame.draw.line(surface, outline, (cx - 6 + i * 6, cy + 68 + bob), (cx - 4 + i * 6, cy + 74 + bob), 1)
        pygame.draw.circle(surface, outline, (cx, cy + 78 + bob), 14, 2)

    def _draw_cat(self, surface, cx, cy):
        fur, shade, outline, nose = (145, 145, 155), (125, 125, 135), (60, 60, 70), (220, 125, 150)
        t = time.time() - self.t0
        sw = int(14 * math.sin(t * 3.2))
        if self.mood() == "critical": sw = int(sw * 0.3)

        pygame.draw.ellipse(surface, shade, (cx - 86, cy + 42, 172, 146))
        pygame.draw.ellipse(surface, fur, (cx - 80, cy + 35, 160, 140))
        pygame.draw.ellipse(surface, outline, (cx - 86, cy + 42, 172, 146), 3)
        self._shine(surface, cx - 40, cy + 50, 52, 36, 80)

        pygame.draw.ellipse(surface, shade, (cx + 74, cy + 74 + sw, 96, 34))
        pygame.draw.ellipse(surface, fur, (cx + 70, cy + 70 + sw, 90, 30))
        pygame.draw.ellipse(surface, outline, (cx + 74, cy + 74 + sw, 96, 34), 3)

        pygame.draw.circle(surface, shade, (cx, cy + 2), 62)
        pygame.draw.circle(surface, fur, (cx, cy), 58)
        pygame.draw.circle(surface, outline, (cx, cy + 2), 62, 3)
        self._shine(surface, cx - 28, cy - 40, 38, 30, 85)

        pygame.draw.polygon(surface, fur, [(cx - 38, cy - 44), (cx - 58, cy - 4), (cx - 22, cy - 18)])
        pygame.draw.polygon(surface, fur, [(cx + 38, cy - 44), (cx + 58, cy - 4), (cx + 22, cy - 18)])
        pygame.draw.polygon(surface, (200, 150, 160), [(cx - 38, cy - 38), (cx - 52, cy - 8), (cx - 28, cy - 18)])
        pygame.draw.polygon(surface, (200, 150, 160), [(cx + 38, cy - 38), (cx + 52, cy - 8), (cx + 28, cy - 18)])
        pygame.draw.polygon(surface, outline, [(cx - 38, cy - 44), (cx - 58, cy - 4), (cx - 22, cy - 18)], 2)
        pygame.draw.polygon(surface, outline, [(cx + 38, cy - 44), (cx + 58, cy - 4), (cx + 22, cy - 18)], 2)

        self._eye(surface, cx - 18, cy - 6, 5); self._eye(surface, cx + 18, cy - 6, 5)
        pygame.draw.polygon(surface, nose, [(cx, cy + 8), (cx - 8, cy + 16), (cx + 8, cy + 16)])
        pygame.draw.line(surface, outline, (cx, cy + 16), (cx, cy + 30), 2)
        pygame.draw.arc(surface, outline, (cx - 18, cy + 20, 18, 16), math.pi * 0.0, math.pi * 1.0, 2)
        pygame.draw.arc(surface, outline, (cx, cy + 20, 18, 16), math.pi * 0.0, math.pi * 1.0, 2)

        for dy in (-4, 4, 12):
            pygame.draw.line(surface, outline, (cx - 10, cy + 14 + dy), (cx - 66, cy + 6 + dy), 2)
            pygame.draw.line(surface, outline, (cx + 10, cy + 14 + dy), (cx + 66, cy + 6 + dy), 2)

        pygame.draw.ellipse(surface, fur, (cx - 65, cy + 160, 50, 22))
        pygame.draw.ellipse(surface, fur, (cx + 15, cy + 160, 50, 22))

    def _draw_rabbit(self, surface, cx, cy):
        fur, shade, outline, inner = (238, 235, 240), (215, 212, 220), (80, 80, 90), (245, 190, 200)
        t = time.time() - self.t0
        hop = int(8 * max(0.0, math.sin(t * 2.6)))
        if self.mood() == "critical": hop = int(hop * 0.2)

        pygame.draw.ellipse(surface, shade, (cx - 80, cy + 48 - hop, 160, 142))
        pygame.draw.ellipse(surface, fur, (cx - 75, cy + 40 - hop, 150, 135))
        pygame.draw.ellipse(surface, outline, (cx - 80, cy + 48 - hop, 160, 142), 3)
        self._shine(surface, cx - 35, cy + 58 - hop, 52, 34, 70)

        pygame.draw.circle(surface, shade, (cx, cy + 2 - hop), 56)
        pygame.draw.circle(surface, fur, (cx, cy - hop), 52)
        pygame.draw.circle(surface, outline, (cx, cy + 2 - hop), 56, 3)
        self._shine(surface, cx - 30, cy - 38 - hop, 40, 30, 90)

        pygame.draw.ellipse(surface, shade, (cx - 52, cy - 124 - hop, 38, 116))
        pygame.draw.ellipse(surface, shade, (cx + 14, cy - 124 - hop, 38, 116))
        pygame.draw.ellipse(surface, fur, (cx - 50, cy - 120 - hop, 34, 110))
        pygame.draw.ellipse(surface, fur, (cx + 16, cy - 120 - hop, 34, 110))
        pygame.draw.ellipse(surface, outline, (cx - 52, cy - 124 - hop, 38, 116), 3)
        pygame.draw.ellipse(surface, outline, (cx + 14, cy - 124 - hop, 38, 116), 3)
        pygame.draw.ellipse(surface, inner, (cx - 44, cy - 110 - hop, 22, 90))
        pygame.draw.ellipse(surface, inner, (cx + 22, cy - 110 - hop, 22, 90))

        self._eye(surface, cx - 16, cy - 10 - hop, 4); self._eye(surface, cx + 16, cy - 10 - hop, 4)
        pygame.draw.circle(surface, (220, 140, 160), (cx, cy + 8 - hop), 5)
        pygame.draw.arc(surface, outline, (cx - 16, cy + 6 - hop, 32, 22), math.pi * 0.1, math.pi * 0.9, 2)

        pygame.draw.circle(surface, shade, (cx + 86, cy + 136 - hop), 18)
        pygame.draw.circle(surface, fur, (cx + 80, cy + 132 - hop), 16)
        pygame.draw.circle(surface, outline, (cx + 86, cy + 136 - hop), 18, 3)

    def _draw_dog(self, surface, cx, cy):
        fur, shade, outline, ear = (185, 145, 95), (160, 120, 78), (75, 55, 40), (155, 115, 80)
        t = time.time() - self.t0
        flop = int(8 * math.sin(t * 4.0))
        if self.mood() == "critical": flop = int(flop * 0.3)

        pygame.draw.ellipse(surface, shade, (cx - 96, cy + 52, 192, 138))
        pygame.draw.ellipse(surface, fur, (cx - 90, cy + 45, 180, 130))
        pygame.draw.ellipse(surface, outline, (cx - 96, cy + 52, 192, 138), 3)
        self._shine(surface, cx - 45, cy + 70, 56, 36, 75)

        pygame.draw.circle(surface, shade, (cx, cy + 4), 66)
        pygame.draw.circle(surface, fur, (cx, cy), 60)
        pygame.draw.circle(surface, outline, (cx, cy + 4), 66, 3)
        self._shine(surface, cx - 32, cy - 42, 40, 30, 85)

        pygame.draw.ellipse(surface, ear, (cx - 74, cy - 22 + flop, 48, 84))
        pygame.draw.ellipse(surface, ear, (cx + 26, cy - 22 - flop, 48, 84))
        pygame.draw.ellipse(surface, outline, (cx - 74, cy - 22 + flop, 48, 84), 3)
        pygame.draw.ellipse(surface, outline, (cx + 26, cy - 22 - flop, 48, 84), 3)

        self._eye(surface, cx - 18, cy - 8, 5); self._eye(surface, cx + 18, cy - 8, 5)

        pygame.draw.ellipse(surface, (100, 80, 62), (cx - 22, cy + 12, 44, 30))
        pygame.draw.ellipse(surface, outline, (cx - 22, cy + 12, 44, 30), 2)
        pygame.draw.circle(surface, (40, 30, 25), (cx, cy + 16), 6)
        pygame.draw.arc(surface, outline, (cx - 22, cy + 18, 44, 30), math.pi * 0.05, math.pi * 0.95, 2)

        pygame.draw.rect(surface, (200, 60, 80), (cx - 60, cy + 62, 120, 14), border_radius=7)
        pygame.draw.circle(surface, (250, 220, 120), (cx, cy + 84), 8)

        wag = int(14 * math.sin(t * 6.2))
        pygame.draw.ellipse(surface, shade, (cx - 142, cy + 98 + wag, 60, 24))
        pygame.draw.ellipse(surface, fur, (cx - 135, cy + 92 + wag, 55, 22))
        pygame.draw.ellipse(surface, outline, (cx - 142, cy + 98 + wag, 60, 24), 3)

    def _draw_parrot(self, surface, cx, cy):
        green, shade, outline, wing, beak = (70, 180, 90), (55, 150, 75), (25, 60, 35), (55, 160, 85), (235, 175, 65)
        t = time.time() - self.t0
        flap = int(10 * math.sin(t * 6.2))
        if self.mood() == "critical": flap = int(flap * 0.2)

        pygame.draw.rect(surface, (150, 110, 70), (cx - 170, cy + 170, 340, 20), border_radius=10)
        pygame.draw.rect(surface, (115, 85, 55), (cx - 170, cy + 186, 340, 6), border_radius=10)

        pygame.draw.ellipse(surface, shade, (cx - 62, cy + 28, 124, 154))
        pygame.draw.ellipse(surface, green, (cx - 55, cy + 20, 110, 140))
        pygame.draw.ellipse(surface, outline, (cx - 62, cy + 28, 124, 154), 3)
        self._shine(surface, cx - 20, cy + 42, 46, 34, 75)

        pygame.draw.ellipse(surface, wing, (cx - 78, cy + 60 + flap, 88, 98))
        pygame.draw.ellipse(surface, outline, (cx - 78, cy + 60 + flap, 88, 98), 3)

        pygame.draw.circle(surface, shade, (cx + 12, cy + 2), 56)
        pygame.draw.circle(surface, green, (cx + 10, cy), 50)
        pygame.draw.circle(surface, outline, (cx + 12, cy + 2), 56, 3)
        self._shine(surface, cx - 10, cy - 38, 38, 28, 85)

        self._eye(surface, cx + 2, cy - 8, 5)
        pygame.draw.polygon(surface, beak, [(cx + 34, cy + 6), (cx + 74, cy + 18), (cx + 34, cy + 28)])
        pygame.draw.polygon(surface, outline, [(cx + 34, cy + 6), (cx + 74, cy + 18), (cx + 34, cy + 28)], 2)

        pygame.draw.line(surface, outline, (cx - 6, cy + 176), (cx - 18, cy + 160), 4)
        pygame.draw.line(surface, outline, (cx + 18, cy + 176), (cx + 6, cy + 160), 4)

    def _draw_tiger(self, surface, cx, cy):
        body, shade, belly, stripe, outline = (245, 155, 45), (210, 120, 35), (255, 225, 185), (25, 20, 18), (80, 50, 30)
        t = time.time() - self.t0
        tail = int(16 * math.sin(t * 3.5))
        if self.mood() == "critical": tail = int(tail * 0.3)

        pygame.draw.ellipse(surface, shade, (cx - 150, cy + 70, 280, 150))
        pygame.draw.ellipse(surface, body, (cx - 140, cy + 60, 260, 140))
        pygame.draw.ellipse(surface, outline, (cx - 150, cy + 70, 280, 150), 3)

        pygame.draw.ellipse(surface, belly, (cx - 40, cy + 100, 120, 90))
        pygame.draw.ellipse(surface, shade, (cx - 80, cy + 50, 120, 100))

        pygame.draw.circle(surface, shade, (cx + 60, cy + 20), 85)
        pygame.draw.circle(surface, body, (cx + 55, cy + 10), 80)
        pygame.draw.circle(surface, outline, (cx + 60, cy + 20), 85, 3)

        pygame.draw.ellipse(surface, belly, (cx + 10, cy + 40, 120, 80))
        pygame.draw.circle(surface, (35, 25, 20), (cx + 70, cy + 55), 10)

        self._eye(surface, cx + 35, cy - 5, 9); self._eye(surface, cx + 95, cy - 5, 9)

        for dy in (-5, 10, 25): pygame.draw.line(surface, outline, (cx + 30, cy + 40 + dy), (cx - 40, cy + 30 + dy), 2)

        pygame.draw.ellipse(surface, shade, (cx - 210, cy + 110 + tail, 120, 35))
        pygame.draw.ellipse(surface, body, (cx - 200, cy + 105 + tail, 100, 30))
        pygame.draw.ellipse(surface, outline, (cx - 210, cy + 110 + tail, 120, 35), 3)

        for s in [-120, -70, -20, 30, 80]:
            pygame.draw.polygon(surface, stripe, [(cx + s, cy + 40), (cx + s + 20, cy + 80), (cx + s - 5, cy + 90)])

        pygame.draw.line(surface, stripe, (cx + 25, cy - 10), (cx + 5, cy + 20), 5)
        pygame.draw.line(surface, stripe, (cx + 105, cy - 10), (cx + 125, cy + 20), 5)

    def _draw_snake(self, surface, cx, cy):
        body, shade, outline = (70, 180, 95), (50, 140, 70), (30, 80, 45)
        t = time.time() - self.t0
        points = [(cx - 120 + i, cy + int(30 * math.sin(i * 0.05 + t * 3))) for i in range(0, 240, 12)]

        pygame.draw.lines(surface, shade, False, points, 24)
        pygame.draw.lines(surface, body, False, points, 18)
        pygame.draw.lines(surface, outline, False, points, 3)

        head = points[-1]
        pygame.draw.circle(surface, shade, head, 28)
        pygame.draw.circle(surface, body, head, 24)
        pygame.draw.circle(surface, outline, head, 28, 3)

        self._eye(surface, head[0] - 8, head[1] - 6, 5); self._eye(surface, head[0] + 8, head[1] - 6, 5)

        if int(time.time() * 4) % 2 == 0:
            pygame.draw.line(surface, (200, 30, 30), (head[0] + 18, head[1]), (head[0] + 38, head[1] - 5), 3)

    def _draw_leopard(self, surface, cx, cy):
        base_fur, belly_fur, rosette_outer, rosette_inner, outline = (215, 160, 85), (245, 235, 210), (30, 25, 20), (165, 110, 55), (60, 45, 30)
        t = time.time() - self.t0
        tail_move, crouch = math.sin(t * 1.5) * 25, int(5 * math.sin(t * 2))
        if self.mood() == "critical": tail_move *= 0.3; crouch = int(crouch * 0.3)

        tail_points = [(cx - 150, cy + 120), (cx - 220, cy + 140 + tail_move), (cx - 280, cy + 100 + tail_move), (cx - 270, cy + 80 + tail_move)]
        pygame.draw.lines(surface, base_fur, False, tail_points, 25)
        pygame.draw.lines(surface, outline, False, tail_points, 2)

        pygame.draw.ellipse(surface, base_fur, (cx - 160, cy + 100 + crouch, 90, 130))
        pygame.draw.ellipse(surface, base_fur, (cx + 30, cy + 110 + crouch, 60, 120))

        body_rect = (cx - 160, cy + 70 + crouch, 320, 140)
        pygame.draw.rect(surface, base_fur, body_rect, border_radius=60)
        pygame.draw.ellipse(surface, belly_fur, (cx - 100, cy + 160 + crouch, 220, 60))
        pygame.draw.rect(surface, outline, body_rect, 3, border_radius=60)

        head_pos = (cx + 140, cy + 40 + crouch)
        pygame.draw.ellipse(surface, base_fur, (head_pos[0], head_pos[1], 110, 100))
        pygame.draw.ellipse(surface, belly_fur, (head_pos[0] + 30, head_pos[1] + 50, 70, 50))
        pygame.draw.polygon(surface, (120, 80, 70), [(head_pos[0] + 65, head_pos[1] + 65), (head_pos[0] + 55, head_pos[1] + 55), (head_pos[0] + 75, head_pos[1] + 55)])

        pygame.draw.circle(surface, base_fur, (head_pos[0] + 20, head_pos[1] + 15), 18)
        pygame.draw.circle(surface, (40, 40, 40), (head_pos[0] + 20, head_pos[1] + 15), 18, 2)

        for ex in [35, 75]:
            ey_pos = (head_pos[0] + ex, head_pos[1] + 35)
            pygame.draw.circle(surface, (180, 190, 50), ey_pos, 8)
            pygame.draw.circle(surface, (0, 0, 0), ey_pos, 4)

        for dx, dy in self.spots:
            sx, sy = cx + dx - 20, cy + dy + 20 + crouch
            pygame.draw.circle(surface, rosette_inner, (sx, sy), 7)
            for angle in [0, 1.5, 3, 4.5]:
                pygame.draw.circle(surface, rosette_outer, (int(sx + math.cos(angle) * 8), int(sy + math.sin(angle) * 8)), 4)

    def _draw_capybara(self, surface, cx, cy):
        body_color, shade_color, highlight_color, nose_color, outline_color = (130, 90, 60), (100, 70, 45), (160, 120, 90), (60, 45, 35), (45, 35, 25)
        t = time.time() - self.t0
        breathe = int(3 * math.sin(t * 1.5))
        if self.mood() == "critical": breathe = int(breathe * 0.2)

        pygame.draw.ellipse(surface, (180, 180, 180), (cx - 220, cy + 245, 400, 30))

        for lx, ly in [(-160, 200), (-80, 210), (60, 210), (140, 200)]:
            pygame.draw.rect(surface, shade_color, (cx + lx, cy + ly + breathe, 50, 60), border_radius=10)
            pygame.draw.rect(surface, outline_color, (cx + lx, cy + ly + breathe, 50, 60), 2, border_radius=10)

        pygame.draw.rect(surface, shade_color, (cx - 220, cy + 80 + breathe, 400, 160), border_radius=70)
        pygame.draw.rect(surface, body_color, (cx - 210, cy + 85 + breathe, 380, 140), border_radius=60)

        for i in range(0, 380, 40): pygame.draw.line(surface, highlight_color, (cx - 200 + i, cy + 100 + breathe), (cx - 180 + i, cy + 120 + breathe), 2)

        pygame.draw.rect(surface, body_color, (cx + 100, cy + 70 + breathe, 80, 100))
        head_rect = (cx + 120, cy + 40 + breathe, 170, 110)
        pygame.draw.rect(surface, body_color, head_rect, border_radius=30)
        pygame.draw.rect(surface, outline_color, head_rect, 3, border_radius=30)

        pygame.draw.rect(surface, nose_color, (cx + 250, cy + 50 + breathe, 50, 70), border_radius=15)
        pygame.draw.circle(surface, (20, 15, 10), (cx + 285, cy + 95 + breathe), 5)

        pygame.draw.circle(surface, (10, 10, 10), (cx + 210, cy + 65 + breathe), 6)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 212, cy + 63 + breathe), 2)

        ear_pos = (cx + 145, cy + 45 + breathe)
        pygame.draw.circle(surface, shade_color, ear_pos, 15)
        pygame.draw.circle(surface, outline_color, ear_pos, 15, 2)
        pygame.draw.circle(surface, (80, 50, 30), ear_pos, 8)

        pygame.draw.arc(surface, outline_color, (cx + 150, cy + 100 + breathe, 100, 40), 3.14, 0, 2)

    def _draw_generic(self, s, cx, cy):
        pygame.draw.circle(s, (200, 200, 200), (cx, cy), 65)

# Initialize ANIMALS
ANIMALS = [
    Animal("squirrel", "Squirrel", "סנאי", ["Squirrels store food for later.", "They can jump far compared to their size.", "They use their tails for balance.", "They help spread seeds in forests."], []),
    Animal("cat", "Cat", "חתול", ["Cats communicate with body language and sounds.", "They are natural hunters.", "Purring can mean comfort, but also stress.", "They sleep many hours to save energy."], []),
    Animal("rabbit", "Rabbit", "ארנב", ["Rabbits have strong hind legs for quick movement.", "They use their ears to regulate heat.", "They are social and like safe spaces.", "They eat mainly plants and grasses."], []),
    Animal("dog", "Dog", "כלב", ["Dogs learn routines and commands quickly.", "They use smell as their main sense.", "Play and praise help training.", "They can be great helpers and friends."], []),
    Animal("parrot", "Parrot", "תוכי", ["Parrots are intelligent and can mimic sounds.", "They need enrichment to avoid boredom.", "Many parrots live in flocks in nature.", "They use their beaks to explore objects."], []),
    Animal("tiger", "Tiger", "טיגריס", ["Tigers are the largest wild cats.", "Each tiger has unique stripes.", "They are strong swimmers.", "They live mostly in Asia."], []),
    Animal("snake", "Snake", "נחש", ["Snakes do not have legs.", "They smell with their tongue.", "Some snakes are venomous.", "They shed their skin."], []),
    Animal("leopard", "Leopard", "נמר", ["Leopards are excellent climbers.", "They have spotted fur.", "They are very fast.", "They live in Africa and Asia."], []),
    Animal("capybara", "Capybara", "קפיברה", ["Capybaras are the largest rodents.", "They love water.", "They live in South America.", "They are very social animals."], []),
]