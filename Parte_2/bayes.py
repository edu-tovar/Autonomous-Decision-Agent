from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, List

Pos = Tuple[int, int]
Tau = str


def neighbors_4(pos: Pos, n: int) -> List[Pos]:
    """
    Funcion que recibe una pociscion, el numero de filas y el numero
    de columnas (nxn) y devuelve una lista con todas las celdas vecinas (ortogonalmente)
    que esten dentro de los limites del tablero.
    """

    fila, col = pos
    cand = [(fila - 1, col), (fila + 1, col), (fila, col - 1), (fila, col + 1)]
    return [(f_vecino, c_vecino) for (f_vecino, c_vecino) in cand if 1 <= f_vecino <= n and 1 <= c_vecino <= n]


@dataclass
class BeliefState:
    """
    Estado de creencias bayesianas del agente en el palacio.

    Esta clase mantiene una distribución de probabilidad sobre todas las celdas
    del tablero, representando la creencia del agente acerca de la posición
    real del elemento.

    Las creencias se actualizan a partir de los perceptos observados.
    """

    n: int = 6
    inicio: Pos = (1, 1)
    taus: Tuple[Tau, ...] = ("F", "P", "D", "M", "S", "CK")
    belief: Dict[Tau, Dict[Pos, float]] = field(default_factory=dict)

    def init_uniform(self) -> None:
        """
        Inicializa las creencias con un prior uniforme.
        """
        
        celdas = [(fila, col) for fila in range(1, self.n + 1) for col in range(1, self.n + 1)]
        otras = [p for p in celdas if p != self.inicio]        # Todas menos la inicial
        p0 = 1.0 / len(otras)

        self.belief = {}
        for tau in self.taus:
            self.belief[tau] = {p: (0.0 if p == self.inicio else p0) for p in celdas}

    def _normalize(self, tau: Tau) -> bool:
        """
        Normaliza la distribucion de probabilidad asociada a un elemento tau.
        """
        
        dist = self.belief[tau]
        suma = sum(dist.values())
        if suma <= 0:
            return False
        for pos in dist:
            dist[pos] /= suma
        return True


    def _likelihood(self, tau_pos: Pos, agent_pos: Pos, visto: bool) -> float:
        """
        Verosimilitud determinista del enunciado:
        P(e_tau(agent_pos) | tau_pos)=1 si tau_pos en adj(agent_pos) U {agent_pos}; si no 0.
        Para ausencia => 1 - anterior.
        """
        adj_self = set(neighbors_4(agent_pos, self.n)) | {agent_pos}
        cerca = 1.0 if tau_pos in adj_self else 0.0
        return cerca if visto else (1.0 - cerca)

    def update(self, agent_pos: Pos, obs: dict) -> None:
        """
        Actualiza las creencias a partir de un nuevo precepto.
        Para cada elemento se aplica la formula de Bayes para calcular el posterior.
        """

        mapping = {"F": "eF", "P": "eP", "D": "eD", "M": "eM", "S": "eS"}

        for tau, k in mapping.items():
            visto = bool(obs[k])
            prior = self.belief[tau]
            post = {}

            for pos, p_prior in prior.items():
                post[pos] = p_prior * self._likelihood(pos, agent_pos, visto)

            self.belief[tau] = post
            ok = self._normalize(tau)

            if not ok:
                post2 = {}
                for pos in prior.keys():
                    post2[pos] = self._likelihood(pos, agent_pos, visto)
                self.belief[tau] = post2
                ok2 = self._normalize(tau)
                if not ok2:
                    celdas = list(prior.keys())
                    p0 = 1.0 / (len(celdas) - 1)
                    self.belief[tau] = {p: (0.0 if p == self.inicio else p0) for p in celdas}

        
    def to_matrix(self, tau: str) -> List[List[float]]:
        """
        Convierte belief[tau] a una matriz nxn.
        """
        mat = [[0.0 for _ in range(self.n)] for _ in range(self.n)]
        for (fila, col), p in self.belief[tau].items():
            mat[fila - 1][col - 1] = p
        return mat

    def traps_any_matrix(self) -> List[List[float]]:
        """
        Devuelve una matriz de riesgo agregado de las trampas.
        """
        mat = [[0.0 for _ in range(self.n)] for _ in range(self.n)]
        for t in ("F", "P", "D"):
            tm = self.to_matrix(t)
            for fila in range(self.n):
                for col in range(self.n):
                    mat[fila][col] += tm[fila][col]
        return mat


    def risk_traps_any(self) -> Dict[Pos, float]:
        """
        Devuelve un diccionario con el riesgo de trampas por celda.
        """
        celdas = [(fila, col) for fila in range(1, self.n + 1) for col in range(1, self.n + 1)]
        out = {p: 0.0 for p in celdas}
        for t in ("F", "P", "D"):
            for p, v in self.belief[t].items():
                out[p] += v
        return out

    def risk_death(self) -> Dict[Pos, float]:
        """
        Devuelve un maapa de riesgo de muerte por cada celda.
        """
        out = self.risk_traps_any()
        for p, v in self.belief["M"].items():
            out[p] += v
        return out
