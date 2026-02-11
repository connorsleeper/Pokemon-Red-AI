import pygame
import sys
import numpy as np
from stable_baselines3 import PPO
from nuzlocke_env import NuzlockeEnv

# --- CONFIG ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
GAME_SCALE = 3 

# RETRO COLOR SCHEME
COLOR_BG = (10, 10, 15)       # Deep dark blue/black
COLOR_PANEL = (25, 25, 30)    # Dark panel
COLOR_TEXT_MAIN = (240, 240, 240)
COLOR_TEXT_LOG = (0, 255, 0)  # Matrix Green
COLOR_ACCENT = (255, 215, 0)  # Gold
COLOR_HP_HIGH = (50, 205, 50)
COLOR_HP_LOW = (220, 20, 60)
COLOR_BORDER = (100, 100, 100)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("POKEMON AI - BROADCAST GUI")
    clock = pygame.time.Clock()
    
    # Fonts
    try:
        font_head = pygame.font.SysFont("impact", 20)
        font_emoji = pygame.font.SysFont("segoe ui emoji", 20)
        font_mono = pygame.font.SysFont("consolas", 14) 
        font_small = pygame.font.SysFont("arial", 14)
    except:
        font_head = pygame.font.SysFont("arial", 20, bold=True)
        font_emoji = pygame.font.SysFont("arial", 20)
        font_mono = pygame.font.SysFont("courier new", 14)
        font_small = pygame.font.SysFont("arial", 14)
    
    print(">> GUI: Initializing Environment...")
    env = NuzlockeEnv("PokemonRed.gb", "states/outside.state")
    
    print(">> GUI: Loading Brain...")
    try:
        model = PPO.load("models/PPO/nuzlocke_live", env=env)
        brain_status = "RESUMED (v.LIVE)"
    except:
        model = PPO('MlpPolicy', env, verbose=0)
        brain_status = "CREATED NEW (v.0)"

    running = True
    obs, _ = env.reset()
    
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            action, _ = model.predict(obs)
            obs, reward, done, trunc, info = env.step(action)
            
            # Periodic Learning
            if env.total_steps % 2048 == 0:
                env.trigger_brain_review()
                model.learn(total_timesteps=2048, reset_num_timesteps=False)
                model.save("models/PPO/nuzlocke_live")

            screen.fill(COLOR_BG)

            # --- 1. HEADER ---
            # Format: COOKIES | BONKS | STEPS | LAST REVIEW | OBJ
            header_text = f"COOKIES: {env.cookies}   BONKS: {env.bonks}   STEPS: {env.total_steps}   LAST REV: {env.last_brain_update}   OBJ: {env.current_objective}"
            header_surf = font_head.render(header_text, True, COLOR_TEXT_MAIN)
            screen.blit(header_surf, (WINDOW_WIDTH//2 - header_surf.get_width()//2, 20))
            
            # --- 2. GAME AREA (CENTER) ---
            raw_screen = env.render()
            if raw_screen.shape == (144, 160, 3):
                game_surface = pygame.surfarray.make_surface(raw_screen.swapaxes(0, 1))
                game_surface = pygame.transform.scale(game_surface, (160 * GAME_SCALE, 144 * GAME_SCALE))
                
                game_x = (WINDOW_WIDTH - (160 * GAME_SCALE)) // 2
                game_y = 60
                
                # Draw Border & Game
                pygame.draw.rect(screen, COLOR_BORDER, (game_x-4, game_y-4, (160*GAME_SCALE)+8, (144*GAME_SCALE)+8))
                screen.blit(game_surface, (game_x, game_y))

            # --- 3. LEFT PANEL: TEAM ---
            panel_y = 60
            pygame.draw.rect(screen, COLOR_PANEL, (20, panel_y, 300, 500))
            pygame.draw.rect(screen, COLOR_ACCENT, (20, panel_y, 300, 500), 1) # Outline
            
            title_surf = font_head.render("ACTIVE TEAM", True, COLOR_ACCENT)
            screen.blit(title_surf, (30, panel_y + 10))
            
            y_offset = panel_y + 50
            for mon in env.party_info:
                # Icon Name Level
                line1 = f"{mon['emoji']} {mon['name']} (L{mon['lvl']})"
                screen.blit(font_emoji.render(line1, True, COLOR_TEXT_MAIN), (30, y_offset))
                
                # Species [Type]
                line2 = f"{mon['species']} [{mon['type']}]"
                screen.blit(font_small.render(line2, True, (150, 150, 150)), (30, y_offset + 20))

                # HP Bar
                bar_y = y_offset + 40
                pygame.draw.rect(screen, (40, 40, 40), (30, bar_y, 200, 8)) # Back
                fill_width = int(200 * mon['pct'])
                hp_color = COLOR_HP_HIGH if mon['pct'] > 0.5 else COLOR_HP_LOW
                pygame.draw.rect(screen, hp_color, (30, bar_y, fill_width, 8)) # Fill
                
                hp_txt = f"{mon['hp']}/{mon['max_hp']}"
                screen.blit(font_small.render(hp_txt, True, (200,200,200)), (240, bar_y - 5))
                
                y_offset += 70

            # --- 4. RIGHT PANEL: LOGS ---
            pygame.draw.rect(screen, COLOR_PANEL, (WINDOW_WIDTH - 320, panel_y, 300, 500))
            pygame.draw.rect(screen, COLOR_ACCENT, (WINDOW_WIDTH - 320, panel_y, 300, 500), 1)
            
            log_title = font_head.render("TERMINAL LOG", True, COLOR_ACCENT)
            screen.blit(log_title, (WINDOW_WIDTH - 310, panel_y + 10))
            
            log_y = panel_y + 50
            for i, log in enumerate(list(env.log_history)[::-1]):
                color = COLOR_ACCENT if "***" in log else COLOR_TEXT_LOG
                log_surf = font_mono.render(log, True, color)
                screen.blit(log_surf, (WINDOW_WIDTH - 310, log_y))
                log_y += 18

            # Graveyard at bottom of right panel
            grave_y = panel_y + 350
            pygame.draw.line(screen, (100, 100, 100), (WINDOW_WIDTH - 310, grave_y), (WINDOW_WIDTH - 30, grave_y), 1)
            grave_title = font_head.render("GRAVEYARD", True, (200, 50, 50))
            screen.blit(grave_title, (WINDOW_WIDTH - 310, grave_y + 5))
            
            gy_offset = grave_y + 30
            for dead_mon in env.graveyard:
                screen.blit(font_emoji.render(f"✝ {dead_mon}", True, (150, 150, 150)), (WINDOW_WIDTH - 310, gy_offset))
                gy_offset += 20

            # --- 5. BOTTOM PANEL: BRAIN INFO ---
            # Box location: Below game, between panels
            bottom_box_y = game_y + (144*GAME_SCALE) + 10
            bottom_box_h = 720 - bottom_box_y - 10
            bottom_box_w = (WINDOW_WIDTH - 320) - 320 - 40 # Space between side panels
            bottom_box_x = 340 # 20 + 300 + 20 padding
            
            pygame.draw.rect(screen, COLOR_PANEL, (bottom_box_x, bottom_box_y, bottom_box_w, bottom_box_h))
            pygame.draw.rect(screen, (50, 50, 100), (bottom_box_x, bottom_box_y, bottom_box_w, bottom_box_h), 1)
            
            # Brain Info Text
            info_title = font_head.render("NEURAL NET DIAGNOSTICS", True, (100, 200, 255))
            screen.blit(info_title, (bottom_box_x + 10, bottom_box_y + 10))
            
            status_txt = f"STATUS: {brain_status} | MODEL: PPO (MlpPolicy)"
            screen.blit(font_small.render(status_txt, True, COLOR_TEXT_MAIN), (bottom_box_x + 10, bottom_box_y + 40))
            
            learn_txt = f"LEARNING RATE: Adaptive | BATCH: 2048 | GAMMA: 0.99"
            screen.blit(font_small.render(learn_txt, True, COLOR_TEXT_MAIN), (bottom_box_x + 10, bottom_box_y + 60))

            pygame.display.flip()
            clock.tick(60) # Smooth 60FPS

    finally:
        print(">> GUI: Saving Brain before shutdown...")
        model.save("models/PPO/nuzlocke_live")
        env.close()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()