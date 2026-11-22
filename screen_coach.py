import os, glob, time, ctypes
import tkinter as tk
import numpy as np
from PIL import ImageGrab
import chess, chess.engine

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

STOCKFISH_DIR = r"C:\Users\user\OneDrive\Desktop\stockfish"
exe_files = glob.glob(os.path.join(STOCKFISH_DIR, "**", "*.exe"), recursive=True)
if not exe_files:
    print("Не найден Stockfish .exe!")
    exit()

EXE_PATH = exe_files.pop(0)
CPU_THREADS = max(2, os.cpu_count() or 4)


def start_engine():
    eng = chess.engine.SimpleEngine.popen_uci(EXE_PATH)
    try:
        eng.configure({
            "Threads": CPU_THREADS,
            "Hash": 1024,
            "UCI_LimitStrength": False,
            "Move Overhead": 10
        })
    except Exception:
        pass
    return eng


engine = start_engine()

root = tk.Tk()
root.withdraw()

bbox = None
ov = None
oc = None
templates = {}
is_black = False
key_was_down = False
game_board = chess.Board()

ctypes.windll.user32.GetAsyncKeyState(0xDC)
print(f"Stockfish 19 PRO ({CPU_THREADS} потоков, 1024 МБ) готов! Нажми '\\' на старте партии Lichess/Samara (ESC — выход).")


def select_board():
    sel = tk.Toplevel(root)
    sel.attributes("-fullscreen", True, "-alpha", 0.3, "-topmost", True)
    c = tk.Canvas(sel, cursor="cross", bg="black", highlightthickness=0)
    c.pack(fill="both", expand=True)
    c.create_text(
        sel.winfo_screenwidth() // 2, 50,
        text="Обведите строго 64 клетки доски (ESC — отмена)",
        font=("Segoe UI", 16, "bold"), fill="#FFD60A"
    )
    pts = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
    rect = None

    def down(e):
        nonlocal rect
        pts["x1"], pts["y1"] = e.x, e.y
        rect = c.create_rectangle(e.x, e.y, e.x, e.y, outline="#0A84FF", width=4)

    def move(e):
        if rect:
            c.coords(rect, pts["x1"], pts["y1"], e.x, e.y)

    def up(e):
        pts["x2"], pts["y2"] = e.x, e.y
        sel.destroy()

    c.bind("<ButtonPress-1>", down)
    c.bind("<B1-Motion>", move)
    c.bind("<ButtonRelease-1>", up)
    sel.bind("<Escape>", lambda e: sel.destroy())
    root.wait_window(sel)

    x1, x2 = sorted([pts["x1"], pts["x2"]])
    y1, y2 = sorted([pts["y1"], pts["y2"]])
    if x2 - x1 < 100 or y2 - y1 < 100:
        return None
    return (x1, y1, x2, y2)
def create_overlay(box):
    global ov, oc
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    ov = tk.Toplevel(root)
    ov.overrideredirect(True)
    ov.geometry(f"{w}x{h}+{x1}+{y1}")
    ov.attributes("-topmost", True, "-transparentcolor", "#010203")
    ov.configure(bg="#010203")
    ov.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(ov.winfo_id())
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, ctypes.windll.user32.GetWindowLongW(hwnd, -20) | 0x80020)
    oc = tk.Canvas(ov, width=w, height=h, bg="#010203", highlightthickness=0)
    oc.pack()


def grab_patches(box):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    img = ImageGrab.grab(bbox=box).convert("L")
    sw, sh = w / 8.0, h / 8.0
    out = np.zeros((8, 8, 28, 28), dtype=np.float32)
    for r in range(8):
        for c in range(8):
            cell = (int(c * sw + sw * 0.14), int(r * sh + sh * 0.14), int((c + 1) * sw - sw * 0.14), int((r + 1) * sh - sh * 0.14))
            out[r, c] = np.asarray(img.crop(cell).resize((28, 28)), dtype=np.float32)
    return out


