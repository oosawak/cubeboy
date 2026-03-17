import pyxel
import random
import os

# Constants
W = 128
H = 128
TILE_SIZE = 8
COLOR_BG = 0
COLOR_WALL = 1
COLOR_PLAYER_READY = 7
COLOR_PLAYER_SPENT = 14
COLOR_PARTICLE = 12
COLOR_ORB = 10
COLOR_SPIKE = 7
COLOR_CRYSTAL = 12
COLOR_MOUNTAIN_1 = 1
COLOR_MOUNTAIN_2 = 13
STATE_START = 0
STATE_PLAY = 1
STATE_BOSS = 2
STATE_GAMEOVER = 3
STATE_GAMECLEAR = 4
STATE_GAMEOVER_SEQ = 5

class Particle:
    def __init__(self, x, y, dx, dy, col, life):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.col = col
        self.life = life

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self):
        pyxel.pset(self.x, self.y, self.col)

class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.width = 6
        self.height = 6
        
        # State
        self.is_on_ground = False
        self.is_on_wall = 0 # -1 left, 1 right, 0 none
        self.can_dash = True
        self.dash_time = 0
        self.dash_dir = (0.0, 0.0)
        
        # Feel
        self.coyote_timer = 0
        self.jump_buffer = 0
        
        # Visuals
        self.stretch_x = 1.0
        self.stretch_y = 1.0
        self.facing = 1 # 1 right, -1 left
        self.is_dead = False

    def get_input(self):
        dx = 0
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            dx -= 1
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            dx += 1
        
        dy = 0
        if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
            dy -= 1
        if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN):
            dy += 1
        
        return dx, dy

    def is_wall(self, x, y):
        # Standardize check with small padding
        x1 = int(x // 8)
        y1 = int(y // 8)
        x2 = int((x + self.width - 0.1) // 8)
        y2 = int((y + self.height - 0.1) // 8)
        
        for ty in range(y1, y2 + 1):
            if not (0 <= ty < 16): continue # Allow passing vertical bounds
            for tx in range(x1, x2 + 1):
                if not (0 <= tx < 16): continue # Allow passing horizontal bounds
                if pyxel.tilemaps[0].pget(tx, ty) == (1, 0):
                    return True
        return False

    def resolve_overlap(self):
        # If stuck, search for the nearest free pixel in a spiral
        if self.is_wall(self.x, self.y):
            for r in range(1, 16):
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        if not self.is_wall(self.x + dx, self.y + dy):
                            self.x += dx
                            self.y += dy
                            return
                    
    def update(self, particles):
        # Ensure we stay out of walls before moving
        self.resolve_overlap()
        # Timers
        if self.coyote_timer > 0: self.coyote_timer -= 1
        if self.jump_buffer > 0: self.jump_buffer -= 1

        # Dash logic
        if self.dash_time > 0:
            self.vx = self.dash_dir[0] * 5
            self.vy = self.dash_dir[1] * 5
            self.dash_time -= 1
            # Particles
            particles.append(Particle(self.x + 3, self.y + 3, pyxel.rndf(-1, 1), pyxel.rndf(-1, 1), COLOR_PARTICLE, 10))
            if self.dash_time == 0:
                self.vx *= 0.5
                self.vy *= 0.5
        else:
            # Horizontal movement
            dx, dy = self.get_input()
            
            if dx != 0:
                # Snappier acceleration
                target_vx = dx * 2.5
                self.vx += (target_vx - self.vx) * 0.2
                self.facing = dx
            else:
                self.vx *= 0.7
            
            # Gravity
            if self.is_on_wall != 0 and self.vy > 0:
                self.vy = pyxel.clamp(self.vy + 0.1, 0, 0.8) # Wall slide
            else:
                grav = 0.3 if (pyxel.btn(pyxel.KEY_SPACE) or pyxel.btn(pyxel.KEY_C)) and self.vy < 0 else 0.5
                self.vy += grav
            
            # Jump Input Buffer
            if (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_Z) or 
                pyxel.btnp(pyxel.KEY_W) or pyxel.btnp(pyxel.KEY_UP) or
                pyxel.btnp(pyxel.KEY_C) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):
                self.jump_buffer = 4
            
            # Jump Logic
            if self.jump_buffer > 0:
                if self.coyote_timer > 0:
                    self.vy = -4.5
                    self.stretch_x = 0.6
                    self.stretch_y = 1.4
                    self.coyote_timer = 0
                    self.jump_buffer = 0
                    pyxel.play(3, 0) # Jump sound
                elif self.is_on_wall != 0:
                    self.vy = -4.2
                    self.vx = -self.is_on_wall * 3.5
                    self.stretch_x = 0.6
                    self.stretch_y = 1.4
                    self.jump_buffer = 0
                    pyxel.play(3, 0) # Jump sound
            
            # Dash Input
            if (pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.KEY_V) or 
                pyxel.btnp(pyxel.KEY_LCTRL) or pyxel.btnp(pyxel.KEY_RCTRL) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)) and self.can_dash:
                idx, idy = self.get_input()
                if idx == 0 and idy == 0: idx = self.facing
                
                mag = pyxel.sqrt(idx*idx + idy*idy)
                self.dash_dir = (idx / mag, idy / mag)
                self.dash_time = 6
                self.can_dash = False
                self.vy = 0
                pyxel.play(3, 1) # Dash sound

        # Collision & Movement (Axis Separated)
        # Move X
        old_x = self.x
        steps_x = int(abs(self.vx) / 0.5) + 1
        step_x = self.vx / steps_x
        for _ in range(steps_x):
            if not self.is_wall(self.x + step_x, self.y):
                self.x += step_x
            else:
                self.vx = 0
                break
        
        # Move Y
        old_y = self.y
        steps_y = int(abs(self.vy) / 0.5) + 1
        step_y = self.vy / steps_y
        for _ in range(steps_y):
            if not self.is_wall(self.x, self.y + step_y):
                self.y += step_y
            else:
                self.vy = 0
                break
        
        # Check ground (1 pixel below)
        self.is_on_ground = self.is_wall(self.x, self.y + 1)
        
        if self.is_on_ground:
            self.coyote_timer = 5
            self.can_dash = True
            if old_y < self.y: # Just landed
                self.stretch_x = 1.4
                self.stretch_y = 0.6
        
        # Check walls (1 pixel side)
        if self.is_wall(self.x + 1, self.y): self.is_on_wall = 1
        elif self.is_wall(self.x - 1, self.y): self.is_on_wall = -1
        else: self.is_on_wall = 0
        
        # Transitions (handled by App)
        pass
        
        # Visual Polish - Recover stretch
        self.stretch_x += (1.0 - self.stretch_x) * 0.2
        self.stretch_y += (1.0 - self.stretch_y) * 0.2
        
        # Death Check (Spikes at (2, 0))
        if pyxel.tilemaps[0].pget(int((self.x + 3)//8), int((self.y + 3)//8)) == (2, 0):
            self.is_dead = True

    def draw(self):
        u = 0 if self.can_dash else 16
        w = 8 if self.facing > 0 else -8
        
        # Squash and stretch application
        sw = 8 * self.stretch_x
        sh = 8 * self.stretch_y
        
        # Idle animation (only for body)
        if self.is_on_ground and abs(self.vx) < 0.2:
            sh += pyxel.sin(pyxel.frame_count * 15) * 0.4
        
        # Draw player sprite
        color = COLOR_PLAYER_READY if self.can_dash else COLOR_PLAYER_SPENT
        pyxel.rect(self.x + (self.width - sw)/2, self.y + (self.height - sh), sw, sh, color)
        
        # Eye (Position stays fixed regardless of idle animation)
        eyex = self.x + (4 if self.facing > 0 else 0)
        pyxel.pset(eyex, self.y + 1, 0)

class Orb:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
        self.timer = 0

    def update(self, player):
        if not self.active:
            self.timer += 1
            if self.timer > 90:
                self.active = True
                self.timer = 0
        else:
            # Enhanced collision: Center-to-center distance check with larger radius
            dx = (player.x + 3) - (self.x + 4)
            dy = (player.y + 3) - (self.y + 4)
            dist = pyxel.sqrt(dx*dx + dy*dy)
            if dist < 10: # More generous threshold for wall accessibility
                if not player.can_dash:
                    player.can_dash = True
                    self.active = False
                    self.timer = 0
                    return True
        return False

    def draw(self):
        if self.active:
            t = pyxel.frame_count // 4
            off = pyxel.sin(t * 20) * 2
            pyxel.circ(self.x + 4, self.y + 4 + off, 3, COLOR_ORB)
            pyxel.circb(self.x + 4, self.y + 4 + off, 3, 7)
        else:
            pyxel.circb(self.x + 4, self.y + 4, 2, 5)

class Boss:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w = 24
        self.h = 24
        self.speed = 0.8
        self.active = False
        self.color = 8 

    def update(self, player, tm):
        # Move towards player
        dx = (player.x + 3) - (self.x + self.w/2)
        dy = (player.y + 3) - (self.y + self.h/2)
        dist = pyxel.sqrt(dx*dx + dy*dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        
        # Destroy tiles on contact
        tx_start = int(self.x // 8)
        ty_start = int(self.y // 8)
        tx_end = int((self.x + self.w) // 8)
        ty_end = int((self.y + self.h) // 8)
        
        for ty in range(ty_start, ty_end + 1):
            for tx in range(tx_start, tx_end + 1):
                if 0 <= tx < 16 and 0 <= ty < 16:
                    if pyxel.tilemaps[0].pget(tx, ty) == (1, 0):
                        pyxel.tilemaps[0].pset(tx, ty, (0, 0))

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, self.color)
        pyxel.rectb(self.x, self.y, self.w, self.h, 7)
        # Eyes
        pyxel.rect(self.x + 4, self.y + 6, 4, 4, 7)
        pyxel.rect(self.x + 16, self.y + 6, 4, 4, 7)

class App:
    def __init__(self):
        pyxel.init(W, H, title="CubeBoy")
        
        # Setup Visuals in Image Bank
        # Wall Tile (1, 0) - Solid dark blue with simple detail
        pyxel.images[0].rect(8, 0, 8, 8, 1)
        pyxel.images[0].pset(10, 2, 5) # Distant grey detail instead of border
        
        # Ice Spike (2, 0) - Concept-accurate crystalline spikes
        # Clear the tile area
        pyxel.images[0].rect(16, 0, 8, 8, 0)
        # Crystal 1 (Center-Left)
        pyxel.images[0].tri(16, 7, 18, 2, 20, 7, 12) # Blue base
        pyxel.images[0].line(18, 3, 18, 7, 7)         # White core
        # Crystal 2 (Center-Right)
        pyxel.images[0].tri(19, 7, 21, 1, 23, 7, 6)  # Purple base
        pyxel.images[0].line(21, 2, 21, 7, 7)         # White core
        # Crystal 3 (Edge-Right)
        pyxel.images[0].tri(21, 7, 22, 3, 23, 7, 12) # Blue base highlight
        
        # Setup Sounds
        pyxel.sounds[0].set("a3a2c1", "p", "7", "v", 5) # Jump
        pyxel.sounds[1].set("c3c3c3", "n", "7", "f", 5) # Dash
        pyxel.sounds[2].set("e3e3", "t", "7", "v", 5) # Orb
        
        # BGM Setup
        self.bgm_files = [
            "BGM/ComfyUI_00001_.mp3",
            "BGM/ComfyUI_00002_.mp3",
            "BGM/ComfyUI_00003_.mp3",
            "BGM/ComfyUI_00004_.mp3"
        ]
        self.bgm_timer = 0
        self.bgm_idx = 0 # 0 or 1
        self.bgm_channels = [0, 1]
        self.bgm_sounds = [62, 63]
        self.bgm_volumes = [0.0, 0.0]
        self.target_volumes = [0.0, 0.0]

        self.room_x = 0
        self.room_y = 0
        self.rooms_data = {}
        self.particles = []
        self.orbs = []
        self.shake = 0
        self.collected_orbs = 0
        self.collected_rooms = set()  # Track which rooms have had their orb collected
        self.boss_countdown = 0
        self.death_seq_timer = 0
        self.state = STATE_PLAY
        self.player = Player(W // 2, H // 2)
        self.boss = Boss(-100, -100)
        
        self.generate_room(0, 0)
        
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.room_x = 0
        self.room_y = 0
        self.rooms_data = {}
        self.particles = []
        self.orbs = []
        self.shake = 0
        self.collected_orbs = 0
        self.collected_rooms = set()
        self.boss_countdown = 0
        self.death_seq_timer = 0
        
        self.state = STATE_PLAY
        self.player = Player(W // 2, H // 2)
        self.boss = Boss(-100, -100)
        self.generate_room(0, 0)

    def play_random_bgm(self):
        try:
            # Alternate index
            old_idx = self.bgm_idx
            self.bgm_idx = 1 - self.bgm_idx
            
            base_dir = os.path.dirname(__file__)
            bgm_rel = random.choice(self.bgm_files)
            bgm_path = os.path.join(base_dir, bgm_rel)
            
            snd_slot = self.bgm_sounds[self.bgm_idx]
            ch_idx = self.bgm_channels[self.bgm_idx]
            
            # Load and Start (at 0 volume)
            if os.path.exists(bgm_path):
                pyxel.sounds[snd_slot].pcm(bgm_path)
            else:
                pyxel.sounds[snd_slot].pcm(bgm_rel)
                
            pyxel.channels[ch_idx].gain = 0.0
            pyxel.play(ch_idx, snd_slot, loop=False)
            
            # Set Target Volumes for crossfade
            self.target_volumes[self.bgm_idx] = 0.4 # Fade in
            self.target_volumes[old_idx] = 0.0 # Fade out
            
            dur = pyxel.sounds[snd_slot].total_sec()
            self.bgm_timer = int(dur * 30) if dur else 30 * 120
        except Exception as e:
            print(f"BGM Error: {e}")
            self.bgm_timer = 30 * 5

    def generate_room(self, rx, ry):
        import random
        state = random.getstate()
        random.seed(f"{rx}_{ry}_cubeboy")
        
        tm = pyxel.tilemaps[0]
        tm.cls((0, 0))
        
        # Borders with exits
        for x in range(W // TILE_SIZE):
            for y in range(H // TILE_SIZE):
                is_edge = (x == 0 or x == (W // TILE_SIZE) - 1 or 
                           y == 0 or y == (H // TILE_SIZE) - 1)
                mid = (W // TILE_SIZE) // 2
                # Narrow exit: 2 tiles wide (7, 8)
                is_exit = (7 <= x <= 8 and (y == 0 or y == (H // TILE_SIZE) - 1)) or \
                          (7 <= y <= 8 and (x == 0 or x == (W // TILE_SIZE) - 1))
                
                if is_edge and not is_exit:
                    tm.pset(x, y, (1, 0))

        # Extreme grid-based platform generation (6x6 internal = 36 slots)
        density = random.uniform(0.7, 0.9)
        for gy in range(1, 7):
            for gx in range(1, 7):
                if random.random() < density:
                    px = gx * 2 
                    py = gy * 2 
                    
                    type = random.randint(0, 3)
                    size = random.randint(2, 3) 
                    
                    if type == 0: # Horizontal
                        for i in range(size):
                            if 0 < px + i < 15: tm.pset(px + i, py, (1, 0))
                    elif type == 1: # Vertical
                        for i in range(size):
                            if 0 < py + i < 15: tm.pset(px, py + i, (1, 0))
                    elif type == 2: # L-Shape
                        for i in range(size):
                            if 0 < px + i < 15: tm.pset(px + i, py, (1, 0))
                        for i in range(size):
                            if 0 < py + i < 15: tm.pset(px, py + i, (1, 0))
                    else: # Island
                        tm.pset(px, py, (1, 0))
                
        # FINAL PASS: Ensure exits and Respawn are ALWAYS clear
        # Narrow exits (2 tiles wide) + 1 tile buffer
        for i in range(7, 9):
            for j in range(0, 2): tm.pset(i, j, (0, 0)) # Top
            for j in range(14, 16): tm.pset(i, j, (0, 0)) # Bottom
        for j in range(7, 9):
            for i in range(0, 2): tm.pset(i, j, (0, 0)) # Left
            for i in range(14, 16): tm.pset(i, j, (0, 0)) # Right

        # SAFE ZONE: Center (W//2, H//2) for respawn
        for i in range(6, 10):
            for j in range(6, 10):
                tm.pset(i, j, (0, 0))

        # MOON SANCTUARY: Top-right corner (approx 3x3 tiles) to protect the moon
        # Moon is drawn at (100, 15) with radius 10, so clearing (12, 1) to (14, 3) 
        for i in range(11, 15):
            for j in range(1, 4):
                tm.pset(i, j, (0, 0))

        # Add Spikes and Crystals with improved placement
        for _ in range(15):
            tx, ty = random.randint(1, 14), random.randint(1, 14)
            # Avoid exit lanes, center safe zone, and MOON SANCTUARY
            if (tx in [7, 8]) or (ty in [7, 8]) or (6 <= tx <= 9 and 6 <= ty <= 9) or (tx >= 11 and ty <= 3):
                continue

            if tm.pget(tx, ty) == (0, 0):
                # Check adjacency to wall for natural look
                adj_wall = False
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    if tm.pget(tx+dx, ty+dy) == (1, 0):
                        adj_wall = True
                        break
                if adj_wall:
                    # Only spikes now
                    tm.pset(tx, ty, (2, 0)) # Spike

        # Room-specific orbs - Reachable placement
        if (rx, ry) not in self.rooms_data:
            orbs = []
            # NO ORBS IN START ROOM AND NO ORBS IF ALREADY COLLECTED
            if not (rx == 0 and ry == 0) and (rx, ry) not in self.collected_rooms: 
                num_orbs = 1 # EXACTLY ONE PER ROOM
                for _ in range(num_orbs):
                    # Try multiple times to find a good spot
                    for _ in range(20):
                        ox, oy = random.randint(24, 104), random.randint(24, 104)
                    tx, ty = ox // 8, oy // 8
                    # Avoid walls and center zone
                    if tm.pget(tx, ty) == (0, 0) and not (6 <= tx <= 9 and 6 <= ty <= 9):
                        # Reachability: Near a wall
                        near_wall = False
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                if (0 <= tx+dx < 16 and 0 <= ty+dy < 16 and 
                                    tm.pget(tx+dx, ty+dy) == (1, 0)):
                                    near_wall = True
                                    break
                        if near_wall:
                            orbs.append(Orb(ox, oy))
                            break
            # Fallback if no good spot found (except start room)
            if not orbs and not (rx == 0 and ry == 0): 
                orbs.append(Orb(W//2, H//2))
            self.rooms_data[(rx, ry)] = orbs
        
        self.orbs = self.rooms_data[(rx, ry)]
        random.setstate(state)

    def update(self):
        if self.state == STATE_START:
            if (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_Z) or 
                pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.KEY_RETURN) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START)):
                self.state = STATE_PLAY
                self.play_random_bgm()
            return

        if self.state == STATE_GAMEOVER or self.state == STATE_GAMECLEAR:
            if (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_Z) or 
                pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.KEY_RETURN) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START)):
                self.reset_game()
                self.play_random_bgm()
            return

        # BGM Crossfade & Timer
        for i in range(2):
            if self.bgm_volumes[i] < self.target_volumes[i]:
                self.bgm_volumes[i] = min(self.bgm_volumes[i] + 0.005, self.target_volumes[i])
            elif self.bgm_volumes[i] > self.target_volumes[i]:
                self.bgm_volumes[i] = max(self.bgm_volumes[i] - 0.005, self.target_volumes[i])
            
            pyxel.channels[self.bgm_channels[i]].gain = self.bgm_volumes[i]
            if self.bgm_volumes[i] == 0:
                pyxel.stop(self.bgm_channels[i])

        if self.bgm_timer > 0:
            self.bgm_timer -= 1
            if self.bgm_timer <= 0:
                self.play_random_bgm()
        elif pyxel.play_pos(self.bgm_channels[self.bgm_idx]) is None:
            self.play_random_bgm()

        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
            
        self.player.update(self.particles)
        
        if self.state == STATE_GAMEOVER_SEQ:
            self.death_seq_timer -= 1
            self.shake = 5
            self.boss.update(self.player, pyxel.tilemaps[0]) # Keep boss moving for drama
            # Continuous shattering particles
            for _ in range(3):
                self.particles.append(Particle(self.player.x+2 + pyxel.rndf(-4, 4), self.player.y+2 + pyxel.rndf(-4, 4), 
                                               pyxel.rndf(-2, 2), pyxel.rndf(-2, 2), 
                                               random.choice([COLOR_PLAYER_READY, COLOR_PARTICLE, 6]), 20))
            for p in self.particles: p.update()
            if self.death_seq_timer <= 0:
                self.state = STATE_GAMEOVER
            return

        if self.player.is_dead:
            # Hazard death (spikes, etc.): immediate reset with burst
            self.shake = 10
            pyxel.play(3, 1)
            for _ in range(15):
                self.particles.append(Particle(self.player.x+4, self.player.y+4, pyxel.rndf(-3, 3), pyxel.rndf(-3, 3), COLOR_PARTICLE, 20))
            # Reset player
            self.player.x, self.player.y = W//2, H//2
            self.player.vx, self.player.vy = 0, 0
            self.player.is_dead = False
        
        # Room(0,0) Exit Reach check
        if self.state == STATE_BOSS and self.room_x == 0 and self.room_y == 0:
            if abs(self.player.x - W//2) < 8 and abs(self.player.y - H//2) < 8:
                self.state = STATE_GAMECLEAR
                return

        # Boss Logic
        if self.state == STATE_BOSS:
            if self.boss_countdown > 0:
                self.boss_countdown -= 1
                if self.boss_countdown == 0:
                    # Spawn Boss at a distance
                    self.boss.x = self.player.x - 64
                    self.boss.y = self.player.y - 64
            else:
                self.boss.update(self.player, pyxel.tilemaps[0])
                # Collision
                if (self.player.x < self.boss.x + self.boss.w and
                    self.player.x + self.player.width > self.boss.x and
                    self.player.y < self.boss.y + self.boss.h and
                    self.player.y + self.player.height > self.boss.y):
                    self.player.is_dead = True
                    self.shake = 15
                    self.state = STATE_GAMEOVER_SEQ
                    self.death_seq_timer = 150 # 5 seconds at 30fps
                    pyxel.play(3, 1) # Death sound
                    for _ in range(40):
                        self.particles.append(Particle(self.player.x+2, self.player.y+2, pyxel.rndf(-4, 4), pyxel.rndf(-4, 4), COLOR_PLAYER_READY, 30))
                    return
            

        # Screen Transitions
        margin = 4
        changed = False
        if self.player.x < -margin:
            self.room_x -= 1
            self.player.x = W - self.player.width - 12
            self.boss.x += W # Shift boss with room
            changed = True
        elif self.player.x > W - self.player.width + margin:
            self.room_x += 1
            self.player.x = 12
            self.boss.x -= W # Shift boss with room
            changed = True
        
        if self.player.y < -margin:
            self.room_y -= 1
            self.player.y = H - self.player.height - 12
            self.boss.y += H # Shift boss with room
            changed = True
        elif self.player.y > H + margin:
            self.room_y += 1
            self.player.y = 12
            self.boss.y -= H # Shift boss with room
            changed = True
            
        if changed:
            self.generate_room(self.room_x, self.room_y)
            self.particles = []
        
        if self.shake > 0:
            self.shake -= 1
        
        for orb in self.orbs:
            if orb.update(self.player):
                self.collected_orbs += 1
                self.collected_rooms.add((self.room_x, self.room_y)) # Persistence tracking
                if self.collected_orbs >= 3 and self.state == STATE_PLAY:
                    self.state = STATE_BOSS
                    self.boss_countdown = 300 # 10 seconds at 30fps
                self.shake = 2
                pyxel.play(3, 2)
                for _ in range(5):
                    self.particles.append(Particle(orb.x+4, orb.y+4, pyxel.rndf(-2, 2), pyxel.rndf(-2, 2), COLOR_ORB, 15))

        for i in range(len(self.particles)-1, -1, -1):
            self.particles[i].update()
            if self.particles[i].life <= 0:
                self.particles.pop(i)
                
        if self.player.dash_time == 5:
            self.shake = 4

    def draw(self):
        pyxel.cls(COLOR_BG)
        
        if self.state == STATE_START:
            pyxel.text(40, 60, "CLICK TO START", pyxel.frame_count % 16)
            return

        if self.state == STATE_GAMEOVER:
            pyxel.text(46, 60, "GAME OVER", 8)
            pyxel.text(26, 75, "PRESS SPACE TO RETRY", 7)
            return

        if self.state == STATE_GAMECLEAR:
            pyxel.text(42, 60, "GAME CLEAR!", 10)
            pyxel.text(30, 75, "CONGRATULATIONS!", 7)
            pyxel.text(26, 85, "PRESS SPACE TO RETRY", 6)
            return
            pyxel.text(48, 60, "GAME CLEAR!", 10)
            pyxel.text(32, 70, "CONGRATULATIONS!", 7)
            return
        
        cam_x, cam_y = 0.0, 0.0
        if self.shake > 0:
            cam_x = float(pyxel.rndf(-self.shake, self.shake))
            cam_y = float(pyxel.rndf(-self.shake, self.shake))
        pyxel.camera(cam_x, cam_y)

        # Background (DRAW AFTER CLS, BEFORE BLTM)
        random.seed(f"{self.room_x}_{self.room_y}_bg")
        # Stars (REMOVED as per user request)
        # Moon
        pyxel.circ(105, 15, 6, 7)
        pyxel.circ(103, 13, 5, COLOR_BG)
        
        # Mountains (Vast Dark Silhouettes)
        for layer in range(3):
            random.seed(f"{self.room_x}_{self.room_y}_mtn_{layer}")
            # Use darker colors distinct from Wall (1): 2 (Dark Purple), 5 (Dark Grey)
            col = [2, 5, 2][layer] 
            h_max = [15, 28, 45][layer] # Significantly taller
            
            # Very wide steps for broad mountains
            step_w = 32
            last_h = random.randint(h_max-10, h_max+10)
            for x in range(0, W + step_w, step_w):
                next_h = random.randint(h_max-10, h_max+10)
                # Curve the transition for a very smooth organic feel
                for i in range(step_w):
                    t = i / step_w
                    smooth_t = t * t * (3 - 2 * t)
                    h = int(last_h * (1 - smooth_t) + next_h * smooth_t)
                    # Use overdraw (+10) to ensure no gap at the bottom edge
                    pyxel.rect(x + i, H - h, 1, h + 10, col)
                last_h = next_h

        pyxel.bltm(0, 0, 0, 0, 0, W, H, 0) # treated 0 as transparent
        
        # Special Exit at 0,0
        if self.state == STATE_BOSS and self.room_x == 0 and self.room_y == 0:
            pyxel.circ(W//2, H//2, 8 + pyxel.sin(pyxel.frame_count*10)*2, 11)
            pyxel.circ(W//2, H//2, 4, 7)
            pyxel.text(W//2-10, H//2-12, "EXIT", 7)

        for orb in self.orbs: orb.draw()
        for p in self.particles: p.draw()
        if not self.player.is_dead:
            self.player.draw()
        if self.state in [STATE_BOSS, STATE_GAMEOVER_SEQ]:
            self.boss.draw()
        
        pyxel.camera()
        # HUD
        color = 7 if self.collected_orbs < 3 else 10
        pyxel.text(4, 4, f"ORBS: {self.collected_orbs}/3", color)
        pyxel.text(4, 12, f"ROOM: {self.room_x},{self.room_y}", 13)
        if self.state == STATE_BOSS:
            if self.boss_countdown > 0:
                sec = self.boss_countdown // 30
                # Move to bottom: y=116 for text, y=122 for bar
                pyxel.text(40, 116, f"BOSS IN: {sec}s", 8)
                pyxel.rect(W//2-20, 122, 40 * (self.boss_countdown/300), 2, 8)
            else:
                pyxel.text(40, 120, "WARNING: BOSS ACTIVE!", 8)

App()
