# Kaboom CLI

`kaboom-cli` is a thin terminal client for `kaboom-engine>=0.3.0,<0.4.0`.

This first rewrite is intentionally simple:

* it renders the current engine state
* it lists legal actions from `get_valid_actions(state)`
* it executes the selected action through `apply_action`
* it prompts only when a power action needs extra target payload
* `state` refreshes the current screen
* `help` prints the command summary and reaction notes

The CLI is meant to be a manual testing and debugging surface before AI and RL simulation layers are added.

## Core assumptions from `kaboom-engine v0.3.x`

* the engine owns all game rules and phase transitions
* a CLI should branch on `GamePhase`, not custom turn flags
* normal play should rely on `get_valid_actions(state)` for legality
* `UsePower` is the only action that needs interactive payload collection
* reaction turns and pending-power resolution are already represented as legal action objects
* opening peek is part of engine setup, not a CLI-side convention

## Installation

```bash
pip install -e .
```

Or install the dependency directly first:

```bash
pip install -r requirements.txt
```

For local development against the sibling `kaboom-core` repo, reinstall the engine in editable mode after core changes:

```bash
pip install -e ../kaboom-core
```

## Usage

```bash
kaboom-cli --players 4 --hand-size 4
```

Helpful flags:

* `--reveal-all` to show every hand for debugging

## Current scope

Implemented:

* manual terminal play
* draw / discard / replace / kaboom flow
* reaction action selection
* power target prompts
* per-player memory display
* full-hand reveal at game over

Not implemented yet:

* replay logging
* AI opponents
* batch simulation / RL environment
* automated CLI tests
