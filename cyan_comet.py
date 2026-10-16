#!/usr/bin/env python3
"""Cyan Comet — full-colour Python 3 neon meteor arcade for ElbowOS.
Steer the comet, blast falling meteors. A/D or arrows move, Space fire.
"""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/CYAN_COMET_ElbowOS.mp4")
TITLE, HANDLE = "CYAN COMET", "x.com/ElbowOS"

# Neon palette — different from recent runs
VOID = (4, 6, 18)
INK = (10, 14, 36)
CYAN = (0, 255, 230)
MAG = (255, 40, 180)
GOLD = (255, 210, 60)
LIME = (80, 255, 120)
WHITE = (240, 248, 255)
ROSE = (255, 80, 140)
AMBER = (255, 160, 40)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("monospace", 72, bold=True)
        self.font_md = pygame.font.SysFont("monospace", 48, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 32)
        self.reset()

    def reset(self):
        self.ship_x = W // 2
        self.ship_y = H - 280
        self.ship_vx = 0
        self.bullets = []
        self.meteors = []
        self.particles = []
        self.score = 0
        self.lives = 3
        self.frame = 0
        self.spawn_timer = 0
        self.combo = 0
        self.shake = 0

    def spawn_meteor(self):
        x = random.randint(80, W - 80)
        size = random.choice([28, 36, 48, 56])
        speed = random.uniform(4, 9)
        color = random.choice([CYAN, MAG, GOLD, LIME, ROSE])
        self.meteors.append({"x": x, "y": -size, "r": size, "vy": speed, "c": color, "hp": size // 16})

    def update(self, keys, auto=False):
        self.frame += 1
        self.spawn_timer += 1
        if self.spawn_timer > max(8, 22 - self.frame // 90):
            self.spawn_meteor()
            self.spawn_timer = 0

        # Ship control
        if auto:
            # Simple AI: track nearest meteor or center
            target = W // 2
            if self.meteors:
                closest = min(self.meteors, key=lambda m: abs(m["x"] - self.ship_x) + m["y"] * 0.3)
                target = closest["x"]
            self.ship_vx = max(-12, min(12, (target - self.ship_x) * 0.15))
            if self.frame % 6 == 0 and self.meteors:
                self.bullets.append({"x": self.ship_x, "y": self.ship_y - 40, "vy": -18})
        else:
            self.ship_vx = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.ship_vx = -14
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.ship_vx = 14
            if keys[pygame.K_SPACE] and self.frame % 5 == 0:
                self.bullets.append({"x": self.ship_x, "y": self.ship_y - 40, "vy": -18})

        self.ship_x = max(60, min(W - 60, self.ship_x + self.ship_vx))

        # Bullets
        for b in self.bullets[:]:
            b["y"] += b["vy"]
            if b["y"] < -20: self.bullets.remove(b)

        # Meteors
        for m in self.meteors[:]:
            m["y"] += m["vy"]
            if m["y"] > H + 40:
                self.meteors.remove(m)
                self.combo = 0
                self.lives -= 1
                self.shake = 12
                continue
            # Ship collision
            if abs(m["x"] - self.ship_x) < m["r"] + 30 and abs(m["y"] - self.ship_y) < m["r"] + 40:
                self.meteors.remove(m)
                self.lives -= 1
                self.combo = 0
                self.shake = 16
                for _ in range(20):
                    self.particles.append({"x": m["x"], "y": m["y"], "vx": random.uniform(-6,6), "vy": random.uniform(-8,2), "life": 30, "c": ROSE})

        # Bullet hits
        for b in self.bullets[:]:
            for m in self.meteors[:]:
                if abs(b["x"] - m["x"]) < m["r"] + 8 and abs(b["y"] - m["y"]) < m["r"] + 8:
                    self.bullets.remove(b)
                    m["hp"] -= 1
                    self.score += 10
                    self.combo += 1
                    if self.combo > 3: self.score += 5
                    for _ in range(8):
                        self.particles.append({"x": m["x"], "y": m["y"], "vx": random.uniform(-4,4), "vy": random.uniform(-6,1), "life": 18, "c": m["c"]})
                    if m["hp"] <= 0:
                        self.meteors.remove(m)
                        self.score += 25
                        for _ in range(16):
                            self.particles.append({"x": m["x"], "y": m["y"], "vx": random.uniform(-7,7), "vy": random.uniform(-9,3), "life": 25, "c": WHITE})
                    break

        # Particles
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0: self.particles.remove(p)

        if self.shake > 0: self.shake -= 1
        if self.lives <= 0:
            self.reset()
            self.score = max(0, self.score - 100)

    def draw(self, surf):
        ox = random.randint(-self.shake, self.shake) if self.shake else 0
        surf.fill(VOID)
        # Grid lines for neon depth
        for i in range(0, W, 90):
            pygame.draw.line(surf, INK, (i, 0), (i, H), 1)
        for j in range(0, H, 90):
            pygame.draw.line(surf, INK, (0, j), (W, j), 1)

        # Particles
        for p in self.particles:
            a = max(0, p["life"] / 25)
            c = tuple(min(255, int(ch * a)) for ch in p["c"])
            pygame.draw.circle(surf, c, (int(p["x"] + ox), int(p["y"])), 3)

        # Meteors
        for m in self.meteors:
            pygame.draw.circle(surf, m["c"], (int(m["x"] + ox), int(m["y"])), m["r"])
            pygame.draw.circle(surf, WHITE, (int(m["x"] + ox), int(m["y"])), m["r"] // 3, 2)
            # Glow
            pygame.draw.circle(surf, m["c"], (int(m["x"] + ox), int(m["y"])), m["r"] + 6, 1)

        # Bullets
        for b in self.bullets:
            pygame.draw.rect(surf, CYAN, (b["x"] - 4 + ox, b["y"] - 12, 8, 24))
            pygame.draw.rect(surf, WHITE, (b["x"] - 2 + ox, b["y"] - 10, 4, 20))

        # Ship — neon comet triangle
        pts = [(self.ship_x + ox, self.ship_y - 50),
               (self.ship_x - 36 + ox, self.ship_y + 30),
               (self.ship_x + 36 + ox, self.ship_y + 30)]
        pygame.draw.polygon(surf, CYAN, pts)
        pygame.draw.polygon(surf, WHITE, pts, 3)
        pygame.draw.circle(surf, MAG, (int(self.ship_x + ox), self.ship_y + 10), 12)

        # UI
        title = self.font_lg.render(TITLE, True, CYAN)
        surf.blit(title, title.get_rect(center=(W // 2, 90)))
        sc = self.font_md.render(f"SCORE {self.score}", True, GOLD)
        surf.blit(sc, sc.get_rect(center=(W // 2, 170)))
        lives_txt = self.font_sm.render(f"LIVES {self.lives}  COMBO x{self.combo}", True, LIME)
        surf.blit(lives_txt, lives_txt.get_rect(center=(W // 2, H - 120)))
        handle = self.font_sm.render(HANDLE, True, MAG)
        surf.blit(handle, handle.get_rect(center=(W // 2, H - 60)))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
            keys = pygame.key.get_pressed()
            self.update(keys, auto=False)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
            "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        for i in range(frames):
            self.update(None, auto=True)
            self.draw(self.screen)
            raw = pygame.image.tostring(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                break
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
