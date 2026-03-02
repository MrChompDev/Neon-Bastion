import pygame
import math
import random
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# Colors (Neon theme)
BLACK = (5, 5, 15)
NEON_BLUE = (0, 150, 255)
NEON_PURPLE = (200, 50, 255)
NEON_YELLOW = (255, 255, 50)
NEON_RED = (255, 50, 50)
NEON_GREEN = (50, 255, 150)
NEON_CYAN = (0, 255, 255)
DARK_BLUE = (10, 20, 40)
GRID_COLOR = (20, 30, 50)

# Game States
class GameState(Enum):
    MENU = 0
    PLAYING = 1
    WON = 2
    LOST = 3
    SETTINGS = 4
    LORE = 5

# Sound System - Generate procedural sounds using MIDI notes
class SoundGenerator:
    """Generate procedural game sounds using MIDI note frequencies"""
    
    @staticmethod
    def midi_to_freq(midi_note):
        """Convert MIDI note number to frequency"""
        return 440 * (2 ** ((midi_note - 69) / 12))
    
    @staticmethod
    def generate_tone(frequency, duration, volume=0.3, sample_rate=22050):
        """Generate a simple sine wave tone"""
        num_samples = int(duration * sample_rate)
        wave = np.sin(2 * np.pi * frequency * np.linspace(0, duration, num_samples))
        
        # Apply envelope (attack, decay)
        envelope = np.ones(num_samples)
        attack_samples = int(0.01 * sample_rate)
        decay_samples = int(0.1 * sample_rate)
        
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        if decay_samples > 0 and decay_samples < num_samples:
            envelope[-decay_samples:] = np.linspace(1, 0, decay_samples)
        
        wave = wave * envelope * volume
        
        # Convert to 16-bit
        wave = np.int16(wave * 32767)
        
        # Stereo
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    @staticmethod
    def generate_background_music():
        """Generate atmospheric background music loop"""
        sample_rate = 22050
        duration = 8.0  # 8 second loop
        num_samples = int(duration * sample_rate)
        
        # Chord progression: Am - F - C - G (in low octave for atmosphere)
        # A2, F2, C2, G2
        chords = [
            [45, 52, 57],  # Am (A2, E3, A3)
            [41, 48, 53],  # F (F2, C3, F3)
            [36, 43, 48],  # C (C2, G2, C3)
            [43, 47, 50]   # G (G2, B2, D3)
        ]
        
        wave = np.zeros(num_samples)
        chord_duration = duration / len(chords)
        
        for i, chord in enumerate(chords):
            start_sample = int(i * chord_duration * sample_rate)
            end_sample = int((i + 1) * chord_duration * sample_rate)
            chunk_samples = end_sample - start_sample
            
            t = np.linspace(0, chord_duration, chunk_samples)
            
            # Mix the chord notes
            for note in chord:
                freq = SoundGenerator.midi_to_freq(note)
                wave[start_sample:end_sample] += np.sin(2 * np.pi * freq * t) * 0.15
        
        # Add subtle high melody
        melody_notes = [69, 67, 65, 64]  # A4, G4, F4, E4
        for i, note in enumerate(melody_notes):
            start_sample = int(i * chord_duration * sample_rate)
            end_sample = int((i + 1) * chord_duration * sample_rate)
            chunk_samples = end_sample - start_sample
            
            t = np.linspace(0, chord_duration, chunk_samples)
            freq = SoundGenerator.midi_to_freq(note)
            
            # Fade in/out envelope for melody
            envelope = np.sin(np.pi * t / chord_duration)
            wave[start_sample:end_sample] += np.sin(2 * np.pi * freq * t) * envelope * 0.08
        
        # Normalize and fade loop points
        wave = wave / np.max(np.abs(wave)) * 0.3
        
        # Fade in/out at loop points
        fade_samples = int(0.1 * sample_rate)
        wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        wave = np.int16(wave * 32767)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    @staticmethod
    def laser_sound():
        """Laser shot - quick high pitch (E6)"""
        freq = SoundGenerator.midi_to_freq(88)  # E6
        return SoundGenerator.generate_tone(freq, 0.08, volume=0.15)
    
    @staticmethod
    def plasma_sound():
        """Plasma cannon - lower, powerful (C4)"""
        freq = SoundGenerator.midi_to_freq(60)  # C4
        return SoundGenerator.generate_tone(freq, 0.15, volume=0.25)
    
    @staticmethod
    def shock_sound():
        """Shock zap - mid range (A5)"""
        freq = SoundGenerator.midi_to_freq(81)  # A5
        return SoundGenerator.generate_tone(freq, 0.1, volume=0.12)
    
    @staticmethod
    def enemy_death_sound():
        """Enemy death - descending tone"""
        sample_rate = 22050
        duration = 0.2
        num_samples = int(duration * sample_rate)
        
        # Descending frequency from C5 to C3
        start_freq = SoundGenerator.midi_to_freq(72)  # C5
        end_freq = SoundGenerator.midi_to_freq(48)    # C3
        
        freqs = np.linspace(start_freq, end_freq, num_samples)
        wave = np.sin(2 * np.pi * np.cumsum(freqs) / sample_rate)
        
        # Decay envelope
        envelope = np.linspace(1, 0, num_samples)
        wave = wave * envelope * 0.2
        
        wave = np.int16(wave * 32767)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    @staticmethod
    def wave_start_sound():
        """Wave start - low boom (C2)"""
        freq = SoundGenerator.midi_to_freq(36)  # C2
        return SoundGenerator.generate_tone(freq, 0.4, volume=0.3)
    
    @staticmethod
    def core_hit_sound():
        """Core damage - alarm (A4 + E4 dissonance)"""
        sample_rate = 22050
        duration = 0.3
        num_samples = int(duration * sample_rate)
        
        freq1 = SoundGenerator.midi_to_freq(69)  # A4
        freq2 = SoundGenerator.midi_to_freq(64)  # E4
        
        t = np.linspace(0, duration, num_samples)
        wave1 = np.sin(2 * np.pi * freq1 * t)
        wave2 = np.sin(2 * np.pi * freq2 * t)
        
        wave = (wave1 + wave2) / 2
        
        # Pulse envelope
        pulse = (np.sin(2 * np.pi * 8 * t) + 1) / 2
        envelope = np.linspace(1, 0.3, num_samples)
        
        wave = wave * envelope * pulse * 0.25
        
        wave = np.int16(wave * 32767)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    @staticmethod
    def upgrade_sound():
        """Upgrade - ascending arpeggio"""
        sample_rate = 22050
        duration = 0.3
        
        # C Major chord arpeggio: C4, E4, G4, C5
        notes = [60, 64, 67, 72]
        note_duration = duration / len(notes)
        
        full_wave = np.array([])
        
        for note in notes:
            freq = SoundGenerator.midi_to_freq(note)
            num_samples = int(note_duration * sample_rate)
            t = np.linspace(0, note_duration, num_samples)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.linspace(0.8, 0, num_samples)
            wave = wave * envelope
            full_wave = np.concatenate([full_wave, wave])
        
        full_wave = full_wave * 0.2
        full_wave = np.int16(full_wave * 32767)
        stereo_wave = np.column_stack((full_wave, full_wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    @staticmethod
    def menu_click_sound():
        """Menu click - short blip"""
        freq = SoundGenerator.midi_to_freq(72)  # C5
        return SoundGenerator.generate_tone(freq, 0.05, volume=0.2)

# Pre-generate sounds at startup
SOUNDS = {
    'laser': None,
    'plasma': None,
    'shock': None,
    'sniper': None,
    'flak': None,
    'tesla': None,
    'death': None,
    'wave': None,
    'core_hit': None,
    'upgrade': None,
    'menu_click': None,
    'music': None
}

# Music tracks (MP3)
MUSIC_TRACKS = {
    'menu': None,
    'game': None,
    'win': None,
    'lose': None
}

# Music channel
MUSIC_CHANNEL = None

def load_music():
    """Load MP3 music files if they exist"""
    music_paths = {
        'menu': 'Assets/Music/MainOST.mp3',
        'game': 'Assets/Music/MainOST.mp3',  # Same for now
        'win': 'Assets/Music/WinOST.mp3',
        'lose': 'Assets/Music/DeadOST.mp3'
    }
    
    for key, path in music_paths.items():
        try:
            # Try to load from current directory
            MUSIC_TRACKS[key] = path
            # Test if file exists
            pygame.mixer.music.load(path)
            print(f"Loaded {key} music: {path}")
        except:
            try:
                # Try to load from uploads directory
                upload_path = f'/mnt/user-data/uploads/{path}'
                MUSIC_TRACKS[key] = upload_path
                pygame.mixer.music.load(upload_path)
                print(f"Loaded {key} music from uploads: {upload_path}")
            except:
                print(f"Music file not found: {path}, using procedural music")
                MUSIC_TRACKS[key] = None

def init_sounds():
    """Initialize all game sounds"""
    global MUSIC_CHANNEL
    try:
        SOUNDS['laser'] = SoundGenerator.laser_sound()
        SOUNDS['plasma'] = SoundGenerator.plasma_sound()
        SOUNDS['shock'] = SoundGenerator.shock_sound()
        SOUNDS['sniper'] = SoundGenerator.laser_sound()  # Reuse laser
        SOUNDS['flak'] = SoundGenerator.plasma_sound()   # Reuse plasma
        SOUNDS['tesla'] = SoundGenerator.shock_sound()   # Reuse shock
        SOUNDS['death'] = SoundGenerator.enemy_death_sound()
        SOUNDS['wave'] = SoundGenerator.wave_start_sound()
        SOUNDS['core_hit'] = SoundGenerator.core_hit_sound()
        SOUNDS['upgrade'] = SoundGenerator.upgrade_sound()
        SOUNDS['menu_click'] = SoundGenerator.menu_click_sound()
        SOUNDS['music'] = SoundGenerator.generate_background_music()
        
        # Load MP3 music
        load_music()
        
        # Set up music channel for procedural music fallback
        MUSIC_CHANNEL = pygame.mixer.Channel(0)
        MUSIC_CHANNEL.set_volume(0.3)
    except Exception as e:
        print(f"Sound initialization failed: {e}")
        # Sounds will remain None, game will skip playing them

# Multiple Maps System
MAPS = {
    'classic': {
        'name': 'Classic Defense',
        'path': [
            (150, 200), (450, 200), (750, 200), (1050, 200),
            (1050, 450), (750, 450), (750, 750), (1050, 750),
            (1350, 750), (1650, 750)
        ],
        'nodes': [
            (300, 350), (600, 80), (900, 350), (600, 600),
            (900, 600), (1200, 600), (1200, 900), (1500, 600)
        ]
    },
    'serpent': {
        'name': 'Serpent\'s Path',
        'path': [
            (150, 540), (350, 540), (350, 300), (650, 300),
            (650, 700), (950, 700), (950, 200), (1250, 200),
            (1250, 600), (1550, 600), (1750, 600)
        ],
        'nodes': [
            (250, 400), (500, 200), (500, 500), (800, 500),
            (800, 350), (1100, 350), (1100, 450), (1400, 450),
            (1400, 750), (1650, 450)
        ]
    },
    'labyrinth': {
        'name': 'The Labyrinth',
        'path': [
            (150, 800), (400, 800), (400, 400), (700, 400),
            (700, 700), (1000, 700), (1000, 300), (1300, 300),
            (1300, 600), (1600, 600), (1750, 600)
        ],
        'nodes': [
            (250, 650), (250, 550), (550, 250), (550, 550),
            (850, 550), (850, 450), (1150, 450), (1150, 150),
            (1450, 450), (1450, 750)
        ]
    }
}

# Current map selection
CURRENT_MAP = 'classic'

def get_current_map():
    """Get current map data"""
    return MAPS[CURRENT_MAP]

# Path definition (will be set from current map)
PATH_POINTS = MAPS['classic']['path']
BUILD_NODES = MAPS['classic']['nodes']

# Tower stats - INCREASED RANGES
TOWER_STATS = {
    'laser': {'cost': 50, 'damage': 5, 'rate': 15, 'range': 220, 'color': NEON_BLUE},
    'plasma': {'cost': 100, 'damage': 20, 'rate': 45, 'range': 240, 'color': NEON_PURPLE},
    'shock': {'cost': 75, 'damage': 2, 'rate': 20, 'range': 200, 'color': NEON_YELLOW},
    'sniper': {'cost': 120, 'damage': 40, 'rate': 90, 'range': 400, 'color': NEON_GREEN},
    'flak': {'cost': 80, 'damage': 8, 'rate': 25, 'range': 220, 'color': NEON_RED},
    'tesla': {'cost': 150, 'damage': 15, 'rate': 30, 'range': 280, 'color': NEON_CYAN}
}

# Enemy stats - Increased sizes
ENEMY_STATS = {
    'drone': {'hp': 20, 'speed': 2.5, 'reward': 10, 'color': NEON_RED, 'size': 20},
    'mech': {'hp': 60, 'speed': 1.0, 'reward': 20, 'color': NEON_PURPLE, 'size': 35},
    'runner': {'hp': 15, 'speed': 4.0, 'reward': 15, 'color': NEON_CYAN, 'size': 18}
}

# Wave definitions - Extended to 12 waves
WAVES = [
    [('drone', 10)],
    [('drone', 12), ('runner', 3)],
    [('mech', 6)],
    [('drone', 8), ('runner', 6)],
    [('mech', 10)],
    [('drone', 10), ('mech', 5), ('runner', 8)],
    [('runner', 15), ('drone', 5)],
    [('mech', 12), ('runner', 5)],
    [('drone', 15), ('mech', 8)],
    [('runner', 20), ('mech', 5)],
    [('mech', 15), ('drone', 10)],
    [('drone', 20), ('mech', 15), ('runner', 15)]  # Epic finale
]

@dataclass
class Enemy:
    type: str
    hp: float
    max_hp: float
    speed: float
    reward: int
    path_index: int
    progress: float
    x: float
    y: float
    color: Tuple[int, int, int]
    size: int
    slow_factor: float = 1.0
    slow_duration: int = 0
    
    def update(self):
        """Move along path"""
        if self.path_index >= len(PATH_POINTS) - 1:
            return True  # Reached end
        
        # Apply slow
        if self.slow_duration > 0:
            self.slow_duration -= 1
            current_speed = self.speed * self.slow_factor
        else:
            current_speed = self.speed
            self.slow_factor = 1.0
        
        # Get current and next point
        current = PATH_POINTS[self.path_index]
        next_point = PATH_POINTS[self.path_index + 1]
        
        # Calculate direction
        dx = next_point[0] - current[0]
        dy = next_point[1] - current[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            # Normalize and move
            dx /= distance
            dy /= distance
            
            self.progress += current_speed
            
            # Check if reached next point
            if self.progress >= distance:
                self.path_index += 1
                self.progress = 0
                if self.path_index >= len(PATH_POINTS) - 1:
                    self.x, self.y = PATH_POINTS[-1]
                    return True
        
        # Update position
        if self.path_index < len(PATH_POINTS) - 1:
            t = self.progress / distance if distance > 0 else 0
            self.x = current[0] + dx * self.progress
            self.y = current[1] + dy * self.progress
        
        return False
    
    def draw(self, screen):
        """Draw enemy with enhanced visuals"""
        # Draw animated glow pulse
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        glow_size = self.size * (2.5 + pulse * 0.5)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(40 + pulse * 20)
        pygame.draw.circle(glow_surf, (*self.color, glow_alpha), 
                         (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))
        
        # Draw main body based on type
        if self.type == 'drone':
            # Diamond shape for drones
            points = [
                (self.x, self.y - self.size),
                (self.x + self.size * 0.7, self.y),
                (self.x, self.y + self.size),
                (self.x - self.size * 0.7, self.y)
            ]
            pygame.draw.polygon(screen, self.color, points, 3)
            # Inner glow
            inner_points = [
                (self.x, self.y - self.size * 0.5),
                (self.x + self.size * 0.35, self.y),
                (self.x, self.y + self.size * 0.5),
                (self.x - self.size * 0.35, self.y)
            ]
            pygame.draw.polygon(screen, (*self.color, 100), inner_points)
            
        elif self.type == 'mech':
            # Octagon for mechs (tank-like)
            points = []
            for i in range(8):
                angle = i * 45 * math.pi / 180
                px = self.x + self.size * 0.8 * math.cos(angle)
                py = self.y + self.size * 0.8 * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points, 4)
            # Center core
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size * 0.4), 2)
            
        else:  # runner
            # Elongated hexagon for runners (speedy)
            points = [
                (self.x - self.size * 1.2, self.y),
                (self.x - self.size * 0.6, self.y - self.size * 0.7),
                (self.x + self.size * 0.6, self.y - self.size * 0.7),
                (self.x + self.size * 1.2, self.y),
                (self.x + self.size * 0.6, self.y + self.size * 0.7),
                (self.x - self.size * 0.6, self.y + self.size * 0.7)
            ]
            pygame.draw.polygon(screen, self.color, points, 2)
            # Speed lines
            for i in range(3):
                line_x = self.x - self.size * (1.5 + i * 0.3)
                pygame.draw.line(screen, (*self.color, 100), 
                               (line_x, self.y - 3), (line_x, self.y + 3), 1)
        
        # Slow effect indicator
        if self.slow_duration > 0:
            slow_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            pygame.draw.circle(slow_surf, (*NEON_YELLOW, 60), 
                             (self.size * 1.5, self.size * 1.5), self.size * 1.2)
            screen.blit(slow_surf, (int(self.x - self.size * 1.5), int(self.y - self.size * 1.5)))
        
        # HP bar
        if self.hp < self.max_hp:
            bar_width = self.size * 1.5
            bar_height = 5
            bar_x = int(self.x - bar_width / 2)
            bar_y = int(self.y - self.size - 12)
            
            # Background
            pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
            # Health
            hp_width = int((self.hp / self.max_hp) * bar_width)
            hp_color = NEON_GREEN if self.hp > self.max_hp * 0.5 else NEON_RED
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, hp_width, bar_height))
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)

