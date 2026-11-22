# 1chess

**1chess** is a lightweight Python screen-overlay chess assistant powered by **Stockfish**. It captures the chessboard directly from your screen, automatically learns piece silhouettes from the starting position, and draws real-time arrows showing the best move and expected opponent reply.

**1chess** — лёгкий экранный шахматный помощник на Python с движком **Stockfish**. Скрипт захватывает доску прямо с экрана, автоматически обучается силуэтам фигур со стартовой позиции и рисует поверх окна стрелки лучшего хода и ожидаемого ответа соперника.

---

## Features / Возможности

* **Zero-Config Vision / Автообучение спрайтам:** Works with any board theme or size — automatically learns piece shapes on the starting position. / Работает с любой темой и размером доски — запоминает силуэты фигур при первом нажатии на старте партии.
* **Click-Through Overlay / Прозрачный оверлей:** Draws red (best move) and blue (opponent reply) arrows over the game window without blocking mouse clicks. / Рисует красную (ваш лучший ход) и синюю (ответ соперника) стрелки поверх окна, не мешая кликам мыши.
* **History Sync / Синхронизация истории:** Tracks move history to preserve turn order, castling rights, and en passant. / Отслеживает историю партии, сохраняя очередь хода, права на рокировку и взятие на проходе.
* **Global Hotkeys / Глобальные горячие клавиши:** Press `\` to analyze the current board state, or `ESC` to exit. / Нажмите `\` для анализа текущей позиции или `ESC` для выхода.

---

## Requirements & Setup / Установка и запуск

1. **OS / ОС:** Windows (uses Win32 API for screen capture and transparent overlay).
2. **Install Python dependencies / Установите библиотеки:**
   ```bash
   pip install numpy pillow chess
   ```
3. **Stockfish:** Download the Stockfish binary for Windows from [stockfishchess.org](https://stockfishchess.org) and set the folder path in `STOCKFISH_DIR` inside the script. / Скачайте Stockfish для Windows и укажите путь к папке с `.exe` в переменной `STOCKFISH_DIR`.
4. **Run / Запуск:**
   ```bash
   screen_coach.py
   ```

---

## Disclaimer / Дисклеймер

This tool is intended for educational purposes, post-game analysis, and playing against bots. Using chess engines during live online rated games violates the Terms of Service of platforms like Lichess and Chess.com.

Инструмент предназначен исключительно для обучения, анализа партий и игры против ботов. Использование шахматных движков в онлайн-партиях против людей нарушает правила платформ (Lichess, Chess.com и др.).
