# palacio.py
from __future__ import annotations
import matplotlib.pyplot as plt

from typing import List, Optional, Tuple
import os
import time

from palacio_world import Palacio, render_ascii, Pos
from bayes import BeliefState

def manhattan(a: Pos, b: Pos) -> int:
    """
    Calcula la distancia manhattan entre dos posiciones.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def best_adjacent_direction(pos_ori: Pos, pos_fin: Pos) -> Optional[str]:
    """
    Devuelve la dirección (UP/DOWN/LEFT/RIGHT) para ir de pos_ori a pos_fin si es contigua.
    """
    f_ori, c_ori = pos_ori
    f_fin, c_fin = pos_fin
    if (f_ori - 1, c_ori) == (f_fin, c_fin):
        return "UP"
    if (f_ori + 1, c_ori) == (f_fin, c_fin):
        return "DOWN"
    if (f_ori, c_ori - 1) == (f_fin, c_fin):
        return "LEFT"
    if (f_ori, c_ori + 1) == (f_fin, c_fin):
        return "RIGHT"
    return None


def choose_action_greedy(palacio: Palacio, belief: BeliefState, agent_pos: Pos, visitado: List[Pos], kurtz_rescatado: bool, p_lim: float = 0.2) -> str:
    """
    Selector simple:
    - Minimiza riesgo estimado de muerte.
    - Si hay varias seguras (<=p), prefiere explorar (no visitadas).
    - Tras rescatar, intenta acercarse a la salida real (para demo); si no, explora.
    """
    actions = ["UP", "DOWN", "LEFT", "RIGHT"]
    risk = belief.risk_death()

    if kurtz_rescatado:
        objetivo = max(belief.belief["S"].items(), key=lambda kv: kv[1])[0]
    else:
        objetivo = None

    best_a = "STAY"
    best_score = float("inf")

    for a in actions:
        nxt = palacio.step_move(agent_pos, a)
        if nxt == agent_pos:
            continue

        r = risk[nxt]

        score = 0.0

        if r <= p_lim:
            score += 10.0 * r
        else:
            score += 1000.0 + 200.0 * r

        if nxt not in visitado:
            score -= 0.5

        if objetivo is not None:
            score += 0.4 * manhattan(nxt, objetivo)

        if score < best_score:
            best_score = score
            best_a = a

    return best_a

def show_heatmaps(belief: BeliefState, agent_pos: Pos) -> None:
    """
    Muestra el mapa de calor con las probabilidades de que esste cada peligro/salida en las celdas.
    """
    traps = belief.traps_any_matrix()
    m = belief.to_matrix("M")
    s = belief.to_matrix("S")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    for ax, data, title in [
        (axes[0], traps, "P(trampa en celda) = F+P+D"),
        (axes[1], m, "P(soldado en celda)"),
        (axes[2], s, "P(salida en celda)"),
    ]:
        im = ax.imshow(data, origin="upper")
        ax.set_title(title)
        ax.set_xlabel("col")
        ax.set_ylabel("row")

        ar, ac = agent_pos
        ax.scatter([ac - 1], [ar - 1], marker="o", s=80, c="red")

        for i in range(len(data)):
            for j in range(len(data[0])):
                value = data[i][j]
                if value == 0:
                    continue
                else:
                    ax.text(
                        j, i,
                        f"{value:.2f}",
                        ha="center",
                        va="center",
                        color="white" if value > 0.15 else "black",
                        fontsize=8
                    )

        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.show()


def decide_grenade( palacio: Palacio, belief: BeliefState, agent_pos: Pos, obs: dict, granada: bool) -> Optional[str]:
    """
    Si percibe eM (soldado cerca) y tiene granada:
    - Lanza hacia la celda contigua con mayor probabilidad de M.
    Devuelve dirección o None.
    """
    if (not granada) or (not obs.get("eM", False)):
        return None

    m = belief.belief["M"]

    cand = palacio.neighbors(agent_pos)
    if not cand:
        return None

    best_pos = max(cand, key=lambda p: m.get(p, 0.0))
    direction = best_adjacent_direction(agent_pos, best_pos)
    return direction


def main(seed: Optional[int] = 0, reveal: bool = True, modo: str = "ascii") -> None:
    palacio = Palacio(n=6, seed=seed)
    belief = BeliefState(n=6, start=(1, 1))
    belief.init_uniform()

    agent_pos: Pos = (1, 1)
    visitado: List[Pos] = [agent_pos]

    granada = True
    kurtz_rescatado = False

    obs = palacio.get_percepts(agent_pos, grito=False)
    belief.update(agent_pos, obs)

    turno = 0
    while True:
        turno += 1
        os.system("cls")
        print(f"Turno: {turno} | Pos: {agent_pos} | Granada: {granada} | Kurtz: {kurtz_rescatado}")
        if modo == "ascii":
            render_ascii(palacio, agent_pos, visitado, reveal=reveal, kurtz_rescatado=kurtz_rescatado)
        elif modo == "heatmap":
            show_heatmaps(belief, agent_pos)

        print("Percepto:", obs)

        if kurtz_rescatado and agent_pos == palacio.salida:
            print("\nVICTORIA: salida alcanzada con Kurtz.")
            return

        if palacio.is_lethal(agent_pos):
            print("\nMUERTE.")
            return

        gdir = decide_grenade(palacio, belief, agent_pos, obs, granada)
        if gdir is not None:
            killed = palacio.throw_grenade(agent_pos, gdir)
            granada = False
            obs = palacio.get_percepts(agent_pos, grito=killed)
            belief.update(agent_pos, obs)
            time.sleep(0.2)
            continue

        action = choose_action_greedy(palacio=palacio, belief=belief, agent_pos=agent_pos, visitado=visitado, kurtz_rescatado=kurtz_rescatado, p_lim=0.2)

        nueva_pos = palacio.step_move(agent_pos, action)
        agent_pos = nueva_pos
        if agent_pos not in visitado:
            visitado.append(agent_pos)

        if palacio.is_lethal(agent_pos):
            os.system("cls")
            print(f"Acción: {action} -> Pos: {agent_pos}")
            render_ascii(palacio, agent_pos, visitado, reveal=reveal, kurtz_rescatado=kurtz_rescatado)
            print("\nMUERTE.")
            return

        if (not kurtz_rescatado) and (agent_pos == palacio.kurtz):
            if (not palacio.soldado_vivo) or (palacio.soldado != palacio.kurtz):
                kurtz_rescatado = True

        obs = palacio.get_percepts(agent_pos, grito=False)
        belief.update(agent_pos, obs)

        time.sleep(0.7)


if __name__ == "__main__":
    modo = input("Modo de visualización [ascii / heatmap]: ").strip().lower()
    main(seed=0, reveal=True, modo=modo)
