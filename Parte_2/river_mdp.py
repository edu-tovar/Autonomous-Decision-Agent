# river_mdp.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
import os
import time

Pos = Tuple[int, int]

ACTIONS = ("UP", "DOWN", "LEFT", "RIGHT", "STAY")

def move(pos: Pos, accion: str) -> Pos:
    """
    Funcion que recibe una posicion y una accion y devuelve la posicion
    obtenida tras realizar la accion
    """
    fila, col = pos
    if accion == "UP":
        return (fila - 1, col)
    if accion == "DOWN":
        return (fila + 1, col)
    if accion == "LEFT":
        return (fila, col - 1)
    if accion == "RIGHT":
        return (fila, col + 1)
    return pos


def in_bounds(pos: Pos, filas: int, cols: int) -> bool:
    """
    Funcion que recibe una posicion, el numero de filas y el numero
    de columnas y devuelve si la posicion esta dentro de los limites
    """

    fila, col = pos
    return 1 <= fila <= filas and 1 <= col <= cols


def neighbors_4(pos: Pos, filas: int, cols: int) -> List[Pos]:
    """
    Funcino que recibe una pociscion, el numero de filas y el numero
    de columnas y devuelve una lista con todas las celdas vecinas (ortogonalmente)
    que esten dentro de los limites del tablero.
    """

    fila, col = pos
    candidatos = [(fila - 1, col), (fila + 1, col), (fila, col - 1), (fila, col + 1)]
    return [p for p in candidatos if in_bounds(p, filas, cols)]


def bfs_path_exists(inicio: Pos, meta: Pos, bloqueados: set[Pos], filas: int, cols: int) -> bool:
    """
    Funcion que recibe la posicion inicial, la meta, las posiciones
    bloqueadas y los limites del tablero y devuelve, mediente busqueda BFS
    si hay un camino posible entre el inicio y el final.
    """

    if inicio in bloqueados or meta in bloqueados:
        return False
    q = [inicio]
    visitados = {inicio}
    while q:
        cur = q.pop(0)
        if cur == meta:
            return True
        for vec in neighbors_4(cur, filas, cols):
            if vec in bloqueados or vec in visitados:
                continue
            visitados.add(vec)
            q.append(vec)
    return False


