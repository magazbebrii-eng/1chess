<div align="center">
  <img src="https://vercel.app" alt="1chess" />
</div>

**1chess** is a lightweight Python screen-overlay chess assistant powered by **Stockfish** and a built-in neural network (`numpy`). It captures the chessboard directly from your screen, recognizes pieces from **any move** (middlegame, endgame, or puzzles), and draws real-time arrows showing the best move and expected opponent reply.

**1chess** — лёгкий экранный шахматный помощник на Python с движком **Stockfish** и встроенной нейросетью (`numpy`). Скрипт захватывает доску прямо с экрана, распознаёт позицию **с любого хода** (миттельшпиль, эндшпиль или задачи) и рисует поверх окна стрелки лучшего хода и ожидаемого ответа соперника.

---

## Features / Возможности

* **AI Vision From Any Move / Нейросеть с любого хода:** Uses a pre-trained neural network (`chess_brain.npz`) trained on board themes from `1chessV2/` — no need to start from the initial position. / Использует встроенную нейросеть (`chess_brain.npz`), обученную на темах досок из `1chessV2/` — можно запускать в любой момент партии.
* **Custom Skin Training / Дообучение на новых скинах:** Press `F2` on a starting position to teach the model a new board or piece theme in seconds. / Нажмите `F2` на стартовой расстановке, чтобы за пару секунд дообучить модель на новой теме доски.
* **Click-Through Overlay / Прозрачный оверлей:** Draws red (best move) and blue (opponent reply) arrows over the game window without blocking mouse clicks. / Рисует красную (ваш лучший ход) и синюю (ответ соперника) стрелки поверх окна, не мешая кликам мыши.
* **History Sync / Синхронизация истории:** Tracks move history to preserve turn order, castling rights, and en passant. / Отслеживает историю партии, сохраняя очередь хода, права на рокировку и взятие на проходе.
* **Global Hotkeys / Глобальные горячие клавиши:**
  * `\` — Select board (on first press) and analyze the current position / Выделить доску и проанализировать текущую позицию.
  * `F2` — Train/update the neural network on a new skin (from starting position) / Дообучить нейросеть на новом скине (со стартовой расстановки).
  * `F3` — Reset board coordinates (if you moved or resized the window) / Сбросить координаты доски (если сдвинули окно).
  * `ESC` — Exit the program / Выход из программы.

---

## Requirements & Setup / Установка и запуск

1. **OS / ОС:** Windows 10/11 (uses Win32 API for screen capture and transparent overlay).
2. **Install Python dependencies / Установите библиотеки Python:**
   ```bash
   pip install numpy pillow chess
   ```
   * `numpy` — built-in neural network (`chess_brain.npz`) and fast matrix processing / работа и обучение нейросети (`chess_brain.npz`).
   * `pillow` — screen capturing (`ImageGrab`) and cell cropping / захват экрана и нарезка клеток.
   * `chess` (`python-chess`) — FEN generation, rule validation, and UCI communication with Stockfish / генерация FEN и связь со Stockfish.
3. **Stockfish:** Download the Stockfish binary for Windows from [stockfishchess.org](https://stockfishchess.org) and unpack it into the `stockfish/` folder next to the script (or set the folder path in `STOCKFISH_DIR` inside `screen_coach.py`). Make sure the `.nnue` network file is in the same folder as the `.exe`. / Скачайте Stockfish для Windows с [stockfishchess.org](https://stockfishchess.org) и распакуйте в папку `stockfish/` рядом со скриптом (убедитесь, что файл `.nnue` лежит рядом с `.exe`).
4. **Run / Запуск:**
   ```bash
   python screen_coach.py
   ```
   *(If `chess_brain.npz` is not present yet, the script will automatically train on the board images inside `1chessV2/` on first launch. / Если файла `chess_brain.npz` ещё нет, скрипт при первом запуске сам обучится на картинках из папки `1chessV2/`).*

---

## Disclaimer / Дисклеймер

This tool is intended for educational purposes, post-game analysis, and playing against bots. Using chess engines during live online rated games violates the Terms of Service of platforms like Lichess and Chess.com.

Инструмент предназначен исключительно для обучения, анализа партий и игры против ботов. Использование шахматных движков в онлайн-партиях против людей нарушает правила платформ (Lichess, Chess.com и др.).