@dataclass
class Tower:
    type: str
    x: float
    y: float
    damage: int
    fire_rate: int
    range: float
    color: Tuple[int, int, int]
    cooldown: int = 0
    target: Optional[Enemy] = None
    upgrade_level: int = 0  # 0 = base, 1 = upgraded
    game: Optional['Game'] = None  # Reference to game for sound
    
    def get_upgrade_cost(self):
        """Calculate upgrade cost (1.5x original)"""
        base_cost = TOWER_STATS[self.type]['cost']
        return int(base_cost * 1.5)
    
    def upgrade(self):
        """Upgrade tower stats"""
        if self.upgrade_level >= 1:
            return False
        
        self.upgrade_level = 1
        old_damage = self.damage
        old_range = self.range
        
        self.damage = int(self.damage * 1.5)
        self.range = int(self.range * 1.2)
        
        # Create upgrade particles through game
        if self.game:
            for _ in range(20):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                self.game.particles.append({
                    'x': self.x,
                    'y': self.y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'life': 30,
                    'color': NEON_GREEN
                })
        
        return True
    
    def update(self, enemies: List[Enemy]):
        """Update tower targeting and shooting"""
        if self.cooldown > 0:
            self.cooldown -= 1
        
        # Find closest enemy in range
        self.target = None
        closest_dist = self.range
        
        for enemy in enemies:
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < closest_dist:
                closest_dist = dist
                self.target = enemy
        
        # Shoot if ready and has target
        if self.target and self.cooldown == 0:
            self.shoot()
            self.cooldown = self.fire_rate
    
    def shoot(self):
        """Apply damage to target"""
        if self.target:
            damage_dealt = self.damage
            self.target.hp -= damage_dealt
            
            # Shock tower applies slow
            if self.type == 'shock':
                self.target.slow_factor = 0.5
                self.target.slow_duration = 30
            
            # Create damage number
            if self.game:
                self.game.create_damage_number(self.target.x, self.target.y - 30, 
                                               damage_dealt, self.color)
            
            # Play sound through game instance
            if self.game:
                self.game.play_sound(self.type)
    
    def draw(self, screen):
        """Draw tower as glowing hexagon/triangle"""
        # Draw range circle when selected or hovering
        mouse_pos = pygame.mouse.get_pos()
        dist_to_mouse = math.sqrt((mouse_pos[0] - self.x)**2 + (mouse_pos[1] - self.y)**2)
        show_range = dist_to_mouse < 40 or self.cooldown == 0
        
        if show_range:
            range_surf = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
            alpha = 25 if dist_to_mouse < 40 else 10
            pygame.draw.circle(range_surf, (*self.color, alpha), (self.range, self.range), self.range, 2)
            screen.blit(range_surf, (int(self.x - self.range), int(self.y - self.range)))
        
        # Upgraded towers have pulsing green aura
        if self.upgrade_level > 0:
            pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) / 2
            upgrade_size = int(50 + pulse * 10)
            upgrade_glow = pygame.Surface((upgrade_size * 2, upgrade_size * 2), pygame.SRCALPHA)
            glow_alpha = int(40 + pulse * 20)
            pygame.draw.circle(upgrade_glow, (*NEON_GREEN, glow_alpha), (upgrade_size, upgrade_size), upgrade_size)
            screen.blit(upgrade_glow, (int(self.x - upgrade_size), int(self.y - upgrade_size)))
        
        # Draw main glow
        glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        glow_intensity = 80 if self.upgrade_level > 0 else 50
        pygame.draw.circle(glow_surf, (*self.color, glow_intensity), (40, 40), 35)
        screen.blit(glow_surf, (int(self.x - 40), int(self.y - 40)))
        
        # Draw tower shape based on type (larger if upgraded)
        size_mult = 1.5 if self.upgrade_level > 0 else 1.2
        
        if self.type == 'laser':
            # Triangle (larger)
            base_size = 20 * size_mult
            points = [
                (self.x, self.y - base_size),
                (self.x - base_size * 0.87, self.y + base_size * 0.67),
                (self.x + base_size * 0.87, self.y + base_size * 0.67)
            ]
            pygame.draw.polygon(screen, self.color, points, 4)
            if self.upgrade_level > 0:
                # Inner triangle
                inner_points = [(p[0] * 0.9 + self.x * 0.1, p[1] * 0.9 + self.y * 0.1) for p in points]
                pygame.draw.polygon(screen, (*NEON_GREEN, 150), inner_points)
                
        elif self.type == 'plasma':
            # Hexagon (larger)
            base_size = 20 * size_mult
            points = []
            for i in range(6):
                angle = i * 60 * math.pi / 180
                px = self.x + base_size * math.cos(angle)
                py = self.y + base_size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points, 4)
            if self.upgrade_level > 0:
                # Inner hexagon
                inner_points = [(p[0] * 0.85 + self.x * 0.15, p[1] * 0.85 + self.y * 0.15) for p in points]
                pygame.draw.polygon(screen, (*NEON_GREEN, 150), inner_points)
                
        elif self.type == 'shock':
            # Circle with lightning (larger)
            base_size = 16 * size_mult
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(base_size), 4)
            if self.upgrade_level > 0:
                pygame.draw.circle(screen, (*NEON_GREEN, 150), (int(self.x), int(self.y)), int(base_size * 0.7))
            # Lightning bolt
            if self.cooldown > self.fire_rate - 5:
                bolt_points = [
                    (self.x - 5, self.y - 10),
                    (self.x + 2, self.y - 2),
                    (self.x - 3, self.y + 2),
                    (self.x + 5, self.y + 10)
                ]
                pygame.draw.lines(screen, self.color, False, bolt_points, 3 if self.upgrade_level > 0 else 2)
                
        elif self.type == 'sniper':
            # Cross/scope design
            base_size = 22 * size_mult
            # Outer circle
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(base_size), 3)
            # Cross hairs
            line_width = 3 if self.upgrade_level > 0 else 2
            pygame.draw.line(screen, self.color, (self.x - base_size, self.y), (self.x + base_size, self.y), line_width)
            pygame.draw.line(screen, self.color, (self.x, self.y - base_size), (self.x, self.y + base_size), line_width)
            # Inner circle
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(base_size * 0.4), 2)
            if self.upgrade_level > 0:
                pygame.draw.circle(screen, (*NEON_GREEN, 150), (int(self.x), int(self.y)), int(base_size * 0.3))
                
        elif self.type == 'flak':
            # Star/burst shape
            base_size = 18 * size_mult
            points = []
            for i in range(8):
                angle = i * 45 * math.pi / 180
                if i % 2 == 0:
                    radius = base_size
                else:
                    radius = base_size * 0.5
                px = self.x + radius * math.cos(angle)
                py = self.y + radius * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points, 4 if self.upgrade_level > 0 else 3)
            if self.upgrade_level > 0:
                # Inner core
                pygame.draw.circle(screen, (*NEON_GREEN, 150), (int(self.x), int(self.y)), int(base_size * 0.4))
                
        elif self.type == 'tesla':
            # Pentagon with energy core
            base_size = 20 * size_mult
            points = []
            for i in range(5):
                angle = i * 72 * math.pi / 180 - math.pi / 2
                px = self.x + base_size * math.cos(angle)
                py = self.y + base_size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points, 4)
            # Energy core
            core_pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
            core_size = int(base_size * 0.4 * (0.8 + core_pulse * 0.2))
            core_color = NEON_GREEN if self.upgrade_level > 0 else self.color
            pygame.draw.circle(screen, (*core_color, 150), (int(self.x), int(self.y)), core_size)
        
        # Draw upgrade level indicator - STARS instead of dots
        if self.upgrade_level > 0:
            # Draw a glowing star
            star_size = 8
            star_x = int(self.x + 18)
            star_y = int(self.y - 18)
            
            # Star points
            star_points = []
            for i in range(5):
                angle = i * 144 * math.pi / 180 - math.pi / 2
                px = star_x + star_size * math.cos(angle)
                py = star_y + star_size * math.sin(angle)
                star_points.append((px, py))
            
            # Draw star glow
            glow_star = pygame.Surface((star_size * 3, star_size * 3), pygame.SRCALPHA)
            pygame.draw.circle(glow_star, (*NEON_GREEN, 80), (star_size * 1.5, star_size * 1.5), star_size * 1.2)
            screen.blit(glow_star, (star_x - star_size * 1.5, star_y - star_size * 1.5))
            
            # Draw star shape
            pygame.draw.polygon(screen, NEON_GREEN, star_points)
        
        # Draw shooting line (thicker and more visible)
        if self.target and self.cooldown > self.fire_rate - 5:
            line_width = 5 if self.upgrade_level > 0 else 3
            # Draw glow line first
            glow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(glow_surf, (*self.color, 100), (self.x, self.y), 
                           (self.target.x, self.target.y), line_width + 4)
            screen.blit(glow_surf, (0, 0))
            # Draw main line
            pygame.draw.line(screen, self.color, (self.x, self.y), 
                           (self.target.x, self.target.y), line_width)

