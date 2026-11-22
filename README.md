# 1chess

**1chess** is a lightweight Python screen-overlay chess assistant powered by **Stockfish** and a built-in neural network (`numpy`), designed to capture board positions from your screen and draw real-time move suggestions.

**1chess** — лёгкий экранный шахматный помощник на Python с движком **Stockfish** и нейросетью (`numpy`), захватывающий позицию с экрана и рисующий подсказки в реальном времени.

---

## Why 1chessV2 is Better / Почему 1chessV2 лучше первой версии (`v1`)

* **Works From Any Move / Работа с любого хода:** Uses a neural network (`chess_brain.npz`) to recognize mid-game or endgame positions immediately, unlike `v1`. / Использует нейросеть (`chess_brain.npz`) для мгновенного распознавания позиций с любого хода.
* **Higher Recognition Accuracy / Высокая точность:** Prevents piece confusion across different themes and lighting. / Исключает путаницу между фигурами при разных темах оформления.
* **Instant Skin Training (`F2`) / Дообучение на новых скинах (`F2`):** Train on a new board style in seconds. / Позволяет за секунды дообучить модель на новом стиле.
* **Quick Coordinate Reset (`F3`) / Быстрый сброс координат (`F3`):** Re-select the board area if the window moves. / Позволяет заново выделить область при смещении окна.

---

## Features / Основные возможности

* **AI Vision / Нейросетевое зрение:** Uses `chess_brain.npz` and `1chessV2/` data. / Использует базу `chess_brain.npz` и данные из папки `1chessV2/`.
* **Click-Through Overlay / Прозрачный оверлей:** Displays best (red) and expected (blue) moves without blocking clicks. / Показывает стрелки лучшего и ответного хода поверх окна.
* **History Sync / Синхронизация истории:** Tracks turn order and special rules. / Отслеживает историю ходов и правила игры.
* **Global Hotkeys / Глобальные горячие клавиши:**
  * `\` — Select board and analyze / Выделить доску и проанализировать.
  * `F2` — Train neural network on a new skin / Дообучить нейросеть на новом скине.
  * `F3` — Reset board coordinates / Сбросить координаты доски.
  * `ESC` — Exit program / Выход из программы.

---

## Requirements & Setup / Установка и запуск

1. **OS / ОС:** Windows 10/11.
2. **Python:** Version 3.10 or higher.
3. **Dependencies / Зависимости:**
   ```bash
   pip install numpy pillow chess
   ```
4. **Stockfish:** Download Stockfish from [stockfishchess.org](https://stockfishchess.org) and place it into the `stockfish/` folder. / Скачайте Stockfish с [stockfishchess.org](https://stockfishchess.org) в папку `stockfish/`.
5. **Run / Запуск:**
   ```bash
   python screen_coach.py
   ```

---

## Disclaimer / Дисклеймер

For educational and post-game analysis purposes only. Using engines in rated online games violates platform terms. / Предназначено для обучения и анализа. Использование в рейтинговых матчах нарушает правила платформ.
