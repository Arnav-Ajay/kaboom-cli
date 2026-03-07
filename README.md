# Kaboom CLI

A terminal interface for playing **Kaboom**, a strategic memory-based card game powered by the [**`kaboom-core`**](https://github.com/Arnav-Ajay/kaboom-core) engine.

This project provides a **command-line version of the Kaboom game** for testing, debugging, and quick gameplay without a graphical interface.

It is primarily intended for:

* testing the Kaboom engine
* validating game mechanics
* debugging rules and edge cases
* rapid gameplay during development
* building AI players and simulations

The CLI uses the **kaboom-core engine**, which contains the full game logic and rules.

---

# Architecture

Kaboom is designed with a **layered architecture**.

```
kaboom-core        → game engine (rules, state, scoring)
kaboom-cli         → terminal interface
kaboom-streamlit   → web interface
```

The CLI acts as a **thin interface layer** over the engine.

```
Player Input
      ↓
kaboom-cli
      ↓
kaboom-core
      ↓
Game State Update
      ↓
CLI Rendering
```

This separation ensures:

* the engine remains UI-agnostic
* multiple interfaces can use the same game logic
* easier debugging and testing

---

# Features

Current features:

* Terminal gameplay
* Player setup
* Initial card dealing
* Pre-game peek phase
* Turn-based play
* Draw / replace / discard actions
* Discard pile tracking
* Instant win detection
* Kaboom endgame
* Final score calculation

Planned features:

* Reaction phase mechanics
* Special card powers
* Multi-card matching discards
* AI players
* Game simulation mode
* Replay logging

---

# Installation

Clone the repository:

```bash
git clone https://github.com/Arnav-Ajay/kaboom-cli.git
cd kaboom-cli
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# How Kaboom Works

Kaboom is a **memory and strategy card game** played with a standard 52-card deck.

Each player starts with **four face-down cards** and may look at any two of them before the game begins.

Players attempt to **minimize the total value of their cards** while remembering card positions and reacting to discards.

Key mechanics include:

* reaction matching discards
* card swapping
* card peeking
* penalty cards
* the Kaboom endgame trigger

Full rules are implemented in [`**kaboom-core**`](https://github.com/Arnav-Ajay/kaboom-core).

---

# Development

The CLI interface is intentionally simple and exists primarily to:

* validate engine behavior
* reproduce edge cases
* test game mechanics quickly

Future interfaces (web, online multiplayer) will use the **same engine**.

---

# Repository Structure

```
kaboom-cli
│
├─ kaboom_cli
│   ├─ cli_game.py
│   ├─ cli_input.py
│   ├─ cli_render.py
│
├─ examples
│   └─ play_cli.py
│
├─ README.md
└─ pyproject.toml
```

---

# Roadmap

Planned improvements:

* full reaction window system
* special card powers
* automated tests
* AI players
* game simulation framework
* multiplayer support

---

# License

MIT License

---