def is_cell_occupied(raw_c):
    center = raw_c[5:23, 5:23]
    corners = [float(raw_c[1:3, 1:3].mean()), float(raw_c[1:3, -3:-1].mean()), float(raw_c[-3:-1, 1:3].mean()), float(raw_c[-3:-1, -3:-1].mean())]
    bg = float(np.median(corners))
    diff_from_bg = np.abs(center - bg)
    return float(np.percentile(diff_from_bg, 82)) > 35.0 and float(center.std()) > 22.0


def extract_silhouette(raw_c):
    corners = [float(raw_c[1:3, 1:3].mean()), float(raw_c[1:3, -3:-1].mean()), float(raw_c[-3:-1, 1:3].mean()), float(raw_c[-3:-1, -3:-1].mean())]
    bg = float(np.median(corners))
    sil = np.abs(raw_c - bg)
    return (sil - sil.mean()) / (sil.std() + 1e-5)


def is_piece_white(raw_c):
    inner = raw_c[6:22, 6:22]
    p88 = float(np.percentile(inner, 88))
    p15 = float(np.percentile(inner, 15))
    if p15 < 65 and p88 < 210:
        return False
    return p88 > 185


def sync_history_with_screen(screen_board, my_color):
    global game_board
    target_fen = screen_board.board_fen()
    if game_board.board_fen() == target_fen and game_board.turn == my_color:
        return game_board

    for m1 in game_board.legal_moves:
        b1 = game_board.copy()
        b1.push(m1)
        if b1.board_fen() == target_fen and b1.turn == my_color:
            game_board = b1
            return game_board

    for m1 in game_board.legal_moves:
        b1 = game_board.copy()
        b1.push(m1)
        for m2 in b1.legal_moves:
            b2 = b1.copy()
            b2.push(m2)
            if b2.board_fen() == target_fen and b2.turn == my_color:
                game_board = b2
                return game_board

    game_board = screen_board.copy()
    game_board.turn = my_color
    try:
        game_board.set_castling_fen("KQkq")
    except Exception:
        pass
    return game_board


def draw_move_arrow(uci, w, h, color="#FF3B30", width=8):
    f1, r1 = chess.square_file(chess.parse_square(uci[:2])), chess.square_rank(chess.parse_square(uci[:2]))
    f2, r2 = chess.square_file(chess.parse_square(uci[2:4])), chess.square_rank(chess.parse_square(uci[2:4]))
    px1, py1 = ((7 - f1 if is_black else f1) + 0.5) * (w / 8), ((r1 if is_black else 7 - r1) + 0.5) * (h / 8)
    px2, py2 = ((7 - f2 if is_black else f2) + 0.5) * (w / 8), ((r2 if is_black else 7 - r2) + 0.5) * (h / 8)
    oc.create_oval(px1 - 7, py1 - 7, px1 + 7, py1 + 7, fill=color, outline="#FFFFFF", width=2)
    oc.create_line(px1, py1, px2, py2, fill=color, width=width, arrow=tk.LAST, arrowshape=(20, 24, 9))
