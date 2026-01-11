from __future__ import annotations
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

Pos = Tuple[int, int]

DIRS = {"UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}

def add(pos: Pos, d: Tuple[int, int]) -> Pos:
    """
    Funcion que añade la direccion a la posicion actual para obtener asi el destino.
    """
    return (pos[0] + d[0], pos[1] + d[1])

def en_limite(pos: Pos, n: int) -> bool:
    """
    Funcino que determina si una posicion esta dentro de los limites.
    """
    return 1 <= pos[0] <= n and 1 <= pos[1] <= n

def bfs_path(n: int, start: Pos, meta: Pos, bloqueado: Set[Pos]) -> Optional[List[Pos]]:
    """
    Camino mínimo (lista de posiciones) evitando bloqueado. Devuelve None si no hay camino.
    """

    if start == meta:
        return [start]

    q = deque([start])
    padre: Dict[Pos, Optional[Pos]] = {start: None}

    while q:
        actual = q.popleft()
        for d in DIRS.values():
            sig = add(actual, d)
            if not en_limite(sig, n):
                continue
            if sig in bloqueado:
                continue
            if sig in padre:
                continue
            padre[sig] = actual
            if sig == meta:
                path = [sig]
                while path[-1] is not None:
                    path.append(padre[path[-1]])
                path.pop()
                path.reverse()
                return path
            q.append(sig)

    return None

def path_to_actions(path: List[Pos]) -> List[str]:
    """
    Convierte el path a una lista de acciones ["UP"/"DOWN"/...].
    """
    acciones: List[str] = []
    for i in range(len(path) - 1):
        a = path[i]
        b = path[i + 1]
        dr = b[0] - a[0]
        dc = b[1] - a[1]
        for name, (r, c) in DIRS.items():
            if (dr, dc) == (r, c):
                acciones.append(name)
                break
    return acciones
