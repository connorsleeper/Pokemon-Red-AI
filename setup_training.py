from pyboy import PyBoy
import os
import sys

# Ensure the states folder exists
if not os.path.exists("states"):
    os.makedirs("states")

rom_path = "PokemonRed.gb"
pyboy = PyBoy(rom_path, window_type="SDL2")
pyboy.set_emulation_speed(1) # Normal speed

# --- LOAD EXISTING STATE ---
# We try to find your best save file
possible_states = [
    "states/rival_defeated.state",
    "states/has_starter.state",
    "has_starter.state",  # Check root folder just in case
    "choice.state"
]

state_loaded = False
for state_path in possible_states:
    if os.path.exists(state_path):
        print(f"? Found existing save: {state_path}")
        with open(state_path, "rb") as f:
            pyboy.load_state(f)
        state_loaded = True
        break

if not state_loaded:
    print("?? No previous save found! Starting fresh.")
else:
    print("resume_game: Loaded your previous progress.")

print("---------------------------------------")
print("?? NUZLOCKE TRAINING SETUP")
print("1. If you haven't beaten Gary, beat him now.")
print("2. Walk OUTSIDE the Lab to Pallet Town.")
print("3. Stand on the grass/path.")
print("4. Click this terminal and press Ctrl+C to save.")
print("---------------------------------------")

try:
    while pyboy.tick():
        pass
except KeyboardInterrupt:
    print("\n?? Saving 'states/outside.state'...")
    with open("states/outside.state", "wb") as f:
        pyboy.save_state(f)
    print("? SUCCESS! 'states/outside.state' created.")
    print("You can now run: python train_ai.py")
    pyboy.stop()