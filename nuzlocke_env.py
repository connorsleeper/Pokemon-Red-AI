import gymnasium as gym
from gymnasium import spaces
import numpy as np
from pyboy import PyBoy

class NuzlockeEnv(gym.Env):
    def __init__(self, rom_path, state_path):
        super(NuzlockeEnv, self).__init__()
        
        # 1. SETUP - NORMAL SPEED (1x)
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

    def get_family_id(self, species_id):
        family_map = {
            1:1, 2:1, 3:1, # Bulbasaur
            4:4, 5:4, 6:4, # Charmander
            7:7, 8:7, 9:7, # Squirtle
            16:16, 17:16, 18:16, # Pidgey
            19:19, 20:19, # Rattata
        }
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

    def step(self, action):
        self.total_steps += 1
        
        # --- THE EXISTENCE TAX ---
        # He loses a tiny bit of score every step.
        # This forces him to keep moving to "break even".
        reward = -0.1 
        
        terminated = False
        bonk_msg = ""
        cookie_msg = ""
        guardian_active = False
        guardian_reason = ""
        
        # --- A. READ STATE ---
        mem = self.pyboy.memory
        in_battle = mem[0xD057] == 1
        battle_menu = mem[0xCC26]
        is_trainer = mem[0xD05C] != 0
        enemy_species = mem[0xCFE5]
        enemy_family = self.get_family_id(enemy_species)
        map_id = mem[0xD35E]
        
        # Catchability Check
        is_dupe = enemy_family in self.caught_species
        route_cleared = map_id in self.caught_locations
        is_catchable = not is_trainer and not is_dupe and not route_cleared

        # --- B. GUARDIAN LOGIC ---
        if in_battle and action == 4 and battle_menu == 1:
            if is_trainer:
                action = 5 
                guardian_active = True
                guardian_reason = "NO ITEMS VS TRAINER"
                reward -= 10
                bonk_msg = "Items banned in Trainer Battles!"
            elif not is_catchable:
                action = 5 
                guardian_active = True
                guardian_reason = "SAVE BALLS (Illegal Target)"
            else:
                reward += 5 
                cookie_msg = "Good throw attempt!"

        # Potion Check
        curr_hp = (mem[0xD16C] << 8) + mem[0xD16D]
        if in_battle and curr_hp > self.last_hp and self.last_hp != 0:
            reward -= 50
            bonk_msg = "POTION DETECTED! No Healing in Battle!"
        self.last_hp = curr_hp

        # --- C. EXECUTE ACTION (HEAVY PRESS) ---
        button_map = {0:'up', 1:'down', 2:'left', 3:'right', 4:'a', 5:'b', 6:'start', 7:'select'}
        btn = button_map[action]
        
        self.pyboy.button(btn)
        for _ in range(24): self.pyboy.tick() # Hold for 0.4s
        self.pyboy.button_release(btn)
        for _ in range(5): self.pyboy.tick()

        # --- D. POST-ACTION CHECKS ---
        if in_battle:
            eff = mem[0xD05D]
            if eff > 10:
                reward += 20
                mem[0xD05D] = 10 
                cookie_msg = "Super Effective!"
            elif eff < 10 and eff > 0:
                reward -= 20
                mem[0xD05D] = 10
                bonk_msg = "Not Very Effective..."

        # GAME OVER CHECK
        valid_mons_left = self.check_party_status()
        if valid_mons_left == 0:
            terminated = True
            reward -= 100
            bonk_msg = "GAME OVER: All Pokemon Dead or Over-Leveled!"

        # --- E. LOGGING ---
        if bonk_msg or cookie_msg or guardian_active:
            print("-" * 40)
            if guardian_active:
                print(f"??? GUARDIAN: {guardian_reason}")
            elif cookie_msg == "Good throw attempt!":
                print(f"?? AI ACTION: ATTEMPT CATCH (Allowed)")
            else:
                print(f"?? AI ACTION: {btn.upper()}")
            
            if cookie_msg: print(f"?? COOKIE: {cookie_msg}")
            if bonk_msg:   print(f"?? BONK: {bonk_msg}")
            print("-" * 40)
            
        else:
            status = "?? BATTLE" if in_battle else "?? ROAMING"
            print(f"[Step {self.total_steps}] Status: {status} | Action: {btn.upper()} | HP: {curr_hp} | Valid Mons: {valid_mons_left}")

        obs = np.array([curr_hp, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint8)
        return obs, reward, terminated, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        with open("states/outside.state", "rb") as f:
            self.pyboy.load_state(f)
        self.total_steps = 0
        return self.step(0)[0], {}