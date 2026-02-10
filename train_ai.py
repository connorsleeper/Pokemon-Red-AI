from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from nuzlocke_env import NuzlockeEnv
import os
import glob
import msvcrt  # Built-in Windows library for keyboard input

# --- CONFIGURATION ---
ROM_PATH = "PokemonRed.gb"
STATE_PATH = "states/outside.state"
MODELS_DIR = "models/PPO"
LOG_DIR = "logs"
TIMESTEPS_PER_SAVE = 2048 

# Ensure folders exist
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# --- THE QUIT CALLBACK (The "Q" Button) ---
class QuitCallback(BaseCallback):
    """
    A custom callback that checks for 'q' key press to stop training.
    """
    def __init__(self, verbose=0):
        super(QuitCallback, self).__init__(verbose)
        self.stop_training_triggered = False

    def _on_step(self) -> bool:
        # Check if a key was pressed (non-blocking)
        if msvcrt.kbhit():
            key = msvcrt.getch()
            # Check for 'q' or 'Q'
            if key in [b'q', b'Q']:
                print("\n\n?? 'Q' PRESSED! Stopping training gracefully...")
                self.stop_training_triggered = True
                return False  # Returning False stops the AI immediately
        return True

# 1. Initialize Environment
print("?? INITIALIZING NEURAL NETWORK...")
env = NuzlockeEnv(ROM_PATH, STATE_PATH)

# 2. SMART LOAD SYSTEM
save_files = glob.glob(os.path.join(MODELS_DIR, "*.zip"))
if save_files:
    latest_file = max(save_files, key=os.path.getctime)
    print(f"?? RESUMING from latest save: {latest_file}")
    model = PPO.load(latest_file, env=env)
else:
    print("? NO SAVES FOUND. Starting fresh training run...")
    # verbose=0 silences the standard text so our HUD can shine
    model = PPO('MlpPolicy', env, verbose=0, tensorboard_log=LOG_DIR, ent_coef=0.01)

print("\n?? TRAINING STARTED!")
print("?? Press 'Q' at any time to Save and Quit safely.")
print("?? (You don't need to click the window, just press Q in the terminal)\n")

# 3. THE MAIN LOOP
try:
    quit_callback = QuitCallback()
    iters = 0
    
    while True:
        iters += 1
        
        # Train with the Quit Callback attached
        model.learn(total_timesteps=TIMESTEPS_PER_SAVE, callback=quit_callback, reset_num_timesteps=False)
        
        # Check if we stopped because of 'Q'
        if quit_callback.stop_training_triggered:
            print("?? Saving final state before exit...")
            model.save(f"{MODELS_DIR}/FINAL_SAVE")
            print("? DONE. Safe to close.")
            break
            
        # Normal Autosave
        save_path = f"{MODELS_DIR}/{TIMESTEPS_PER_SAVE*iters}"
        model.save(save_path)
        print(f"? Autosaved Model: {save_path}")

except Exception as e:
    print(f"? Error occurred: {e}")
    model.save(f"{MODELS_DIR}/CRASH_SAVE")
finally:
    env.close()