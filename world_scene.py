import pygame
import math
import random
import time
from player_drawer import draw_realistic_player_complex


class WorldScene:
    def __init__(self, animals, add_xp, unlock_callback, info_callback,
                 get_selected_character, draw_boy_fn, draw_girl_fn,
                 floating_button_class):
        self.animals = animals
        self.add_xp = add_xp
        self.unlock_callback = unlock_callback
        self.info_callback = info_callback
        self.FloatingButton = floating_button_class
        self.get_selected_character = get_selected_character

        # --- CRITICAL: Initialize these BEFORE calling layout/render methods ---
        self.unlocked_max = 0  # <--- MUST BE HERE
        self.active_encounter = None
        self.floating_alpha = 0.0
        self.is_moving = False
        self.walk_timer = 0.0
        self.facing_right = True

        self.ui_font = pygame.font.SysFont("Arial", 26, bold=True)
        self.base_shadow = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.ellipse(self.base_shadow, (0, 0, 0, 35), (0, 0, 200, 200))

        self.world_width, self.world_height = 3000, 3000
        self.player_x, self.player_y = 1500, 1500
        self.player_speed, self.player_collision_r = 380, 15

        # Now you can safely call these:
        self.animal_cache, self.building_cache, self.fence_cache = {}, {}, {}
        self._pre_render_all_assets()

        self.positions = []
        for i in range(len(animals)):
            angle = i * (math.pi * 2 / len(animals)) + random.uniform(-0.1, 0.1)
            dist = random.randint(600, 1200)
            self.positions.append((self.player_x + int(math.cos(angle) * dist),
                                   self.player_y + int(math.sin(angle) * dist)))

        self.border_elements = []
        self._generate_farm_layout()  # This calls the collision logic that needs unlocked_max

        self.bushes, self.flowers, self.tall_grass = [], [], []
        self._generate_scattered_decor()

        # Interaction Cooldowns
        self.tractor_sound_cooldown = 0.0

        # House & Barn UI
        self.near_house, self.house_alpha = False, 0.0
        self.near_barn, self.barn_alpha = False, 0.0  # NEW: Barn proximity and alpha

        # UI Buttons
        self.feed_btn = self.FloatingButton("FEED", "Feed", -75, 0, "green")
        self.pet_btn = self.FloatingButton("PET", "Pet", 75, 0, "pink")
        self.info_btn = self.FloatingButton("INFO", "Info", 0, -85, "purple")
        self.enter_house_btn = self.FloatingButton("ENTER", "Enter House", 0, -100, "purple")
        self.enter_barn_btn = self.FloatingButton("ENTER_BARN", "Enter Barn", 0, -100,
                                                  "orange")  # NEW: Enter Barn button

    def _draw_shadow(self, surface, x, y, w, h):
        if w < 1 or h < 1: return
        sw, sh = surface.get_size()
        if -w < x < sw + w and -h < y < sh + h:
            try:
                scaled = pygame.transform.scale(self.base_shadow, (int(w), int(h)))
                surface.blit(scaled, (int(x - w // 2), int(y - h // 2)))
            except:
                pass

    def _is_near_active_animal(self, x, y, radius=80):
        # Collision only for unlocked animals
        for i in range(self.unlocked_max + 1):
            ax, ay = self.positions[i]
            if math.hypot(x - ax, y - ay) < radius:
                return True
        return False

    def _pre_render_all_assets(self):
        for animal in self.animals:
            temp = pygame.Surface((500, 500), pygame.SRCALPHA)
            animal.draw(temp, 250, 250)
            self.animal_cache[animal.kind] = pygame.transform.smoothscale(temp, (220, 220))

        self.building_cache['house1'] = self._draw_detailed_house((240, 200, 150))
        self.building_cache['barn'] = self._draw_detailed_barn()
        self.building_cache['tractor'] = self._draw_detailed_tractor()
        self.fence_cache['h'] = self._draw_fence_segment(True)
        self.fence_cache['v'] = self._draw_fence_segment(False)

    def _draw_detailed_house(self, color):
        surf = pygame.Surface((400, 400), pygame.SRCALPHA)
        roof_color, door_color = (139, 69, 19), (100, 50, 20)
        window_color, fence_color = (173, 216, 230), (245, 245, 245)
        bush_color, flower_color = (34, 139, 34), (255, 105, 180)

        for bx in [60, 90, 210, 240]:
            pygame.draw.circle(surf, bush_color, (bx, 240), 18)
            pygame.draw.circle(surf, flower_color, (bx + 5, 235), 3)

        pygame.draw.rect(surf, color, (50, 100, 200, 150), border_radius=5)
        pygame.draw.polygon(surf, roof_color, [(35, 110), (265, 110), (150, 30)])
        pygame.draw.rect(surf, door_color, (125, 170, 50, 80), border_radius=2)
        pygame.draw.circle(surf, (218, 165, 32), (165, 210), 3)

        pygame.draw.rect(surf, (50, 50, 50), (65, 125, 55, 55), border_radius=3)
        pygame.draw.rect(surf, window_color, (70, 130, 45, 45), border_radius=2)
        pygame.draw.line(surf, (255, 255, 255, 100), (92, 130), (92, 175), 2)
        pygame.draw.line(surf, (255, 255, 255, 100), (70, 152), (115, 152), 2)

        fence_y, post_w, post_h = 250, 8, 35
        for fx in range(30, 110, 15):
            pygame.draw.rect(surf, fence_color, (fx, fence_y, post_w, post_h))
            pygame.draw.polygon(surf, fence_color, [(fx, fence_y), (fx + post_w, fence_y), (fx + post_w // 2, fence_y - 8)])
        for fx in range(190, 280, 15):
            pygame.draw.rect(surf, fence_color, (fx, fence_y, post_w, post_h))
            pygame.draw.polygon(surf, fence_color, [(fx, fence_y), (fx + post_w, fence_y), (fx + post_w // 2, fence_y - 8)])

        pygame.draw.rect(surf, (230, 230, 230), (30, fence_y + 10, 80, 4))
        pygame.draw.rect(surf, (230, 230, 230), (190, fence_y + 10, 85, 4))

        gate_rect = pygame.Rect(120, fence_y - 5, 60, post_h + 5)
        pygame.draw.rect(surf, (220, 220, 220), gate_rect, border_radius=2)
        pygame.draw.rect(surf, (180, 180, 180), gate_rect, 2, border_radius=2)
        for gx in range(125, 175, 12):
            pygame.draw.line(surf, (180, 180, 180), (gx, fence_y), (gx, fence_y + post_h), 1)

        return surf

    def _draw_detailed_barn(self):
        surf = pygame.Surface((350, 350), pygame.SRCALPHA)
        pygame.draw.rect(surf, (180, 40, 40), (50, 100, 250, 180), border_radius=3)
        pygame.draw.polygon(surf, (100, 20, 20), [(30, 110), (320, 110), (175, 20)])
        pygame.draw.rect(surf, (240, 240, 240), (120, 180, 110, 100))
        pygame.draw.line(surf, (180, 40, 40), (120, 180), (230, 280), 5)
        pygame.draw.line(surf, (180, 40, 40), (230, 180), (120, 280), 5)
        return surf

    def _draw_detailed_tractor(self):
        surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        body_color, acc_color, silver = (85, 107, 47), (40, 40, 40), (200, 200, 200)
        pygame.draw.circle(surf, acc_color, (60, 150), 35)
        pygame.draw.circle(surf, silver, (60, 150), 15)
        pygame.draw.circle(surf, acc_color, (150, 160), 20)
        pygame.draw.circle(surf, silver, (150, 160), 8)
        pygame.draw.rect(surf, body_color, (70, 100, 90, 60), border_radius=5)
        pygame.draw.polygon(surf, body_color, [(110, 100), (160, 115), (160, 160), (110, 160)])
        pygame.draw.line(surf, silver, (115, 108), (155, 120), 2)
        pygame.draw.rect(surf, (20, 20, 20), (80, 85, 30, 15), border_radius=3)
        pygame.draw.line(surf, acc_color, (105, 100), (115, 85), 3)
        pygame.draw.ellipse(surf, acc_color, (110, 75, 20, 10))
        pygame.draw.rect(surf, acc_color, (130, 65, 8, 40), border_radius=2)
        pygame.draw.circle(surf, (255, 255, 200), (155, 125), 5)
        pygame.draw.circle(surf, (255, 255, 200), (155, 145), 5)
        return surf

    def _draw_fence_segment(self, horizontal=True):
        """Creates a detailed rustic wooden fence segment with posts and rails."""
        # Increase surface size slightly to accommodate posts without cutting off
        surf = pygame.Surface((200, 200), pygame.SRCALPHA)

        # Colors
        wood_main = (139, 90, 43)  # Warm brown
        wood_dark = (100, 70, 40)  # Darker brown for details/outline

        if horizontal:
            # Drawing a horizontal segment (for top/bottom borders)

            # 1. Main horizontal rails (2 rails)
            # Top rail
            pygame.draw.rect(surf, wood_main, (0, 85, 200, 10), border_radius=2)
            pygame.draw.rect(surf, wood_dark, (0, 85, 200, 10), 2, border_radius=2)  # Outline
            # Bottom rail
            pygame.draw.rect(surf, wood_main, (0, 110, 200, 10), border_radius=2)
            pygame.draw.rect(surf, wood_dark, (0, 110, 200, 10), 2, border_radius=2)  # Outline

            # 2. Rustic Posts (Vertical, placed periodically)
            # Post 1 (Left)
            pygame.draw.rect(surf, wood_main, (30, 60, 20, 90), border_radius=3)
            pygame.draw.rect(surf, wood_dark, (30, 60, 20, 90), 3, border_radius=3)
            # Wood grain detail on post
            pygame.draw.line(surf, wood_dark, (35, 70), (35, 140), 1)
            pygame.draw.line(surf, wood_dark, (45, 75), (45, 135), 1)

            # Post 2 (Right)
            pygame.draw.rect(surf, wood_main, (150, 60, 20, 90), border_radius=3)
            pygame.draw.rect(surf, wood_dark, (150, 60, 20, 90), 3, border_radius=3)
            pygame.draw.line(surf, wood_dark, (155, 70), (155, 140), 1)
            pygame.draw.line(surf, wood_dark, (165, 75), (165, 135), 1)

        else:
            # Drawing a vertical segment (for left/right borders)

            # 1. Main vertical rails (2 rails)
            # Left rail
            pygame.draw.rect(surf, wood_main, (85, 0, 10, 200), border_radius=2)
            pygame.draw.rect(surf, wood_dark, (85, 0, 10, 200), 2, border_radius=2)
            # Right rail
            pygame.draw.rect(surf, wood_main, (110, 0, 10, 200), border_radius=2)
            pygame.draw.rect(surf, wood_dark, (110, 0, 10, 200), 2, border_radius=2)

            # 2. Rustic Posts (Horizontal, placed periodically)
            # Post 1 (Top)
            pygame.draw.rect(surf, wood_main, (60, 30, 90, 20), border_radius=3)
            pygame.draw.rect(surf, wood_dark, (60, 30, 90, 20), 3, border_radius=3)
            # Wood grain detail
            pygame.draw.line(surf, wood_dark, (70, 35), (140, 35), 1)
            pygame.draw.line(surf, wood_dark, (75, 45), (135, 45), 1)

            # Post 2 (Bottom)
            pygame.draw.rect(surf, wood_main, (60, 150, 90, 20), border_radius=3)
            pygame.draw.rect(surf, wood_dark, (60, 150, 90, 20), 3, border_radius=3)
            pygame.draw.line(surf, wood_dark, (70, 155), (140, 155), 1)
            pygame.draw.line(surf, wood_dark, (75, 165), (135, 165), 1)

        return surf

    def _generate_farm_layout(self):
        occupied_rects, step = [], 195
        def is_area_clear(rect):
            if self._is_near_active_animal(rect.centerx, rect.centery, 300): return False
            return not any(rect.inflate(50, 50).colliderect(r) for r in occupied_rects)

        for item, w, h in [('house1', 250, 250), ('barn', 300, 300), ('tractor', 150, 150)]:
            for _ in range(100):
                rx, ry = random.randint(400, 2600), random.randint(400, 2600)
                new_rect = pygame.Rect(rx - w // 2, ry - h // 2, w, h)
                if is_area_clear(new_rect):
                    self.border_elements.append((item, rx, ry))
                    occupied_rects.append(new_rect)
                    break
        for x in range(200, 2800, step):
            self.border_elements.append(('h_fence', x, 200))
            self.border_elements.append(('h_fence', x, 2800))
        for y in range(200, 2800, step):
            self.border_elements.append(('v_fence', 150, y))
            self.border_elements.append(('v_fence', 2850, y))

    def _generate_scattered_decor(self):
        build_rects = [pygame.Rect(ox-130, oy-130, 260, 260) for t, ox, oy in self.border_elements if t in ['house1', 'barn', 'tractor']]
        for _ in range(130):
            bx, by = random.randint(300, 2700), random.randint(300, 2700)
            if not any(pygame.Rect(bx-40, by-40, 80, 80).colliderect(br) for br in build_rects):
                self.bushes.append((bx, by, random.uniform(0.8, 1.2)))
        for _ in range(350):
            gx, gy = random.randint(300, 2700), random.randint(300, 2700)
            if not any(pygame.Rect(gx-10, gy-10, 20, 20).colliderect(br) for br in build_rects):
                self.tall_grass.append((gx, gy, random.uniform(0.7, 1.3)))
        for _ in range(400):
            fx, fy = random.randint(300, 2700), random.randint(300, 2700)
            if not any(pygame.Rect(fx-10, fy-10, 20, 20).colliderect(br) for br in build_rects):
                self.flowers.append((fx, fy, random.choice([(255, 120, 150), (255, 230, 100), (160, 120, 255)])))

    def update(self, dt, keys):
        if dt == 0: return
        event_result = None
        if self.tractor_sound_cooldown > 0: self.tractor_sound_cooldown -= dt

        solid_rects, tractor_rects = [], []
        for t, ox, oy in self.border_elements:
            if t == 'house1': solid_rects.append(pygame.Rect(ox - 100, oy - 20, 200, 100))
            elif t == 'barn': solid_rects.append(pygame.Rect(ox - 120, oy - 10, 240, 120))
            elif t == 'tractor':
                tr = pygame.Rect(ox - 70, oy + 20, 140, 80)
                solid_rects.append(tr); tractor_rects.append(tr)
            elif t == 'h_fence': solid_rects.append(pygame.Rect(ox - 100, oy - 10, 200, 20))
            elif t == 'v_fence': solid_rects.append(pygame.Rect(ox - 10, oy - 100, 20, 200))

        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.is_moving = dx != 0 or dy != 0
        if dx != 0: self.facing_right = dx > 0
        self.walk_timer += dt * 14 if self.is_moving else 0

        if self.is_moving:
            mag = math.hypot(dx, dy)
            new_x = self.player_x + (dx / mag) * self.player_speed * dt
            new_y = self.player_y + (dy / mag) * self.player_speed * dt
            p_rect = pygame.Rect(0, 0, 30, 15)

            p_rect.center = (new_x, self.player_y + 160)
            hit_sr = next((sr for sr in solid_rects if p_rect.colliderect(sr)), None)
            # FIX: Collision check only for active animals
            if not hit_sr and not self._is_near_active_animal(new_x, self.player_y + 160, 80):
                self.player_x = new_x
            elif hit_sr in tractor_rects and self.tractor_sound_cooldown <= 0:
                event_result = "hit_tractor"; self.tractor_sound_cooldown = 1.5

            p_rect.center = (self.player_x, new_y + 160)
            hit_sr = next((sr for sr in solid_rects if p_rect.colliderect(sr)), None)
            # FIX: Collision check only for active animals
            if not hit_sr and not self._is_near_active_animal(self.player_x, new_y + 160, 80):
                self.player_y = new_y
            elif hit_sr in tractor_rects and self.tractor_sound_cooldown <= 0:
                event_result = "hit_tractor"; self.tractor_sound_cooldown = 1.5

        self.near_house = False
        for t, ox, oy in self.border_elements:
            if t == 'house1' and math.hypot(self.player_x - ox, self.player_y - (oy + 80)) < 100:
                self.near_house = True; break
        self.house_alpha = min(255.0, self.house_alpha + 500 * dt) if self.near_house else max(0.0, self.house_alpha - 500 * dt)

        self.near_barn = False
        for t, ox, oy in self.border_elements:
            # Check proximity to the barn's door area
            if t == 'barn' and math.hypot(self.player_x - ox, self.player_y - (oy + 120)) < 120:
                self.near_barn = True;
                break
        self.barn_alpha = min(255.0, self.barn_alpha + 500 * dt) if self.near_barn else max(0.0,
                                                                                            self.barn_alpha - 500 * dt)

        nearest_dist, encounter_idx = 170, None
        for i in range(self.unlocked_max + 1):
            d = math.hypot(self.player_x - self.positions[i][0], self.player_y - self.positions[i][1])
            if d < nearest_dist: nearest_dist, encounter_idx = d, i
        if encounter_idx is not None:
            self.active_encounter, self.floating_alpha = encounter_idx, min(255.0, self.floating_alpha + 500 * dt)
        else:
            self.floating_alpha = max(0.0, self.floating_alpha - 500 * dt)
            if self.floating_alpha <= 0: self.active_encounter = None
        return event_result

    def draw(self, surface, unlocked_max):
        self.unlocked_max = unlocked_max
        sw, sh = surface.get_size()
        cam_x, cam_y = self.player_x - sw // 2, self.player_y - sh // 2
        surface.fill((90, 150, 90)); t = time.time()

        for gx, gy, sc in self.tall_grass:
            sx, sy = int(gx - cam_x), int(gy - cam_y)
            if -20 < sx < sw + 20 and -20 < sy < sh + 20:
                sway = math.sin(t * 1.5 + gx * 0.05) * (5 * sc)
                for off in [-4, 0, 4]: pygame.draw.line(surface, (60, 110, 60), (sx + off, sy + 5), (sx + off + int(sway), sy - int(15 * sc)), 2)

        for fx, fy, col in self.flowers:
            sx, sy = int(fx - cam_x), int(fy - cam_y)
            if -20 < sx < sw + 20 and -20 < sy < sh + 20:
                sway = math.sin(t * 1.2 + fx * 0.02) * 6
                pygame.draw.line(surface, (45, 95, 45), (sx + int(sway), sy), (sx, sy + 18), 2)
                pygame.draw.circle(surface, col, (sx + int(sway), sy), 6)
                pygame.draw.circle(surface, (255, 255, 120), (sx + int(sway), sy), 2)

        render_queue = []
        for t_type, ox, oy in self.border_elements: render_queue.append(('static', oy, (t_type, ox, oy)))
        for bx, by, sc in self.bushes: render_queue.append(('bush', by, (bx, by, sc)))
        for i in range(unlocked_max + 1): render_queue.append(('animal', self.positions[i][1], (self.animals[i], self.positions[i][0], self.positions[i][1])))
        render_queue.append(('player', self.player_y, ("player", sw // 2, sh // 2)))
        render_queue.sort(key=lambda x: x[1])

        for r_type, _, r_data in render_queue:
            if r_type == 'static':
                tt, ox, oy = r_data; sx, sy = int(ox - cam_x), int(oy - cam_y)
                if tt in self.building_cache:
                    self._draw_shadow(surface, sx, sy + 130, 220, 60)
                    surface.blit(self.building_cache[tt], (sx - 200, sy - 200))
                elif tt == 'h_fence': surface.blit(self.fence_cache['h'], (sx - 100, sy - 100))
                elif tt == 'v_fence': surface.blit(self.fence_cache['v'], (sx - 100, sy - 100))
            elif r_type == 'bush':
                bx, by, sc = r_data; sx, sy = int(bx - cam_x), int(by - cam_y)
                self._draw_shadow(surface, sx, sy + 15, int(100 * sc), int(40 * sc))
                for ox_b, oy_b, rs in [(-15, 0, 1.0), (15, 0, 0.9), (0, -15, 1.1)]:
                    px, py = sx + int(ox_b * sc), sy + int(oy_b * sc)
                    pygame.draw.circle(surface, (40, 90, 40), (px, py), int(30 * sc * rs))
                    pygame.draw.circle(surface, (60, 110, 60), (px - int(5 * sc), py - int(5 * sc)), int(10 * sc * rs))
            elif r_type == 'animal':
                an, ax, ay = r_data; sx, sy = int(ax - cam_x), int(ay - cam_y)
                self._draw_shadow(surface, sx, sy + 35, 160, 40)
                cached = self.animal_cache.get(an.kind)
                if cached: surface.blit(cached, (sx - 110, sy - 150))
                bx_b, by_b = sx - 30, sy + 55
                pygame.draw.rect(surface, (40, 40, 40), (bx_b, by_b, 60, 5))
                pygame.draw.rect(surface, (76, 175, 80), (bx_b, by_b, int(60 * (an.hunger / 100)), 5))
                pygame.draw.rect(surface, (40, 40, 40), (bx_b, by_b + 8, 60, 5))
                pygame.draw.rect(surface, (233, 30, 99), (bx_b, by_b + 8, int(60 * (an.affection / 100)), 5))
            elif r_type == 'player':
                self._draw_shadow(surface, r_data[1], r_data[2] + 160, 120, 30)
                draw_realistic_player_complex(surface, r_data[1], r_data[2], self.get_selected_character(), self.walk_timer, self.is_moving, self.facing_right)

        if self.house_alpha > 0:
            self.enter_house_btn.update_position(sw // 2, sh // 2 - 50)
            self.enter_house_btn.draw(surface, int(self.house_alpha))

        if self.barn_alpha > 0:
            self.enter_barn_btn.update_position(sw // 2, sh // 2 - 50);
            self.enter_barn_btn.draw(surface, int(self.barn_alpha))

        if self.barn_alpha > 0:
            self.enter_barn_btn.update_position(sw // 2, sh // 2 - 50);
            self.enter_barn_btn.draw(surface, int(self.barn_alpha))

        if self.active_encounter is not None and self.floating_alpha > 0:
            ax, ay = self.positions[self.active_encounter]
            sx, sy = int(ax - cam_x), int(ay - cam_y) - 45
            for b in [self.feed_btn, self.pet_btn, self.info_btn]: b.update_position(sx, sy); b.draw(surface, int(self.floating_alpha))

    def handle_click(self, pos):
        if self.near_house and self.enter_house_btn.hit(*pos): return "enter_house"
        if self.near_barn and self.enter_barn_btn.hit(*pos): return "enter_barn"
        if self.active_encounter is not None and self.floating_alpha > 0:
            an = self.animals[self.active_encounter]
            if self.feed_btn.hit(*pos) and an.hunger < 80: an.hunger = min(100, an.hunger + 25); self.add_xp(10); return "feed"
            if self.pet_btn.hit(*pos) and an.affection < 80: an.affection = min(100, an.affection + 25); an.add_heart_burst(*pos); self.add_xp(10); return "pet"
            if self.info_btn.hit(*pos): self.info_callback(self.active_encounter); return "info"
        return None