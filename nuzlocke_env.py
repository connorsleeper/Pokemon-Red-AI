import gymnasium as gym
from gymnasium import spaces
import numpy as np
from pyboy import PyBoy
from collections import deque

class NuzlockeEnv(gym.Env):
    def __init__(self, rom_path, state_path):
        super(NuzlockeEnv, self).__init__()
        
        # 1. EMULATOR SETUP
        self.pyboy = PyBoy(rom_path, window="SDL2") 
        self.pyboy.set_emulation_speed(1)
        
        with open(state_path, "rb") as f:
            self.pyboy.load_state(f)
            
        self.action_space = spaces.Discrete(8)
        self.observation_space = spaces.Box(low=0, high=255, shape=(10,), dtype=np.uint8)
        
        # --- RENDER HOOK ---
        self.render_callback = None
        
        # --- PHYSICAL APPEARANCE DATABASE ---
        self.ROM_DB = {
            153: ("Bulbasaur", "🐸", "GRS"), 154: ("Ivysaur", "🐸", "GRS"), 155: ("Venusaur", "🌺", "GRS"),
            176: ("Charmander", "🦎", "FIR"), 178: ("Charmeleon", "🦎", "FIR"), 180: ("Charizard", "🐉", "FIR"),
            177: ("Squirtle", "🐢", "WTR"), 179: ("Wartortle", "🐢", "WTR"), 181: ("Blastoise", "🐢", "WTR"),
            123: ("Caterpie", "🐛", "BUG"), 124: ("Metapod", "Cocoon", "BUG"), 125: ("Butterfree", "🦋", "BUG"),
            112: ("Weedle", "🐛", "BUG"), 113: ("Kakuna", "Cocoon", "BUG"), 114: ("Beedrill", "🐝", "BUG"),
            36: ("Pidgey", "🐦", "FLY"), 150: ("Pidgeotto", "🦅", "FLY"), 151: ("Pidgeot", "🦅", "FLY"),
            165: ("Rattata", "🐀", "NRM"), 166: ("Raticate", "🐀", "NRM"),
            5: ("Spearow", "🐦", "FLY"), 35: ("Fearow", "🦅", "FLY"),
            108: ("Ekans", "🐍", "PSN"), 45: ("Arbok", "🐍", "PSN"),
            84: ("Pikachu", "🐭", "ELC"), 85: ("Raichu", "🐭", "ELC"),
            96: ("Sandshrew", "🐁", "GND"), 97: ("Sandslash", "🦔", "GND"),
            15: ("NidoranF", "🐇", "PSN"), 168: ("Nidorina", "🐇", "PSN"), 16: ("Nidoqueen", "👑", "PSN"),
            3: ("NidoranM", "🐇", "PSN"), 167: ("Nidorino", "🐇", "PSN"), 7: ("Nidoking", "👑", "PSN"),
            4: ("Clefairy", "🧚", "NRM"), 142: ("Clefable", "🧚", "NRM"),
            82: ("Vulpix", "🦊", "FIR"), 83: ("Ninetales", "🦊", "FIR"),
            100: ("Jigglypuff", "🎈", "NRM"), 101: ("Wigglytuff", "🎈", "NRM"),
            107: ("Zubat", "🦇", "PSN"), 130: ("Golbat", "🦇", "PSN"),
            185: ("Oddish", "🌱", "GRS"), 186: ("Gloom", "🌺", "GRS"), 187: ("Vileplume", "🌺", "GRS"),
            109: ("Paras", "🦀", "BUG"), 46: ("Parasect", "🦀", "BUG"),
            65: ("Venonat", "👾", "BUG"), 119: ("Venomoth", "🦋", "BUG"),
            59: ("Diglett", "🥔", "GND"), 118: ("Dugtrio", "🥔", "GND"),
            77: ("Meowth", "🐱", "NRM"), 144: ("Persian", "🐆", "NRM"),
            47: ("Psyduck", "🦆", "WTR"), 128: ("Golduck", "🦆", "WTR"),
            57: ("Mankey", "🐒", "FGT"), 117: ("Primeape", "🦍", "FGT"),
            33: ("Growlithe", "🐕", "FIR"), 48: ("Arcanine", "🐕", "FIR"),
            71: ("Poliwag", "tadpole", "WTR"), 110: ("Poliwhirl", "🐸", "WTR"), 143: ("Poliwrath", "🐸", "FGT"),
            148: ("Abra", "🦊", "PSY"), 38: ("Kadabra", "🦊", "PSY"), 149: ("Alakazam", "🧙", "PSY"),
            106: ("Machop", "💪", "FGT"), 41: ("Machoke", "💪", "FGT"), 126: ("Machamp", "💪", "FGT"),
            188: ("Bellsprout", "🌱", "GRS"), 189: ("Weepinbell", "🌱", "GRS"), 190: ("Victreebel", "🌱", "GRS"),
            24: ("Tentacool", "🦑", "WTR"), 154: ("Tentacruel", "🦑", "WTR"),
            169: ("Geodude", "🪨", "RCK"), 39: ("Graveler", "🪨", "RCK"), 49: ("Golem", "🪨", "RCK"),
            163: ("Ponyta", "🐎", "FIR"), 164: ("Rapidash", "🦄", "FIR"),
            37: ("Slowpoke", "🦥", "WTR"), 8: ("Slowbro", "🐚", "WTR"),
            173: ("Magnemite", "🧲", "ELC"), 174: ("Magneton", "🧲", "ELC"),
            64: ("Farfetch'd", "🦆", "NRM"),
            70: ("Doduo", "🐦", "FLY"), 116: ("Dodrio", "🐦", "FLY"),
            58: ("Seel", "🦭", "WTR"), 120: ("Dewgong", "🦭", "WTR"),
            13: ("Grimer", "💩", "PSN"), 136: ("Muk", "💩", "PSN"),
            23: ("Shellder", "🐚", "WTR"), 139: ("Cloyster", "🐚", "WTR"),
            25: ("Gastly", "👻", "GST"), 147: ("Haunter", "👻", "GST"), 14: ("Gengar", "😈", "GST"),
            34: ("Onix", "🐍", "RCK"),
            48: ("Drowzee", "🐘", "PSY"), 115: ("Hypno", "PENDULUM", "PSY"),
            76: ("Krabby", "🦀", "WTR"), 138: ("Kingler", "🦀", "WTR"),
            6: ("Voltorb", "🔴", "ELC"), 141: ("Electrode", "🔴", "ELC"),
            12: ("Exeggcute", "🥚", "GRS"), 10: ("Exeggutor", "🌴", "GRS"),
            17: ("Cubone", "🦴", "GND"), 145: ("Marowak", "🦴", "GND"),
            43: ("Hitmonlee", "🥋", "FGT"), 44: ("Hitmonchan", "🥊", "FGT"),
            11: ("Lickitung", "👅", "NRM"),
            55: ("Koffing", "☁️", "PSN"), 143: ("Weezing", "☁️", "PSN"),
            1: ("Rhyhorn", "🦏", "GND"), 2: ("Rhydon", "🦏", "GND"),
            40: ("Chansey", "🥚", "NRM"),
            30: ("Tangela", "🍝", "GRS"),
            2: ("Kangaskhan", "🦘", "NRM"),
            92: ("Horsea", "🌊", "WTR"), 93: ("Seadra", "🌊", "WTR"),
            157: ("Goldeen", "🐟", "WTR"), 158: ("Seaking", "🐟", "WTR"),
            27: ("Staryu", "⭐", "WTR"), 152: ("Starmie", "⭐", "WTR"),
            42: ("Mr. Mime", "🤡", "PSY"),
            26: ("Scyther", "🦗", "BUG"),
            72: ("Jynx", "💋", "ICE"),
            53: ("Electabuzz", "⚡", "ELC"),
            51: ("Magmar", "🔥", "FIR"),
            29: ("Pinsir", "🦗", "BUG"),
            60: ("Tauros", "🐂", "NRM"),
            133: ("Magikarp", "🐟", "WTR"), 22: ("Gyarados", "🐉", "WTR"),
            19: ("Lapras", "🦕", "WTR"),
            76: ("Ditto", "😐", "NRM"),
            102: ("Eevee", "🐕", "NRM"), 105: ("Vaporeon", "🧜", "WTR"), 104: ("Jolteon", "⚡", "ELC"), 103: ("Flareon", "🔥", "FIR"),
            170: ("Porygon", "👾", "NRM"),
            98: ("Omanyte", "🐚", "RCK"), 99: ("Omastar", "🐚", "RCK"),
            90: ("Kabuto", "🐚", "RCK"), 91: ("Kabutops", "🐚", "RCK"),
            171: ("Aerodactyl", "🦖", "FLY"),
            132: ("Snorlax", "😴", "NRM"),
            74: ("Articuno", "❄️", "ICE"), 75: ("Zapdos", "⚡", "ELC"), 73: ("Moltres", "🔥", "FIR"),
            88: ("Dratini", "🐉", "DRG"), 89: ("Dragonair", "🐉", "DRG"), 66: ("Dragonite", "🐉", "DRG"),
            131: ("Mewtwo", "🧬", "PSY"), 21: ("Mew", "🧬", "PSY")
        }
        
        self.party_info = [] 
        self.total_steps = 0
        self.cookies = 0
        self.bonks = 0
        self.last_brain_update = 0
        self.map_id = 0
        self.x, self.y = 0, 0
        self.badges = 0
        self.current_objective = "OAK'S PARCEL"
        
        self.graveyard = deque(maxlen=8)
        self.log_history = deque(maxlen=20)
        self.last_party_count = 0
        self.last_party_levels = [0] * 6
        self.last_party_species = [0] * 6
        self.last_total_hp = 0
        self.last_cookie_step = 0
        self.hunger_threshold = 1000

    def set_render_callback(self, callback):
        """Allows the GUI to update while the emulator holds buttons."""
        self.render_callback = callback

    def render(self):
        try:
            raw = np.array(self.pyboy.screen.ndarray, dtype=np.uint8, copy=True, order='C')
            if raw.shape == (144, 160, 4): return raw[:, :, :3]
            if raw.shape == (144, 160, 3): return raw
            return np.zeros((144, 160, 3), dtype=np.uint8)
        except:
            return np.zeros((144, 160, 3), dtype=np.uint8)

    def get_ram_nickname(self, slot):
        addr = 0xD2B5 + (slot * 11)
        name = ""
        for i in range(11):
            val = self.pyboy.memory[addr + i]
            if val == 0x50: break 
            if 0x80 <= val <= 0x99: name += chr(val - 0x80 + 65)
        return name if name else "NEW"

    def get_objective(self):
        if self.badges == 0: return "DELIVER PARCEL -> BROCK"
        if self.badges == 1: return "MT MOON -> MISTY"
        if self.badges == 2: return "SS ANNE -> SURGE"
        if self.badges == 3: return "ROCK TUNNEL -> ERIKA"
        if self.badges == 4: return "POKEMON TOWER -> KOGA"
        return "BECOME CHAMPION"

    def update_data(self):
        mem = self.pyboy.memory
        self.map_id = mem[0xD35E]
        self.x = mem[0xD362]
        self.y = mem[0xD361]
        self.badges = bin(mem[0xD356]).count('1')
        self.current_objective = self.get_objective()
        
        party_count = mem[0xD163]
        if party_count > 6: party_count = 0
        
        if party_count > self.last_party_count and self.last_party_count != 0:
            self.handle_nicknaming()
        self.last_party_count = party_count

        self.party_info = []
        current_total_hp = 0

        for i in range(party_count):
            base = 0xD16B + (i * 44)
            species = mem[base]
            name, emoji, type_label = self.ROM_DB.get(species, ("UNK", "❓", "???"))
            
            hp = (mem[base + 1] << 8) + mem[base + 2]
            max_hp = (mem[base + 0x22] << 8) + mem[base + 0x23] 
            lvl = mem[base + 0x21]
            nickname = self.get_ram_nickname(i)
            current_total_hp += hp

            if self.last_party_levels[i] != 0 and lvl > self.last_party_levels[i]:
                self.cookies += 1
                self.last_cookie_step = self.total_steps
            self.last_party_levels[i] = lvl
            
            if hp == 0 and max_hp > 0:
                 death_msg = f"{nickname} ({emoji})"
                 if death_msg not in self.graveyard:
                     self.graveyard.append(death_msg)

            self.party_info.append({
                "name": nickname,
                "species": name,
                "emoji": emoji,   
                "type": type_label,
                "lvl": lvl,
                "hp": hp,
                "max_hp": max_hp,
                "pct": hp / max_hp if max_hp > 0 else 0
            })

        if self.last_total_hp > 0 and current_total_hp < self.last_total_hp:
             self.bonks += 1
        self.last_total_hp = current_total_hp
        
        if (self.total_steps - self.last_cookie_step) > self.hunger_threshold and self.total_steps % 100 == 0:
             self.bonks += 1

    def handle_nicknaming(self):
        for _ in range(50):
            self.pyboy.button('a')
            self.pyboy.tick()
            if self.render_callback: self.render_callback()
        self.pyboy.button_release('a')
        self.cookies += 5
        self.last_cookie_step = self.total_steps

    def step(self, action):
        self.total_steps += 1
        btn_map = ['UP','DOWN','LEFT','RIGHT','A','B','START','SELECT']
        btn = btn_map[action]
        
        # --- THE FIX: RENDER WHILE HOLDING ---
        # 16 Frames Hold (0.25s)
        for _ in range(16):
            self.pyboy.button(btn.lower())
            self.pyboy.tick()
            # ** FORCE GUI UPDATE **
            if self.render_callback: self.render_callback()
        
        # 16 Frames Cooldown (0.25s)
        self.pyboy.button_release(btn.lower())
        for _ in range(16):
            self.pyboy.tick()
            # ** FORCE GUI UPDATE **
            if self.render_callback: self.render_callback()
        
        log_entry = f"{self.total_steps} | M{self.map_id} | ({self.x},{self.y}) | {btn}"
        self.log_history.append(log_entry)
        
        self.update_data()
        return np.zeros(10, dtype=np.uint8), 0, False, False, {}

    def reset(self, seed=None, options=None):
        with open("states/outside.state", "rb") as f: self.pyboy.load_state(f)
        return np.zeros(10, dtype=np.uint8), {}
    
    def trigger_brain_review(self):
        self.last_brain_update = self.total_steps
        self.log_history.append(f"*** BRAIN UPDATE: {self.total_steps} ***")

    def close(self):
        self.pyboy.stop()