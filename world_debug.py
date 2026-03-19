import pygame

class WorldDebug:
    def __init__(self):
        self.enabled = True

    def draw_hover_radius(self, surface, cx, cy):
        pygame.draw.circle(surface, (255, 0, 0), (int(cx), int(cy)), 110, 2)

    def draw_button_bounds(self, surface, rects):
        for _, rect in rects:
            pygame.draw.rect(surface, (0, 0, 255), rect, 2)

    def draw_text(self, surface, text, x, y):
        font = pygame.font.SysFont(None, 22)
        t = font.render(text, True, (255, 0, 0))
        surface.blit(t, (x, y))