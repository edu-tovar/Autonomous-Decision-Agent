from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
import random
import shutil

Pos = Tuple[int, int]
Tau = str

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


class Palacio:
    """
    Entorno del palacio:
    - 3 trampas tipadas: F, P, D (pueden compartir celda entre sí).
    - M, S, CK están en celda sin trampas, pero pueden compartir celda entre ellos.
    - Perceptos: eF, eP, eD, eM, eS, paredes, grito.
    """
    def __init__(self, n: int = 6, seed: Optional[int] = None) -> None:
        self.n = n
        self.seed = seed
        self._rng = random.Random(seed)

        self.inicio: Pos = (1, 1)

        self.trampas: Dict[Tau, Pos] = {}

        self.soldado: Pos | None = None
        self.soldado_vivo: bool = True
        self.kurtz: Pos | None = None
        self.salida: Pos | None = None

        self.reset()

    def reset(self) -> None:
        """
        Genera una nueva configuracion del palacio. Colocando las trampas,
        el soldado, la salida y Kurtz y garantiza quqe el inicio este libre de peligro.
        """
        celdas: List[Pos] = [(fila, col) for fila in range(1, self.n + 1) for col in range(1, self.n + 1)]
        celdas.remove(self.inicio)

        self.trampas = {
            "F": self._rng.choice(celdas),
            "P": self._rng.choice(celdas),
            "D": self._rng.choice(celdas),
        }
        celdas_trampa = set(self.trampas.values())

        celdas_seguras = [p for p in celdas if p not in celdas_trampa]
        if not celdas_seguras:
            raise RuntimeError("No hay celdas sin trampas para colocar M/S/CK. Cambia seed.")

        self.soldado = self._rng.choice(celdas_seguras)
        self.salida = self._rng.choice(celdas_seguras)
        self.kurtz = self._rng.choice(celdas_seguras)

        self.soldado_vivo = True
        self._validate()

    def _validate(self) -> None:
        """
        Comprueba la validezz de la configuracion generada.
        """
        assert self.inicio != self.trampas["F"]
        assert self.inicio != self.trampas["P"]
        assert self.inicio != self.trampas["D"]

        celdas_trampa = set(self.trampas.values())
        assert self.soldado not in celdas_trampa
        assert self.salida not in celdas_trampa
        assert self.kurtz not in celdas_trampa

    def limites(self, pos: Pos) -> bool:
        """
        Comprueba que una posicion este entre los limites del tablero.
        """
        fila, col = pos
        return 1 <= fila <= self.n and 1 <= col <= self.n

    def neighbors(self, pos: Pos) -> List[Pos]:
        """
        Devuelve las posiciones vecinas ortogonales de una celda.
        """
        fila, col = pos
        cand = [(fila - 1, col), (fila + 1, col), (fila, col - 1), (fila, col + 1)]
        return [p for p in cand if self.limites(p)]

    def _adj_self(self, pos: Pos) -> Set[Pos]:
        """
        Devuelve el conjunto de la celda actual + sus vecinos.
        """
        return set(self.neighbors(pos)) | {pos}

    def get_percepts(self, agent_pos: Pos, grito: bool = False) -> dict:
        """
        Devuelve el conjunto de perceptos observables desde una posicion.
        """
        fila, col = agent_pos
        pared_up = (fila == 1)
        pared_down = (fila == self.n)
        pared_left = (col == 1)
        pared_right = (col == self.n)

        adj_self = self._adj_self(agent_pos)

        eF = self.trampas["F"] in adj_self
        eP = self.trampas["P"] in adj_self
        eD = self.trampas["D"] in adj_self

        eM = self.soldado_vivo and (self.soldado in adj_self)
        eS = (self.salida in adj_self)

        return {"eF": eF, "eP": eP, "eD": eD, "eM": eM, "eS": eS, "pared_up": pared_up, "pared_down": pared_down, "pared_left": pared_left, "pared_right": pared_right, "grito": grito}
    
    def step_move(self, agent_pos: Pos, accion: str) -> Pos:
        """
        Ejecuta el intento de movimiento del agente.
        """
        new_pos = move(agent_pos, accion)
        if not self.limites(new_pos):
            return agent_pos
        return new_pos

    def cell_has_trap(self, pos: Pos) -> bool:
        """
        Determina si una celda contiene una trampa.
        """
        return pos in set(self.trampas.values())

    def is_lethal(self, pos: Pos) -> bool:
        """Determina si es mortal, si hay trampa o si hay soldado vivo en esa celda."""
        if self.cell_has_trap(pos):
            return True
        if self.soldado_vivo and pos == self.soldado:
            return True
        return False

    def throw_grenade(self, origen: Pos, direccion: str) -> bool:
        """
        Lanza granada 1 celda. Si cae sobre el soldado lo mata.
        """
        objetivo = move(origen, direccion)
        if not self.limites(objetivo):
            return False

        if self.soldado_vivo and (objetivo == self.soldado):
            self.soldado_vivo = False
            return True
        return False


def render_ascii(palacio: Palacio, agent_pos: Pos, visitado: list, reveal: bool = True, kurtz_rescatado: bool = False) -> None:
    """
    Representa visualmente el entorno del palacio con formato ASCII.
    Se puede elegir si revelar el mapa completo o solo lo observado."""
    
    RESET = "\033[0m"
    ORANGE = "\033[38;5;208m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    MAGENTA = "\033[38;5;89m"
    BLUE = "\033[34m"
    GRAY = "\033[90m"
    ROSE = '\033[95m'

    def cell_symbol(pos: Pos) -> str:
        if pos == agent_pos:
            return f"{ORANGE}CW{RESET}"

        if not reveal:
            if pos in visitado:
                return f"{GRAY} .{RESET}"
            return f"{GRAY}??{RESET}"

        hay_trampas = []
        for t in ("F", "P", "D"):
            if palacio.trampas[t] == pos:
                hay_trampas.append(t)

        if hay_trampas:
            color = {"F": RED, "D": ROSE, "P": BLUE}
            text = "".join(f"{color[t]}{t}{RESET}" for t in hay_trampas)

            if len(hay_trampas) == 1:
                return " " + text
            return text


        if palacio.soldado_vivo and pos == palacio.soldado:
            return f"{YELLOW} M{RESET}"
        if (not kurtz_rescatado) and pos == palacio.kurtz:
            return f"{MAGENTA}CK{RESET}"
        if pos == palacio.salida:
            return f"{GREEN} S{RESET}"
        return f"{GRAY} .{RESET}"

    ancho_terminal = shutil.get_terminal_size((80, 20)).columns
    ancho_mapa = palacio.n * 3 + (palacio.n - 1)
    margen = max(0, (ancho_terminal - ancho_mapa) // 2)
    prefijo = " " * margen

    for fila in range(1, palacio.n + 1):
        row = [cell_symbol((fila, col)) for col in range(1, palacio.n + 1)]
        print(prefijo + " ".join(row))
    print()


if __name__ == '__main__':
    p = Palacio()
    render_ascii(p, agent_pos=(1,1),reveal=True, visitado=[])