from pyboy import PyBoy
import os
import sys

# --- FORCE THE PATH ---
script_dir = os.path.dirname(os.path.abspath(__file__))
rom_path = os.path.join(script_dir, "PokemonRed.gb")
states_dir = os.path.join(script_dir, "states")

if not os.path.exists(states_dir):
    os.makedirs(states_dir)

if not os.path.exists(rom_path):
    print(f"? ERROR: Cannot find ROM at: {rom_path}")
    sys.exit(1)

# --- START GAME ---
print("-------------------------------------------------")
print("?? MANUAL MODE STARTED")
print("1. Play using the window.")
print("2. When ready to save, CLICK THIS TERMINAL.")
print("3. Press Ctrl+C to save 'manual_entry.state'.")
print("-------------------------------------------------")

pyboy = PyBoy(rom_path, window_type="SDL2")
pyboy.set_emulation_speed(1)

try:
    while pyboy.tick():
        pass
except KeyboardInterrupt:
    print("\n?? SNAPSHOT! Saving 'manual_entry.state'...")
    save_path = os.path.join(states_dir, "manual_entry.state")
    with open(save_path, "wb") as f:
        pyboy.save_state(f)
    print(f"? SUCCESS! Saved to {save_path}")
    pyboy.stop()