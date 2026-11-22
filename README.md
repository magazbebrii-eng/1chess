# 1chess

**1chess** is a lightweight Python screen-overlay chess assistant powered by **Stockfish** and a built-in neural network (`numpy`), designed to draw real-time move arrows without blocking mouse clicks.

**1chess** — лёгкий экранный шахматный помощник на Python с движком **Stockfish** и встроенной нейросетью (`numpy`), рисующий стрелки лучших ходов в реальном времени.

---

## Versions Comparison / Отличия версий

* **1chessV2 (AI From Any Move / Нейросеть с любого хода — Recommended):** Uses a pre-trained neural network (`chess_brain.npz`) for instant position recognition, skin training (`F2`), and coordinate reset (`F3`). / Использует нейросеть (`chess_brain.npz`) для мгновенного распознавания позиций, дообучения (`F2`) и сброса координат (`F3`).
* **1chess v1 (Classic / Классическая версия):** Calibrates piece silhouettes on `\` strictly from the 32-piece starting position. / Калибруется по силуэтам 32 фигур при нажатии `\` со стартовой расстановки.

---

## Features & Hotkeys / Возможности и горячие клавиши

* **Overlay / Оверлей:** Draws move arrows over the game window. / Рисует стрелки поверх окна игры.
* **Hotkeys / Горячие клавиши:**
  * `\` — Analyze current position / Выделить доску и проанализировать позицию.
  * `F2` — Train neural network on a new skin (`1chessV2`) / Дообучить нейросеть (`1chessV2`).
  * `F3` — Reset board coordinates (`1chessV2`) / Сбросить координаты доски (`1chessV2`).
  * `ESC` — Exit program / Выход из программы.

---

## Requirements & Setup / Установка и запуск

1. **OS / ОС:** Windows 10/11.
2. **Python:** 3.10+.
3. **Dependencies / Библиотеки:**
   ```bash
   pip install numpy pillow chess
   ```
4. **Stockfish:** Download from [stockfishchess.org](https://stockfishchess.org) and unpack into the `stockfish/` folder. / Скачайте с [stockfishchess.org](https://stockfishchess.org) и распакуйте в папку `stockfish/`.

### Run Options / Варианты запуска

* **1chessV2:** `python build_brain.py`
* **1chess v1:** `python screen_coach.py`

---

## Disclaimer / Дисклеймер

For educational purposes and playing against bots. Using chess engines in rated online games violates platform rules (Lichess, Chess.com). / Для обучения и игры против ботов. Использование движков в онлайн-матчах нарушает правила платформ (Lichess, Chess.com).
