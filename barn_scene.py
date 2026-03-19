import pygame
import math
import time
import random
from player_drawer import draw_realistic_player_complex


class BarnScene:
    def __init__(self, get_selected_character):
        self.get_selected_character = get_selected_character
        self.player_x, self.player_y = 640, 400
        self.player_speed = 300
        self.facing_right = True
        self.is_moving = False
        self.walk_timer = 0.0
        self.feeds_this_visit = 0

        self.exit_ui_alpha = 0
        self.feed_ui_alpha = 0
        self.is_feeding_timer = 0.0
        self.peck_sound_timer = 0.0
        self.food_particles = []

        self.straw_piles = []
        for _ in range(8):
            sx = random.randint(350, 900)
            sy = random.randint(300, 550)
            self.straw_piles.append((sx, sy))

        self.chickens = []
        for _ in range(random.randint(5, 8)):
            self.chickens.append({
                'x': random.randint(400, 1000),
                'y': random.randint(300, 550),
                'offset': random.random() * 10,
                'speed': random.uniform(0.4, 0.8),
                'facing_right': True,
                'state': 'wanding',
                'peck_timer': 0.0
            })

        self.cow_pos = (120, 380)
        self.horse_pos = (1190, 360)

        self.solids = [
            pygame.Rect(80, 350, 200, 180),
            pygame.Rect(1120, 330, 150, 200),
            pygame.Rect(280, 0, 80, 720),
            pygame.Rect(960, 0, 80, 720),
        ]

    def update(self, dt, keys, current_time, last_visit_time):
        if dt == 0: return None
        t = current_time
        sound_trigger = None

        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.is_moving = dx != 0 or dy != 0
        if dx != 0: self.facing_right = dx > 0
        self.walk_timer += dt * 12 if self.is_moving else 0

        if self.is_moving:
            mag = math.hypot(dx, dy)
            nx = self.player_x + (dx / mag) * self.player_speed * dt
            ny = self.player_y + (dy / mag) * self.player_speed * dt
            p_feet = pygame.Rect(nx - 15, ny + 155, 30, 10)
            if not any(p_feet.colliderect(s) for s in self.solids):
                if 220 < ny < 660: self.player_y = ny
                if 50 < nx < 1230: self.player_x = nx

        food_p_center = None
        if self.is_feeding_timer > 0:
            self.is_feeding_timer -= dt
            px, py, count = 0, 0, 0
            for p in self.food_particles:
                p['y'] += p['speed'] * dt
                if p['y'] > p['ground']:
                    p['y'] = p['ground']
                    px += p['x'];
                    py += p['y'];
                    count += 1
            if count > 0: food_p_center = (px // count, py // count)
            if self.is_feeding_timer <= 0: self.food_particles = []

        near_any_chicken = False
        any_pecking = False

        for c in self.chickens:
            dist_to_food = 999
            if food_p_center: dist_to_food = math.hypot(c['x'] - food_p_center[0], c['y'] - food_p_center[1])

            if self.is_feeding_timer > 0 and dist_to_food < 150:
                c['state'] = 'pecking'
                c['peck_timer'] += dt
                any_pecking = True
                if dist_to_food > 30:
                    ang = math.atan2(food_p_center[1] - c['y'], food_p_center[0] - c['x'])
                    c['x'] += math.cos(ang) * (self.player_speed * 0.4) * dt
                    c['y'] += math.sin(ang) * (self.player_speed * 0.4) * dt
                    c['facing_right'] = food_p_center[0] > c['x']
            else:
                c['state'] = 'wanding'
                c['peck_timer'] = 0.0
                old_x = c['x']
                c['x'] += math.sin(t * c['speed'] + c['offset']) * 0.8
                if c['x'] > old_x:
                    c['facing_right'] = True
                elif c['x'] < old_x:
                    c['facing_right'] = False

            if math.hypot(self.player_x - c['x'], self.player_y - c['y']) < 140:
                near_any_chicken = True

        if any_pecking:
            self.peck_sound_timer += dt
            if self.peck_sound_timer > 0.4:
                sound_trigger = "chicken_eat_sound"
                self.peck_sound_timer = 0.0
        else:
            self.peck_sound_timer = 0.0

        self.exit_ui_alpha = min(255, self.exit_ui_alpha + 15) if self.player_y > 550 else max(0,
                                                                                               self.exit_ui_alpha - 15)

        cooldown_ok = (last_visit_time == 0 or current_time - last_visit_time >= 300)
        can_feed = self.feeds_this_visit < 10 and cooldown_ok

        if near_any_chicken and can_feed:
            self.feed_ui_alpha = min(255, self.feed_ui_alpha + 15)
        else:
            self.feed_ui_alpha = max(0, self.feed_ui_alpha - 15)

        return sound_trigger

    def draw(self, surface):
        t = time.time()
        surface.fill((110, 65, 35))
        pygame.draw.rect(surface, (80, 50, 25), (0, 0, 1280, 240))
        pygame.draw.rect(surface, (60, 40, 20), (0, 230, 1280, 10))

        self._draw_wall_tools(surface, 550, 80)

        for sx, sy in self.straw_piles:
            self._draw_hay_bale(surface, sx, sy)

        self._draw_cubist_cow(surface, self.cow_pos[0], self.cow_pos[1], t)
        self._draw_realistic_horse(surface, self.horse_pos[0], self.horse_pos[1], t)

        pygame.draw.rect(surface, (60, 35, 15), (300, 0, 40, 720))
        pygame.draw.rect(surface, (60, 35, 15), (960, 0, 40, 720))

        sorted_chickens = sorted(self.chickens, key=lambda c: c['y'])
        for c in sorted_chickens:
            self._draw_detailed_chicken(surface, c['x'], c['y'], t + c['offset'], c['facing_right'], c['state'],
                                        c['peck_timer'])

        if self.is_feeding_timer > 0:
            for p in self.food_particles: pygame.draw.circle(surface, (235, 210, 120), (int(p['x']), int(p['y'])), 2)

        shadow = pygame.Surface((120, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, 120, 30))
        surface.blit(shadow, (self.player_x - 60, self.player_y + 140))
        draw_realistic_player_complex(surface, self.player_x, self.player_y, self.get_selected_character(),
                                      self.walk_timer, self.is_moving, self.facing_right)

        if self.exit_ui_alpha > 0: self._draw_ui_button(surface, 640, 650, "EXIT BARN", (200, 50, 50),
                                                        self.exit_ui_alpha)
        if self.feed_ui_alpha > 0: self._draw_ui_button(surface, self.player_x, self.player_y - 130, "FEED",
                                                        (76, 175, 80), self.feed_ui_alpha)

    def _draw_detailed_chicken(self, surface, x, y, t, facing_right, state, peck_timer):
        bob = math.sin(t * 8) * 3
        leg_move = math.sin(t * 12) * 2
        d = 1 if facing_right else -1
        peck_y, peck_x = 0, 0
        if state == 'pecking':
            peck_deep = (math.sin(peck_timer * 15) * 0.5 + 0.5)
            peck_y, peck_x = 12 * peck_deep, 5 * peck_deep * d
            leg_move, bob = 0, 0

        pygame.draw.line(surface, (255, 165, 0), (x - 4 * d, y + 10 + bob), (x - 6 * d + leg_move, y + 22 + bob), 2)
        pygame.draw.line(surface, (255, 165, 0), (x + 4 * d, y + 10 + bob), (x + 6 * d - leg_move, y + 22 + bob), 2)
        pygame.draw.ellipse(surface, (255, 255, 250), (x - 18, y - 12 + bob, 36, 26))
        hx, hy = x + 14 * d + peck_x, y - 8 + bob + peck_y
        pygame.draw.circle(surface, (255, 255, 250), (int(hx), int(hy)), 11)
        pygame.draw.circle(surface, (220, 40, 40), (int(hx), int(hy - 10)), 5)
        pygame.draw.polygon(surface, (255, 165, 0), [(hx + 10 * d, hy - 2), (hx + 17 * d, hy), (hx + 10 * d, hy + 2)])
        pygame.draw.circle(surface, (0, 0, 0), (int(hx + 4 * d), int(hy - 2)), 2)

    def _draw_cubist_cow(self, surface, x, y, t):
        c_skin, c_spot, c_outline = (245, 245, 245), (40, 40, 45), (20, 20, 25)
        bob = math.sin(t * 1.0) * 2
        head_turn_angle = math.sin(t * 0.5) * 15
        legs = [(x + 10, y + 70), (x + 50, y + 70), (x + 120, y + 70)]
        for lx, ly in legs:
            pygame.draw.rect(surface, c_skin, (lx, ly, 16, 50), border_radius=3)
            pygame.draw.rect(surface, c_outline, (lx, ly, 16, 50), 2, border_radius=3)
        pygame.draw.rect(surface, c_skin, (x, y, 160, 100), border_radius=10)
        pygame.draw.rect(surface, c_spot, (x + 20, y + 15, 45, 45), border_radius=5)
        pygame.draw.rect(surface, c_spot, (x + 100, y + 50, 35, 35), border_radius=5)
        pygame.draw.line(surface, c_outline, (x + 155, y + 30), (x + 180, y + 60), 3)
        pygame.draw.rect(surface, c_spot, (x + 175, y + 55, 12, 18), border_radius=4)

        hx_base, hy_base = x - 50, y - 30 + bob
        head_surf = pygame.Surface((100, 120), pygame.SRCALPHA)
        for ex in [10, 70]:
            pygame.draw.rect(head_surf, c_skin, (ex, 0, 20, 30), border_radius=4)
            pygame.draw.rect(head_surf, c_outline, (ex, 0, 20, 30), 2, border_radius=4)
            pygame.draw.rect(head_surf, (255, 200, 210), (ex + 4, 4, 12, 22), border_radius=2)
        pygame.draw.rect(head_surf, c_skin, (15, 10, 70, 85), border_radius=8)
        pygame.draw.rect(head_surf, c_outline, (15, 10, 70, 85), 4, border_radius=8)
        pygame.draw.rect(head_surf, (255, 195, 205), (20, 55, 60, 35), border_radius=8)
        pygame.draw.rect(head_surf, (20, 20, 25), (30, 30, 8, 8), border_radius=2)
        pygame.draw.rect(head_surf, (20, 20, 25), (60, 30, 8, 8), border_radius=2)
        rotated_head = pygame.transform.rotate(head_surf, head_turn_angle)
        h_rect = rotated_head.get_rect(center=(hx_base + 35, hy_base + 42))
        surface.blit(rotated_head, h_rect.topleft)

    def _draw_realistic_horse(self, surface, x, y, t):
        c_body, c_legs, c_hair, c_outline, c_hoof, c_snout = (139, 69, 19), (110, 50, 10), (20, 20, 25), (30, 15, 5), (
            50, 50, 55), (60, 35, 15)
        bob = math.sin(t * 1.2) * 3
        h_shake, h_bob = math.sin(t * 0.8) * 4, math.cos(t * 1.6) * 2
        t_swish, m_wave = math.sin(t * 2.0) * 15, math.sin(t * 4.0) * 2

        t_surf = pygame.Surface((60, 100), pygame.SRCALPHA)
        t_pts = [(30, 0), (50, 30), (45, 80), (15, 90), (10, 60)]
        pygame.draw.polygon(t_surf, c_hair, t_pts)
        pygame.draw.polygon(t_surf, c_outline, t_pts, 3)
        r_tail = pygame.transform.rotate(t_surf, t_swish)
        surface.blit(r_tail, r_tail.get_rect(midtop=(x + 10, y + 25)).topleft)

        pygame.draw.rect(surface, c_body, (x - 140, y, 160, 110), border_radius=25)
        pygame.draw.rect(surface, c_outline, (x - 140, y, 160, 110), 5, border_radius=25)
        for lx, ly in [(x - 40, y + 65), (x - 110, y + 65), (x - 60, y + 70), (x - 130, y + 70)]:
            pygame.draw.rect(surface, c_legs, (lx, ly, 14, 80), border_radius=4)
            pygame.draw.rect(surface, c_hoof, (lx, ly + 70, 14, 10), border_radius=2)

        n_pts = [(x - 130, y + 10), (x - 160 + h_shake, y - 30 + bob + h_bob),
                 (x - 140 + h_shake, y - 50 + bob + h_bob), (x - 110, y - 10)]
        pygame.draw.polygon(surface, c_body, n_pts)
        m_pts = [(x - 135, y + 5), (x - 150 + h_shake, y - 10 + bob + h_bob + m_wave),
                 (x - 158 + h_shake, y - 30 + bob + h_bob + m_wave), (x - 140 + h_shake, y - 48 + bob + h_bob + m_wave),
                 (x - 135, y - 20)]
        pygame.draw.polygon(surface, c_hair, m_pts)

        hx, hy = x - 185 + h_shake, y - 80 + bob + h_bob
        pygame.draw.rect(surface, c_body, (hx, hy, 65, 80), border_radius=10)
        pygame.draw.rect(surface, c_outline, (hx, hy, 65, 80), 4, border_radius=10)
        pygame.draw.polygon(surface, c_hair, [(hx + 20, hy), (hx + 10, hy + 10 + m_wave), (hx + 40, hy + 10 + m_wave)])
        pygame.draw.rect(surface, c_snout, (hx + 5, hy + 45, 60, 35), border_radius=8)
        pygame.draw.circle(surface, (10, 10, 10), (int(hx + 18), int(hy + 68)), 3)
        pygame.draw.circle(surface, (10, 10, 10), (int(hx + 47), int(hy + 68)), 3)
        pygame.draw.circle(surface, (250, 250, 255), (int(hx + 48), int(hy + 28)), 5);
        pygame.draw.circle(surface, (20, 20, 25), (int(hx + 48), int(hy + 28)), 3)
        pygame.draw.circle(surface, (250, 250, 255), (int(hx + 18), int(hy + 28)), 4);
        pygame.draw.circle(surface, (20, 20, 25), (int(hx + 18), int(hy + 28)), 2)
        for ex in [10, 40]: pygame.draw.polygon(surface, c_body,
                                                [(hx + ex, hy), (hx + ex + 5, hy - 25), (hx + ex + 15, hy)])

    def _draw_wall_tools(self, surface, x, y):
        wood, metal, dark_metal = (139, 90, 43), (150, 150, 160), (100, 100, 110)
        pygame.draw.rect(surface, wood, (x, y, 6, 120))
        pygame.draw.rect(surface, metal, (x - 8, y + 110, 22, 6))
        for tx in [-6, 2, 10]: pygame.draw.line(surface, metal, (x + tx, y + 115), (x + tx, y + 140), 2)
        sx, sy = x + 70, y + 10
        pygame.draw.rect(surface, wood, (sx, sy, 6, 100))
        pygame.draw.rect(surface, metal, (sx - 11, sy + 90, 28, 35), border_radius=8)
        rx, ry = x + 140, y
        pygame.draw.rect(surface, wood, (rx, ry, 6, 130))
        pygame.draw.rect(surface, metal, (rx - 25, ry + 125, 56, 8))
        for tx in range(-22, 35, 6): pygame.draw.line(surface, dark_metal, (rx + tx, ry + 133), (rx + tx, ry + 150), 2)

    def _draw_hay_bale(self, surface, x, y):
        pygame.draw.ellipse(surface, (218, 165, 32), (x, y, 60, 30))
        pygame.draw.ellipse(surface, (255, 215, 0), (x + 5, y + 2, 50, 20))

    def _draw_ui_button(self, surface, x, y, label, color, alpha):
        bw, bh = 130, 45
        s = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, bw, bh), border_radius=12)
        pygame.draw.rect(s, (40, 40, 40, alpha), (0, 0, bw, bh), 2, border_radius=12)
        f = pygame.font.SysFont("Arial", 20, bold=True)
        txt = f.render(label, True, (255, 255, 255))
        txt.set_alpha(alpha)
        s.blit(txt, (bw // 2 - txt.get_width() // 2, bh // 2 - txt.get_height() // 2))
        surface.blit(s, (x - bw // 2, y))

    def handle_click(self, pos):
        mx, my = pos
        exit_btn = pygame.Rect(640 - 65, 650, 130, 45)
        feed_btn = pygame.Rect(self.player_x - 55, self.player_y - 130, 110, 40)

        if self.exit_ui_alpha > 100 and exit_btn.collidepoint(mx, my):
            self.feeds_this_visit = 0
            return "exit_barn"

        if self.feed_ui_alpha > 100 and feed_btn.collidepoint(mx, my):
            if self.feeds_this_visit < 10:
                self.feeds_this_visit += 1
                self.is_feeding_timer = 2.0
                self.food_particles = [{'x': self.player_x + random.randint(-50, 50), 'y': self.player_y + 120,
                                        'ground': self.player_y + 160 + random.randint(0, 25),
                                        'speed': random.randint(120, 220)} for _ in range(20)]
                return "feed_chicken_xp"
            else:
                return "barn_full"
        return None