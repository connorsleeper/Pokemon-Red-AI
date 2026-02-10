import gymnasium as gym
from gymnasium import spaces
import numpy as np
from pyboy import PyBoy
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from collections import deque

class NuzlockeEnv(gym.Env):
    def __init__(self, rom_path, state_path):
        super(NuzlockeEnv, self).__init__()
        
        # 1. SETUP
        self.pyboy = PyBoy(rom_path, window_type="SDL2")
        self.pyboy.set_emulation_speed(1)
        
        with open(state_path, "rb") as f:
            self.pyboy.load_state(f)
            
        self.action_space = spaces.Discrete(8)
        self.observation_space = spaces.Box(low=0, high=255, shape=(10,), dtype=np.uint8)
        
        # 2. TRACKING
        self.caught_species = set()
        self.caught_locations = set()
        self.level_cap = 15 
        self.banned_species = {144, 145, 146, 150, 151} 
        
        self.last_hp = 0
        self.total_steps = 0
        self.last_badges = 0
        self.seen_key_items = set()
        self.key_item_ids = {70, 57, 63, 64, 69, 72, 73, 74, 196, 197, 198, 199, 200}

        # 3. DASHBOARD SETUP
        self.console = Console()
        self.log_history = deque(maxlen=8) # Keeps the last 8 lines
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body")
        )
        # We start the "Live" display in a non-blocking way
        self.live = Live(self.layout, refresh_per_second=4, auto_refresh=True)
        self.live.start()

    def get_family_id(self, species_id):
        # Simplified mapping (Add full list if needed)
        family_map = {1:1, 2:1, 3:1, 4:4, 5:4, 6:4, 7:7, 8:7, 9:7}
        return family_map.get(species_id, species_id)

    def check_party_status(self):
        mem = self.pyboy.memory
        party_count = mem[0xD163]
        valid_mons = 0
        for i in range(party_count):
            base_addr = 0xD16B + (i * 44)
            hp = (mem[base_addr + 1] << 8) + mem[base_addr + 2]
            level = mem[base_addr + 0x21]
            species = mem[base_addr]
            
            is_alive = hp > 0
            is_legal_level = level <= self.level_cap
            is_legal_species = species not in self.banned_species
            
            if is_alive and is_legal_level and is_legal_species:
                valid_mons += 1
        return valid_mons

    def update_dashboard(self, step, hp, party_count, badges, last_action, reward, log_msg=""):
        # 1. Update Header (Fixed Info)
        status_text = f"[bold green]STEPS:[/bold green] {step} | [bold blue]BADGES:[/bold blue] {badges} | [bold red]HP:[/bold red] {hp} | [bold yellow]ALIVE:[/bold yellow] {party_count}/6"
        self.layout["header"].update(Panel(status_text, title="?? POKEMON RED AI HUD"))

        # 2. Update Log (Scrolling Info)
        if log_msg:
            self.log_history.append(log_msg)
        
        log_content = "\n".join(self.log_history)
        self.layout["body"].update(Panel(log_content, title="?? EVENT LOG"))

    def step(self, action):
        self.total_steps += 1
        reward = -0.1 # Existence Tax
        terminated = False
        log_msg = ""
        
        # --- READ STATE ---
        mem = self.pyboy.memory
        curr_hp = (mem[0xD16C] << 8) + mem[0xD16D]
        curr_badges = mem[0xD356]
        
        # --- STORY CHECKS ---
        if curr_badges > self.last_badges:
            reward += 2000
            log_msg = f"[bold cyan]?? NEW BADGE EARNED! (+2000)[/bold cyan]"
            self.last_badges = curr_badges
            self.level_cap += 10
        
        # Key Items
        item_count = mem[0xD31D]
        for i in range(item_count):
            item_id = mem[0xD31E + (i*2)]
            if item_id in self.key_item_ids and item_id not in self.seen_key_items:
                reward += 1000
                log_msg = f"[bold magenta]?? FOUND KEY ITEM {item_id}! (+1000)[/bold magenta]"
                self.seen_key_items.add(item_id)

        # --- COMBAT / GUARDIAN LOGIC ---
        # (Simplified for brevity - your logic goes here!)
        button_map = {0:'up', 1:'down', 2:'left', 3:'right', 4:'a', 5:'b', 6:'start', 7:'select'}
        btn = button_map[action]
        
        # EXECUTE
        self.pyboy.button(btn)
        for _ in range(24): self.pyboy.tick()
        self.pyboy.button_release(btn)
        for _ in range(5): self.pyboy.tick()

        # Check Party
        valid_mons = self.check_party_status()
        if valid_mons == 0:
            terminated = True
            reward -= 100
            log_msg = "[bold red]?? GAME OVER: TEAM WIPED[/bold red]"

        # --- LOGGING ---
        # We only log "interesting" things to keep the chat clean
        if not log_msg:
            # Standard movement log (grayed out so it's subtle)
            log_msg = f"[dim]Step {self.total_steps}: {btn.upper()} (HP: {curr_hp})[/dim]"
        
        # Update the HUD
        self.update_dashboard(self.total_steps, curr_hp, valid_mons, curr_badges, btn, reward, log_msg)

        obs = np.array([curr_hp, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint8)
        return obs, reward, terminated, False, {}

    def close(self):
        self.live.stop() # Clean up the display when done
        super().close()