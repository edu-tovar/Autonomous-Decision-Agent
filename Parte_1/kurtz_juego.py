
import pygame
import random
from typing import Tuple

Pos = Tuple[int, int]


GRID_N = 6
CELL_SIZE = 90
MARGEN = 20
HUD = 160

W = MARGEN * 2 + GRID_N * CELL_SIZE
H = MARGEN * 2 + GRID_N * CELL_SIZE + HUD
FPS = 60


BG = (18, 18, 22)
GRID_LINE = (45, 45, 55)
FLOOR = (28, 28, 35)
FOG = (22, 22, 28)

PLAYER_FILL = (80, 170, 255)
PLAYER_EDGE = (255, 255, 255)

EXIT_COLOR = (60, 220, 120)
KURTZ_COLOR = (170, 90, 230)

TEXT = (230, 230, 235)
WARNING = (255, 210, 90)

NUM_PITS = 3


def rand_board(n: int) -> dict:
    rng = random.Random()
    start_player = (0, 0)

    cells = [(r, c) for r in range(n) for c in range(n)]
    cells.remove(start_player)
    rng.shuffle(cells)

    pits = set(cells[:NUM_PITS])
    rest = cells[NUM_PITS:]

    soldier_danger = rest[0]
    exit_ = rest[1]
    kurtz = rest[2]

    return {
        "mode": "MANUAL",
        "reveal_map": False,


        "n": n,
        "player": start_player,

        "pits": pits,
        "soldier": soldier_danger,
        "exit": exit_,
        "kurtz": kurtz,

        "visited": {start_player},

        "discovered_exit": False,
        "discovered_kurtz": False,

        "soldier_alive": True,
        "has_kurtz": False,

        "grenades": 1,

        
        "aiming": False,
        "aim_dir": (0, 1),

        "game_over": False,
        "win": False,
        "msg": "Move: flechas/WASD | G: apuntar granada | ENTER: lanzar | ESC: cancelar | R: reset",

        "scream_text": "",
        "scream_until_ms": 0,

        "near_soldier_prev": False,
        "near_exit_prev": False,
        "near_pit_prev": False,
    }

def in_bounds(n: int, pos: Pos) -> bool:
    r, c = pos
    return 0 <= r < n and 0 <= c < n

def neighbors(n: int, pos: Pos):
    r, c = pos
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        p = (r + dr, c + dc)
        if in_bounds(n, p):
            yield p

def step(state: dict, dr: int, dc: int) -> None:
    if state["game_over"]:
        return

    r, c = state["player"]
    nxt = (r + dr, c + dc)
    if not in_bounds(state["n"], nxt):
        state["msg"] = "No puedes salirte del tablero."
        return

    state["player"] = nxt
    state["visited"].add(nxt)

    if nxt in state["pits"]:
        state["game_over"] = True
        state["win"] = False
        state["msg"] = "Has caído al precipicio. R para reiniciar."
        return

    if state["soldier_alive"] and nxt == state["soldier"]:
        state["game_over"] = True
        state["win"] = False
        state["msg"] = "El soldado te ha cazado. R para reiniciar."
        return

    if nxt == state["kurtz"]:
        state["has_kurtz"] = True
        state["discovered_kurtz"] = True
        state["msg"] = "Has encontrado a Kurtz. Ahora ve a la salida."
        return

    if nxt == state["exit"]:
        state["discovered_exit"] = True
        if state["has_kurtz"]:
            state["game_over"] = True
            state["win"] = True
            state["msg"] = "Has salido con Kurtz. Victoria. R para reiniciar."
        else:
            state["msg"] = "Has encontrado la salida, pero aún no tienes a Kurtz."
        return

    state["msg"] = "Sigues avanzando..."

def throw_grenade(state: dict, now_ms: int) -> None:
    if state["game_over"]:
        return
    if state["grenades"] <= 0:
        state["msg"] = "No te quedan granadas."
        return

    dr, dc = state["aim_dir"]
    if dr == 0 and dc == 0:
        state["msg"] = "Dirección inválida."
        return

    state["grenades"] -= 1

    r, c = state["player"]
    target = (r + dr, c + dc)

    hit = False
    if in_bounds(state["n"], target):
        if state["soldier_alive"] and target == state["soldier"]:
            hit = True


    if hit:
        state["soldier_alive"] = False
        state["scream_text"] = "AAAAAAAH!!!"
        state["scream_until_ms"] = now_ms + 1200
        state["msg"] = "Granada: has matado al soldado."
    else:
        state["msg"] = "Granada lanzada. No has dado al soldado."


