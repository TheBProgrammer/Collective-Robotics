import numpy as np
import random
from firefly import Firefly
import matplotlib.pyplot as plt

VISUALIZE = True
NUM_FIREFLIES = 150
L             = 50
RADII         = [0.05, 0.1, 0.5, 1.4]
TIME_STEPS    = 5000
SPAWN_MARGIN  = 0.05

# Visualisation layout
WIN_W       = 1020
WIN_H       = 860

TITLE_H     = 48                    # height of the top title bar

ARENA_X     = 40
ARENA_Y     = TITLE_H + 14
ARENA_W     = 620
ARENA_H     = 620
FPS         = 60
FF_RADIUS   = 2

# Right sidebar (controls / stats)
SIDE_X      = ARENA_X + ARENA_W + 22
SIDE_W      = WIN_W - SIDE_X - 16

BG_COLOR    = (10,  10,  20)
TITLE_BG    = (14,  14,  30)        # slightly lighter for title bar
FLASH_COLOR = (255, 240, 80)
DIM_COLOR   = (110, 110, 110)       # grey when not flashing
PANEL_COLOR = (18,  18,  32)
ACCENT      = (100, 160, 255)
ACCENT2     = (160, 220, 255)

# Speed levels: steps advanced per rendered frame
SPEED_LEVELS = [1, 2, 5, 10, 20, 50]

def calculate_average_neighbors(fireflies, radius):
    total = 0
    for f in fireflies:
        for o in fireflies:
            if f is o:
                continue
            if (f.x - o.x)**2 + (f.y - o.y)**2 < radius**2:
                total += 1
    return total / len(fireflies)


def run_simulation(R):
    """Run one headless simulation; return (positions, flash_states, avg_n, flashing_history)."""
    fireflies = [Firefly(L) for _ in range(NUM_FIREFLIES)]

    # Override positions to keep fireflies away from the border
    for f in fireflies:
        f.x = random.uniform(SPAWN_MARGIN, 1.0 - SPAWN_MARGIN)
        f.y = random.uniform(SPAWN_MARGIN, 1.0 - SPAWN_MARGIN)

    positions = [(f.x, f.y) for f in fireflies]
    avg_n     = calculate_average_neighbors(fireflies, R)

    flash_states     = []
    flashing_history = []

    for _ in range(TIME_STEPS):
        to_correct = []
        for firefly in fireflies:
            if firefly.should_check_neighbors():
                total = flashing = 0
                for other in fireflies:
                    if firefly is other:
                        continue
                    if (firefly.x - other.x)**2 + (firefly.y - other.y)**2 < R**2:
                        total += 1
                        if other.is_flashing():
                            flashing += 1
                if total > 0 and flashing > total / 2:
                    to_correct.append(firefly)

        for f in to_correct:
            f.corrects_clock()
        for f in fireflies:
            f.tick()

        flash_states.append([f.is_flashing() for f in fireflies])
        flashing_history.append(sum(1 for f in fireflies if f.is_flashing()))

    return positions, flash_states, avg_n, flashing_history


# Pygame helpers
def make_glow(color, radius, alpha=200):
    import pygame
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        a = int(alpha * (r / radius) ** 0.6)
        pygame.draw.circle(surf, (*color, min(255, a)), (radius, radius), r)
    return surf


def world_to_screen(x, y):
    sx = int(ARENA_X + x * ARENA_W)
    sy = int(ARENA_Y + (1.0 - y) * ARENA_H)
    return sx, sy


