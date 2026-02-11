# -*- coding: utf-8 -*-
import sys
import io

# NUCLEAR OPTION: Force Standard Output to UTF-8
# This fixes the Unicode Error and allows Emojis to print
sys.stdout.reconfigure(encoding='utf-8')

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from pyboy import PyBoy
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from collections import deque
import random

class NuzlockeEnv(gym.Env):
    def __init__(self, rom_path, state_path):
        super(NuzlockeEnv, self).__init__()
        # 1. EMULATOR (1X SPEED)
        self.pyboy = PyBoy(rom_path, window_type="SDL2")
        self.pyboy.set_emulation_speed(1) 
        with open(state_path, "rb") as f:
            self.pyboy.load_state(f)
            
        self.action_space = spaces.Discrete(8)
        self.observation_space = spaces.Box(low=0, high=255, shape=(10,), dtype=np.uint8)
        
        # --- THE 151 EMOJI SPRITE DATABASE ---
        # Maps Internal ID -> (Unique Emoji, Type)
        self.ROM_DB = {
            1: ("🦏", "GND/RCK"), 2: ("🦘", "NORM"), 3: ("🚹", "PSN"), 4: ("🧚", "NORM"), 5: ("🦅", "NORM/FLY"), 
            6: ("🌀", "PSN"), 7: ("🐛", "BUG/GRS"), 8: ("🐚", "WTR/ICE"), 9: ("👻", "GHOST"), 10: ("👻", "GHOST"), 
            11: ("👻", "GHOST"), 12: ("🐛", "BUG/GRS"), 13: ("🐝", "BUG/GRS"), 14: ("🦀", "WTR"), 15: ("🚺", "PSN"), 
            16: ("🚺", "PSN"), 17: ("🧞", "WTR"), 18: ("🦏", "RCK/GND"), 19: ("🦁", "FIRE"), 20: ("🐞", "BUG"), 
            21: ("⚡", "ELEC"), 22: ("⚡", "ELEC"), 23: ("🐟", "WTR"), 24: ("🦑", "WTR/PSN"), 25: ("💩", "PSN"), 
            26: ("🐚", "WTR/ICE"), 27: ("🐚", "WTR/ICE"), 28: ("🐎", "FIRE"), 29: ("🐎", "FIRE"), 30: ("🐚", "WTR"), 
            31: ("🐚", "WTR"), 32: ("🐊", "PSN/GND"), 33: ("🐕", "FIRE"), 34: ("🐕", "FIRE"), 35: ("🧱", "RCK/GND"), 
            36: ("🐦", "NORM/FLY"), 37: ("🐦", "NORM/FLY"), 38: ("🐦", "NORM/FLY"), 39: ("🦅", "NORM/FLY"), 40: ("🦅", "NORM/FLY"), 
            41: ("🐊", "PSN/GND"), 42: ("🐊", "PSN/GND"), 43: ("💪", "FGT"), 44: ("🌴", "GRS/PSY"), 45: ("🌴", "GRS/PSY"), 
            46: ("😴", "PSY"), 47: ("🦆", "WTR"), 48: ("🦆", "WTR"), 49: ("🐒", "FGT"), 50: ("🦭", "WTR"), 
            51: ("🦢", "WTR/FLY"), 52: ("💪", "FGT"), 53: ("🌴", "GRS/PSY"), 54: ("💪", "FGT"), 55: ("🐊", "PSN/GND"), 
            56: ("👽", "PSY"), 57: ("🐒", "FGT"), 58: ("❄️", "ICE/FLY"), 59: ("🥔", "GND"), 60: ("🥔", "GND"), 
            61: ("🦅", "NORM/FLY"), 62: ("🐜", "BUG/PSN"), 63: ("🐝", "BUG/PSN"), 64: ("🐝", "BUG/PSN"), 65: ("🐦", "NORM/FLY"), 
            66: ("🦆", "NORM/FLY"), 67: ("🐦", "NORM/FLY"), 68: ("🦑", "WTR/PSN"), 69: ("💩", "PSN"), 70: ("💩", "PSN"), 
            71: ("🔥", "FIRE/FLY"), 72: ("🔥", "FIRE/FLY"), 73: ("🔥", "FIRE/FLY"), 74: ("🤴", "WTR/PSN"), 75: ("🐟", "WTR"), 
            76: ("🐟", "WTR"), 77: ("🐱", "NORM"), 78: ("🐱", "NORM"), 79: ("🐌", "RCK/WTR"), 80: ("🐌", "RCK/WTR"), 
            81: ("🌋", "FIRE"), 82: ("🦊", "FIRE"), 83: ("🦊", "FIRE"), 84: ("🐭", "ELEC"), 85: ("🐭", "ELEC"), 
            86: ("👾", "NORM"), 87: ("👾", "NORM"), 88: ("🦕", "WTR/ICE"), 89: ("⚡", "ELEC/FLY"), 90: ("🐙", "WTR/PSN"), 
            91: ("🐙", "WTR/PSN"), 92: ("🐛", "BUG/PSN"), 93: ("🐜", "BUG/PSN"), 94: ("🐜", "BUG/PSN"), 95: ("🐛", "BUG/PSN"), 
            96: ("🐀", "GND"), 97: ("🐀", "GND"), 98: ("🐚", "WTR/ICE"), 99: ("🐚", "WTR/ICE"), 100: ("🎈", "NORM"), 
            101: ("🎈", "NORM"), 102: ("🐕", "NORM"), 103: ("🔥", "FIRE"), 104: ("⚡", "ELEC"), 105: ("💧", "WTR"), 
            106: ("💪", "FGT"), 107: ("🦇", "PSN/FLY"), 108: ("🐍", "PSN"), 109: ("🌺", "BUG/GRS"), 110: ("🌺", "BUG/GRS"), 
            111: ("🌺", "BUG/GRS"), 112: ("🐛", "BUG/PSN"), 113: ("🐝", "BUG/PSN"), 114: ("🐝", "BUG/PSN"), 115: ("🐊", "GND/RCK"), 
            116: ("🌳", "GRS/PSY"), 117: ("🦕", "RCK/WTR"), 118: ("🦕", "RCK/WTR"), 119: ("🦴", "GND"), 120: ("🦴", "GND"), 
            121: ("🧟", "FGT"), 122: ("🧟", "FGT"), 123: ("🐛", "BUG"), 124: ("🦋", "BUG"), 125: ("🦋", "BUG/FLY"), 
            126: ("💪", "FGT"), 127: ("🌞", "GRS/PSN"), 128: ("🌞", "GRS/PSN"), 129: ("🦘", "NORM"), 130: ("🦏", "GND/RCK"), 
            131: ("👽", "PSY"), 132: ("🦇", "PSN/FLY"), 133: ("🐟", "WTR"), 134: ("🐉", "WTR/FLY"), 135: ("🦵", "FGT"), 
            136: ("🥊", "FGT"), 137: ("🐂", "NORM"), 138: ("🐉", "WTR"), 139: ("🦭", "WTR/ICE"), 140: ("🐉", "WTR/ICE"), 
            141: ("🐚", "WTR/ICE"), 142: ("🐉", "DRGN"), 143: ("🐉", "DRGN"), 144: ("🐉", "DRGN/FLY"), 145: ("👽", "PSY"), 
            146: ("👺", "PSY"), 147: ("👺", "PSY"), 148: ("🦊", "PSY"), 149: ("🦊", "PSY"), 150: ("🦊", "PSY"), 
            151: ("🚜", "WTR"), 152: ("🚜", "WTR"), 153: ("🐸", "GRS/PSN"), 154: ("🐸", "GRS/PSN"), 155: ("🐸", "GRS/PSN"), 
            156: ("🦄", "FIRE"), 157: ("🧱", "RCK/GND"), 158: ("🐦", "FIRE/FLY"), 159: ("🐦", "ELEC/FLY"), 160: ("🐦", "ICE/FLY"), 
            161: ("🐲", "DRGN"), 162: ("🐲", "DRGN"), 163: ("🐉", "DRGN/FLY"), 164: ("👽", "PSY"), 165: ("🐀", "NORM"), 
            166: ("🐀", "NORM"), 167: ("🚺", "PSN"), 168: ("🚺", "PSN"), 169: ("🪨", "RCK/GND"), 170: ("🪨", "RCK/GND"), 
            171: ("🪨", "RCK/GND"), 172: ("🥔", "GRS/PSY"), 173: ("🥔", "GRS/PSY"), 174: ("🌱", "GRS/PSY"), 175: ("🌱", "GRS/PSY"), 
            176: ("🦎", "FIRE"), 177: ("🐢", "WTR"), 178: ("🐢", "WTR"), 179: ("🐢", "WTR"), 180: ("🦎", "FIRE"), 
            181: ("🦎", "FIRE"), 182: ("🐦", "NORM/FLY"), 183: ("🐦", "NORM/FLY"), 184: ("🐦", "NORM/FLY"), 185: ("🌱", "GRS/PSN"), 
            186: ("🌱", "GRS/PSN"), 187: ("🌺", "GRS/PSN"), 188: ("🌻", "GRS/PSN"), 189: ("🌻", "GRS/PSN"), 190: ("🌻", "GRS/PSN")
        }
        self.BADGE_SYMBOLS = ["🌑", "💧", "⚡", "🌈", "💀", "🔮", "🌋", "🚩"]
        
        # --- TRACKING ---
        self.total_steps = 0
        self.total_reward = 0.0
        self.cookies = 0
        self.bonks = 0
        self.level_cap = 15
        self.last_party_count = 0
        self.last_party_species = [0] * 6
        self.current_objective = "Find Oaks Parcel"
        self.graveyard = deque(maxlen=15)
        self.log_history = deque(maxlen=12)
        
        # State Tracking
        self.last_brain_update = 0 
        self.last_cookie_step = 0
        self.hunger_threshold = 1000 
        self.last_total_hp = 0
        self.last_party_levels = [0] * 6

        # --- HUD LAYOUT (32:56:32) ---
        self.console = Console()
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1)
        )
        self.layout["main"].split_row(
            Layout(name="side", ratio=32),   
            Layout(name="spacer", ratio=56), 
            Layout(name="body", ratio=32)    
        )
        self.live = Live(self.layout, refresh_per_second=10, auto_refresh=False)
        self.live.start()

    def get_ram_nickname(self, slot):
        """Reads nickname from RAM (0xD2B5)."""
        addr = 0xD2B5 + (slot * 11)
        name = ""
        for i in range(11):
            val = self.pyboy.memory[addr + i]
            if val == 0x50: break 
            if 0x80 <= val <= 0x99: name += chr(val - 0x80 + 65)
        return name if name else "NEW"

    def trigger_brain_review(self):
        """Called by the launcher to update the REVIEW counter."""
        self.last_brain_update = self.total_steps
        self.log_history.append(f"[bold magenta]{self.total_steps}: BRAIN UPDATED[/]")
        self.update_dashboard(0, "") # Force Refresh

    def get_party_info(self):
        mem = self.pyboy.memory
        party_count = mem[0xD163]
        if party_count > 6: party_count = 0 
        
        # Auto-Naming Trigger
        if party_count > self.last_party_count and self.last_party_count != 0:
            self.handle_nicknaming()
        self.last_party_count = party_count

        party_list, valid_count, evo_bonus = [], 0, 0
        current_total_hp = 0

        for i in range(party_count):
            base = 0xD16B + (i * 44)
            species = mem[base]
            
            # --- AUTOMATED LOOKUP (With Emoji) ---
            icon, type_label = self.ROM_DB.get(species, ("❓", "UNK"))
            
            hp = (mem[base + 1] << 8) + mem[base + 2]
            max_hp = (mem[base + 3] << 8) + mem[base + 4]
            lvl = mem[base + 0x21]
            nickname = self.get_ram_nickname(i)
            
            current_total_hp += hp

            # Level Up = Cookie (Resets Hunger)
            if self.last_party_levels[i] != 0 and lvl > self.last_party_levels[i]:
                self.cookies += 1
                self.last_cookie_step = self.total_steps
                self.log_history.append(f"[green]🍪 {nickname} -> L{lvl}![/]")
            self.last_party_levels[i] = lvl

            # Evolution = Big Reward (Resets Hunger)
            if self.last_party_species[i] != 0 and self.last_party_species[i] != species:
                evo_bonus += 500
                self.cookies += 5
                self.last_cookie_step = self.total_steps
                self.log_history.append(f"[bold gold1]✨ {nickname} Evolved![/]")
            self.last_party_species[i] = species

            if hp <= 0 or lvl > self.level_cap:
                death = f"{nickname} {icon}"
                if death not in self.graveyard: self.graveyard.append(death)
            else:
                valid_count += 1
            
            party_list.append({
                "icon": icon, "name": nickname, "types": type_label, 
                "lvl": lvl, "hp_str": f"{hp}/{max_hp}"
            })

        # Hunger/Bonk Logic
        if self.last_total_hp > 0 and current_total_hp < self.last_total_hp:
             self.bonks += 1
        self.last_total_hp = current_total_hp
        
        steps_since_food = self.total_steps - self.last_cookie_step
        if steps_since_food > self.hunger_threshold and self.total_steps % 100 == 0:
             self.bonks += 1

        return party_list, valid_count, evo_bonus

    def handle_nicknaming(self):
        self.log_history.append(f"[yellow]{self.total_steps}: NAMING...[/]")
        self.press_button('a', 60)
        for _ in range(5):
            for _ in range(random.randint(1, 4)):
                self.press_button(random.choice(['up', 'down', 'left', 'right']), 5)
            self.press_button('a', 12)
        self.press_button('start', 60)
        self.cookies += 5 
        self.last_cookie_step = self.total_steps 

    def press_button(self, btn, ticks):
        self.pyboy.button(btn)
        for _ in range(ticks): self.pyboy.tick()
        self.pyboy.button_release(btn)
        for _ in range(5): self.pyboy.tick()

    def update_dashboard(self, reward_delta, log_msg=""):
        self.total_reward += reward_delta
        party_data, valid_count, evo_bonus = self.get_party_info()
        mem = self.pyboy.memory
        
        # Header
        badges_val = mem[0xD356]
        badges_bin = bin(badges_val)[2:].zfill(8)[::-1]
        gallery = " ".join([self.BADGE_SYMBOLS[i] if badges_bin[i] == '1' else "⚪" for i in range(8)])
        
        steps_since_food = self.total_steps - self.last_cookie_step
        bonk_color = "red" if steps_since_food > self.hunger_threshold else "white"
        
        stats = (f"[bold green]🍪 {self.cookies}[/] | [bold {bonk_color}]🔨 {self.bonks}[/] | [bold magenta]REV: {self.last_brain_update}[/] | [bold blue]SCR: {self.total_reward:.0f}[/]\n"
                 f"BADGES: {gallery} | OBJ: {self.current_objective}")
        self.layout["header"].update(Panel(stats, style="white on black"))

        # Team Table
        team = Table(expand=True, box=None)
        team.add_column("PKMN", style="bold yellow")
        team.add_column("TYPE", justify="center")
        team.add_column("LVL", justify="right")
        team.add_column("HP", justify="right")
        for p in party_data:
            # Displays the Emoji Sprite (if terminal supports it)
            team.add_row(f"{p['icon']} {p['name']}", p["types"], str(p["lvl"]), p["hp_str"])
        self.layout["side"].update(Panel(team, title="ACTIVE TEAM", border_style="yellow"))

        # Log with Step Count
        if log_msg: 
            self.log_history.append(f"{self.total_steps}: {log_msg}")
            
        map_id = mem[0xD35E]
        x_coord = mem[0xD362]
        y_coord = mem[0xD361]
        telemetry = f"MAP:{map_id:03d} POS:({x_coord},{y_coord})"
        combined = f"[dim]{telemetry}[/dim]\n" + \
                   "[bold blue]LOGS[/]\n" + "\n".join(self.log_history) + \
                   "\n\n[bold red]GRAVE[/]\n" + "\n".join(self.graveyard)
        self.layout["body"].update(Panel(combined, title="DATA", border_style="blue"))
        self.layout["spacer"].update(Panel("", border_style="white"))
        self.live.refresh()
        return evo_bonus

    def step(self, action):
        self.pyboy.set_emulation_speed(1)
        self.total_steps += 1
        btns = ['up','down','left','right','a','b','start','select']
        btn = btns[action]
        self.press_button(btn, 24)
        
        evo_bonus = self.update_dashboard(-0.1, f">> {btn.upper()}")
        return np.zeros(10, dtype=np.uint8), float(-0.1 + evo_bonus), False, False, {}

    def reset(self, seed=None, options=None):
        with open("states/outside.state", "rb") as f: self.pyboy.load_state(f)
        self.last_party_species = [0] * 6
        self.pyboy.set_emulation_speed(1)
        return np.zeros(10, dtype=np.uint8), {}

    def close(self):
        self.live.stop(); self.pyboy.stop()