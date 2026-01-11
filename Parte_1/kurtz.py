from __future__ import annotations
import os
import time
from world import Palacio, render_ascii
from agent import Agente
from search_agent import bfs_path, path_to_actions


def main() -> None:
    palacio = Palacio()
    agente = Agente()
    visitados = []
    mostrar = False
    kurtz = False
    modo = input("Modo MANUAL o AUTO: ").upper()
    if modo == "AUTO": 
        mostrar = True
        inicio = agente.state.pos

        bloqueado = set(palacio.precipicios)
        if palacio.soldado_vivo:
            bloqueado.add(palacio.soldado)

        path1 = bfs_path(palacio.n, inicio, palacio.kurtz, bloqueado)
        if path1 is None:
            print("No existe camino seguro hasta Kurtz.")
            return

        path2 = bfs_path(palacio.n, palacio.kurtz, palacio.salida, bloqueado)
        if path2 is None:
            print("No existe camino seguro desde Kurtz a la salida.")
            return

        full_path = path1 + path2[1:]
        plan = path_to_actions(full_path)

        plan_idx = 0

    while agente.state.alive:
        os.system("cls")
        visitados.append(agente.state.pos)
        render_ascii(palacio, agent_pos=agente.state.pos, visitado=visitados, reveal=mostrar, kurtz=kurtz)

        percepts = agente.perceive(palacio)
        print("percept(s) =", percepts)
        
        if modo == "AUTO":
            time.sleep(1)
            if plan_idx >= len(plan):
                action = "EXIT"
            else:
                action = plan[plan_idx]
                plan_idx += 1
        else:
            action = agente.choose_action_manual()

        if action in ("UP", "DOWN", "LEFT", "RIGHT"):
            new_pos = palacio.step_move(agente.state.pos, action)
            agente.state.pos = new_pos

            if new_pos in palacio.precipicios:
                agente.state.alive = False
                print("Has caído en un precipicio.")
                break

            if palacio.soldado_vivo and (new_pos == palacio.soldado):
                agente.state.alive = False
                print("El soldado enemigo te ha eliminado.")
                break

            if new_pos == palacio.kurtz:
                agente.state.has_kurtz = True
                kurtz = True
                print("Has encontrado al Coronel Kurtz. Ahora viajáis juntos.")
                time.sleep(3)

        elif action == "EXIT":
            if palacio.salida == agente.state.pos and agente.state.has_kurtz:
                print("¡Misión completada! Has salido con Kurtz.")
                return
            else:
                print("No puedes salir: necesitas estar en la salida y haber encontrado a Kurtz.")
                time.sleep(3)
        elif action == "MAPA":
            mostrar = not mostrar
            
        elif action == "GRANADA":
            if not agente.state.has_grenade:
                print("Ya no te quedan granadas.")
                time.sleep(2)
            else:
                d = input("Dirección granada [w/a/s/d]: ").strip().lower()
                dir_map = {"w": "UP", "s": "DOWN", "a": "LEFT", "d": "RIGHT"}

                if d not in dir_map:
                    print("Dirección inválida.")
                    time.sleep(2)
                else:
                    direction = dir_map[d]

                    killed = palacio.throw_grenade(agente.state.pos, direction)

                    agente.state.has_grenade = False

                    if killed:
                        agente.state.last_scream = True
                        print("¡Impacto! Has eliminado al soldado (grito).")
                    else:
                        print("La granada no ha tenido efecto.")

                    time.sleep(2)
        else:
            print("Acción no válida.")

    print("Fin del juego.")


if __name__ == "__main__":
    main()