@dataclass
class RiverWorld:
    """
    Entorno del río modelado como un Proceso de Decisión de Markov (MDP).

    El río se representa como un grid bidimensional de tamaño (filas x columnas),
    donde cada celda corresponde a un estado del MDP. El agente comienza en
    una posición inicial y debe alcanzar la salida evitando caer en islas.

    - Estados: posiciones (fila, columna) del grid.
    - Acciones: UP, DOWN, LEFT, RIGHT, STAY.
    - Dinámica estocástica: la corriente del río empuja al agente hacia abajo
      con probabilidad dependiente de la columna.
    - Estados terminales: salida (E) e islas (I).
    - Recompensas: +100 al alcanzar la salida, -100 al caer en una isla,
      y -1 por cada paso.
    """

    filas: int = 7
    cols: int = 6
    nislas: int = 2
    seed: Optional[int] = 0

    inicio: Pos = (1, 1)
    exit: Pos = field(default_factory=lambda: (4, 6))
    islas: set[Pos] = field(default_factory=set)
    strengths: Dict[int, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        # salida por defecto: fila central, última columna
        self.exit = (self.filas // 2 + 1, self.cols)

    def river_strength(self, col: int) -> float:
        return self.strengths[col]

    def reset(self) -> None:
        """
        Genera una nueva configuracion del rio, asignando una fuerza de corriente a cada
        columna y asegurandose de que hay minimo un camino alcanzable.
        """
        self.strengths = {}
        for col in range(1, self.cols + 1):
            if col == 1 or col == self.cols:
                self.strengths[col] = 0.0
            else:
                self.strengths[col] = round(self._rng.uniform(0.06, 0.94), 1)

        candidatos = [(r, c) for r in range(2, self.filas) for c in range(1, self.cols + 1)]

        for _ in range(500):
            self._rng.shuffle(candidatos)
            isl = set(candidatos[: self.nislas])
            if bfs_path_exists(self.inicio, self.exit, isl, self.filas, self.cols):
                self.islas = isl
                return

        raise RuntimeError("No se pudo generar un río con camino válido (prueba otra seed o tamaño).")

    def is_terminal(self, s: Pos) -> bool:
        """
        Indica si un estado es terminal. Es decir, si corresponde a la salida
        o a una isla.
        """

        return s == self.exit or s in self.islas

    def transitions(self, s: Pos, a: str) -> Dict[Pos, float]:
        """
        Implementa P(s'|s,a) del enunciado:
        - Si a != DOWN:
            pdir = 1 - river_strength(col_actual)
            pdown = river_strength(col_actual) hacia la casilla inferior
        - Si a == DOWN:
            pdir = 1 hacia abajo
        - Si destino está fuera o es isla: esa prob. se acumula en 'stay' (s)
        """
        if a not in ACTIONS:
            raise ValueError(f"Acción inválida: {a}")

        if self.is_terminal(s):
            return {s: 1.0}

        fila, col = s
        strength = self.river_strength(col)

        if a == "DOWN":
            deseado = (fila + 1, col)
            abajo = deseado
            pdir = 1.0
            pdown = 0.0
        else:
            deseado = move(s, a)
            abajo = (fila + 1, col)
            pdir = 1.0 - strength
            pdown = strength

        dist: Dict[Pos, float] = {}

        def add_mass(dest: Pos, p: float) -> None:
            if p <= 0:
                return
            
            if (not in_bounds(dest, self.filas, self.cols)) or (dest in self.islas):
                dist[s] = dist.get(s, 0.0) + p
            else:
                dist[dest] = dist.get(dest, 0.0) + p

        add_mass(deseado, pdir)
        if a != "DOWN":
            add_mass(abajo, pdown)

        total = sum(dist.values())
        if total <= 0:
            return {s: 1.0}
        for k in list(dist.keys()):
            dist[k] /= total
        return dist

    def reward(self, sprima: Pos) -> float:
        """
        Funcion de recompensa. Como en el enunciado no afecta ni la accion
        ni el estado, solo se tiene en cuenta el estado al que se llega.
        
        Devuelve la recompensa inmediata asociada a la transición:
        - +100 si el estado siguiente es la salida.
        - -100 si el estado siguiente es una isla.
        - -1 en cualquier otro caso.
        """

        if sprima == self.exit:
            return 100.0
        if sprima in self.islas:
            return -100.0
        return -1.0

    def render_ascii(self, agent_pos: Pos, show_strength: bool = True) -> None:
        """
        Representacion visual del rio en formato ASCII.
        
        Muestra la posicion del agente, de las islas y de la salida.
        """
        
        RESET = "\033[0m"
        ORANGE = "\033[38;5;208m"
        BLUE = "\033[34m"
        GREEN = "\033[32m"
        RED = "\033[31m"
        GRAY = "\033[90m"

        if show_strength:
            header = []
            for c in range(1, self.cols + 1):
                header.append(f"{self.strengths[c]:>3}")
            print("     " + " ".join(header))
            print("     " + " ".join(["---"] * self.cols))

        for r in range(1, self.filas + 1):
            row_cells = []
            for c in range(1, self.cols + 1):
                p = (r, c)
                if p == agent_pos:
                    sym = f"{ORANGE}CW{RESET}"
                elif p == self.exit:
                    sym = f"{GREEN} E{RESET}"
                elif p in self.islas:
                    sym = f"{RED} I{RESET}"
                else:
                    sym = f"{BLUE} R{RESET}"
                row_cells.append(sym)

            print(f"{GRAY}|{RESET} " + " ".join(row_cells) + f" {GRAY}|{RESET}")
        print()


def value_iteration(rio: RiverWorld, gamma: float = 0.95, theta: float = 1e-6, max_iter: int = 50_000) -> Tuple[Dict[Pos, float], Dict[Pos, str]]:
    """
    Implementa el algoritmo de Value Iteration para resolver el MDP del entorno del rio.
    
    Calcula la funcion de valor optima V(s) y su politica pi(s) asociada.


    Parámetros:
    - rio: entorno del río que define estados, transiciones y recompensas.
    - gamma: factor de descuento (0 < gamma < 1), que pondera la importancia
      de recompensas futuras.
    - theta: umbral de convergencia; el algoritmo se detiene cuando el cambio
      máximo en V(s) es menor que este valor.
    - max_iter: número máximo de iteraciones permitidas.

    Devuelve:
    - V: diccionario que asigna a cada estado s su valor óptimo V(s).
    - pi: diccionario que asigna a cada estado s la acción óptima π(s).
    """
    states = [(fila, col) for fila in range(1, rio.filas + 1) for col in range(1, rio.cols + 1)]
    V: Dict[Pos, float] = {s: 0.0 for s in states}
    pi: Dict[Pos, str] = {s: "STAY" for s in states}

    for _ in range(max_iter):
        delta = 0.0
        for s in states:
            if rio.is_terminal(s):
                pi[s] = "STAY"
                continue

            best_a = None
            best_q = float("-inf")

            for a in ACTIONS:
                trans = rio.transitions(s, a)
                q = 0.0
                for sprima, p in trans.items():
                    q += p * (rio.reward(sprima) + gamma * V[sprima])
                if q > best_q:
                    best_q = q
                    best_a = a

            old = V[s]
            V[s] = best_q
            pi[s] = best_a if best_a is not None else "STAY"
            delta = max(delta, abs(old - V[s]))

        if delta < theta:
            break

    return V, pi


def sample_next(rng: random.Random, dist: Dict[Pos, float]) -> Pos:
    x = rng.random()
    p_acumulada = 0.0
    last = None
    for s, p in dist.items():
        p_acumulada += p
        last = s
        if x <= p_acumulada:
            return s
    return last


def simulate_episode( rio: RiverWorld, pi: Dict[Pos, str], seed: Optional[int] = 0, max_steps: int = 200, render: bool = True) -> Tuple[bool, float, List[Pos]]:
    """
    Simula el episodio completo del entorno del rio siguiendo la politica dada.
    Permite realizar la simulacion sin necesidad de renderizarla por pantalla.
    
    Parámetros:
    - rio: entorno del río que define el MDP.
    - pi: política a seguir, que asigna una acción a cada estado.
    - seed: semilla para el generador de números aleatorios.
    - max_steps: número máximo de pasos del episodio.
    - render: indica si se muestra la evolución del episodio en formato ASCII.

    Devuelve:
    - success: True si el episodio termina en la salida, False si termina en una isla.
    - total: recompensa total acumulada durante el episodio.
    - path: lista de estados visitados durante la simulación."""
    
    rng = random.Random(seed)
    s = rio.inicio
    total = 0.0
    path = [s]

    for step in range(1, max_steps + 1):
        if render:
            os.system("cls")
            print(f"Paso: {step} | Pos: {s} | Acción π(s): {pi.get(s,'STAY')}")
            rio.render_ascii(s, show_strength=True)

        if rio.is_terminal(s):
            break

        a = pi.get(s, "STAY")
        dist = rio.transitions(s, a)
        sprima = sample_next(rng, dist)
        total += rio.reward(sprima)
        s = sprima
        path.append(s)

        if render:
            time.sleep(0.2)

        if rio.is_terminal(s):
            if render:
                os.system("cls")
                print(f"FINAL | Pos: {s} | Recompensa total: {total}")
                rio.render_ascii(s, show_strength=True)
            break

    success = (s == rio.exit)
    return success, total, path


def render_policy(rio: RiverWorld, pi: Dict[Pos, str]) -> None:
    """
    Representa visualmente la politica optima del rio.
    
    Para cada estado se muestra una flecha indicando la accion optima calculada
    mediante Value Iteration. Esto permite interpretar la estrategia que el agente 
    seguira.
    """
    
    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    GRAY = "\033[90m"
    ORANGE = "\033[38;5;208m"

    arrow = {"UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→", "STAY": "·"}

    for fila in range(1, rio.filas + 1):
        row = []
        for col in range(1, rio.cols + 1):
            s = (fila, col)
            if s == rio.inicio:
                row.append(f"{ORANGE}ST{RESET}")
            elif s == rio.exit:
                row.append(f"{GREEN} E{RESET}")
            elif s in rio.islas:
                row.append(f"{RED} I{RESET}")
            else:
                row.append(f"{GRAY} {arrow[pi.get(s,'STAY')]}{RESET}")
        print(" ".join(row))
    print()


def main() -> None:
    rio = RiverWorld(filas=7, cols=6, nislas=2, seed=0)
    rio.reset()

    print("=== Río generado ===")
    rio.render_ascii(rio.inicio, show_strength=True)

    print("Calculando política óptima con Value Iteration...")
    V, pi = value_iteration(rio, gamma=0.95, theta=1e-6)

    print("\n=== Política óptima (flechas) ===")
    render_policy(rio, pi)

    mode = input("Simular episodio? [s/n]: ").strip().lower()
    if mode == "s":
        simulate_episode(rio, pi, seed=1, render=True, delay=0.25)
    else:
        print("Fin.")


if __name__ == "__main__":
    main()
