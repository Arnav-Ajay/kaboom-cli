# Kaboom CLI

A command-line interface for interacting with the **Kaboom game engine**, powered by the [**`kaboom-core`**](https://github.com/Arnav-Ajay/kaboom-core) engine.

This repository contains an **early-stage terminal interface** used to interact with and test the Kaboom engine without a graphical UI.

The CLI is intended primarily as a **development and debugging tool**, and acts as a thin interface layer over the deterministic game engine.

---

# Status

⚠️ **This project is in early development.**

The CLI is currently being built incrementally to support engine testing and debugging.
Many gameplay features are still being implemented or refined.

---

# Purpose

The CLI exists primarily to:

* test and validate the Kaboom engine
* reproduce edge cases during development
* debug game state transitions
* allow quick manual gameplay without a graphical interface
* support future **AI agents and simulation experiments**

All game rules and core mechanics are implemented in **kaboom-core**.

---

# Architecture

Kaboom is designed with a layered architecture.

```
kaboom-core        → deterministic game engine
kaboom-cli         → command-line interface
kaboom-ui          → future graphical interface
```

The CLI forwards user actions to the engine and renders the resulting game state.

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

* the engine remains **UI-agnostic**
* multiple interfaces can reuse the same logic
* debugging and testing remain straightforward
* simulation tools can run directly on the engine

---

# Current State

The CLI currently provides **basic interaction with the engine** and is primarily used during development.

Some gameplay mechanics may still be incomplete or evolving as the engine continues to develop.

---

# Planned Features

Planned improvements include:

* complete gameplay flow support
* reaction phase mechanics
* special card powers
* multi-card discard matching
* automated tests
* AI players
* simulation mode for running multiple games
* replay logging
* multiplayer support

---

# Installation

Clone the repository:

```
git clone https://github.com/Arnav-Ajay/kaboom-cli.git
cd kaboom-cli
```

Install dependencies:

```
pip install -r requirements.txt
```

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

# Development Philosophy

The CLI is intentionally lightweight.

Its role is to:

* validate engine behavior
* provide a debugging surface
* allow rapid manual testing
* support future simulation tools

All game logic lives in **kaboom-core**, keeping the interface layer simple and maintainable.

---

# License

MIT License
