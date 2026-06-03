import sys
import pygame
from interface.constants import FPS, TITLE, DIFFICULTIES
from interface.game_screen import GameScreen

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Display temporal para que convert_alpha() funcione al cargar imagenes
    pygame.display.set_mode((1, 1))

    # Iniciar directamente en el juego (dificultad Novato por defecto)
    current = GameScreen(dict(DIFFICULTIES["novato"]))
    screen  = pygame.display.set_mode(current.get_size())

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            result = current.handle_event(event)

            if result:
                action, data = result

                if action == "start_game":
                    current = GameScreen(data)
                    screen  = pygame.display.set_mode(current.get_size())

                elif action == "resize":
                    nuevo_tamano = current.get_size()
                    screen = pygame.display.set_mode(nuevo_tamano)
                    
                    # HACK WINDOWS: Forzar actualización si el panel está totalmente cerrado
                    if current._drawer_visible <= 0:
                        screen = pygame.display.set_mode(nuevo_tamano)

        # ¡AQUÍ ESTÁ LA MAGIA!
        # Atrapamos lo que devuelve update() para animar la ventana frame por frame
        res_update = current.update()
        
        if res_update:
            action, data = res_update
            if action == "resize":
                nuevo_tamano = current.get_size()
                screen = pygame.display.set_mode(nuevo_tamano)
                
                # HACK WINDOWS: Forzar actualización si el panel terminó de cerrarse
                if current._drawer_visible <= 0:
                    screen = pygame.display.set_mode(nuevo_tamano)

        current.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()