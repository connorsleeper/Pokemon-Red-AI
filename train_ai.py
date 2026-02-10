from stable_baselines3 import PPO
from nuzlocke_env import NuzlockeEnv
import os
import glob

# --- CONFIGURATION ---
ROM_PATH = "PokemonRed.gb"
STATE_PATH = "states/outside.state"
MODELS_DIR = "models/PPO"
LOG_DIR = "logs"

# Ensure folders exist
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 1. Initialize Environment
print("?? INITIALIZING NEURAL NETWORK...")
env = NuzlockeEnv(ROM_PATH, STATE_PATH)

# 2. SMART LOAD SYSTEM
# Look for existing save files
save_files = glob.glob(os.path.join(MODELS_DIR, "*.zip"))

if save_files:
    # Find the newest file based on creation time
    latest_file = max(save_files, key=os.path.getctime)
    print(f"?? RESUMING from latest save: {latest_file}")
    
    # Load the brain
    model = PPO.load(latest_file, env=env)
else:
    # No files found? Create a new brain
    print("? NO SAVES FOUND. Starting fresh training run...")
    model = PPO('MlpPolicy', env, verbose=1, tensorboard_log=LOG_DIR, ent_coef=0.01)

# TIMESTEPS: How often to autosave
TIMESTEPS = 2048 
iters = 0

print("?? TRAINING STARTED! (Press Ctrl+C to save and quit)")

# 3. The Safety Loop
try:
    while True:
        iters += 1
        
        # Train for one "Batch"
        model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False)
        
        # Autosave with a number (so we have history)
        save_path = f"{MODELS_DIR}/{TIMESTEPS*iters}"
        model.save(save_path)
        print(f"? Autosaved Model: {save_path}")

except KeyboardInterrupt:
    print("\n?? INTERRUPT DETECTED! Saving final brain state...")
    # Save as FINAL_SAVE so we always have a generic 'latest' reference if needed
    model.save(f"{MODELS_DIR}/FINAL_SAVE")
    print("?? Saved 'models/PPO/FINAL_SAVE.zip'. Safe to close.")
    env.close()