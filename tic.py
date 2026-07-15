import random
import sys

import numpy as np
import pygame

CELL_SIZE = 150
GRID_SIZE = 3
WIDTH = CELL_SIZE * GRID_SIZE
HEIGHT = CELL_SIZE * GRID_SIZE
SCOREBOARD_HEIGHT = 50
WINDOW_HEIGHT = HEIGHT + SCOREBOARD_HEIGHT
LINE_WIDTH = 4

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
LIGHT_GRAY = (150, 150, 160)
RED = (200, 0, 0)
BLUE = (0, 120, 220)
YELLOW = (230, 200, 0)
GOLD = (240, 195, 60)
BUTTON_BG = (25, 25, 38)
BUTTON_HOVER = (48, 48, 70)

MARK_PADDING = 30

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]

HUMAN = "X"
COMPUTER = "O"
COMPUTER_DELAY_MS = 400
COMPUTER_SKILL = 0.7  # chance the computer plays its best move instead of a random one
MARK_ANIM_MS = 220

STATE_WELCOME = "welcome"
STATE_PLAYING = "playing"

SAMPLE_RATE = 44100


def check_winner(board):
    for line in WIN_LINES:
        a, b, c = line
        if board[a] is not None and board[a] == board[b] == board[c]:
            return board[a], line
    return None, None


def minimax(board, player):
    winner, _ = check_winner(board)
    if winner == COMPUTER:
        return 1
    if winner == HUMAN:
        return -1
    empty = [i for i, mark in enumerate(board) if mark is None]
    if not empty:
        return 0

    scores = []
    for i in empty:
        board[i] = player
        scores.append(minimax(board, HUMAN if player == COMPUTER else COMPUTER))
        board[i] = None

    return max(scores) if player == COMPUTER else min(scores)


def best_move(board):
    empty = [i for i, mark in enumerate(board) if mark is None]

    if random.random() > COMPUTER_SKILL:
        return random.choice(empty)

    best_score = None
    best_index = None
    for i in empty:
        board[i] = COMPUTER
        score = minimax(board, HUMAN)
        board[i] = None
        if best_score is None or score > best_score:
            best_score = score
            best_index = i
    return best_index


def tone_array(frequency, duration_ms, volume=0.3, fade_ms=12):
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, False)
    wave = np.sin(frequency * t * 2 * np.pi)

    fade_samples = max(1, int(SAMPLE_RATE * fade_ms / 1000))
    envelope = np.ones(n_samples)
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

    return wave * envelope * volume


def make_sound(*arrays):
    audio = np.concatenate(arrays)
    samples = (audio * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([samples, samples]))
    return pygame.sndarray.make_sound(stereo)


def load_sounds():
    try:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
    except pygame.error:
        return None

    return {
        "click": make_sound(tone_array(350, 50, 0.2)),
        "place": make_sound(tone_array(520, 70, 0.25)),
        "win": make_sound(
            tone_array(523, 90, 0.3), tone_array(659, 90, 0.3), tone_array(784, 160, 0.35)
        ),
        "draw": make_sound(tone_array(200, 300, 0.25)),
    }


def play(sounds, name):
    if sounds:
        sounds[name].play()


def draw_winning_line(surface, line):
    top = SCOREBOARD_HEIGHT
    bottom = SCOREBOARD_HEIGHT + HEIGHT

    if line in ((0, 1, 2), (3, 4, 5), (6, 7, 8)):
        row = line[0] // GRID_SIZE
        y = top + row * CELL_SIZE + CELL_SIZE // 2
        start, end = (0, y), (WIDTH, y)
    elif line in ((0, 3, 6), (1, 4, 7), (2, 5, 8)):
        col = line[0]
        x = col * CELL_SIZE + CELL_SIZE // 2
        start, end = (x, top), (x, bottom)
    elif line == (0, 4, 8):
        start, end = (0, top), (WIDTH, bottom)
    else:
        start, end = (WIDTH, top), (0, bottom)

    pygame.draw.line(surface, YELLOW, start, end, LINE_WIDTH + 4)


def draw_grid(surface):
    for i in range(1, GRID_SIZE):
        pygame.draw.line(
            surface, GRAY,
            (i * CELL_SIZE, SCOREBOARD_HEIGHT),
            (i * CELL_SIZE, SCOREBOARD_HEIGHT + HEIGHT),
            LINE_WIDTH,
        )
        pygame.draw.line(
            surface, GRAY,
            (0, SCOREBOARD_HEIGHT + i * CELL_SIZE),
            (WIDTH, SCOREBOARD_HEIGHT + i * CELL_SIZE),
            LINE_WIDTH,
        )