class DiscreteSlider:
    """Horizontal slider that snaps to N discrete positions."""

    def __init__(self, x, y, w, h, labels, font):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.labels   = labels
        self.n        = len(labels)
        self.value    = 0
        self.font     = font
        self.dragging = False

    def _notch_x(self, idx):
        return self.x + int(idx * self.w / (self.n - 1))

    def draw(self, surface):
        import pygame
        cy = self.y + self.h // 2

        pygame.draw.rect(surface, (50, 50, 80),
                         (self.x, cy - 3, self.w, 6), border_radius=3)
        pygame.draw.rect(surface, ACCENT,
                         (self.x, cy - 3, self._notch_x(self.value) - self.x, 6),
                         border_radius=3)

        for i, label in enumerate(self.labels):
            nx  = self._notch_x(i)
            col = ACCENT if i == self.value else (80, 80, 120)
            pygame.draw.circle(surface, col, (nx, cy), 6)
            txt = self.font.render(f"R={label}", True, col)
            surface.blit(txt, (nx - txt.get_width() // 2, cy + 14))

        tx = self._notch_x(self.value)
        pygame.draw.circle(surface, (255, 255, 255), (tx, cy), 10)
        pygame.draw.circle(surface, ACCENT,           (tx, cy),  7)

    def handle_event(self, event):
        import pygame
        cy = self.y + self.h // 2
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.x <= mx <= self.x + self.w and abs(my - cy) < 22:
                self.dragging = True
                self._snap(mx)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._snap(event.pos[0])

    def _snap(self, mx):
        frac = (mx - self.x) / self.w
        self.value = max(0, min(self.n - 1, round(frac * (self.n - 1))))

# Controls legend
CONTROLS = [
    ("[SPACE]",    "Pause / Resume"),
    ("[R]",        "Restart from step 0"),
    ("[↑] / [↓]", "Speed up / Slow down"),
    ("[← →]",     "Step back / forward (paused)"),
    ("[ESC]",      "Quit"),
]

def draw_controls(surface, font, x, y):
    import pygame
    for key, desc in CONTROLS:
        k_surf = font.render(key, True, ACCENT)
        d_surf = font.render(f"  {desc}", True, (160, 160, 200))
        surface.blit(k_surf, (x, y))
        surface.blit(d_surf, (x + k_surf.get_width(), y))
        y += k_surf.get_height() + 2

# Main visualisation window
def visualize_all(sim_data):
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Firefly Synchronisation Visualiser")
    pg_clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Consolas", 22, bold=True)
    font_lg    = pygame.font.SysFont("Consolas", 16, bold=True)
    font_md    = pygame.font.SysFont("Consolas", 13)
    font_sm    = pygame.font.SysFont("Consolas", 12)

    glow_flash = make_glow(FLASH_COLOR, FF_RADIUS * 4, alpha=210)
    glow_dim   = make_glow(DIM_COLOR,   FF_RADIUS * 2, alpha=90)
    gf_off = glow_flash.get_width() // 2
    gd_off = glow_dim.get_width()   // 2

    # Bottom panel
    panel_y = ARENA_Y + ARENA_H + 10
    panel_h = WIN_H - panel_y - 6

    slider = DiscreteSlider(
        x      = ARENA_X + 50,
        y      = panel_y + 46,
        w      = ARENA_W - 100,
        h      = 44,
        labels = [str(r) for r in RADII],
        font   = font_md,
    )

    step           = 0
    paused         = False
    r_idx          = 0
    speed_idx      = 0
    playback_speed = SPEED_LEVELS[speed_idx]

    while True:
        prev_r_idx = r_idx

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    step = 0
                elif event.key == pygame.K_UP:
                    speed_idx = min(speed_idx + 1, len(SPEED_LEVELS) - 1)
                    playback_speed = SPEED_LEVELS[speed_idx]
                elif event.key == pygame.K_DOWN:
                    speed_idx = max(speed_idx - 1, 0)
                    playback_speed = SPEED_LEVELS[speed_idx]
                elif event.key == pygame.K_RIGHT:
                    step = min(step + 1, TIME_STEPS - 1)
                elif event.key == pygame.K_LEFT:
                    step = max(step - 1, 0)

            slider.handle_event(event)

        r_idx = slider.value
        if r_idx != prev_r_idx:
            step = 0

        positions, flash_states, avg_n, flashing_history = sim_data[r_idx]
        R = RADII[r_idx]

        if not paused:
            step = min(step + playback_speed, TIME_STEPS - 1)

        n_flash  = flashing_history[step]
        sync_pct = n_flash / NUM_FIREFLIES * 100

        # Background
        screen.fill(BG_COLOR)

        # Title bar
        pygame.draw.rect(screen, TITLE_BG, (0, 0, WIN_W, TITLE_H))
        pygame.draw.line(screen, (50, 60, 120), (0, TITLE_H - 1), (WIN_W, TITLE_H - 1), 1)

        t1 = font_title.render("Firefly Synchronisation", True, ACCENT2)
        t2 = font_md.render("Local Majority Rule  ·  Task 2a", True, (140, 150, 190))
        screen.blit(t1, (20, (TITLE_H - t1.get_height()) // 2 - 4))
        screen.blit(t2, (20 + t1.get_width() + 18,
                         (TITLE_H - t2.get_height()) // 2 + 4))

        # Active R badge (top-right of title bar)
        badge = font_lg.render(f"R = {R}  |  Avg N = {avg_n:.2f}", True, ACCENT)
        screen.blit(badge, (WIN_W - badge.get_width() - 16,
                            (TITLE_H - badge.get_height()) // 2))

        # Arena border
        pygame.draw.rect(screen, (40, 40, 70),
                         (ARENA_X - 2, ARENA_Y - 2, ARENA_W + 4, ARENA_H + 4), 2)

        # Fireflies
        flash_now = flash_states[step]
        for i, (fx, fy) in enumerate(positions):
            sx, sy = world_to_screen(fx, fy)
            if flash_now[i]:
                screen.blit(glow_flash, (sx - gf_off, sy - gf_off),
                            special_flags=pygame.BLEND_RGBA_ADD)
                pygame.draw.circle(screen, FLASH_COLOR, (sx, sy), FF_RADIUS)
            else:
                screen.blit(glow_dim, (sx - gd_off, sy - gd_off),
                            special_flags=pygame.BLEND_RGBA_ADD)
                pygame.draw.circle(screen, DIM_COLOR, (sx, sy), FF_RADIUS)

        # Bottom panel
        pygame.draw.rect(screen, PANEL_COLOR,
                         (ARENA_X - 5, panel_y, ARENA_W + 10, panel_h),
                         border_radius=8)

        # Sync progress bar
        bar_y = panel_y + 4
        pygame.draw.rect(screen, (40, 40, 65),
                         (ARENA_X, bar_y, ARENA_W, 5), border_radius=3)
        bar_w   = int(ARENA_W * n_flash / NUM_FIREFLIES)
        bar_col = (min(255, 80 + int(175 * n_flash / NUM_FIREFLIES)),
                   max(80,  220 - int(100 * n_flash / NUM_FIREFLIES)), 80)
        pygame.draw.rect(screen, bar_col,
                         (ARENA_X, bar_y, bar_w, 5), border_radius=3)

        # Slider label + widget
        lbl = font_sm.render("Interaction Radius  R →", True, (150, 150, 200))
        screen.blit(lbl, (ARENA_X + 2, panel_y + 14))
        slider.draw(screen)

        # Right sidebar
        pygame.draw.rect(screen, PANEL_COLOR,
                         (SIDE_X - 6, ARENA_Y, SIDE_W + 6, WIN_H - ARENA_Y - 6),
                         border_radius=8)

        sy_cur = ARENA_Y + 14

        # Stats block
        def side_label(text, color=(180, 180, 220)):
            nonlocal sy_cur
            surf = font_sm.render(text, True, color)
            screen.blit(surf, (SIDE_X, sy_cur))
            sy_cur += surf.get_height() + 4

        def side_value(text, color=ACCENT2):
            nonlocal sy_cur
            surf = font_md.render(text, True, color)
            screen.blit(surf, (SIDE_X, sy_cur))
            sy_cur += surf.get_height() + 10

        side_label("STEP")
        side_value(f"{step+1:>5} / {TIME_STEPS}")

        side_label("FLASHING")
        side_value(f"{n_flash:>3} / {NUM_FIREFLIES}  ({sync_pct:.1f}%)")

        side_label("SYNC BAR")

        # Mini vertical sync bar in sidebar
        mini_bar_h = 8
        mini_bar_w = SIDE_W - 8
        pygame.draw.rect(screen, (40, 40, 65),
                         (SIDE_X, sy_cur, mini_bar_w, mini_bar_h), border_radius=4)
        pygame.draw.rect(screen, bar_col,
                         (SIDE_X, sy_cur, int(mini_bar_w * n_flash / NUM_FIREFLIES),
                          mini_bar_h), border_radius=4)
        sy_cur += mini_bar_h + 16

        side_label("SPEED")
        spd_col = (220, 200, 100) if paused else (100, 220, 140)
        state   = "PAUSED" if paused else "PLAYING"
        side_value(f"x{playback_speed}  [{state}]", color=spd_col)

        # Divider
        pygame.draw.line(screen, (50, 55, 90),
                         (SIDE_X, sy_cur), (SIDE_X + SIDE_W - 8, sy_cur), 1)
        sy_cur += 12

        # Controls legend
        ctrl_title = font_sm.render("CONTROLS", True, (150, 150, 200))
        screen.blit(ctrl_title, (SIDE_X, sy_cur))
        sy_cur += ctrl_title.get_height() + 6

        for key, desc in CONTROLS:
            k_surf = font_sm.render(key, True, ACCENT)
            d_surf = font_sm.render(f" {desc}", True, (150, 155, 195))
            screen.blit(k_surf, (SIDE_X, sy_cur))
            # Wrap desc below key if too wide
            if k_surf.get_width() + d_surf.get_width() > SIDE_W - 6:
                sy_cur += k_surf.get_height() + 1
                screen.blit(d_surf, (SIDE_X + 8, sy_cur))
            else:
                screen.blit(d_surf, (SIDE_X + k_surf.get_width(), sy_cur))
            sy_cur += font_sm.get_height() + 5

        pygame.display.flip()
        pg_clock.tick(FPS)


# Entry point
sim_data = []
for R in RADII:
    print(f"Running simulation for R = {R} ...", end=" ", flush=True)
    data = run_simulation(R)
    sim_data.append(data)
    print(f"avg neighbours = {data[2]:.2f}")

if VISUALIZE:
    visualize_all(sim_data)