def analyze_on_press():
    global bbox, templates, is_black, engine, game_board
    if bbox is None:
        bbox = select_board()
        if bbox is None:
            print("Выделение отменено. Нажми '\\' снова.")
            return
        create_overlay(bbox)

    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1

    ov.withdraw()
    root.update()
    time.sleep(0.08)
    p = grab_patches(bbox)
    ov.deiconify()

    if not templates:
        bot_w = sum(1 for r in range(6, 8) for c in range(8) if is_cell_occupied(p[r, c]) and is_piece_white(p[r, c]))
        top_w = sum(1 for r in range(0, 2) for c in range(8) if is_cell_occupied(p[r, c]) and is_piece_white(p[r, c]))
        is_black = bool(top_w > bot_w)
        sb = chess.Board()
        for r in range(8):
            for c in range(8):
                rk = r if is_black else 7 - r
                fl = 7 - c if is_black else c
                piece = sb.piece_at(chess.square(fl, rk))
                if piece:
                    templates.setdefault(piece.symbol(), []).append(extract_silhouette(p[r, c]))
        game_board = chess.Board()
        print(f"[Обучение] Спрайты доски сохранены! Цвет: {'ЧЁРНЫЕ' if is_black else 'БЕЛЫЕ'}.")

    nb = chess.Board(None)
    for r in range(8):
        for c in range(8):
            raw_c = p[r, c]
            if not is_cell_occupied(raw_c):
                continue

            w_flag = is_piece_white(raw_c)
            sil = extract_silhouette(raw_c)
            bs, bd = None, 1e9
            for sym, lst in templates.items():
                if sym.isupper() != w_flag:
                    continue
                for t in lst:
                    d = float(np.mean(np.abs(sil - t)))
                    if d < bd:
                        bd, bs = d, sym
            if bs:
                rk = r if is_black else 7 - r
                fl = 7 - c if is_black else c
                nb.set_piece_at(chess.square(fl, rk), chess.Piece.from_symbol(bs))

    for color, k_sym in [(chess.WHITE, "K"), (chess.BLACK, "k")]:
        kings = list(nb.pieces(chess.KING, color))
        if len(kings) > 1:
            best_k = min(kings, key=lambda sq: float(np.mean(np.abs(
                extract_silhouette(p[chess.square_rank(sq) if is_black else 7 - chess.square_rank(sq),
                                     7 - chess.square_file(sq) if is_black else chess.square_file(sq)]) - templates[k_sym].pop(0)
            ))))
            for sq in kings:
                if sq != best_k:
                    nb.set_piece_at(sq, chess.Piece(chess.QUEEN, color))
        elif len(kings) == 0 and k_sym in templates:
            best_sq, best_kd = None, 1e9
            for r in range(8):
                for c in range(8):
                    rk = r if is_black else 7 - r
                    fl = 7 - c if is_black else c
                    sq = chess.square(fl, rk)
                    if nb.piece_at(sq) is not None or not is_cell_occupied(p[r, c]):
                        continue
                    sil = extract_silhouette(p[r, c])
                    for t in templates[k_sym]:
                        d = float(np.mean(np.abs(sil - t)))
                        if d < best_kd:
                            best_kd, best_sq = d, sq
            if best_sq is not None:
                nb.set_piece_at(best_sq, chess.Piece.from_symbol(k_sym))

    my_color = chess.BLACK if is_black else chess.WHITE
    opp_color = not my_color
    nb.turn = my_color

    if not nb.is_valid() and nb.king(opp_color) is not None:
        for att_sq in list(nb.attackers(my_color, nb.king(opp_color))):
            if att_sq != nb.king(my_color):
                nb.remove_piece_at(att_sq)

    oc.delete("all")
    print(f"[Снимок | {'Чёрные' if is_black else 'Белые'}] FEN: {nb.board_fen()}")

    if not nb.is_valid():
        templates.clear()
        print("[Внимание] Позиция с помехой. Нажми '\\' на старте партии (все 32 фигуры на месте).")
        return

    board_to_think = sync_history_with_screen(nb, my_color)

    try:
        info = engine.analyse(board_to_think, chess.engine.Limit(time=2.0))
    except Exception:
        try:
            engine.quit()
        except Exception:
            pass
        engine = start_engine()
        info = engine.analyse(board_to_think, chess.engine.Limit(time=2.0))

    pv = info.get("pv", [])
    score = info.get("score")
    eval_str = ""
    if score:
        pov = score.pov(my_color)
        eval_str = f"Мат в {pov.mate()}" if pov.is_mate() else f"{pov.score() / 100.0:+.2f}"

    if len(pv) > 0:
        best_move = pv.pop(0)
        print(f"[Stockfish 3500+ | Оценка: {eval_str} | Глубина: {info.get('depth', '?')}] -> {board_to_think.san(best_move)} ({best_move.uci()})")
        if len(pv) > 0:
            reply_move = pv.pop(0)
            draw_move_arrow(reply_move.uci(), w, h, color="#0A84FF", width=4)
        draw_move_arrow(best_move.uci(), w, h, color="#FF3B30", width=8)


def loop():
    global key_was_down
    if (ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000) != 0:
        root.destroy()
        return
    key_down = (ctypes.windll.user32.GetAsyncKeyState(0xDC) & 0x8000) != 0
    if key_down and not key_was_down:
        analyze_on_press()
    key_was_down = key_down
    root.after(100, loop)


root.after(100, loop)
root.mainloop()
try:
    engine.quit()
except Exception:
    pass
