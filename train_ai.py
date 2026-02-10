from stable_baselines3 import PPO
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

if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

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

if __name__ == "__main__":
    env = None
    try:
        print("?? INITIALIZING ENVIRONMENT...")
        env = NuzlockeEnv(ROM_PATH, STATE_PATH)
        
        print("?? CHECKING FOR SAVES...")
        save_files = glob.glob(os.path.join(MODELS_DIR, "*.zip"))
        
        model = None
        if save_files:
            try:
                latest_file = max(save_files, key=os.path.getctime)
                print(f"   -> Loading: {latest_file}")
                model = PPO.load(latest_file, env=env)
                print("   -> LOAD SUCCESSFUL!")
            except Exception as load_error:
                print(f"?? LOAD FAILED: {load_error}")
        
        if model is None:
            print("? CREATING NEW BRAIN...")
            model = PPO('MlpPolicy', env, verbose=0, tensorboard_log=LOG_DIR, ent_coef=0.01)

        print("\n?? TRAINING STARTED! (Press 'Q' to Quit)")
        time.sleep(1)

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
        if env:
            env.close()
        print("\n" + "!"*40)
        print(f"? ERROR: {e}")
        print("!"*40 + "\n")

    finally:
        if env:
            env.close()
        print("?? Shutdown complete.")