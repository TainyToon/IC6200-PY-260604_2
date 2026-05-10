"""
Buscaminas - Punto de Entrada
IC6200-PY-260604_2

Controles:
    Click izquierdo  - revelar celda
    Click derecho    - bandera / interrogacion / sin marcar
    Click en carita  - reiniciar
    R                - reiniciar
    ESC              - reiniciar
    Toolbar zoom+/-  - ajustar tamanio de celdas
    Toolbar [^/^^/*] - cambiar dificultad
"""

import sys
import pygame
from interface.constants import FPS, TITLE, DIFFICULTIES
from interface.game_screen import GameScreen


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

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
                    screen = pygame.display.set_mode(current.get_size())

        current.update()
        current.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
