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
    
    posibles_peligros = set()
    seguros_peligros = set()

    while agente.state.vivo:
        os.system("cls")
        visitados.append(agente.state.pos)
        percepts = agente.perceive(palacio)

        visitados_set = set(visitados)

        def vecinos(p):
            return palacio.neighbors(p)

        no_pit = set()
        brisa_pos = []
        for pos, per in agente.history:
            if not per.get("brisa", False):
                no_pit.update(vecinos(pos))
            else:
                brisa_pos.append(pos)

        cand_pit = set()
        sure_pit = set()
        for pos in brisa_pos:
            cand = set(vecinos(pos)) - no_pit
            cand_pit.update(cand)
            if len(cand) == 1:
                sure_pit.update(cand)

        no_sold = set()
        ronq_pos = []
        for pos, per in agente.history:
            if not per.get("ronquido", False):
                no_sold.update(vecinos(pos))
            else:
                ronq_pos.append(pos)

        cand_sold = set()
        sure_sold = set()
        for pos in ronq_pos:
            cand = set(vecinos(pos)) - no_sold
            cand_sold.update(cand)
            if len(cand) == 1:
                sure_sold.update(cand)

        posibles_peligros = set().union(cand_pit, cand_sold) - visitados_set
        seguros_peligros  = set().union(sure_pit, sure_sold) - visitados_set


        render_ascii(palacio, agent_pos=agente.state.pos, visitado=visitados, reveal=mostrar, kurtz=kurtz, posibles_peligros=posibles_peligros, seguros_peligros=seguros_peligros)

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
                agente.state.vivo = False
                print("Has caído en un precipicio.")
                break

            if palacio.soldado_vivo and (new_pos == palacio.soldado):
                agente.state.vivo = False
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
                        agente.state.ult_grito = True
                        print("¡Impacto! Has eliminado al soldado (grito).")
                    else:
                        print("La granada no ha tenido efecto.")

                    time.sleep(2)
        else:
            print("Acción no válida.")

    print("Fin del juego.")


if __name__ == "__main__":
    main()
