import os
import sys
from stable_baselines3 import PPO
from nuzlocke_env import NuzlockeEnv

if __name__ == "__main__":
    if sys.platform == "win32":
        os.system('mode con: cols=120 lines=30')

    env = NuzlockeEnv("PokemonRed.gb", "states/outside.state")
    model = PPO('MlpPolicy', env, verbose=0)

    try:
        print("SYSTEM ONLINE. BROADCAST ACTIVE.")
        while True:
            # Learning in blocks of 2048 steps
            model.learn(total_timesteps=2048, reset_num_timesteps=False)
            
            # Update the HUD counter after the block finishes
            env.trigger_brain_review()
            model.save("models/PPO/nuzlocke_live")
            
    except KeyboardInterrupt:
        env.close()