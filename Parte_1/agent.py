from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from world import Pos, Palacio


@dataclass
class AgentState:
    pos: Pos = (1, 1)
    has_grenade: bool = True
    has_kurtz: bool = False
    vivo: bool = True
    ult_grito: bool = False


class Agente:
    def __init__(self) -> None:
        self.state = AgentState()
        self.history: List[Tuple[Pos, List[bool]]] = []  # (pos, percepts)

    def perceive(self, palacio: Palacio) -> List[bool]:
        percepts = palacio.get_percepts(self.state.pos, grito=self.state.ult_grito)
        self.history.append((self.state.pos, percepts))
        self.state.ult_grito = False
        return percepts

    def choose_action_manual(self) -> str:
        key = input("Acción [w/a/s/d, x=salir, g=granada, m=mapa]: ").strip().lower()
        return {
            "w": "UP",
            "s": "DOWN",
            "a": "LEFT",
            "d": "RIGHT",
            "x": "EXIT",
            "m": "MAPA",
            "g": "GRANADA",
        }.get(key, "NOOP")
