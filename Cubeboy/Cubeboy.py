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

    def get_input(self):
        dx = 0
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT): dx -= 1
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT): dx += 1
        
        dy = 0
        if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP): dy -= 1
        if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN): dy += 1
        
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
            if abs(player.x - self.x) < 8 and abs(player.y - self.y) < 8:
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

class App:
    def __init__(self):
        pyxel.init(W, H, title="Pyxel Celeste Mini")
        
        # Setup Visuals in Image Bank
        # Wall Tile (1, 0)
        pyxel.images[0].rect(8, 0, 8, 8, 1)
        pyxel.images[0].rectb(8, 0, 8, 8, 5)
        pyxel.images[0].pset(10, 2, 6)
        
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
        self.orbs = [] # Ensure this exists before generate_room
        self.shake = 0
        self.player = Player(W // 2, H // 2)
        self.started = False # Wait for first click to start BGM/Logic
        
        self.generate_room(0, 0)
        
        pyxel.run(self.update, self.draw)

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
        random.seed(f"{rx}_{ry}_celeste")
        
        tm = pyxel.tilemaps[0]
        tm.cls((0, 0))
        
        # Borders with exits
        for x in range(W // TILE_SIZE):
            for y in range(H // TILE_SIZE):
                is_edge = (x == 0 or x == (W // TILE_SIZE) - 1 or 
                           y == 0 or y == (H // TILE_SIZE) - 1)
                mid = (W // TILE_SIZE) // 2
                is_exit = (mid-2 <= x <= mid+1 and (y == 0 or y == (H // TILE_SIZE) - 1)) or \
                          (mid-2 <= y <= mid+1 and (x == 0 or x == (W // TILE_SIZE) - 1))
                
                if is_edge and not is_exit:
                    tm.pset(x, y, (1, 0))

        # Random platforms
        for _ in range(8):
            px = random.randint(1, (W // TILE_SIZE) - 4)
            py = random.randint(1, (H // TILE_SIZE) - 2)
            # SAFETY: Skip platforms that block the middle spawn/path areas
            # Exit holes are at tiles 6-9. Protecting 5-10 range.
            if 5 <= px <= 10 or 5 <= py <= 10:
                continue
            
            pw = random.randint(2, 4)
            for i in range(pw):
                if 0 < px + i < 15:
                    tm.pset(px + i, py, (1, 0))

        # Room-specific orbs
        if (rx, ry) not in self.rooms_data:
            num_orbs = random.randint(1, 2)
            orbs = []
            for _ in range(num_orbs):
                orbs.append(Orb(random.randint(20, W-20), random.randint(20, H-20)))
            self.rooms_data[(rx, ry)] = orbs
        
        self.orbs = self.rooms_data[(rx, ry)]
        random.setstate(state)

    def update(self):
        if not self.started:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) or pyxel.btnp(pyxel.KEY_SPACE) or \
               pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START):
                self.started = True
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
        
        # Screen Transitions
        margin = 4
        changed = False
        if self.player.x < -margin:
            self.room_x -= 1
            self.player.x = W - self.player.width - 12
            changed = True
        elif self.player.x > W - self.player.width + margin:
            self.room_x += 1
            self.player.x = 12
            changed = True
        
        if self.player.y < -margin:
            self.room_y -= 1
            self.player.y = H - self.player.height - 12
            changed = True
        elif self.player.y > H + margin:
            self.room_y += 1
            self.player.y = 12
            changed = True
            
        if changed:
            self.generate_room(self.room_x, self.room_y)
            self.particles = []
        
        for orb in self.orbs:
            if orb.update(self.player):
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
        
        if not self.started:
            pyxel.text(40, 60, "CLICK TO START", pyxel.frame_count % 16)
            return
        
        cam_x, cam_y = 0.0, 0.0
        if self.shake > 0:
            cam_x = float(pyxel.rndf(-self.shake, self.shake))
            cam_y = float(pyxel.rndf(-self.shake, self.shake))
            self.shake -= 1
        pyxel.camera(cam_x, cam_y)
        
        pyxel.bltm(0, 0, 0, 0, 0, W, H)
        for orb in self.orbs: orb.draw()
        for p in self.particles: p.draw()
        self.player.draw()
        
        pyxel.camera()
        pyxel.text(4, 4, f"ROOM: {self.room_x},{self.room_y}", 7)

App()