class Projectile:
    """Visual projectile effect"""
    def __init__(self, start, end, color):
        self.start = start
        self.end = end
        self.color = color
        self.lifetime = 10
    
    def update(self):
        self.lifetime -= 1
        return self.lifetime <= 0
    
    def draw(self, screen):
        alpha = int(255 * (self.lifetime / 10))
        pygame.draw.line(screen, self.color, self.start, self.end, 2)

class DamageNumber:
    """Floating damage number"""
    def __init__(self, x, y, damage, color):
        self.x = x
        self.y = y
        self.damage = damage
        self.color = color
        self.lifetime = 30
        self.vy = -2
    
    def update(self):
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime <= 0
    
    def draw(self, screen, font):
        alpha = int(255 * (self.lifetime / 30))
        text = font.render(str(self.damage), True, self.color)
        text.set_alpha(alpha)
        screen.blit(text, (int(self.x), int(self.y)))

class Notification:
    """Screen notification"""
    def __init__(self, message, color, duration=90):
        self.message = message
        self.color = color
        self.duration = duration
        self.lifetime = duration
    
    def update(self):
        self.lifetime -= 1
        return self.lifetime <= 0
    
    def draw(self, screen, font, y_pos):
        alpha = min(255, int(255 * (self.lifetime / 30))) if self.lifetime < 30 else 255
        text = font.render(self.message, True, self.color)
        text.set_alpha(alpha)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        
        # Background
        bg_rect = text_rect.inflate(40, 15)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (*BLACK, 200), bg_surf.get_rect())
        pygame.draw.rect(bg_surf, self.color, bg_surf.get_rect(), 2)
        bg_surf.set_alpha(alpha)
        screen.blit(bg_surf, bg_rect)
        
        screen.blit(text, text_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("NEON BASTION - Hold the Line")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 120)
        self.subtitle_font = pygame.font.Font(None, 48)
        
        # Initialize sounds
        init_sounds()
        
        # Settings
        self.music_enabled = True
        self.sfx_enabled = True
        self.current_music_track = None
        
        # Map selection
        self.selected_map = 'classic'
        self.map_list = list(MAPS.keys())
        self.map_selection_index = 0
        
        # Game state
        self.state = GameState.MENU
        self.energy = 200
        self.core_hp = 100
        self.max_core_hp = 100
        self.wave = 0
        self.wave_timer = 0
        self.wave_delay = 180  # 3 seconds between waves
        
        # Entities
        self.enemies: List[Enemy] = []
        self.towers: List[Tower] = []
        self.projectiles: List[Projectile] = []
        self.damage_numbers: List[DamageNumber] = []
        self.notifications: List[Notification] = []
        
        # UI
        self.selected_node = None
        self.selected_tower_type = None
        self.selected_tower = None  # For upgrades
        self.menu_selected = 0  # Menu selection
        
        # Wave spawning
        self.enemies_to_spawn = []
        self.spawn_timer = 0
        
        # Effects
        self.shake_amount = 0
        self.particles = []
        
        # Start background music
        self.play_music('menu')
    
    def play_music(self, track_name):
        """Play music track (MP3 or procedural)"""
        if not self.music_enabled:
            return
        
        # Don't restart if already playing this track
        if self.current_music_track == track_name:
            return
        
        self.current_music_track = track_name
        
        # Try to play MP3 first
        if MUSIC_TRACKS.get(track_name):
            try:
                pygame.mixer.music.load(MUSIC_TRACKS[track_name])
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                return
            except Exception as e:
                print(f"Failed to play MP3: {e}")
        
        # Fallback to procedural music
        if MUSIC_CHANNEL and SOUNDS.get('music'):
            MUSIC_CHANNEL.play(SOUNDS['music'], loops=-1)
    
    def stop_music(self):
        """Stop all music"""
        pygame.mixer.music.stop()
        if MUSIC_CHANNEL:
            MUSIC_CHANNEL.stop()
        self.current_music_track = None
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            # Resume appropriate track
            if self.state == GameState.MENU:
                self.play_music('menu')
            elif self.state == GameState.PLAYING:
                self.play_music('game')
            elif self.state == GameState.WON:
                self.play_music('win')
            elif self.state == GameState.LOST:
                self.play_music('lose')
        else:
            self.stop_music()
        if self.sfx_enabled and SOUNDS.get('menu_click'):
            SOUNDS['menu_click'].play()
    
    def toggle_sfx(self):
        """Toggle sound effects on/off"""
        self.sfx_enabled = not self.sfx_enabled
        if self.sfx_enabled and SOUNDS.get('menu_click'):
            SOUNDS['menu_click'].play()
    
    def play_sound(self, sound_name):
        """Play a sound effect if SFX enabled"""
        if self.sfx_enabled and SOUNDS.get(sound_name):
            SOUNDS[sound_name].play()
    
    def create_damage_number(self, x, y, damage, color):
        """Create a floating damage number"""
        self.damage_numbers.append(DamageNumber(x, y, damage, color))
    
    def add_notification(self, message, color=NEON_CYAN):
        """Add a notification message"""
        self.notifications.append(Notification(message, color))
    
    def load_map(self, map_name):
        """Load a specific map"""
        global PATH_POINTS, BUILD_NODES, CURRENT_MAP
        CURRENT_MAP = map_name
        self.selected_map = map_name
        map_data = MAPS[map_name]
        PATH_POINTS = map_data['path']
        BUILD_NODES = map_data['nodes']
    
    def reset_game_state(self):
        """Reset game to playing state"""
        # Load selected map
        self.load_map(self.selected_map)
        
        self.state = GameState.PLAYING
        self.energy = 200
        self.core_hp = 100
        self.wave = 0
        self.wave_timer = 0
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.selected_node = None
        self.selected_tower = None
        self.enemies_to_spawn = []
        self.spawn_timer = 0
        self.shake_amount = 0
        self.particles = []
        self.damage_numbers = []
        self.notifications = []
        self.start_wave()
        
        # Play game music
        self.play_music('game')
    
    def start_wave(self):
        """Start next wave"""
        if self.wave >= len(WAVES):
            self.state = GameState.WON
            self.play_music('win')
            return
        
        # Play wave start sound
        self.play_sound('wave')
        
        # Add notification
        self.add_notification(f"⚠ WAVE {self.wave + 1} INCOMING ⚠", NEON_YELLOW)
        
        wave_def = WAVES[self.wave]
        self.enemies_to_spawn = []
        
        for enemy_type, count in wave_def:
            for _ in range(count):
                self.enemies_to_spawn.append(enemy_type)
        
        random.shuffle(self.enemies_to_spawn)
        self.spawn_timer = 0
    
    def spawn_enemy(self, enemy_type):
        """Spawn a single enemy"""
        stats = ENEMY_STATS[enemy_type]
        enemy = Enemy(
            type=enemy_type,
            hp=stats['hp'],
            max_hp=stats['hp'],
            speed=stats['speed'],
            reward=stats['reward'],
            path_index=0,
            progress=0,
            x=PATH_POINTS[0][0],
            y=PATH_POINTS[0][1],
            color=stats['color'],
            size=stats['size']
        )
        self.enemies.append(enemy)
        
        # Spawn particles
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 4)
            self.particles.append({
                'x': PATH_POINTS[0][0],
                'y': PATH_POINTS[0][1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 20,
                'color': stats['color']
            })
    
    def build_tower(self, node_pos, tower_type):
        """Build a tower at node position"""
        stats = TOWER_STATS[tower_type]
        
        if self.energy >= stats['cost']:
            tower = Tower(
                type=tower_type,
                x=node_pos[0],
                y=node_pos[1],
                damage=stats['damage'],
                fire_rate=stats['rate'],
                range=stats['range'],
                color=stats['color'],
                game=self
            )
            self.towers.append(tower)
            self.energy -= stats['cost']
            return True
        return False
    
    def update(self):
        """Main game update"""
        if self.state != GameState.PLAYING:
            return
        
        # Wave management
        self.wave_timer += 1
        
        if not self.enemies_to_spawn and len(self.enemies) == 0:
            # Wave complete
            if self.wave_timer >= self.wave_delay:
                # Award wave completion bonus
                wave_bonus = 50 + (self.wave * 25)
                self.energy += wave_bonus
                
                # Add notification
                self.add_notification(f"✓ WAVE {self.wave + 1} CLEARED! +{wave_bonus} Energy", NEON_GREEN)
                
                # Create bonus particles
                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(3, 6)
                    self.particles.append({
                        'x': SCREEN_WIDTH // 2,
                        'y': 50,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed,
                        'life': 40,
                        'color': NEON_CYAN
                    })
                
                self.wave += 1
                self.start_wave()
                self.wave_timer = 0
        
        # Spawn enemies
        if self.enemies_to_spawn:
            self.spawn_timer += 1
            if self.spawn_timer >= 30:  # Spawn every 0.5 seconds
                enemy_type = self.enemies_to_spawn.pop(0)
                self.spawn_enemy(enemy_type)
                self.spawn_timer = 0
        
        # Update enemies
        dead_enemies = []
        for enemy in self.enemies[:]:
            reached_end = enemy.update()
            
            if reached_end:
                # Damage core
                self.core_hp -= 10
                self.shake_amount = 10
                self.enemies.remove(enemy)
                
                # Play core hit sound
                self.play_sound('core_hit')
                
                if self.core_hp <= 0:
                    self.state = GameState.LOST
                    self.play_music('lose')
            elif enemy.hp <= 0:
                # Enemy died
                self.energy += enemy.reward
                dead_enemies.append(enemy)
                self.enemies.remove(enemy)
                
                # Play death sound
                self.play_sound('death')
                
                # Particle effect
                for _ in range(5):
                    self.particles.append({
                        'x': enemy.x,
                        'y': enemy.y,
                        'vx': random.uniform(-3, 3),
                        'vy': random.uniform(-3, 3),
                        'life': 20,
                        'color': enemy.color
                    })
        
        # Update towers
        for tower in self.towers:
            tower.update(self.enemies)
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Update damage numbers
        for dmg_num in self.damage_numbers[:]:
            if dmg_num.update():
                self.damage_numbers.remove(dmg_num)
        
        # Update notifications
        for notif in self.notifications[:]:
            if notif.update():
                self.notifications.remove(notif)
        
        # Update shake
        if self.shake_amount > 0:
            self.shake_amount -= 1
    
    def draw_grid(self):
        """Draw background grid"""
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)
    
    def draw_path(self):
        """Draw the enemy path"""
        for i in range(len(PATH_POINTS) - 1):
            start = PATH_POINTS[i]
            end = PATH_POINTS[i + 1]
            
            # Draw glow
            pygame.draw.line(self.screen, (*NEON_CYAN, 50), start, end, 20)
            # Draw line
            pygame.draw.line(self.screen, NEON_CYAN, start, end, 4)
            
            # Draw direction arrows
            if i % 2 == 0:  # Every other segment
                # Calculate midpoint
                mid_x = (start[0] + end[0]) / 2
                mid_y = (start[1] + end[1]) / 2
                
                # Calculate direction
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > 0:
                    # Normalize
                    dx /= length
                    dy /= length
                    
                    # Arrow points
                    arrow_size = 12
                    arrow_tip = (mid_x + dx * arrow_size, mid_y + dy * arrow_size)
                    arrow_left = (mid_x - dy * arrow_size * 0.5 - dx * arrow_size * 0.3,
                                 mid_y + dx * arrow_size * 0.5 - dy * arrow_size * 0.3)
                    arrow_right = (mid_x + dy * arrow_size * 0.5 - dx * arrow_size * 0.3,
                                  mid_y - dx * arrow_size * 0.5 - dy * arrow_size * 0.3)
                    
                    pygame.draw.polygon(self.screen, NEON_CYAN, 
                                      [arrow_tip, arrow_left, arrow_right])
        
        # Draw spawn portal (animated)
        spawn = PATH_POINTS[0]
        pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) / 2
        portal_size = int(30 + pulse * 8)
        
        # Outer ring
        pygame.draw.circle(self.screen, NEON_RED, spawn, portal_size, 3)
        # Pulsing glow
        portal_glow = pygame.Surface((portal_size * 3, portal_size * 3), pygame.SRCALPHA)
        glow_alpha = int(40 + pulse * 30)
        pygame.draw.circle(portal_glow, (*NEON_RED, glow_alpha), 
                         (portal_size * 1.5, portal_size * 1.5), portal_size)
        self.screen.blit(portal_glow, (spawn[0] - portal_size * 1.5, spawn[1] - portal_size * 1.5))
        
        # Inner circle
        pygame.draw.circle(self.screen, (*NEON_RED, 50), spawn, int(portal_size * 0.7))
        
        # Draw core (animated)
        core = PATH_POINTS[-1]
        core_pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        core_size = int(40 + core_pulse * 5)
        
        # Health-based color
        hp_ratio = max(0, self.core_hp) / self.max_core_hp
        if hp_ratio > 0.7:
            core_color = NEON_GREEN
        elif hp_ratio > 0.3:
            core_color = NEON_YELLOW
        else:
            core_color = NEON_RED
        
        # Outer shield
        pygame.draw.circle(self.screen, core_color, core, core_size, 4)
        # Shield glow
        shield_glow = pygame.Surface((core_size * 3, core_size * 3), pygame.SRCALPHA)
        shield_alpha = int(30 + core_pulse * 20)
        pygame.draw.circle(shield_glow, (*core_color, shield_alpha), 
                         (core_size * 1.5, core_size * 1.5), core_size)
        self.screen.blit(shield_glow, (core[0] - core_size * 1.5, core[1] - core_size * 1.5))
        
        # Inner core
        pygame.draw.circle(self.screen, (*core_color, 40), core, int(core_size * 0.85))
    
    def draw_build_nodes(self):
        """Draw available build locations"""
        mouse_pos = pygame.mouse.get_pos()
        
        for i, node in enumerate(BUILD_NODES):
            # Check if occupied
            occupied = any(t.x == node[0] and t.y == node[1] for t in self.towers)
            
            if occupied:
                continue
            
            # Check if hovering
            dist_to_mouse = math.sqrt((mouse_pos[0] - node[0])**2 + (mouse_pos[1] - node[1])**2)
            is_hovering = dist_to_mouse < 25
            
            # Highlight if selected or hovering
            if self.selected_node == i:
                # Selected - pulsing yellow
                pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
                size = int(25 + pulse * 5)
                pygame.draw.circle(self.screen, NEON_YELLOW, node, size, 3)
                pygame.draw.circle(self.screen, (*NEON_YELLOW, 30), node, size - 3)
            elif is_hovering:
                # Hovering - green highlight
                pygame.draw.circle(self.screen, NEON_GREEN, node, 25, 3)
                pygame.draw.circle(self.screen, (*NEON_GREEN, 20), node, 22)
                
                # Show tooltip
                tooltip = self.small_font.render("Click to BUILD", True, NEON_GREEN)
                tooltip_rect = tooltip.get_rect(center=(node[0], node[1] - 40))
                
                # Tooltip background
                bg_rect = tooltip_rect.inflate(10, 5)
                tooltip_bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(tooltip_bg, (*BLACK, 200), tooltip_bg.get_rect())
                pygame.draw.rect(tooltip_bg, NEON_GREEN, tooltip_bg.get_rect(), 2)
                self.screen.blit(tooltip_bg, bg_rect)
                self.screen.blit(tooltip, tooltip_rect)
            else:
                # Default state
                pygame.draw.circle(self.screen, (100, 100, 100), node, 20, 2)
    
    def draw_hud(self):
        """Draw HUD"""
        # Energy with icon
        energy_text = self.font.render(f"⚡ ENERGY: {self.energy}", True, NEON_CYAN)
        self.screen.blit(energy_text, (20, 20))
        
        # Wave with progress
        if self.wave < len(WAVES):
            remaining = len(self.enemies_to_spawn) + len(self.enemies)
            wave_text = self.font.render(f"WAVE {self.wave + 1}/{len(WAVES)} ({remaining} enemies)", True, NEON_YELLOW)
        else:
            wave_text = self.font.render("FINAL WAVE!", True, NEON_RED)
        text_rect = wave_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
        self.screen.blit(wave_text, text_rect)
        
        # Core HP
        core_text = self.font.render(f"❤ CORE: {max(0, self.core_hp)}/{self.max_core_hp}", True, NEON_GREEN)
        core_rect = core_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        self.screen.blit(core_text, core_rect)
        
        # Core HP bar
        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_WIDTH - 20 - bar_width
        bar_y = 60
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        hp_width = int((max(0, self.core_hp) / self.max_core_hp) * bar_width)
        hp_color = NEON_GREEN if self.core_hp > 50 else NEON_RED
        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, hp_width, bar_height))
        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Build/Upgrade UI - More detailed
        if self.selected_tower:
            # Tower info panel
            panel_x = 20
            panel_y = 120
            panel_width = 450
            panel_height = 280
            
            # Draw panel background
            panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (*DARK_BLUE, 220), (0, 0, panel_width, panel_height))
            pygame.draw.rect(panel_surf, NEON_CYAN, (0, 0, panel_width, panel_height), 3)
            self.screen.blit(panel_surf, (panel_x, panel_y))
            
            y_offset = panel_y + 20
            
            # Tower title
            title = self.font.render(f"▼ {self.selected_tower.type.upper()} TOWER", True, NEON_CYAN)
            self.screen.blit(title, (panel_x + 15, y_offset))
            y_offset += 45
            
            # Stats
            stats = [
                f"Damage: {self.selected_tower.damage}",
                f"Range: {int(self.selected_tower.range)}",
                f"Fire Rate: {60 // max(1, self.selected_tower.fire_rate)}/sec"
            ]
            
            for stat in stats:
                stat_text = self.small_font.render(stat, True, (200, 200, 200))
                self.screen.blit(stat_text, (panel_x + 15, y_offset))
                y_offset += 28
            
            y_offset += 10
            
            # Upgrade section
            if self.selected_tower.upgrade_level == 0:
                upgrade_cost = self.selected_tower.get_upgrade_cost()
                can_afford = self.energy >= upgrade_cost
                
                # Divider
                pygame.draw.line(self.screen, NEON_GREEN, 
                               (panel_x + 15, y_offset), (panel_x + panel_width - 15, y_offset), 2)
                y_offset += 15
                
                upgrade_title = self.small_font.render("UPGRADE AVAILABLE:", True, NEON_GREEN)
                self.screen.blit(upgrade_title, (panel_x + 15, y_offset))
                y_offset += 30
                
                # Preview stats
                preview = [
                    f"→ Damage: {int(self.selected_tower.damage * 1.5)} (+{int(self.selected_tower.damage * 0.5)})",
                    f"→ Range: {int(self.selected_tower.range * 1.2)} (+{int(self.selected_tower.range * 0.2)})"
                ]
                
                for prev in preview:
                    prev_text = self.small_font.render(prev, True, NEON_YELLOW)
                    self.screen.blit(prev_text, (panel_x + 15, y_offset))
                    y_offset += 26
                
                y_offset += 10
                
                # Cost and button
                cost_color = NEON_GREEN if can_afford else NEON_RED
                cost_text = self.small_font.render(f"Cost: {upgrade_cost} Energy", True, cost_color)
                self.screen.blit(cost_text, (panel_x + 15, y_offset))
                
                if can_afford:
                    button_text = self.font.render("Press [U] to UPGRADE", True, NEON_GREEN)
                else:
                    button_text = self.small_font.render("Insufficient Energy", True, NEON_RED)
                    
                button_rect = button_text.get_rect(center=(panel_x + panel_width // 2, panel_y + panel_height - 25))
                self.screen.blit(button_text, button_rect)
            else:
                # Fully upgraded
                pygame.draw.line(self.screen, NEON_GREEN, 
                               (panel_x + 15, y_offset), (panel_x + panel_width - 15, y_offset), 2)
                y_offset += 20
                
                upgraded_text = self.font.render("★ FULLY UPGRADED ★", True, NEON_GREEN)
                upgraded_rect = upgraded_text.get_rect(center=(panel_x + panel_width // 2, y_offset + 20))
                self.screen.blit(upgraded_text, upgraded_rect)
            
            # Deselect hint at bottom
            deselect = self.small_font.render("[ESC] Deselect", True, (150, 150, 150))
            self.screen.blit(deselect, (panel_x + 15, panel_y + panel_height - 25))
                
        elif self.selected_node is not None:
            # Build panel
            panel_x = 20
            panel_y = 120
            panel_width = 500
            
            # Calculate panel height based on towers
            panel_height = 100 + len(TOWER_STATS) * 35
            
            # Draw panel background
            panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (*DARK_BLUE, 220), (0, 0, panel_width, panel_height))
            pygame.draw.rect(panel_surf, NEON_YELLOW, (0, 0, panel_width, panel_height), 3)
            self.screen.blit(panel_surf, (panel_x, panel_y))
            
            # Title
            title = self.font.render("▼ BUILD TOWER", True, NEON_YELLOW)
            self.screen.blit(title, (panel_x + 15, panel_y + 15))
            
            # Tower list
            y_offset = panel_y + 60
            tower_keys = ['1', '2', '3', '4', '5', '6']
            tower_types = ['laser', 'plasma', 'shock', 'sniper', 'flak', 'tesla']
            
            for i, (key, tower_type) in enumerate(zip(tower_keys, tower_types)):
                stats = TOWER_STATS[tower_type]
                can_afford = self.energy >= stats['cost']
                
                # Color based on affordability
                if can_afford:
                    text_color = stats['color']
                    key_color = NEON_GREEN
                else:
                    text_color = (100, 100, 100)
                    key_color = NEON_RED
                
                # Tower info
                tower_info = f"[{key}] {tower_type.upper()} - {stats['cost']}⚡ | DMG:{stats['damage']} RNG:{stats['range']}"
                tower_text = self.small_font.render(tower_info, True, text_color)
                self.screen.blit(tower_text, (panel_x + 15, y_offset))
                
                y_offset += 35
            
            # Cancel hint
            cancel = self.small_font.render("[ESC] Cancel", True, (150, 150, 150))
            self.screen.blit(cancel, (panel_x + 15, panel_y + panel_height - 30))
        else:
            # General hint
            hint1 = self.small_font.render("💡 Click TOWER to upgrade | Click NODE to build", True, (150, 150, 150))
            self.screen.blit(hint1, (20, 120))
            
            hint2 = self.small_font.render("💡 Hover over towers to see their range", True, (150, 150, 150))
            self.screen.blit(hint2, (20, 150))
    
    def draw_end_screen(self):
        """Draw win/lose screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        if self.state == GameState.WON:
            title_text = self.font.render("CORE STABLE – VICTORY", True, NEON_GREEN)
            subtitle = self.small_font.render("All waves eliminated", True, NEON_CYAN)
        else:
            title_text = self.font.render("SYSTEM FAILURE", True, NEON_RED)
            subtitle = self.small_font.render("Core destroyed", True, NEON_RED)
        
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        
        restart_text = self.small_font.render("Press SPACE to restart", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        
        menu_text = self.small_font.render("Press ESC for menu", True, (150, 150, 150))
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle, subtitle_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(menu_text, menu_rect)
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(BLACK)
        
        # Animated grid background
        time_offset = pygame.time.get_ticks() * 0.05
        for x in range(0, SCREEN_WIDTH, 50):
            alpha = int(30 + 20 * math.sin(time_offset * 0.01 + x * 0.01))
            pygame.draw.line(self.screen, (*GRID_COLOR, alpha), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 50):
            alpha = int(30 + 20 * math.sin(time_offset * 0.01 + y * 0.01))
            pygame.draw.line(self.screen, (*GRID_COLOR, alpha), (0, y), (SCREEN_WIDTH, y), 1)
        
        # Title with glow
        title_text = "NEON BASTION"
        title_surface = self.title_font.render(title_text, True, NEON_CYAN)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 200))
        
        # Glow effect
        glow_surface = self.title_font.render(title_text, True, (*NEON_CYAN, 100))
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_rect = title_rect.copy()
            glow_rect.x += offset[0]
            glow_rect.y += offset[1]
            self.screen.blit(glow_surface, glow_rect)
        
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle = self.subtitle_font.render("Hold the Line. Upgrade the Future.", True, NEON_YELLOW)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Map selection
        map_label = self.font.render("SELECT MAP:", True, NEON_GREEN)
        map_label_rect = map_label.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(map_label, map_label_rect)
        
        # Map options
        map_text = f"< {MAPS[self.selected_map]['name']} >"
        map_surface = self.subtitle_font.render(map_text, True, NEON_CYAN)
        map_rect = map_surface.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(map_surface, map_rect)
        
        map_hint = self.small_font.render("Use LEFT/RIGHT arrows to change map", True, (150, 150, 150))
        map_hint_rect = map_hint.get_rect(center=(SCREEN_WIDTH // 2, 490))
        self.screen.blit(map_hint, map_hint_rect)
        
        # Menu options
        menu_options = [
            "START GAME",
            "LORE",
            "SETTINGS",
            "QUIT"
        ]
        
        start_y = 580
        for i, option in enumerate(menu_options):
            if i == self.menu_selected:
                color = NEON_GREEN
                text = f"> {option} <"
                font = self.subtitle_font
            else:
                color = (150, 150, 150)
                text = option
                font = self.font
            
            option_surface = font.render(text, True, color)
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 80))
            self.screen.blit(option_surface, option_rect)
        
        # Controls hint
        hint = self.small_font.render("Use UP/DOWN arrows and ENTER to select", True, (100, 100, 100))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)
    
    def draw_lore(self):
        """Draw lore screen"""
        self.screen.fill(BLACK)
        self.draw_grid()
        
        # Title
        title = self.subtitle_font.render("THE NEON BASTION", True, NEON_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Lore text
        lore_text = [
            "Year 2847. The last human colony.",
            "",
            "After the AI Singularity Wars, humanity retreated to the Neon Bastion—",
            "a fortress built from the wreckage of fallen mega-cities. The Core,",
            "humanity's last quantum reactor, powers our shields and keeps us alive.",
            "",
            "But the Swarm never rests. Automated war machines from the old world",
            "still hunt us, drawn to the Core's energy signature like moths to flame.",
            "",
            "DRONES - Fast recon units from the pre-war surveillance grid",
            "MECHS - Heavy assault platforms, relics of corporate armies",
            "RUNNERS - Prototype interceptors, built for one thing: speed",
            "",
            "You are the last Defense Commander. Your tower network is all that",
            "stands between survival and extinction. The Swarm comes in waves.",
            "",
            "Hold. The. Line.",
            "",
            "The future depends on it."
        ]
        
        start_y = 180
        for i, line in enumerate(lore_text):
            if line == "":
                continue
            
            # Color coding
            if "DRONES" in line or "MECHS" in line or "RUNNERS" in line:
                color = NEON_RED
            elif "Core" in line or "Bastion" in line:
                color = NEON_GREEN
            elif "Defense Commander" in line:
                color = NEON_YELLOW
            else:
                color = (200, 200, 200)
            
            text_surface = self.small_font.render(line, True, color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 35))
            self.screen.blit(text_surface, text_rect)
        
        # Back hint
        back_hint = self.small_font.render("Press ESC to return", True, NEON_CYAN)
        back_rect = back_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(back_hint, back_rect)
    
    def draw_settings(self):
        """Draw settings screen"""
        self.screen.fill(BLACK)
        self.draw_grid()
        
        # Title
        title = self.subtitle_font.render("SETTINGS", True, NEON_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Settings options
        settings_y = 300
        
        # Music toggle
        music_text = f"Music: {'ON' if self.music_enabled else 'OFF'}"
        music_color = NEON_GREEN if self.music_enabled else NEON_RED
        music_surface = self.font.render(music_text, True, music_color)
        music_rect = music_surface.get_rect(center=(SCREEN_WIDTH // 2, settings_y))
        self.screen.blit(music_surface, music_rect)
        
        music_hint = self.small_font.render("Press M to toggle", True, (150, 150, 150))
        music_hint_rect = music_hint.get_rect(center=(SCREEN_WIDTH // 2, settings_y + 40))
        self.screen.blit(music_hint, music_hint_rect)
        
        # SFX toggle
        sfx_text = f"Sound Effects: {'ON' if self.sfx_enabled else 'OFF'}"
        sfx_color = NEON_GREEN if self.sfx_enabled else NEON_RED
        sfx_surface = self.font.render(sfx_text, True, sfx_color)
        sfx_rect = sfx_surface.get_rect(center=(SCREEN_WIDTH // 2, settings_y + 150))
        self.screen.blit(sfx_surface, sfx_rect)
        
        sfx_hint = self.small_font.render("Press S to toggle", True, (150, 150, 150))
        sfx_hint_rect = sfx_hint.get_rect(center=(SCREEN_WIDTH // 2, settings_y + 190))
        self.screen.blit(sfx_hint, sfx_hint_rect)
        
        # Resolution info
        res_text = f"Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}"
        res_surface = self.small_font.render(res_text, True, (150, 150, 150))
        res_rect = res_surface.get_rect(center=(SCREEN_WIDTH // 2, settings_y + 300))
        self.screen.blit(res_surface, res_rect)
        
        # Back hint
        back_hint = self.small_font.render("Press ESC to return", True, NEON_CYAN)
        back_rect = back_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(back_hint, back_rect)
    
    def draw(self):
        """Main draw function"""
        # Handle different game states
        if self.state == GameState.MENU:
            self.draw_menu()
            pygame.display.flip()
            return
        elif self.state == GameState.LORE:
            self.draw_lore()
            pygame.display.flip()
            return
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
            pygame.display.flip()
            return
        
        # Screen shake (for playing states)
        shake_x = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        shake_y = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        
        # Clear
        self.screen.fill(BLACK)
        
        # Create offset surface for shake
        if self.shake_amount > 0:
            game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            game_surface.fill(BLACK)
            draw_surface = game_surface
        else:
            draw_surface = self.screen
        
        # Draw game
        self.draw_grid()
        self.draw_path()
        self.draw_build_nodes()
        
        # Draw towers
        for tower in self.towers:
            tower.draw(draw_surface)
            
            # Highlight selected tower
            if tower == self.selected_tower:
                pygame.draw.circle(draw_surface, NEON_CYAN, (int(tower.x), int(tower.y)), 35, 3)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(draw_surface)
        
        # Draw particles
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / 20))
            color = (*particle['color'][:3], alpha)
            pygame.draw.circle(draw_surface, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 3)
        
        # Draw damage numbers
        for dmg_num in self.damage_numbers:
            dmg_num.draw(draw_surface, self.small_font)
        
        # Blit shaken surface
        if self.shake_amount > 0:
            self.screen.blit(game_surface, (shake_x, shake_y))
        
        # Draw HUD (no shake)
        self.draw_hud()
        
        # Draw notifications (above HUD)
        notif_y = 120
        for notif in self.notifications:
            notif.draw(self.screen, self.font, notif_y)
            notif_y += 50
        
        # Draw end screen
        if self.state in [GameState.WON, GameState.LOST]:
            self.draw_end_screen()
        
        pygame.display.flip()
    
    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # Menu navigation
                if self.state == GameState.MENU:
                    if event.key == pygame.K_UP:
                        self.menu_selected = (self.menu_selected - 1) % 4
                        self.play_sound('menu_click')
                    elif event.key == pygame.K_DOWN:
                        self.menu_selected = (self.menu_selected + 1) % 4
                        self.play_sound('menu_click')
                    elif event.key == pygame.K_LEFT:
                        # Change map left
                        self.map_selection_index = (self.map_selection_index - 1) % len(self.map_list)
                        self.selected_map = self.map_list[self.map_selection_index]
                        self.play_sound('menu_click')
                    elif event.key == pygame.K_RIGHT:
                        # Change map right
                        self.map_selection_index = (self.map_selection_index + 1) % len(self.map_list)
                        self.selected_map = self.map_list[self.map_selection_index]
                        self.play_sound('menu_click')
                    elif event.key == pygame.K_RETURN:
                        self.play_sound('menu_click')
                        if self.menu_selected == 0:  # Start Game
                            self.reset_game_state()
                        elif self.menu_selected == 1:  # Lore
                            self.state = GameState.LORE
                        elif self.menu_selected == 2:  # Settings
                            self.state = GameState.SETTINGS
                        elif self.menu_selected == 3:  # Quit
                            return False
                
                # Lore screen
                elif self.state == GameState.LORE:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                        self.play_sound('menu_click')
                        self.play_music('menu')
                
                # Settings screen
                elif self.state == GameState.SETTINGS:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                        self.play_sound('menu_click')
                        self.play_music('menu')
                    elif event.key == pygame.K_m:
                        self.toggle_music()
                    elif event.key == pygame.K_s:
                        self.toggle_sfx()
                
                # Game over screens
                elif self.state in [GameState.WON, GameState.LOST]:
                    if event.key == pygame.K_SPACE:
                        self.reset_game_state()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                        self.play_sound('menu_click')
                        self.play_music('menu')
                
                # Playing state
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        if self.selected_node is not None or self.selected_tower is not None:
                            self.selected_node = None
                            self.selected_tower_type = None
                            self.selected_tower = None
                        else:
                            self.state = GameState.MENU
                            self.play_sound('menu_click')
                            self.play_music('menu')
                    
                    # Upgrade selected tower
                    if event.key == pygame.K_u and self.selected_tower:
                        if self.selected_tower.upgrade_level == 0:
                            cost = self.selected_tower.get_upgrade_cost()
                            if self.energy >= cost:
                                self.energy -= cost
                                self.selected_tower.upgrade()
                                self.play_sound('upgrade')
                                self.add_notification(f"⬆ {self.selected_tower.type.upper()} UPGRADED!", NEON_GREEN)
                            else:
                                self.add_notification("⚠ Not enough Energy!", NEON_RED)
                    
                    # Build towers
                    if self.selected_node is not None:
                        tower_map = {
                            pygame.K_1: 'laser',
                            pygame.K_2: 'plasma',
                            pygame.K_3: 'shock',
                            pygame.K_4: 'sniper',
                            pygame.K_5: 'flak',
                            pygame.K_6: 'tesla'
                        }
                        
                        if event.key in tower_map:
                            node_pos = BUILD_NODES[self.selected_node]
                            tower_type = tower_map[event.key]
                            if self.build_tower(node_pos, tower_type):
                                self.selected_node = None
                                self.add_notification(f"✓ {tower_type.upper()} Built!", NEON_GREEN)
                            else:
                                self.add_notification("⚠ Not enough Energy!", NEON_RED)
            
            if event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.PLAYING:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check tower clicks first (for upgrades)
                clicked_tower = False
                for tower in self.towers:
                    dist = math.sqrt((mouse_pos[0] - tower.x)**2 + (mouse_pos[1] - tower.y)**2)
                    if dist < 30:
                        self.selected_tower = tower
                        self.selected_node = None
                        clicked_tower = True
                        break
                
                # If no tower clicked, check build nodes
                if not clicked_tower:
                    self.selected_tower = None
                    for i, node in enumerate(BUILD_NODES):
                        dist = math.sqrt((mouse_pos[0] - node[0])**2 + (mouse_pos[1] - node[1])**2)
                        if dist < 25:
                            # Check if occupied
                            occupied = any(t.x == node[0] and t.y == node[1] for t in self.towers)
                            if not occupied:
                                self.selected_node = i
                                break
        
        return True
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            running = self.handle_events()
            
            # Only update game logic when playing
            if self.state == GameState.PLAYING:
                self.update()
            
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()