import gymnasium as gym
from gymnasium import spaces
import numpy as np
from pyboy import PyBoy
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from collections import deque

class NuzlockeEnv(gym.Env):
    def __init__(self, rom_path, state_path):
        super(NuzlockeEnv, self).__init__()
        self.pyboy = PyBoy(rom_path, window_type="SDL2")
        self.pyboy.set_emulation_speed(1)
        with open(state_path, "rb") as f:
            self.pyboy.load_state(f)
            
        self.action_space = spaces.Discrete(8)
        self.observation_space = spaces.Box(low=0, high=255, shape=(10,), dtype=np.uint8)
        
        # --- TELEMENTRY & ECONOMY ---
        self.total_steps = 0
        self.total_reward = 0.0
        self.cookies = 0
        self.bonks = 0
        self.level_cap = 15
        self.last_badges = 0
        self.last_hp = 0
        
        # --- STORY TRACKING ---
        self.seen_key_items = set()
        self.key_item_ids = {70, 57, 63, 64, 69, 72, 73, 74, 196, 197, 198, 199, 200}
        self.current_objective = "Get Oak's Parcel"

        # --- DASHBOARD CONFIG ---
        self.console = Console()
        self.log_history = deque(maxlen=35) 
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body", ratio=1)
        )
        
        self.live = Live(self.layout, refresh_per_second=10, auto_refresh=False)
        self.live.start()

    def update_objective(self, mem):
        # Logic to update the HUD objective string based on inventory/events
        badges = mem[0xD356]
        has_parcel = 70 in self.seen_key_items
        
        if badges == 0:
            self.current_objective = "Deliver Parcel to Oak" if has_parcel else "Find Oak's Parcel"
        elif badges == 1: self.current_objective = "Misty (Cerulean Gym)"
        elif badges == 2: self.current_objective = "Lt. Surge (Vermilion Gym)"
        # Add more as he progresses!

    def update_dashboard(self, hp, party, badges, reward_delta, log_msg=""):
        self.total_reward += reward_delta
        
        # Top HUD: Economy & Stats
        stats = (f"[bold green]STEP:[/bold green] {self.total_steps} | "
                 f"[bold blue]BADGES:[/bold blue] {badges} | "
                 f"[bold red]SCORE:[/bold red] {self.total_reward:.1f} | "
                 f"[bold white]?? {self.cookies}[/bold white] | "
                 f"[bold orange3]?? {self.bonks}[/bold orange3]")
        
        obj_text = f"[bold cyan]CURRENT OBJECTIVE:[/bold cyan] {self.current_objective} | [bold yellow]PARTY:[/bold yellow] {party}/6"
        
        full_header = stats + "\n" + obj_text
        self.layout["header"].update(Panel(full_header, style="white on black"))
        
        if log_msg: self.log_history.append(log_msg)
        self.layout["body"].update(Panel("\n".join(self.log_history), title="[bold white]LIVE TELEMETRY[/bold white]", border_style="blue"))
        self.live.refresh()

    def step(self, action):
        self.total_steps += 1
        reward = -0.1
        log_msg = ""
        
        mem = self.pyboy.memory
        # --- TELEMETRY ---
        curr_hp = (mem[0xD16C] << 8) + mem[0xD16D]
        map_id = mem[0xD35E]
        x_coord = mem[0xD362]
        y_coord = mem[0xD361]
        in_battle = mem[0xD057] == 1
        
        # --- ACTION ---
        btn_list = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'A', 'B', 'START', 'SELECT']
        btn = btn_list[action]
        self.pyboy.button(btn.lower())
        for _ in range(24): self.pyboy.tick()
        self.pyboy.button_release(btn.lower())
        for _ in range(5): self.pyboy.tick()

        # --- REWARDS & LOGS ---
        self.update_objective(mem)
        valid_mons = 0 # (Insert your full check_party_status logic here)
        
        # Badge Reward
        if mem[0xD356] > self.last_badges:
            r = 2000; reward += r; self.cookies += 1
            log_msg = f"[bold cyan]?? COOKIE: NEW BADGE! (+{r})[/bold cyan]"
            self.last_badges = mem[0xD356]
        
        # Potion Bonk
        elif in_battle and curr_hp > self.last_hp and self.last_hp != 0:
            r = 50; reward -= r; self.bonks += 1
            log_msg = f"[bold orange3]?? BONK: ILLEGAL HEAL! (-{r})[/bold orange3]"

        # Standard Telemetry Log
        if not log_msg:
            log_msg = f"[dim]MAP:{map_id} ({x_coord},{y_coord}) | ACTION:{btn} | HP:{curr_hp}[/dim]"

        self.last_hp = curr_hp
        self.update_dashboard(curr_hp, 6, mem[0xD356], reward, log_msg)
        
        return np.zeros(10, dtype=np.uint8), float(reward), False, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        with open("states/outside.state", "rb") as f:
            self.pyboy.load_state(f)
        # End-of-Run Summary
        print(f"\n--- BRAIN REVIEW: Steps {self.total_steps} | Cookies: {self.cookies} | Bonks: {self.bonks} ---")
        return np.zeros(10, dtype=np.uint8), {}

    def close(self):
        if self.live: self.live.stop()
        # Final Exit Summary
        print("\n" + "="*40)
        print(f"?? FINAL SESSION SUMMARY")
        print(f"   Total Score: {self.total_reward:.2f}")
        print(f"   Total Cookies: {self.cookies}")
        print(f"   Total Bonks: {self.bonks}")
        print("="*40)
        super().close()