def draw_scoreboard(surface, font, scores):
    text = f"X: {scores['X']}    O: {scores['O']}    Draws: {scores['Draws']}"
    text_surf = font.render(text, True, WHITE)
    surface.blit(text_surf, text_surf.get_rect(center=(WIDTH // 2, SCOREBOARD_HEIGHT // 2)))


def draw_menu_button(surface, rect, font, hovered):
    pygame.draw.rect(surface, BUTTON_HOVER if hovered else BUTTON_BG, rect, border_radius=6)
    pygame.draw.rect(surface, GOLD if hovered else LIGHT_GRAY, rect, 1, border_radius=6)
    text_surf = font.render("Menu", True, WHITE)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_marks(surface, board, board_times, now):
    full_reach = CELL_SIZE // 2 - MARK_PADDING

    for index, mark in enumerate(board):
        if mark is None:
            continue
        row, col = divmod(index, GRID_SIZE)
        left = col * CELL_SIZE
        top = SCOREBOARD_HEIGHT + row * CELL_SIZE
        center_x = left + CELL_SIZE // 2
        center_y = top + CELL_SIZE // 2

        placed_at = board_times[index]
        if placed_at is None:
            progress = 1.0
        else:
            t = min(1.0, (now - placed_at) / MARK_ANIM_MS)
            progress = 1 - (1 - t) ** 2  # ease-out

        reach = int(full_reach * progress)

        if mark == "X":
            pygame.draw.line(
                surface, RED,
                (center_x - reach, center_y - reach),
                (center_x + reach, center_y + reach),
                LINE_WIDTH,
            )
            pygame.draw.line(
                surface, RED,
                (center_x + reach, center_y - reach),
                (center_x - reach, center_y + reach),
                LINE_WIDTH,
            )
        elif reach > 0:
            pygame.draw.circle(surface, BLUE, (center_x, center_y), reach, LINE_WIDTH)


def cell_at(pos):
    x, y = pos
    y -= SCOREBOARD_HEIGHT
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        return row * GRID_SIZE + col
    return None


def lerp_color(color_a, color_b, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))


def draw_welcome_background(surface):
    top_color = (18, 18, 40)
    bottom_color = (0, 0, 0)
    for y in range(WINDOW_HEIGHT):
        t = y / WINDOW_HEIGHT
        pygame.draw.line(surface, lerp_color(top_color, bottom_color, t), (0, y), (WIDTH, y))

    ghost = pygame.Surface((WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    pygame.draw.line(ghost, (*RED, 35), (10, 300), (150, 440), 18)
    pygame.draw.line(ghost, (*RED, 35), (150, 300), (10, 440), 18)
    pygame.draw.circle(ghost, (*BLUE, 35), (WIDTH - 80, 370), 70, 18)
    surface.blit(ghost, (0, 0))


def draw_button(surface, rect, text, font, hovered):
    pygame.draw.rect(surface, BUTTON_HOVER if hovered else BUTTON_BG, rect, border_radius=10)
    pygame.draw.rect(surface, GOLD if hovered else LIGHT_GRAY, rect, 2, border_radius=10)
    text_surf = font.render(text, True, WHITE)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_welcome(screen, fonts, buttons, mouse_pos):
    draw_welcome_background(screen)

    shadow = fonts["title"].render("TIC TAC TOE", True, BLACK)
    screen.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 3, 93)))
    title = fonts["title"].render("TIC TAC TOE", True, GOLD)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 90)))

    subtitle = fonts["subtitle"].render("You (X) vs Computer (O)", True, WHITE)
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 140)))

    for key, rect, label in buttons:
        draw_button(screen, rect, label, fonts["button"], rect.collidepoint(mouse_pos))

    footer = fonts["small"].render("Click R button to Restart   |   Esc to quit", True, LIGHT_GRAY)
    screen.blit(footer, footer.get_rect(center=(WIDTH // 2, WINDOW_HEIGHT - 30)))


def main():
    pygame.init()
    sounds = load_sounds()
    screen = pygame.display.set_mode((WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Tic-Tac-Toe - You: X, Computer: O")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)
    button_font = pygame.font.SysFont(None, 30)
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 28)
    score_font = pygame.font.SysFont(None, 32)
    menu_font = pygame.font.SysFont(None, 22)

    fonts = {
        "title": title_font,
        "subtitle": subtitle_font,
        "button": button_font,
        "small": small_font,
    }

    welcome_buttons = [
        ("human_first", pygame.Rect(35, 190, WIDTH - 70, 55), "You Go First (X)"),
        ("computer_first", pygame.Rect(35, 260, WIDTH - 70, 55), "Computer Goes First (O)"),
    ]
    menu_button_rect = pygame.Rect(8, 8, 65, 34)

    def new_game(first_player):
        board = [None] * (GRID_SIZE * GRID_SIZE)
        board_times = [None] * (GRID_SIZE * GRID_SIZE)
        computer_move_at = pygame.time.get_ticks() + COMPUTER_DELAY_MS if first_player == COMPUTER else None
        return board, board_times, first_player, None, None, False, computer_move_at

    def apply_move(board, board_times, player, index):
        board[index] = player
        board_times[index] = pygame.time.get_ticks()
        play(sounds, "place")
        winner, win_line = check_winner(board)
        if winner is None and all(mark is not None for mark in board):
            scores["Draws"] += 1
            play(sounds, "draw")
            return winner, win_line, True
        if winner is not None:
            scores[winner] += 1
            play(sounds, "win")
        return winner, win_line, False

    state = STATE_WELCOME
    scores = {"X": 0, "O": 0, "Draws": 0}
    first_player = HUMAN
    board, board_times, current_player, winner, win_line, is_draw, computer_move_at = new_game(first_player)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if state == STATE_WELCOME:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for key, rect, _ in welcome_buttons:
                        if rect.collidepoint(event.pos):
                            play(sounds, "click")
                            first_player = HUMAN if key == "human_first" else COMPUTER
                            board, board_times, current_player, winner, win_line, is_draw, computer_move_at = new_game(first_player)
                            state = STATE_PLAYING

            elif state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and (winner or is_draw):
                        board, board_times, current_player, winner, win_line, is_draw, computer_move_at = new_game(first_player)
                    elif event.key == pygame.K_m:
                        play(sounds, "click")
                        state = STATE_WELCOME
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if menu_button_rect.collidepoint(event.pos):
                        play(sounds, "click")
                        state = STATE_WELCOME
                    elif not winner and not is_draw and current_player == HUMAN:
                        index = cell_at(event.pos)
                        if index is not None and board[index] is None:
                            winner, win_line, is_draw = apply_move(board, board_times, HUMAN, index)
                            if not winner and not is_draw:
                                current_player = COMPUTER
                                computer_move_at = pygame.time.get_ticks() + COMPUTER_DELAY_MS

        if (
            state == STATE_PLAYING
            and current_player == COMPUTER
            and not winner
            and not is_draw
            and computer_move_at is not None
            and pygame.time.get_ticks() >= computer_move_at
        ):
            index = best_move(board)
            winner, win_line, is_draw = apply_move(board, board_times, COMPUTER, index)
            current_player = HUMAN
            computer_move_at = None

        if state == STATE_WELCOME:
            draw_welcome(screen, fonts, welcome_buttons, mouse_pos)
        else:
            screen.fill(BLACK)
            draw_scoreboard(screen, score_font, scores)
            draw_menu_button(screen, menu_button_rect, menu_font, menu_button_rect.collidepoint(mouse_pos))
            draw_grid(screen)
            draw_marks(screen, board, board_times, pygame.time.get_ticks())
            if win_line:
                draw_winning_line(screen, win_line)

            if winner or is_draw:
                message = f"{winner} wins!" if winner else "Draw!"
                over_surf = font.render(message, True, WHITE)
                restart_surf = small_font.render("R: restart   M: menu   Esc: quit", True, WHITE)
                center_y = SCOREBOARD_HEIGHT + HEIGHT // 2
                overlay_rect = pygame.Rect(0, center_y - 40, WIDTH, 80)
                pygame.draw.rect(screen, BLACK, overlay_rect)
                screen.blit(over_surf, over_surf.get_rect(center=(WIDTH // 2, center_y - 20)))
                screen.blit(restart_surf, restart_surf.get_rect(center=(WIDTH // 2, center_y + 20)))

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()
