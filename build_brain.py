import os
import glob
import time
import ctypes
import traceback
import tkinter as tk
import numpy as np
from PIL import Image, ImageGrab
import chess
import chess.engine

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOARDS_DIR = os.path.join(BASE_DIR, "boards")
BRAIN_PATH = os.path.join(BASE_DIR, "chess_brain.npz")
STOCKFISH_DIR = os.path.join(BASE_DIR, "stockfish")
if not os.path.exists(STOCKFISH_DIR):
    STOCKFISH_DIR = r"C:\Users\user\OneDrive\Desktop\stockfish"

CLASSES = ["1", "P", "N", "B", "R", "Q", "K", "p", "n", "b", "r", "q", "k"]

exe_files = glob.glob(os.path.join(STOCKFISH_DIR, "**", "*.exe"), recursive=True)
if not exe_files:
    print("Не найден Stockfish .exe! Положите папку stockfish рядом со скриптом.")
    exit()

EXE_PATH = next(iter(exe_files))
CPU_THREADS = max(2, os.cpu_count() or 4)


def start_engine():
    eng = chess.engine.SimpleEngine.popen_uci(EXE_PATH)
    try:
        eng.configure({
            "Threads": max(1, CPU_THREADS // 2),
            "Hash": 128
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
key_slash_down = False
key_f2_down = False
key_f3_down = False
game_board = chess.Board()
brain_weights = None


def extract_features(raw_c):
    corners = [
        float(raw_c[1:3, 1:3].mean()),
        float(raw_c[1:3, -3:-1].mean()),
        float(raw_c[-3:-1, 1:3].mean()),
        float(raw_c[-3:-1, -3:-1].mean())
    ]
    bg = float(np.median(corners))
    diff = (raw_c - bg) / 255.0
    norm = (raw_c - raw_c.mean()) / (raw_c.std() + 1e-5)
    inner = raw_c[5:23, 5:23]
    stats = np.array([
        float(np.abs(diff[4:24, 4:24]).mean()),
        float(inner.std()) / 128.0,
        float(np.percentile(inner, 88)) / 255.0,
        float(np.percentile(inner, 15)) / 255.0
    ], dtype=np.float32)
    return np.concatenate([diff[2:26, 2:26].flatten(), norm[2:26, 2:26].flatten(), stats])


def slice_board_image(img_path):
    img = Image.open(img_path).convert("L")
    w, h = img.size
    margin_x = int(w * 0.015)
    margin_y = int(h * 0.015)
    board_img = img.crop((margin_x, margin_y, w - margin_x, h - margin_y))
    bw, bh = board_img.size
    sw, sh = bw / 8.0, bh / 8.0

    patches = np.zeros((8, 8, 28, 28), dtype=np.float32)
    for r in range(8):
        for c in range(8):
            cell = (
                int(c * sw + sw * 0.14),
                int(r * sh + sh * 0.14),
                int((c + 1) * sw - sw * 0.14),
                int((r + 1) * sh - sh * 0.14)
            )
            patches[r, c] = np.asarray(board_img.crop(cell).resize((28, 28)), dtype=np.float32)
    return patches


def augment_patches_to_dataset(patches, is_black_start=False):
    sb = chess.Board()
    X_part, y_part = [], []
    for r in range(8):
        for c in range(8):
            rk = r if is_black_start else 7 - r
            fl = 7 - c if is_black_start else c
            piece = sb.piece_at(chess.square(fl, rk))
            sym = piece.symbol() if piece else "1"
            cls_idx = CLASSES.index(sym)
            base_patch = patches[r, c]

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    shifted = np.roll(np.roll(base_patch, dy, axis=0), dx, axis=1)
                    for scale in (0.92, 1.0, 1.08):
                        aug = np.clip(shifted * scale, 0, 255)
                        X_part.append(extract_features(aug))
                        y_part.append(cls_idx)
    return X_part, y_part


def fit_and_save_network(X_list, y_list):
    global brain_weights
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int64)
    n_samples = len(X)
    print(f"[Нейросеть] Обучение на {n_samples} примерах...")

    rng = np.random.default_rng(42)
    in_dim = len(next(iter(X)))
    hidden_dim = 160
    W1 = rng.normal(0, 0.05, (in_dim, hidden_dim)).astype(np.float32)
    b1 = np.zeros(hidden_dim, dtype=np.float32)
    W2 = rng.normal(0, 0.05, (hidden_dim, len(CLASSES))).astype(np.float32)
    b2 = np.zeros(len(CLASSES), dtype=np.float32)

    Y_oh = np.eye(len(CLASSES), dtype=np.float32)[y]
    lr = 0.08

    for epoch in range(250):
        perm = rng.permutation(n_samples)
        Xp, Yp = X[perm], Y_oh[perm]
        z1 = Xp @ W1 + b1
        a1 = np.maximum(0, z1)
        z2 = a1 @ W2 + b2
        z2 -= z2.max(axis=1, keepdims=True)
        exp_z = np.exp(z2)
        probs = exp_z / exp_z.sum(axis=1, keepdims=True)

        dz2 = (probs - Yp) / n_samples
        dW2 = a1.T @ dz2 + 1e-4 * W2
        db2 = dz2.sum(axis=0)
        da1 = dz2 @ W2.T
        dz1 = da1 * (z1 > 0)
        dW1 = Xp.T @ dz1 + 1e-4 * W1
        db1 = dz1.sum(axis=0)

        W1 -= lr * dW1
        b1 -= lr * db1
        W2 -= lr * dW2
        b2 -= lr * db2

    np.savez_compressed(BRAIN_PATH, W1=W1, b1=b1, W2=W2, b2=b2, X=X, y=y)
    brain_weights = (W1, b1, W2, b2)
    print(f"[Нейросеть] Готово! База сохранена в {os.path.basename(BRAIN_PATH)}.")


def init_brain():
    global brain_weights
    if os.path.exists(BRAIN_PATH):
        data = np.load(BRAIN_PATH)
        brain_weights = (data["W1"], data["b1"], data["W2"], data["b2"])
        print(f"[Нейросеть] Загружена база {os.path.basename(BRAIN_PATH)}. Можно анализировать с любого хода!")
        return

    image_files = []
    if os.path.exists(BOARDS_DIR):
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            image_files.extend(glob.glob(os.path.join(BOARDS_DIR, ext)))

    if image_files:
        print(f"[Нейросеть] Найдено {len(image_files)} досок в папке boards/. Запускаю первичное обучение...")
        X_all, y_all = [], []
        for path in image_files:
            print(f"  -> Обработка {os.path.basename(path)}")
            patches = slice_board_image(path)
            xp, yp = augment_patches_to_dataset(patches, is_black_start=False)
            X_all.extend(xp)
            y_all.extend(yp)
        fit_and_save_network(X_all, y_all)
    else:
        print("[Внимание] База не найдена. Откройте стартовую позицию и нажмите F2 для обучения.")
def predict_board(patches):
    W1, b1, W2, b2 = brain_weights
    feats = np.array([extract_features(patches[r, c]) for r in range(8) for c in range(8)], dtype=np.float32)
    a1 = np.maximum(0, feats @ W1 + b1)
    logits = a1 @ W2 + b2
    pred_ids = np.argmax(logits, axis=1)
    labels = [CLASSES[int(i)] for i in pred_ids]

    w_rows = [idx // 8 for idx, s in enumerate(labels) if s == "K"]
    b_rows = [idx // 8 for idx, s in enumerate(labels) if s == "k"]
    w_r = next(iter(w_rows), 7)
    b_r = next(iter(b_rows), 0)
    is_blk = bool(b_r > w_r)

    nb = chess.Board(None)
    for idx, sym in enumerate(labels):
        if sym == "1":
            continue
        r, c = divmod(idx, 8)
        rk = r if is_blk else 7 - r
        fl = 7 - c if is_blk else c
        nb.set_piece_at(chess.square(fl, rk), chess.Piece.from_symbol(sym))

    return nb, is_blk


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
    if ov and ov.winfo_exists():
        ov.destroy()
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
            cell = (
                int(c * sw + sw * 0.14),
                int(r * sh + sh * 0.14),
                int((c + 1) * sw - sw * 0.14),
                int((r + 1) * sh - sh * 0.14)
            )
            out[r, c] = np.asarray(img.crop(cell).resize((28, 28)), dtype=np.float32)
    return out


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

    castling = ""
    if screen_board.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE):
        if screen_board.piece_at(chess.H1) == chess.Piece(chess.ROOK, chess.WHITE):
            castling += "K"
        if screen_board.piece_at(chess.A1) == chess.Piece(chess.ROOK, chess.WHITE):
            castling += "Q"
    if screen_board.piece_at(chess.E8) == chess.Piece(chess.KING, chess.BLACK):
        if screen_board.piece_at(chess.H8) == chess.Piece(chess.ROOK, chess.BLACK):
            castling += "k"
        if screen_board.piece_at(chess.A8) == chess.Piece(chess.ROOK, chess.BLACK):
            castling += "q"

    try:
        game_board.set_castling_fen(castling or "-")
    except Exception:
        pass
    return game_board


def draw_move_arrow(uci, w, h, is_blk, color="#FF3B30", width=8):
    f1, r1 = chess.square_file(chess.parse_square(uci[:2])), chess.square_rank(chess.parse_square(uci[:2]))
    f2, r2 = chess.square_file(chess.parse_square(uci[2:4])), chess.square_rank(chess.parse_square(uci[2:4]))
    px1 = ((7 - f1 if is_blk else f1) + 0.5) * (w / 8)
    py1 = ((r1 if is_blk else 7 - r1) + 0.5) * (h / 8)
    px2 = ((7 - f2 if is_blk else f2) + 0.5) * (w / 8)
    py2 = ((r2 if is_blk else 7 - r2) + 0.5) * (h / 8)
    oc.create_oval(px1 - 7, py1 - 7, px1 + 7, py1 + 7, fill=color, outline="#FFFFFF", width=2)
    oc.create_line(px1, py1, px2, py2, fill=color, width=width, arrow=tk.LAST, arrowshape=(20, 24, 9))


def handle_train_from_screen():
    global bbox
    bbox = select_board()
    if bbox is None:
        print("Выделение отменено.")
        return
    create_overlay(bbox)
    ov.withdraw()
    root.update()
    time.sleep(0.08)
    p = grab_patches(bbox)
    ov.deiconify()
    root.update()

    bot_w = sum(1 for r in range(6, 8) for c in range(8) if float(p[r, c, 6:22, 6:22].mean()) > 140)
    top_w = sum(1 for r in range(0, 2) for c in range(8) if float(p[r, c, 6:22, 6:22].mean()) > 140)
    is_blk_start = bool(top_w > bot_w)

    X_all, y_all = [], []
    if os.path.exists(BRAIN_PATH):
        d = np.load(BRAIN_PATH)
        if "X" in d and "y" in d:
            X_all.extend(list(d["X"]))
            y_all.extend(list(d["y"]))

    xp, yp = augment_patches_to_dataset(p, is_black_start=is_blk_start)
    X_all.extend(xp)
    y_all.extend(yp)
    fit_and_save_network(X_all, y_all)


def reset_board_box():
    global bbox, ov, oc
    bbox = None
    if ov and ov.winfo_exists():
        ov.destroy()
    ov = None
    oc = None
    print("[Сброс] Координаты доски очищены. Нажмите '\\' для нового выделения.")


def analyze_on_press():
    global bbox, engine, game_board
    if brain_weights is None:
        print("[Внимание] База скинов не найдена! Откройте стартовую позицию и нажмите F2 для обучения.")
        return

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
    root.update()

    nb, is_blk = predict_board(p)
    my_color = chess.BLACK if is_blk else chess.WHITE
    opp_color = not my_color
    nb.turn = my_color

    if not nb.is_valid() and nb.king(opp_color) is not None:
        for att_sq in list(nb.attackers(my_color, nb.king(opp_color))):
            if att_sq != nb.king(my_color):
                nb.remove_piece_at(att_sq)

    oc.delete("all")
    root.update()
    print(f"[Снимок | {'Чёрные' if is_blk else 'Белые'}] FEN: {nb.board_fen()}")

    if not nb.is_valid():
        print("[Внимание] Позиция распознана с ошибкой. Нажмите F2 на стартовой позиции этого скина для дообучения.")
        return

    board_to_think = sync_history_with_screen(nb, my_color).copy()
    print("[Движок] Считаю лучший ход...")

    try:
        info = engine.analyse(board_to_think, chess.engine.Limit(time=1.0))
    except Exception as e:
        print(f"[Ошибка Stockfish]: {e}")
        print("Проверьте, что в папке со Stockfish рядом с .exe лежит файл .nnue и хватает памяти!")
        try:
            engine = start_engine()
        except Exception:
            pass
        return

    pv = info.get("pv", [])
    score = info.get("score")
    eval_str = ""
    if score:
        pov = score.pov(my_color)
        eval_str = f"Мат в {pov.mate()}" if pov.is_mate() else f"{pov.score() / 100.0:+.2f}"

    if len(pv) > 0:
        best_move, *rest = pv
        reply_move = next(iter(rest), None)
        san_move = board_to_think.san(best_move)
        depth = info.get("depth", "?")
        print(f"[Stockfish | Оценка: {eval_str} | Глубина: {depth}] -> {san_move} ({best_move.uci()})")
        if reply_move:
            draw_move_arrow(reply_move.uci(), w, h, is_blk, color="#0A84FF", width=4)
        draw_move_arrow(best_move.uci(), w, h, is_blk, color="#FF3B30", width=8)
        root.update()
    else:
        print("[Движок] Нет доступных ходов (мат или пат).")


init_brain()
ctypes.windll.user32.GetAsyncKeyState(0xDC)
ctypes.windll.user32.GetAsyncKeyState(0x71)
ctypes.windll.user32.GetAsyncKeyState(0x72)
print(f"\n1chess PRO ({CPU_THREADS} потоков) готов!")
print("  '\\'  — выделить доску и проанализировать ЛЮБУЮ позицию")
print("  'F2'  — дообучить нейросеть на новом скине доски (на стартовой позиции)")
print("  'F3'  — сбросить координаты доски (если сдвинули окно)")
print("  'ESC' — выход")


def loop():
    global key_slash_down, key_f2_down, key_f3_down
    try:
        if (ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000) != 0:
            try:
                engine.quit()
            except Exception:
                pass
            root.destroy()
            return

        slash_now = (ctypes.windll.user32.GetAsyncKeyState(0xDC) & 0x8000) != 0
        if slash_now and not key_slash_down:
            analyze_on_press()
        key_slash_down = slash_now

        f2_now = (ctypes.windll.user32.GetAsyncKeyState(0x71) & 0x8000) != 0
        if f2_now and not key_f2_down:
            handle_train_from_screen()
        key_f2_down = f2_now

        f3_now = (ctypes.windll.user32.GetAsyncKeyState(0x72) & 0x8000) != 0
        if f3_now and not key_f3_down:
            reset_board_box()
        key_f3_down = f3_now
    except Exception as e:
        print("[Ошибка]:", e)
        traceback.print_exc()
    root.after(100, loop)


root.after(100, loop)
root.mainloop()
