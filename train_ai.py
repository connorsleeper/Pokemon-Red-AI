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
    def __init__(self, verbose=0):
        super(QuitCallback, self).__init__(verbose)
        self.stop_training_triggered = False

    def _on_step(self) -> bool:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in [b'q', b'Q']:
                print("\n\n?? 'Q' PRESSED! Stopping training gracefully...")
                self.stop_training_triggered = True
                return False 
        return True

# 1. Initialize Environment
print("?? INITIALIZING NEURAL NETWORK...")
env = NuzlockeEnv(ROM_PATH, STATE_PATH)

# 2. SMART LOAD SYSTEM (This fixes your crash!)
save_files = glob.glob(os.path.join(MODELS_DIR, "*.zip"))

if save_files:
    # If we find saves, load the newest one
    latest_file = max(save_files, key=os.path.getctime)
    print(f"?? RESUMING from latest save: {latest_file}")
    model = PPO.load(latest_file, env=env)
else:
    # If NO saves exist, create a new brain (This prevents the FileNotFoundError)
    print("? NO SAVES FOUND. Starting fresh training run...")
    model = PPO('MlpPolicy', env, verbose=0, tensorboard_log=LOG_DIR, ent_coef=0.01)

print("\n?? TRAINING STARTED!")
print("?? Press 'Q' at any time to Save and Quit safely.\n")

# 3. THE MAIN LOOP
try:
    quit_callback = QuitCallback()
    iters = 0
    
    while True:
        iters += 1
        model.learn(total_timesteps=TIMESTEPS_PER_SAVE, callback=quit_callback, reset_num_timesteps=False)
        
        if quit_callback.stop_training_triggered:
            print("?? Saving final state before exit...")
            model.save(f"{MODELS_DIR}/FINAL_SAVE")
            print("? DONE. Safrom stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from nuzlocke_env import NuzlockeEnv
import os
import glob
import msvcrt
import time

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

class QuitCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(QuitCallback, self).__init__(verbose)
        self.stop_training_triggered = False

    def _on_step(self) -> bool:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in [b'q', b'Q']:
                self.stop_training_triggered = True
                return False 
        return True

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    env = None
    try:
        print("?? INITIALIZING ENVIRONMENT...")
        env = NuzlockeEnv(ROM_PATH, STATE_PATH)
        
        # --- SMART LOAD SYSTEM (Now Crash-Proof) ---
        print("?? CHECKING FOR SAVES...")
        save_files = glob.glob(os.path.join(MODELS_DIR, "*.zip"))
        
        model = None
        if save_files:
            try:
                latest_file = max(save_files, key=os.path.getctime)
                print(f"   -> Found save: {latest_file}")
                print("   -> Loading...")
                model = PPO.load(latest_file, env=env)
                print("   -> LOAD SUCCESSFUL!")
            except Exception as load_error:
                print(f"?? LOAD FAILED: {load_error}")
                print("   -> Starting FRESH brain instead.")
        
        if model is None:
            print("? CREATING NEW BRAIN...")
            model = PPO('MlpPolicy', env, verbose=0, tensorboard_log=LOG_DIR, ent_coef=0.01)

        print("\n?? TRAINING STARTED! (Press 'Q' to Quit)")
        time.sleep(2) # Give you a second to read the text before HUD starts

        # --- TRAINING LOOP ---
        quit_callback = QuitCallback()
        iters = 0
        
        while True:
            iters += 1
            model.learn(total_timesteps=TIMESTEPS_PER_SAVE, callback=quit_callback, reset_num_timesteps=False)
            
            if quit_callback.stop_training_triggered:
                print("?? Saving final state...")
                model.save(f"{MODELS_DIR}/FINAL_SAVE")
                break
                
            save_path = f"{MODELS_DIR}/{TIMESTEPS_PER_SAVE*iters}"
            model.save(save_path)

    except Exception as e:
        # !!! CRITICAL FIX: Close the HUD *before* printing the error !!!
        if env:
            env.close()
        print("\n" + "="*40)
        print("? CRITICAL ERROR CAUGHT")
        print(f"Error Details: {e}")
        print("="*40 + "\n")
        
        # Try to save emergency backup
        if model:
            print("Attempting emergency save...")
            try:
                model.save(f"{MODELS_DIR}/CRASH_BACKUP")
                print("Saved to CRASH_BACKUP.zip")
            except:
                print("Could not save backup.")

    finally:
        if env:
            env.close()
        print("?? Program Closed.")fe to close.")
            break
            
        save_path = f"{MODELS_DIR}/{TIMESTEPS_PER_SAVE*iters}"
        model.save(save_path)

except Exception as e:
    print(f"? Error occurred: {e}")
    # Try to save whatever we have
    model.save(f"{MODELS_DIR}/CRASH_SAVE")
finally:
    env.close()