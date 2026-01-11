from __future__ import annotations
from typing import Set, Tuple, List
import random
import shutil

Pos = Tuple[int, int]

def move(pos: Pos, accion: str) -> Pos:
    """
    Funcion que recibe una posicion y una accion y devuelve
    la posicion obtenida tras la accion.
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
    def __init__(self, n: int = 6) -> None:
        self.n = n
        self.precipicios: Set[Pos] = set()
        self.soldado: Pos | None = None
        self.soldado_vivo: bool = True
        self.kurtz: Pos | None = None
        self.salida: Pos | None = None
        self.reset()

    def reset(self) -> None:
        """
        Reinicia la configuracion del palacio.
        """
        inicio = (1, 1)
        cells: List[Pos] = [(fila, col) for fila in range(1, self.n + 1) for col in range(1, self.n + 1)]
        cells.remove(inicio)
        random.shuffle(cells)

        self.precipicios = set(cells[:3])
        restantes = cells[3:]

        self.soldado = restantes[0]
        self.salida = restantes[1]
        self.kurtz = restantes[2]
        self.soldado_vivo = True

        self._validate()

    def _validate(self) -> None:
        """
        Valida la configuracion generada.
        """
        inicio = (1, 1)
        assert len(self.precipicios) == 3
        assert inicio not in self.precipicios
        assert self.soldado not in self.precipicios
        assert self.kurtz not in self.precipicios
        assert self.kurtz != self.soldado
        posiciones = list(self.precipicios) + [self.soldado, self.kurtz, self.salida]
        assert len(set(posiciones)) == len(posiciones)

    def limites(self, pos: Pos) -> bool:
        """
        Indica si una celda esta dentro de los limites del tablero.
        """
        fila, col = pos
        return 1 <= fila <= self.n and 1 <= col <= self.n

    def neighbors(self, pos: Pos) -> List[Pos]:
        """
        Indica los vecinos en distancia manhattan que tiene la celda actual.
        """
        fila, col = pos
        cand = [(fila - 1, col), (fila + 1, col), (fila, col - 1), (fila, col + 1)]
        return [p for p in cand if self.limites(p)]

    def get_percepts(self, agent_pos: Pos, grito: bool = False) -> List[bool]:
        """
        Funcion que determina los preceptos observables desde la posicion actual.
        """
        fila, col = agent_pos
        pared_up = (fila == 1)
        pared_down = (fila == self.n)
        pared_left = (col == 1)
        pared_right = (col == self.n)

        ady = self.neighbors(agent_pos)

        brisa = any(p in self.precipicios for p in ady)
        ronquido = self.soldado_vivo and (self.soldado in ady)
        resplandor = (agent_pos == self.salida) or (self.salida in ady)

        return {"brisa": brisa, "ronquido": ronquido, "resplandor": resplandor, "pared_up": pared_up, "pared_down": pared_down, "pared_left": pared_left, "pared_right": pared_right, "grito": grito,}    

    def step_move(self, agent_pos: Pos, accion: str) -> Pos:
        """
        Devuelve la nueva posición tras intentar moverse (si hay pared, se queda).
        """
        new_pos = move(agent_pos, accion)
        if not self.limites(new_pos):
            return agent_pos
        return new_pos
    
    def throw_grenade(self, origen: Pos, direccion: str) -> bool:
        """
        Lanza granada 1 celda en dirección UP/DOWN/LEFT/RIGHT.
        Devuelve True si mata al soldado (=> grito en el siguiente percepto).
        """
        objetivo = move(origen, direccion)
        if not self.limites(objetivo):
            return False

        if self.soldado_vivo and (objetivo == self.soldado):
            self.soldado_vivo = False
            return True

        return False



def render_ascii(palacio: Palacio, agent_pos: Pos, visitado:list, reveal: bool = True, kurtz: bool = False) -> None:
    """
    Representa el entorno del palacio en formato ASCII, se puede elegir si mostrar todo el mapa
    o solo las celdas visitadas.
    """
    RESET = "\033[0m"
    ORANGE = "\033[38;5;208m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    MAGENTA = "\033[35m"
    GRAY = "\033[90m"

    def cell_symbol(pos: Pos, visitado: list, kurtz: bool) -> str:
        if pos == agent_pos:
            return f"{ORANGE}CW{RESET}"
        if not reveal:
            if pos in visitado:
                return f"{GRAY} .{RESET}"
            
            return f"{GRAY}??{RESET}"
        if pos in palacio.precipicios:
            return f"{RED} P{RESET}"
        if palacio.soldado_vivo and pos == palacio.soldado:
            return f"{YELLOW} S{RESET}"
        if (not kurtz) and pos == palacio.kurtz:
            return f"{MAGENTA}CK{RESET}"
        if pos == palacio.salida:
            return f"{GREEN} E{RESET}"
        return f"{GRAY} .{RESET}"
     
    ancho_terminal = shutil.get_terminal_size((80, 20)).columns

    ancho_mapa = palacio.n * 3 + (palacio.n - 1)
    margen = max(0, (ancho_terminal - ancho_mapa) // 2)
    prefijo = " " * margen

    for fila in range(1, palacio.n + 1):
        row = [cell_symbol((fila, col), visitado, kurtz) for col in range(1, palacio.n + 1)]
        print(prefijo + " ".join(row))
    print()