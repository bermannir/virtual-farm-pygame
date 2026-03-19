import pygame
import math

def draw_realistic_player_complex(surface, cx, cy, char_type, walk_timer, is_moving, facing_right):
    # 1. Setup colors and constants
    skin, outline = (255, 220, 185), (50, 40, 30)
    if char_type == "girl":
        shirt, hair, shoes = (250, 120, 170), (250, 210, 100), (220, 60, 60)
    else:
        shirt, pants, hair, shoes = (70, 140, 230), (60, 70, 90), (90, 60, 40), (40, 40, 45)

    dir_mult = 1 if facing_right else -1

    # Internal surface for drawing before scaling (base size 200x200)
    temp_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
    tcx, tcy = 100, 140  # Drawing center

    # 2. Pendulum physics for walk animation
    swing = math.sin(walk_timer) * 45 if is_moving else 0
    arm_swing = math.sin(walk_timer) * 35 if is_moving else 0

    # Body dimensions
    head_r, torso_h, leg_l, arm_l = 20, 36, 32, 28

    # Joint points Y positions
    head_y = tcy - torso_h - head_r + 5
    neck_y = tcy - torso_h + 5
    pelvis_y = tcy

    # 3. Define Limbs Geometry
    b_leg_angle = math.radians(swing * dir_mult)
    b_leg_end = (tcx + int(math.sin(b_leg_angle) * leg_l),
                 pelvis_y + int(math.cos(b_leg_angle) * leg_l))

    b_arm_angle = math.radians(-arm_swing * dir_mult)
    b_arm_end = (tcx + int(math.sin(b_arm_angle) * arm_l),
                 neck_y + int(math.cos(b_arm_angle) * arm_l))

    f_leg_angle = math.radians(-swing * dir_mult)
    f_leg_end = (tcx + int(math.sin(f_leg_angle) * leg_l),
                 pelvis_y + int(math.cos(f_leg_angle) * leg_l))

    f_arm_angle = math.radians(arm_swing * dir_mult)
    f_arm_end = (tcx + int(math.sin(f_arm_angle) * arm_l),
                 neck_y + int(math.cos(f_arm_angle) * arm_l))

    dress_bottom_y = pelvis_y + 16

    # Helper function to draw shoes
    def draw_shoe(surface, pos, direction):
        toe_r = 9
        heel_w, heel_h = 14, 12
        shoe_color = shoes
        heel_x = pos[0] - (heel_w // 2)
        heel_y = pos[1] - 2
        toe_cx = pos[0] + (heel_w // 2 + toe_r - 4) * direction
        toe_cy = heel_y + heel_h // 2 + 1
        pygame.draw.rect(surface, outline, (heel_x - 1, heel_y - 1, heel_w + 2, heel_h + 2), border_radius=4)
        pygame.draw.circle(surface, outline, (toe_cx, toe_cy), toe_r + 1)
        pygame.draw.rect(surface, shoe_color, (heel_x, heel_y, heel_w, heel_h), border_radius=3)
        pygame.draw.circle(surface, shoe_color, (toe_cx, toe_cy), toe_r)

    # 5. RENDER ORDER
    # --- A. Back Limbs ---
    pygame.draw.line(temp_surf, outline, (tcx, pelvis_y), b_leg_end, 12)
    pygame.draw.line(temp_surf, skin, (tcx, pelvis_y), b_leg_end, 10)
    if char_type == "boy": pygame.draw.line(temp_surf, pants, (tcx, pelvis_y), b_leg_end, 10)
    draw_shoe(temp_surf, b_leg_end, dir_mult)

    pygame.draw.line(temp_surf, outline, (tcx, neck_y), b_arm_end, 11)
    pygame.draw.line(temp_surf, skin, (tcx, neck_y), b_arm_end, 9)
    pygame.draw.circle(temp_surf, outline, b_arm_end, 6)
    pygame.draw.circle(temp_surf, skin, b_arm_end, 5)

    # --- B. Near Leg (Girl) ---
    if char_type == "girl":
        pygame.draw.line(temp_surf, outline, (tcx, pelvis_y), f_leg_end, 12)
        pygame.draw.line(temp_surf, skin, (tcx, pelvis_y), f_leg_end, 10)
        draw_shoe(temp_surf, f_leg_end, dir_mult)

    # --- C. Torso ---
    if char_type == "boy":
        pygame.draw.rect(temp_surf, outline, (tcx - 15, neck_y - 5, 30, torso_h + 6), border_radius=10)
        pygame.draw.rect(temp_surf, shirt, (tcx - 14, neck_y - 4, 28, torso_h + 4), border_radius=9)
        pygame.draw.rect(temp_surf, (30, 30, 30), (tcx - 14, pelvis_y - 8, 28, 6))
        pygame.draw.rect(temp_surf, (220, 200, 100), (tcx - 4, pelvis_y - 8, 8, 6), 2)
    else:
        pygame.draw.polygon(temp_surf, outline, [(tcx - 13, neck_y - 5), (tcx + 13, neck_y - 5), (tcx + 22, dress_bottom_y + 1), (tcx - 22, dress_bottom_y + 1)])
        pygame.draw.polygon(temp_surf, shirt, [(tcx - 12, neck_y - 4), (tcx + 12, neck_y - 4), (tcx + 21, dress_bottom_y), (tcx - 21, dress_bottom_y)])
        pygame.draw.arc(temp_surf, outline, (tcx - 21, dress_bottom_y - 5, 42, 12), math.pi, 0, 2)
        pygame.draw.arc(temp_surf, shirt, (tcx - 21, dress_bottom_y - 4, 42, 10), math.pi, 0, 1)

    # --- D. Near Leg (Boy) ---
    if char_type == "boy":
        pygame.draw.line(temp_surf, outline, (tcx, pelvis_y), f_leg_end, 12)
        pygame.draw.line(temp_surf, pants, (tcx, pelvis_y), f_leg_end, 10)
        draw_shoe(temp_surf, f_leg_end, dir_mult)

    # --- E. Front Arm ---
    pygame.draw.line(temp_surf, outline, (tcx, neck_y), f_arm_end, 11)
    pygame.draw.line(temp_surf, skin, (tcx, neck_y), f_arm_end, 9)
    sleeve_len = 14 if char_type == "girl" else 18
    s_end = (tcx + int(math.sin(f_arm_angle) * sleeve_len), neck_y + int(math.cos(f_arm_angle) * sleeve_len))
    pygame.draw.line(temp_surf, shirt, (tcx, neck_y), s_end, 10)
    pygame.draw.circle(temp_surf, outline, f_arm_end, 6)
    pygame.draw.circle(temp_surf, skin, f_arm_end, 5)

    # --- F. Head & Face ---
    pygame.draw.line(temp_surf, skin, (tcx, neck_y), (tcx, neck_y - 10), 8)
    pygame.draw.circle(temp_surf, outline, (tcx, head_y), head_r + 1)
    pygame.draw.circle(temp_surf, skin, (tcx, head_y), head_r)
    eye_x_base = tcx + 7 * dir_mult
    pygame.draw.circle(temp_surf, (255, 255, 255), (eye_x_base, head_y - 3), 6)
    pygame.draw.circle(temp_surf, (50, 110, 190), (eye_x_base + 3 * dir_mult, head_y - 3), 3)
    pygame.draw.circle(temp_surf, (10, 10, 10), (eye_x_base + 3 * dir_mult, head_y - 3), 1)
    pygame.draw.polygon(temp_surf, (235, 180, 150), [(tcx + 15 * dir_mult, head_y + 5), (tcx + 11 * dir_mult, head_y + 9), (tcx + 15 * dir_mult, head_y + 10)])
    if is_moving:
        pygame.draw.circle(temp_surf, (190, 90, 90), (tcx + 9 * dir_mult, head_y + 11), 3)
    else:
        pygame.draw.line(temp_surf, (190, 90, 90), (tcx + 6 * dir_mult, head_y + 11), (tcx + 12 * dir_mult, head_y + 11), 2)

    # --- G. Hair (FIXED) ---
    if char_type == "boy":
        pygame.draw.arc(temp_surf, hair, (tcx - head_r - 2, head_y - head_r - 5, head_r * 2 + 4, head_r * 2), 0, math.pi, 9)
        start_point = -14 if facing_right else -7
        end_point = 9 if facing_right else 16
        for i in range(start_point, end_point, 7):
            pygame.draw.polygon(temp_surf, hair, [
                (tcx + i, head_y - head_r + 2),
                (tcx + i + 5, head_y - head_r - 9),
                (tcx + i + 10, head_y - head_r + 2)
            ])
    else:
        # 1. Base cover for the back of the neck/head to prevent bald spots
        back_offset = -10 * dir_mult
        pygame.draw.circle(temp_surf, hair, (tcx + back_offset, head_y + 3), 14)

        # 2. Crown / Top of the head
        pygame.draw.arc(temp_surf, hair, (tcx - head_r - 2, head_y - head_r - 4, head_r * 2 + 4, head_r * 2 + 4), 0, math.pi, 12)

        # 3. Flowing Ponytail / Back hair (animated)
        hair_bob = math.sin(walk_timer - math.pi / 4) * 6 if is_moving else 0
        rect_left = tcx - 14 * dir_mult - 9
        pygame.draw.ellipse(temp_surf, hair, (rect_left, head_y - 2, 18, 42 + hair_bob))

        # 4. Swooping Bangs / Fringe
        pygame.draw.polygon(temp_surf, hair, [
            (tcx - head_r * dir_mult, head_y - head_r + 5),
            (tcx + 8 * dir_mult, head_y - head_r - 3),
            (tcx + 12 * dir_mult, head_y - head_r + 6),
            (tcx + 2 * dir_mult, head_y - 2)
        ])

    # --- H. Final Blit ---
    scaled_player = pygame.transform.smoothscale(temp_surf, (264, 264))
    surface.blit(scaled_player, (cx - 132, cy - 170))