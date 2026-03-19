import pygame
import math
import time
import random
from player_drawer import draw_realistic_player_complex


class HouseScene:
    def __init__(self, get_selected_character):
        self.get_selected_character = get_selected_character
        self.player_x, self.player_y = 640, 500
        self.player_speed = 300
        self.facing_right = True
        self.is_moving = False
        self.walk_timer = 0.0

        # Interactive States
        self.lamp_on = False
        self.fish_fed_timer = 0.0
        self.food_particles = []

        # UI Visibility
        self.aq_ui_alpha = 0
        self.lamp_ui_alpha = 0
        self.exit_ui_alpha = 0

        # Fixed Assets
        self.book_colors = [(random.randint(100, 255), random.randint(50, 150), random.randint(50, 150)) for _ in
                            range(16)]
        self._generate_landscape_art_data()

        # Detailed Fish System
        # Boundaries relative to center x=180, y=320:
        self.fishes = [
            {'x': 0, 'y': -60, 'speed': 40, 'col': (255, 165, 0), 'dir': 1, 'target_p': None},
            {'x': 20, 'y': -40, 'speed': -35, 'col': (100, 100, 255), 'dir': -1, 'target_p': None},
            {'x': -30, 'y': -80, 'speed': 25, 'col': (180, 50, 255), 'dir': 1, 'target_p': None}
        ]

        # Collision Hitboxes (Updated to match new sofa size)
        self.solids = [
            pygame.Rect(100, 320, 160, 100),  # Aquarium Stand
            pygame.Rect(350, 310, 400, 130),  # Improved, larger Sofa area
            pygame.Rect(1000, 500, 80, 80),  # Lamp Base
        ]

    def _generate_landscape_art_data(self):
        w, h = 160, 100
        self.landscape_forest_trees = []
        for _ in range(25):
            # Define foliage bottom y
            ty_base = 55

            # --- PATCH START: Fix left clipping ---
            tw = random.randint(8, 16)

            # The inner frame starts at x+6. We draw from tx - tw//2.
            # To stay inside, tx - tw//2 must be >= 6.
            # So tx must be >= 6 + tw//2.
            # We add a tiny buffer (e.g., +2) so it's not right on the edge.
            min_tx = 6 + (tw // 2) + 2
            max_tx = w - 15  # Keep max as is

            tx = random.randint(min_tx, max_tx)
            # --- PATCH END ---

            c_var = random.randint(-10, 10)
            color = (max(0, min(255, 40 + c_var)), max(0, min(255, 100 + c_var)), max(0, min(255, 50 + c_var)))
            # tuple: (rel_x, rel_y_foliage_bottom, width, height, color)
            self.landscape_forest_trees.append((tx, ty_base, tw, random.randint(15, 30), color))

        self.landscape_clouds = []
        for _ in range(3):
            self.landscape_clouds.append(
                (random.randint(20, w - 50), random.randint(10, 35), random.randint(20, 40), random.randint(10, 20)))
    def update(self, dt, keys):
        if dt == 0: return None
        t = time.time()

        # 1. Player Movement
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.is_moving = dx != 0 or dy != 0
        if dx != 0: self.facing_right = dx > 0
        self.walk_timer += dt * 12 if self.is_moving else 0

        if self.is_moving:
            mag = math.hypot(dx, dy)
            nx, ny = self.player_x + (dx / mag) * self.player_speed * dt, self.player_y + (
                    dy / mag) * self.player_speed * dt
            if not any(pygame.Rect(nx - 15, ny + 155, 30, 10).colliderect(s) for s in self.solids):
                if 220 < ny < 650: self.player_y = ny
                if 50 < nx < 1230: self.player_x = nx

        # 2. Food Sinking Logic
        if self.fish_fed_timer > 0:
            self.fish_fed_timer -= dt
            for p in self.food_particles:
                if not p['eaten']:
                    p['y'] += p['speed'] * dt * 0.4
                    if p['y'] >= -15: p['y'] = -15
            if self.fish_fed_timer <= 0: self.food_particles = []

        # 3. Fish Hunting AI & Boundary Checking
        for f in self.fishes:
            found_target = False
            if self.food_particles:
                for p in self.food_particles:
                    if not p['eaten']:
                        dist = math.hypot(f['x'] - p['x'], f['y'] - p['y'])
                        if dist < 80:
                            f['x'] += (p['x'] - f['x']) * dt * 2
                            f['y'] += (p['y'] - f['y']) * dt * 2
                            f['dir'] = 1 if p['x'] > f['x'] else -1
                            found_target = True
                            if dist < 10: p['eaten'] = True
                            break

            if not found_target:
                f['x'] += f['speed'] * dt
                f['y'] += math.sin(t + f['x'] * 0.05) * 0.2
                f['dir'] = 1 if f['speed'] > 0 else -1

            # --- NEW: Boundary Constraints ---
            if f['x'] > 60:
                f['x'] = 60
                if f['speed'] > 0: f['speed'] *= -1
            elif f['x'] < -60:
                f['x'] = -60
                if f['speed'] < 0: f['speed'] *= -1

            if f['y'] > -20:
                f['y'] = -20
            elif f['y'] < -95:
                f['y'] = -95

        # UI Updates
        dist_aq = math.hypot(self.player_x - 180, self.player_y - 320)

        # Check if feeding is allowed (timer must be <= 0)
        can_feed_fish = (self.fish_fed_timer <= 0)
        self.aq_ui_alpha = min(255, self.aq_ui_alpha + 15) if (dist_aq < 200 and can_feed_fish) else max(0,
                                                                                                         self.aq_ui_alpha - 15)

        dist_lamp = math.hypot(self.player_x - 1040, self.player_y - 520)
        self.lamp_ui_alpha = min(255, self.lamp_ui_alpha + 15) if dist_lamp < 200 else max(0, self.lamp_ui_alpha - 15)
        self.exit_ui_alpha = min(255, self.exit_ui_alpha + 15) if self.player_y > 600 else max(0,
                                                                                               self.exit_ui_alpha - 15)

        return None

    def draw(self, surface):
        t = time.time()
        surface.fill((120, 80, 50))
        pygame.draw.rect(surface, (90, 70, 55), (0, 0, 1280, 240))
        pygame.draw.rect(surface, (60, 45, 30), (0, 230, 1280, 10))

        self._draw_window(surface, 850, 50)
        self._draw_bookshelf(surface, 50, 80)
        self._draw_clock(surface, 1150, 120, t)
        self._draw_art(surface, 450, 60, "Landscape")
        self._draw_art(surface, 620, 80, "Portrait")
        self._draw_aquarium(surface, 180, 320, t)

        # Rug drawn BEFORE Sofa
        pygame.draw.ellipse(surface, (40, 60, 90), (340, 480, 600, 180))
        self._draw_sofa(surface, 350, 330)

        shadow = pygame.Surface((120, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, 120, 30))
        surface.blit(shadow, (self.player_x - 60, self.player_y + 140))
        draw_realistic_player_complex(surface, self.player_x, self.player_y, self.get_selected_character(),
                                      self.walk_timer, self.is_moving, self.facing_right)

        self._draw_lamp(surface, 1040, 520, self.lamp_on)

        if self.lamp_on:
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (255, 255, 150, 120), (1040, 455), 25)
            surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_ADD)

        if self.exit_ui_alpha > 0: self._draw_ui_button(surface, 640, 650, "EXIT HOUSE", (200, 50, 50),
                                                        self.exit_ui_alpha)
        if self.lamp_ui_alpha > 0: self._draw_ui_button(surface, 1040, 360, "LIGHT",
                                                        (76, 175, 80) if not self.lamp_on else (255, 87, 34),
                                                        self.lamp_ui_alpha)
        if self.aq_ui_alpha > 0: self._draw_ui_button(surface, 180, 150, "FEED", (255, 165, 0), self.aq_ui_alpha)

    def _draw_aquarium(self, surface, x, y, t):
        pygame.draw.rect(surface, (80, 50, 30), (x - 85, y, 170, 100), border_radius=5)
        pygame.draw.rect(surface, (30, 30, 40), (x - 80, y - 110, 160, 115), border_radius=5)
        pygame.draw.rect(surface, (150, 225, 255), (x - 75, y - 105, 150, 105))
        pygame.draw.rect(surface, (120, 90, 60), (x - 75, y - 25, 150, 25))

        plant_base_x, plant_base_y = x - 45, y - 25
        for i in range(6):
            seg_y = plant_base_y - i * 14
            seg_x = plant_base_x + math.sin(t * 2 + i * 0.6) * 6
            pygame.draw.circle(surface, (34, 139, 34), (int(seg_x), int(seg_y)), 5 - i // 2)
            if i % 2 == 0:
                leaf_x = seg_x + (12 if i % 4 == 0 else -12)
                pygame.draw.ellipse(surface, (50, 160, 50), (leaf_x - 5, seg_y - 3, 10, 6))

        if self.fish_fed_timer > 0:
            for p in self.food_particles:
                if not p['eaten']: pygame.draw.circle(surface, p['color'], (x + p['x'], y + p['y']), p['size'])

        for f in self.fishes:
            fx, fy = x + f['x'], y + f['y']
            d, swing = f['dir'], math.sin(t * 10 + f['x']) * 4
            pygame.draw.ellipse(surface, f['col'], (fx - 10, fy - 6, 20, 12))
            pts = [(fx - 8 * d, fy), (fx - 18 * d, fy - 8 + swing), (fx - 18 * d, fy + 8 - swing)]
            pygame.draw.polygon(surface, f['col'], pts)
            pygame.draw.circle(surface, (255, 255, 255), (int(fx + 6 * d), int(fy - 2)), 2)
            pygame.draw.circle(surface, (0, 0, 0), (int(fx + 6 * d), int(fy - 2)), 1)

    def _draw_window(self, surface, x, y):
        pygame.draw.rect(surface, (50, 35, 25), (x - 5, y - 5, 160, 130), border_radius=5)
        pygame.draw.rect(surface, (135, 206, 235), (x, y, 150, 120))
        pygame.draw.rect(surface, (34, 139, 34), (x, y + 80, 150, 40))
        pygame.draw.rect(surface, (101, 67, 33), (x + 100, y + 50, 15, 40))
        pygame.draw.circle(surface, (0, 100, 0), (x + 108, y + 45), 25)
        pygame.draw.line(surface, (255, 255, 255, 100), (x + 75, y), (x + 75, y + 120), 2)
        pygame.draw.line(surface, (255, 255, 255, 100), (x, y + 60), (x + 150, y + 60), 2)

    def _draw_bookshelf(self, surface, x, y):
        pygame.draw.rect(surface, (70, 40, 20), (x, y, 150, 10))
        pygame.draw.rect(surface, (70, 40, 20), (x, y + 50, 150, 10))
        for i in range(8):
            pygame.draw.rect(surface, self.book_colors[i], (x + 10 + i * 15, y - 30, 12, 30))
            pygame.draw.rect(surface, self.book_colors[i + 8], (x + 10 + i * 15, y + 20, 12, 30))

    def _draw_sofa(self, surface, x, y):
        main, shadow, wood = (160, 40, 40), (110, 20, 20), (70, 50, 30)
        shadow_base = (40, 30, 20)
        w, h = 400, 130
        cushion_w = (w - 30) // 3

        pygame.draw.ellipse(surface, (30, 25, 20, 100), (x + 10, y + h - 10, w - 20, 20))
        for lx in [x + 30, x + w - 45]:
            pygame.draw.rect(surface, wood, (lx, y + h - 5, 15, 20), border_radius=4)
        pygame.draw.rect(surface, shadow_base, (x, y + h - 10, w, 15), border_radius=5)
        pygame.draw.rect(surface, shadow, (x, y, w, h - 10), border_radius=15)

        for i in range(3):
            bx = x + 15 + i * cushion_w
            pygame.draw.rect(surface, shadow, (bx, y - 50, cushion_w, 80), border_radius=12)
            pygame.draw.rect(surface, main, (bx, y - 45, cushion_w, 75), border_radius=12)
            pygame.draw.circle(surface, (20, 10, 10, 50), (int(bx + cushion_w // 2), int(y - 5)), 2)

        for i in range(3):
            cx = x + 15 + i * cushion_w
            pygame.draw.rect(surface, shadow, (cx, y + 35, cushion_w, 90), border_radius=15)
            pygame.draw.rect(surface, main, (cx, y + 40, cushion_w, 85), border_radius=15)
            pygame.draw.rect(surface, (190, 60, 60), (cx + 5, y + 45, cushion_w - 10, 20), border_radius=8)

        for ax in [x - 10, x + w - 40]:
            pygame.draw.rect(surface, shadow, (ax, y + 15, 50, 110), border_radius=25)
            pygame.draw.rect(surface, main, (ax, y + 10, 50, 110), border_radius=25)
            pygame.draw.rect(surface, (190, 60, 60), (ax + 5, y + 15, 40, 50), border_radius=20)

    def _draw_clock(self, surface, x, y, t):
        pygame.draw.rect(surface, (70, 40, 20), (x - 35, y - 80, 70, 180), border_radius=5)
        pygame.draw.circle(surface, (255, 255, 240), (x, y - 40), 28)
        m_ang = math.radians(time.localtime().tm_min * 6 - 90)
        pygame.draw.line(surface, (0, 0, 0), (x, y - 40), (x + math.cos(m_ang) * 20, y - 40 + math.sin(m_ang) * 20), 2)
        px = x + math.sin(t * 3) * 20
        pygame.draw.line(surface, (50, 30, 10), (x, y + 10), (px, y + 80), 3)
        pygame.draw.circle(surface, (218, 165, 32), (px, y + 80), 10)

    def _draw_art(self, surface, x, y, type):
        w, h = (160, 100) if type == "Landscape" else (90, 110)
        pygame.draw.rect(surface, (218, 165, 32), (x, y, w, h), 6, border_radius=2)
        inner = pygame.Rect(x + 6, y + 6, w - 12, h - 12)

        if type == "Landscape":
            # Colors
            trunk_brown = (101, 67, 33)
            ground_y = y + 60

            pygame.draw.rect(surface, (135, 206, 235), inner)  # Sky
            pygame.draw.circle(surface, (255, 255, 100), (x + 120, y + 25), 15)  # Sun

            for cx, cy, cw, ch in self.landscape_clouds:
                pygame.draw.ellipse(surface, (255, 255, 255), (x + cx, y + cy, cw, ch))

            # Draw trees (Trunks first, then foliage)
            for tx, ty, tw, th, color in self.landscape_forest_trees:
                # Tree trunk positioning
                trunk_w = max(2, tw // 4)
                # Trunk goes from foliage bottom (y+ty) down to ground level (y+60)
                trunk_h = ground_y - (y + ty)
                if trunk_h > 0:
                    pygame.draw.rect(surface, trunk_brown,
                                     (x + tx - trunk_w // 2, y + ty, trunk_w, trunk_h))

                # Tree foliage
                pts = [(x + tx, y + ty - th), (x + tx - tw // 2, y + ty), (x + tx + tw // 2, y + ty)]
                pygame.draw.polygon(surface, color, pts)

            # Ground over the trunks bottom
            pygame.draw.rect(surface, (50, 140, 60), (x + 6, ground_y, w - 12, h - 66))

            # Mountains in front
            pygame.draw.polygon(surface, (34, 139, 34), [(x + 30, y + 60), (x + 50, y + 30), (x + 70, y + 60)])
            pygame.draw.polygon(surface, (34, 139, 34), [(x + 70, y + 60), (x + 100, y + 20), (x + 130, y + 60)])
        else:
            pygame.draw.rect(surface, (210, 180, 150), inner)
            pygame.draw.rect(surface, (40, 60, 120), (x + 25, y + 65, 40, 40), border_radius=10)
            pygame.draw.rect(surface, (230, 190, 160), (x + 35, y + 55, 20, 15))
            pygame.draw.circle(surface, (230, 190, 160), (x + 45, y + 35), 20)
            pygame.draw.polygon(surface, (100, 50, 20),
                                [(x + 20, y + 35), (x + 45, y + 5), (x + 70, y + 35), (x + 70, y + 50)])
            pygame.draw.circle(surface, (0, 0, 0), (x + 38, y + 32), 2)
            pygame.draw.circle(surface, (0, 0, 0), (x + 52, y + 32), 2)

    def _draw_lamp(self, surface, x, y, on):
        sh_col = (220, 210, 150) if on else (130, 120, 90)
        pygame.draw.polygon(surface, sh_col, [(x - 40, y - 100), (x + 40, y - 100), (x + 60, y - 30), (x - 60, y - 30)])
        pygame.draw.rect(surface, (50, 40, 30), (x - 5, y - 30, 10, 130))
        pygame.draw.rect(surface, (50, 40, 20), (x - 40, y + 100, 80, 15), border_radius=5)

    def _draw_ui_button(self, surface, x, y, label, color, alpha):
        bw, bh = 110, 40
        s = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, bw, bh), border_radius=12)
        pygame.draw.rect(s, (40, 40, 40, alpha), (0, 0, bw, bh), 2, border_radius=12)
        f = pygame.font.SysFont("Arial", 22, bold=True)
        txt = f.render(label, True, (255, 255, 255))
        txt.set_alpha(alpha)
        s.blit(txt, (bw // 2 - txt.get_width() // 2, bh // 2 - txt.get_height() // 2))
        surface.blit(s, (x - bw // 2, y))

    def handle_click(self, pos):
        mx, my = pos
        lamp_btn = pygame.Rect(1040 - 55, 360, 110, 40)
        aq_btn = pygame.Rect(180 - 55, 150, 110, 40)
        exit_btn = pygame.Rect(640 - 55, 650, 110, 40)

        # Added condition to ensure button can only be clicked when no food is present
        if self.aq_ui_alpha > 100 and aq_btn.collidepoint(mx, my) and self.fish_fed_timer <= 0:
            self.fish_fed_timer = 5.0
            self.food_particles = []
            for _ in range(12):
                self.food_particles.append({
                    'x': random.randint(-60, 60), 'y': -100,
                    'color': random.choice([(218, 165, 32), (180, 140, 60)]),
                    'speed': random.randint(30, 60), 'size': random.randint(2, 4),
                    'eaten': False
                })
            return "feed_fish"

        if self.lamp_ui_alpha > 100 and lamp_btn.collidepoint(mx, my):
            self.lamp_on = not self.lamp_on
            return "toggle_lamp"

        if self.exit_ui_alpha > 100 and exit_btn.collidepoint(mx, my):
            return "exit_house"

        return None