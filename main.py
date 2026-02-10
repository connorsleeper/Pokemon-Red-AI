import os
import glob
import random
from pyboy import PyBoy

# --- CONFIGURATION ---
ROM_PATH = "PokemonRed.gb"
STATES_DIR = "states"

# --- MEMORY ADDRESSES ---
MEM_HP_CURRENT = 0xD16C  # 2 Bytes (Current HP of Party Leader)
MEM_MAP_ID     = 0xD35E  
MEM_X_COORD    = 0xD362
MEM_Y_COORD    = 0xD361
MEM_PARTY_COUNT = 0xD163 

# --- OBJECTIVE ---
ITEM_ID_PARCEL = 70      # Oak's Parcel

# --- SCOREBOARD ---
cookies = 0  
bonks = 0    

def load_latest_state(pyboy):
    """Loads the most recent save state."""
    if not os.path.exists(STATES_DIR):
        print("? Error: 'states' folder missing.")
        return False
        
    files = glob.glob(os.path.join(STATES_DIR, "*.state"))
    if not files:
        print("? Error: No .state files found!")
        return False
    
    latest = max(files, key=os.path.getmtime)
    print(f"? Loading state: {os.path.basename(latest)}...")
    with open(latest, "rb") as f:
        pyboy.load_state(f)
    return True

def check_inventory_for_parcel(pyboy):
    """Scans memory for Oak's Parcel."""
    item_count = pyboy.memory[0xD31D]
    for i in range(item_count):
        addr = 0xD31E + (i * 2)
        if pyboy.memory[addr] == ITEM_ID_PARCEL:
            return True
    return False

def get_gps_weights(curr_map, curr_x, curr_y):
    """Drunken GPS Navigation."""
    target_x, target_y = curr_x, curr_y
    mode = "Roaming"
    
    # PALLET TOWN -> Go North
    if curr_map == 0:
        target_x, target_y = 10, 0
        mode = "Go North (Route 1)"
    # ROUTE 1 -> Go North
    elif curr_map == 12:
        target_x, target_y = 10, 0
        mode = "Go North (Viridian)"
    # VIRIDIAN CITY -> Go to Mart
    elif curr_map == 1:
        target_x, target_y = 29, 19
        mode = "Find Mart"
    # INSIDE MART -> Clerk
    elif curr_map == 6:
        target_x, target_y = 4, 1 
        mode = "Talk to Clerk"
    else:
        # INDOORS -> Leave
        return [0, 50, 5, 5, 20, 5], "Exit Building"

    dx = target_x - curr_x
    dy = target_y - curr_y
    weights = [5, 5, 5, 5, 5, 2] 
    
    if dy < 0: weights[0] += 40 
    if dy > 0: weights[1] += 40 
    if dx < 0: weights[2] += 40 
    if dx > 0: weights[3] += 40 
    
    return weights, mode

# --- MAIN EXECUTION ---
pyboy = PyBoy(ROM_PATH, window_type="SDL2")
pyboy.set_emulation_speed(1)

if not load_latest_state(pyboy):
    exit()

print("--- NUZLOCKE MODE ACTIVE ---")
print("??? SPAWN PROTECTION: AI is invincible for 5 seconds.")

step_count = 0
grace_period = 300 # 5 Seconds of immunity

while pyboy.tick():
    step_count += 1
    
    # --- 1. HEALTH MONITOR (With Safety Checks) ---
    hp_current = (pyboy.memory[MEM_HP_CURRENT] << 8) + pyboy.memory[MEM_HP_CURRENT + 1]
    party_count = pyboy.memory[MEM_PARTY_COUNT]

    # ONLY check for death if:
    # 1. We have passed the grace period (Invincibility frame)
    # 2. We actually have a Pokemon (Party > 0)
    if step_count > grace_period and party_count > 0:
        if hp_current == 0:
            bonks += 1
            print(f"\n?? FAINTED! (Bonks: {bonks}) - RESTARTING TIMELINE...")
            load_latest_state(pyboy)
            step_count = 0 # Reset invincibility timer on reload
            continue 

    # --- 2. OBJECTIVE MONITOR ---
    if check_inventory_for_parcel(pyboy):
        cookies += 1
        print(f"\n?? COOKIE EARNED! Oak's Parcel Obtained!")
        if not os.path.exists(STATES_DIR): os.makedirs(STATES_DIR)
        with open(os.path.join(STATES_DIR, "tutorial_parcel.state"), "wb") as f:
            pyboy.save_state(f)
        print("? MISSION COMPLETE. Shutting down.")
        break

    # --- 3. NAVIGATION ---
    curr_map = pyboy.memory[MEM_MAP_ID]
    curr_x   = pyboy.memory[MEM_X_COORD]
    curr_y   = pyboy.memory[MEM_Y_COORD]
    weights, mode = get_gps_weights(curr_map, curr_x, curr_y)
    
    # --- 4. ACTION ---
    actions = ['up', 'down', 'left', 'right', 'a', 'b']
    choice = random.choices(actions, weights=weights, k=1)[0]
    
    hold = 5
    for _ in range(hold):
        pyboy.button(choice)
        pyboy.tick()
    pyboy.button_release(choice)
    
    # --- 5. LOGGING ---
    if step_count % 60 == 0:
        # Show "INV" if in grace period
        hp_display = "INV" if step_count < grace_period else hp_current
        print(f"[Map:{curr_map}] HP:{hp_display} | Mode: {mode:<20} | Bonks: {bonks} | Cookies: {cookies}")
        
    for _ in range(10): pyboy.tick()