def cell_rect(r: int, c: int) -> pygame.Rect:
    x = MARGEN + c * CELL_SIZE
    y = MARGEN + r * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

def draw_aim_line(screen, state: dict):
    if not state["aiming"]:
        return

    dr, dc = state["aim_dir"]
    if dr == 0 and dc == 0:
        return

    r, c = state["player"]
    target = (r + dr, c + dc)

    if not in_bounds(state["n"], target):
        return

    tr, tc = target
    rect = cell_rect(tr, tc).inflate(-26, -26)
    pygame.draw.rect(screen, (255, 210, 90), rect, width=4, border_radius=10)

def draw_board(screen, font, small, big, state: dict, now_ms: int, near_exit: bool):
    screen.fill(BG)

    for r in range(state["n"]):
        for c in range(state["n"]):
            rect = cell_rect(r, c)
            pygame.draw.rect(screen, FLOOR, rect, border_radius=10)
            pygame.draw.rect(screen, GRID_LINE, rect, width=2, border_radius=10)

            pos = (r, c)

            if (not state["reveal_map"]) and pos not in state["visited"] and pos != state["player"]:
                fog = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                fog.fill((22, 22, 28, 210))
                screen.blit(fog, (rect.x, rect.y))

            if state["discovered_exit"] and pos == state["exit"]:
                pygame.draw.rect(screen, EXIT_COLOR, rect.inflate(-18, -18), border_radius=10)

            if state["discovered_kurtz"] and pos == state["kurtz"]:
                pygame.draw.rect(screen, KURTZ_COLOR, rect.inflate(-18, -18), border_radius=10)
            if state["reveal_map"]:
                if pos in state["pits"]:
                    pygame.draw.rect(screen, (230, 70, 70), rect.inflate(-18, -18), border_radius=10)

                if state["soldier_alive"] and pos == state["soldier"]:
                    pygame.draw.rect(screen, (200, 200, 200), rect.inflate(-18, -18), border_radius=10)

                if pos == state["exit"]:
                    pygame.draw.rect(screen, EXIT_COLOR, rect.inflate(-18, -18), border_radius=10)
                if pos == state["kurtz"]:
                    pygame.draw.rect(screen, KURTZ_COLOR, rect.inflate(-18, -18), border_radius=10)


    draw_aim_line(screen, state)

    if near_exit and not state["discovered_exit"]:
        pr, pc = state["player"]
        halo = cell_rect(pr, pc).inflate(-8, -8)
        pygame.draw.rect(screen, (255, 230, 120), halo, width=6, border_radius=14)

    pr, pc = state["player"]
    prect = cell_rect(pr, pc).inflate(-20, -20)
    pygame.draw.rect(screen, PLAYER_FILL, prect, border_radius=14)
    pygame.draw.rect(screen, PLAYER_EDGE, prect, width=3, border_radius=14)

    hud_y = MARGEN + state["n"] * CELL_SIZE + 6
    hud_rect = pygame.Rect(MARGEN, hud_y, W - 2*MARGEN, HUD - 12)
    pygame.draw.rect(screen, (12, 12, 16), hud_rect, border_radius=18)
    pygame.draw.rect(screen, GRID_LINE, hud_rect, width=2, border_radius=18)

    cx = W // 2
    y = hud_y + 10
    gap = 22

    
    if state["game_over"]:
        titulo = "VICTORIA" if state["win"] else "DERROTA"
        color = EXIT_COLOR if state["win"] else (255, 70, 70)
        t_surf = big.render(titulo, True, color)
        screen.blit(t_surf, (cx - t_surf.get_width()//2, y))
        y += gap + 10

    

    msg_surf = font.render(state["msg"], True, TEXT)
    screen.blit(msg_surf, (cx - msg_surf.get_width()//2, y))
    y += gap

    estado = (
        f"Pos {state['player']} | "
        f"Kurtz {'SI' if state['has_kurtz'] else 'NO'} | "
        f"Soldado {'VIVO' if state['soldier_alive'] else 'MUERTO'} | "
        f"Granadas {state['grenades']}"
        f"Modo {state['mode']} | "
        f"Mapa {'ON' if state['reveal_map'] else 'OFF'}"
    )

    estado_surf = small.render(estado, True, (160, 160, 170))
    screen.blit(estado_surf, (cx - estado_surf.get_width()//2, y))
    y += gap

    controls = (
        "WASD/Flechas · G apuntar · ENTER lanzar · R reset · M mapa · "
        "1 Modo manual · 2 Busqueda 1 · 3 Busqueda 2"
    )

    controls_lines = [
    "WASD/Flechas · G apuntar · ENTER lanzar · R reset · M mapa",
    "1 Modo manual · 2 Busqueda 1 · 3 Busqueda 2"
]

    for ln in controls_lines:
        surf = small.render(ln, True, (120, 120, 130))
        screen.blit(surf, (cx - surf.get_width() // 2, y))
        y += 18




    if now_ms < state["scream_until_ms"] and state["scream_text"]:
        scream = big.render(state["scream_text"], True, (255, 70, 70))
        screen.blit(scream, (W//2 - scream.get_width()//2, 10))


def main():
    pygame.init()

    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Palacio 6x6 | Granada con apuntado (sin sonido)")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 18)
    small = pygame.font.SysFont("consolas", 16)
    big = pygame.font.SysFont("consolas", 44, bold=True)

    state = rand_board(GRID_N)

    running = True
    while running:
        now_ms = pygame.time.get_ticks()
        clock.tick(FPS)

        p = state["player"]
        near_soldier = state["soldier_alive"] and any(nb == state["soldier"] for nb in neighbors(state["n"], p))
        near_exit = any(nb == state["exit"] for nb in neighbors(state["n"], p))
        near_pit = any(nb in state["pits"] for nb in neighbors(state["n"], p))

        if near_soldier and not state["near_soldier_prev"]:
            state["msg"] = "Oyes ronquidos... (soldado cerca)"
        state["near_soldier_prev"] = near_soldier

        if near_exit and not state["near_exit_prev"] and not state["discovered_exit"]:
            state["msg"] = "Ves un destello... (salida cerca)"
        state["near_exit_prev"] = near_exit

        if (not near_soldier) and near_pit and not state["near_pit_prev"]:
            state["msg"] = "Sientes una brisa... (precipicio cerca)"
        state["near_pit_prev"] = near_pit

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_m:
                    state["reveal_map"] = not state["reveal_map"]
                    state["msg"] = f"Mapa completo: {'ON' if state['reveal_map'] else 'OFF'}"

                if event.key == pygame.K_1:
                    state["mode"] = "MANUAL"
                    state["msg"] = "Modo: MANUAL"
                if event.key == pygame.K_2:
                    state["mode"] = "BUSQUEDA_1"
                    state["msg"] = "Modo: BUSQUEDA_1"
                if event.key == pygame.K_3:
                    state["mode"] = "BUSQUEDA_2"
                    state["msg"] = "Modo: BUSQUEDA_2"



                if event.key == pygame.K_r:
                    state = rand_board(GRID_N)

                if event.key == pygame.K_g and not state["game_over"]:
                    state["aiming"] = True
                    state["msg"] = "Elige dirección de granada."

                if state["aiming"]:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        state["aim_dir"] = (-1, 0)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        state["aim_dir"] = (1, 0)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        state["aim_dir"] = (0, -1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        state["aim_dir"] = (0, 1)
                    elif event.key == pygame.K_RETURN:
                        throw_grenade(state, now_ms)
                        state["aiming"] = False
                    elif event.key == pygame.K_ESCAPE:
                        state["aiming"] = False
                        state["msg"] = "Apuntado cancelado."
                    continue

                if event.key in (pygame.K_UP, pygame.K_w):
                    step(state, -1, 0)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    step(state, 1, 0)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    step(state, 0, -1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    step(state, 0, 1)

        draw_board(screen, font, small, big, state, now_ms, near_exit)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
