from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable

from kaboom import (
    ActionResult,
    CallKaboom,
    CloseReaction,
    Discard,
    Draw,
    GameEngine,
    GamePhase,
    InvalidActionError,
    OpeningPeek,
    Player,
    PowerType,
    ReactionResult,
    Replace,
    ResolvePendingPower,
    UsePower,
    apply_action,
    get_valid_actions,
)
from kaboom.game.actions import (
    ReactDiscardOtherCard,
    ReactDiscardOwnCard,
)


SUIT_MAP = {
    "\u2660": "S",
    "\u2665": "H",
    "\u2666": "D",
    "\u2663": "C",
}


@dataclass(slots=True)
class CliConfig:
    num_players: int
    hand_size: int
    reveal_all: bool


class KaboomCliApp:
    def __init__(self, config: CliConfig) -> None:
        self.config = config
        self.engine = GameEngine(
            game_id=0,
            num_players=config.num_players,
            hand_size=config.hand_size,
        )

    def run(self) -> int:
        self._print_welcome()
        self._run_opening_peek()
        self._print_starting_memories()

        while not self.engine.is_game_over():
            state = self.engine.state
            player = state.current_player()

            if not player.active:
                state.advance_turn()
                continue

            self._render_state(player)
            actions = get_valid_actions(state)

            if not actions:
                print("No legal actions are available. Ending game.")
                break

            if state.reaction_open and state.pending_power_action is not None:
                print(
                    "Contested discard window: the first action chosen below wins "
                    "priority for this discard event."
                )
                print("")

            self._render_actions(actions)
            try:
                raw = input("Choose action number, or type 'help', 'state', 'quit': ").strip()
            except EOFError:
                print("\nExiting without finishing the game.")
                return 0

            if not raw:
                continue
            if raw.lower() == "quit":
                print("Exiting without finishing the game.")
                return 0
            if raw.lower() == "help":
                self._print_help()
                continue
            if raw.lower() == "state":
                continue

            try:
                index = int(raw) - 1
            except ValueError:
                print("Input must be an action number, 'state', or 'quit'.")
                continue

            if index < 0 or index >= len(actions):
                print("Action number out of range.")
                continue

            base_action = actions[index]

            try:
                resolved_action = self._resolve_action(base_action, player)
                results = apply_action(state, resolved_action)
            except InvalidActionError as exc:
                print(f"Invalid action: {exc}")
                continue
            except KeyboardInterrupt:
                print("\nAction cancelled.")
                continue

            self._print_results(results)

        self._print_game_over()
        return 0

    def _print_welcome(self) -> None:
        print("Kaboom CLI")
        print(f"Players: {self.config.num_players} | Hand size: {self.config.hand_size}")
        print("")

    def _print_starting_memories(self) -> None:
        print("Starting two-card view:")
        for player in self.engine.state.players:
            visible = []
            for index in range(len(player.hand)):
                card = player.memory.get((player.id, index))
                if card is not None:
                    visible.append(f"{index}:{self._format_card(card)}")
            cards_text = "[" + ", ".join(visible) + "]" if visible else "[]"
            print(f"  P{player.id} {player.name}: {cards_text}")
        print("")

    def _run_opening_peek(self) -> None:
        state = self.engine.state
        while state.phase == GamePhase.OPENING_PEEK:
            player = state.current_player()
            print(f"Opening peek: P{player.id} {player.name}")
            print(
                "Choose exactly two of your own card positions to see once. "
                "The cards remain face down after this."
            )
            print(
                "Slots: ["
                + ", ".join(f"{idx}:??" for idx, _ in enumerate(player.hand))
                + "]"
            )

            indices = self._ask_opening_peek_indices(len(player.hand))
            try:
                results = apply_action(state, OpeningPeek(actor_id=player.id, card_indices=indices))
            except InvalidActionError as exc:
                print(f"Invalid opening peek: {exc}")
                continue

            remembered = ", ".join(
                f"{idx}:{self._format_card(player.memory[(player.id, idx)])}"
                for idx in indices
            )
            self._print_results(results)
            print(f"Peeked: [{remembered}]")
            print("")

    def _render_state(self, viewer: Player) -> None:
        state = self.engine.state
        print("=" * 72)
        print(
            f"Round {state.round_number} | Phase: {state.phase.value} | "
            f"Current player: {viewer.name} (P{viewer.id})"
        )
        print(
            f"Deck: {len(state.deck)} | Discard top: {self._format_card(state.top_discard())} | "
            f"Drawn: {self._format_card(state.drawn_card)}"
        )
        if state.kaboom_called_by is not None:
            print(f"Kaboom called by: P{state.kaboom_called_by}")
        if state.reaction_open:
            print(
                f"Reaction open for rank {state.reaction_rank} | "
                f"Initiator: P{state.reaction_initiator}"
            )
            print(
                "Reaction rule: a correct claim discards the card; a wrong guess "
                "reveals it to everyone and gives the guesser a penalty card."
            )
        if state.pending_power_action is not None:
            pending = state.pending_power_action
            print(
                "Pending power claim: "
                f"P{pending.actor_id} -> {pending.power_name.value}"
            )
        print("")
        for player in state.players:
            print(self._format_player_line(viewer, player))
        print("")
        self._print_memories()
        print("")

    def _format_player_line(self, viewer: Player, player: Player) -> str:
        status = []
        if player.id == self.engine.state.current_player().id:
            status.append("current")
        if not player.active:
            status.append("inactive")
        if player.revealed:
            status.append("revealed")
        status_text = f" [{' | '.join(status)}]" if status else ""

        reveal_full_hand = self.config.reveal_all or viewer.id == player.id or player.revealed
        cards = self._format_hand(player, reveal_full_hand)
        score = player.total_score() if self._can_show_score(player, reveal_full_hand) else "?"
        return (
            f"P{player.id} {player.name}{status_text} | "
            f"Cards: {cards} | Score: {score}"
        )

    def _print_memories(self) -> None:
        print("Memory:")
        any_memory = False
        for player in self.engine.state.players:
            remembered = []
            for (target_player_id, card_index), card in sorted(player.memory.items()):
                remembered.append(
                    f"P{target_player_id}[{card_index}]={self._format_card(card)}"
                )

            if remembered:
                any_memory = True
                print(f"  P{player.id} {player.name}: [{', '.join(remembered)}]")

        if not any_memory:
            print("  none")

    def _render_actions(self, actions: Iterable[object]) -> None:
        print("Legal actions:")
        for number, action in enumerate(actions, start=1):
            print(f"  {number}. {self._describe_action(action)}")
        print("")

    def _print_help(self) -> None:
        print("")
        print("Commands:")
        print("  <number>  Execute that legal action")
        print("  state     Refresh the current game state")
        print("  help      Show this command summary")
        print("  quit      Exit without finishing the game")
        print("")
        print("Notes:")
        print("  Reaction choices are attempts, not guaranteed outcomes.")
        print("  Wrong guesses reveal the attempted card and add a penalty card.")
        print("  During contested power windows, the first chosen valid action wins priority.")
        print("")

    def _describe_action(self, action: object) -> str:
        if isinstance(action, Draw):
            return "Draw from deck"
        if isinstance(action, OpeningPeek):
            return "Opening peek at " + ", ".join(str(index) for index in action.card_indices)
        if isinstance(action, Discard):
            return "Discard drawn card"
        if isinstance(action, Replace):
            return f"Replace hand card at index {action.target_index}"
        if isinstance(action, CallKaboom):
            return "Call Kaboom"
        if isinstance(action, CloseReaction):
            return f"P{action.actor_id}: close reaction window"
        if isinstance(action, ResolvePendingPower):
            return f"P{action.actor_id}: resolve pending power"
        if isinstance(action, UsePower):
            return f"Use power: {action.power_name.value}"
        if isinstance(action, ReactDiscardOwnCard):
            return (
                f"P{action.actor_id}: attempt own-card claim at index {action.card_index} "
                "(wrong guess = reveal + penalty)"
            )
        if isinstance(action, ReactDiscardOtherCard):
            return (
                f"P{action.actor_id}: attempt claim on "
                f"P{action.target_player_id}[{action.target_card_index}] "
                f"using your card {action.give_card_index} "
                "(if correct, target card is discarded and your card is given)"
            )
        return action.__class__.__name__

    def _resolve_action(self, action: object, actor: Player) -> object:
        if not isinstance(action, UsePower):
            return action

        print(f"Resolving power payload for {action.power_name.value}")

        if action.power_name == PowerType.SEE_SELF:
            target_card_index = self._ask_index(
                prompt="Choose your own card index to inspect",
                upper=len(actor.hand),
            )
            return UsePower(
                actor_id=actor.id,
                power_name=action.power_name,
                source_card=action.source_card,
                target_card_index=target_card_index,
            )

        if action.power_name == PowerType.SEE_OTHER:
            target_player_id = self._ask_player_id(
                prompt="Choose target player id",
                exclude={actor.id},
            )
            target_player = self.engine.state.resolve_player(target_player_id)
            target_card_index = self._ask_index(
                prompt=f"Choose card index from P{target_player_id}",
                upper=len(target_player.hand),
            )
            return UsePower(
                actor_id=actor.id,
                power_name=action.power_name,
                source_card=action.source_card,
                target_player_id=target_player_id,
                target_card_index=target_card_index,
            )

        if action.power_name in {PowerType.BLIND_SWAP, PowerType.SEE_AND_SWAP}:
            first_card_index = self._ask_index(
                prompt=f"Choose your own card index from P{actor.id}",
                upper=len(actor.hand),
            )
            second_player_id = self._ask_player_id(
                prompt="Choose target player id",
                exclude={actor.id},
            )
            second_player = self.engine.state.resolve_player(second_player_id)
            second_card_index = self._ask_index(
                prompt=f"Choose card index from P{second_player_id}",
                upper=len(second_player.hand),
            )
            return UsePower(
                actor_id=actor.id,
                power_name=action.power_name,
                source_card=action.source_card,
                target_player_id=actor.id,
                target_card_index=first_card_index,
                second_target_player_id=second_player_id,
                second_target_card_index=second_card_index,
            )

        raise InvalidActionError(f"Unsupported power type: {action.power_name}")

    def _ask_player_id(self, prompt: str, exclude: set[int]) -> int:
        valid = {player.id for player in self.engine.state.players if player.id not in exclude}
        while True:
            raw = input(f"{prompt} {sorted(valid)}: ").strip()
            try:
                player_id = int(raw)
            except ValueError:
                print("Player id must be an integer.")
                continue
            if player_id not in valid:
                print("Player id is not valid here.")
                continue
            return player_id

    def _ask_index(self, prompt: str, upper: int) -> int:
        while True:
            raw = input(f"{prompt} [0-{upper - 1}]: ").strip()
            try:
                index = int(raw)
            except ValueError:
                print("Index must be an integer.")
                continue
            if index < 0 or index >= upper:
                print("Index out of range.")
                continue
            return index

    def _ask_opening_peek_indices(self, upper: int) -> tuple[int, ...]:
        required = min(2, upper)
        while True:
            raw = input(
                f"Choose {required} distinct card indices separated by spaces [0-{upper - 1}]: "
            ).strip()
            parts = raw.replace(",", " ").split()
            try:
                indices = tuple(int(part) for part in parts)
            except ValueError:
                print("Indices must be integers.")
                continue
            if len(indices) != required:
                print(f"You must choose exactly {required} indices.")
                continue
            if len(set(indices)) != len(indices):
                print("Indices must be distinct.")
                continue
            if any(index < 0 or index >= upper for index in indices):
                print("Index out of range.")
                continue
            return indices

    def _print_results(self, results: list[ActionResult | ReactionResult]) -> None:
        print("")
        for result in results:
            if isinstance(result, ActionResult):
                fragments = [f"Action: {result.action}", f"Actor: P{result.actor_id}"]
                if result.card is not None:
                    fragments.append(f"Card: {self._format_card(result.card)}")
                if result.peeked_indices is not None:
                    fragments.append(f"Indices: {list(result.peeked_indices)}")
                if result.power_name is not None:
                    fragments.append(f"Power: {result.power_name}")
                if result.discarded_rank is not None:
                    fragments.append(f"Discard rank: {result.discarded_rank}")
                if result.target_player_id is not None:
                    fragments.append(f"Target: P{result.target_player_id}")
                if result.target_card_index is not None:
                    fragments.append(f"Target idx: {result.target_card_index}")
                if result.reaction_opened:
                    fragments.append("Reaction opened")
                if result.reaction_closed:
                    fragments.append("Reaction closed")
                if result.pending_power_created:
                    fragments.append("Pending power created; discard event is now contested")
                if result.pending_power_resolved:
                    fragments.append("Pending power resolved and won priority")
                if result.pending_power_cancelled:
                    fragments.append("Pending power cancelled by another winning action")
                if result.phase_before is not None and result.phase_after is not None:
                    fragments.append(f"Phase: {result.phase_before}->{result.phase_after}")
                if result.next_player_id is not None:
                    fragments.append(f"Next: P{result.next_player_id}")
                if result.instant_winner is not None:
                    fragments.append(f"Instant winner: P{result.instant_winner}")
                print(" | ".join(fragments))
                continue

            fragments = [f"Reaction success: {result.success}"]
            if result.actor_id is not None:
                fragments.append(f"Actor: P{result.actor_id}")
            if result.reaction_type is not None:
                fragments.append(f"Type: {result.reaction_type}")
            if result.revealed_card is not None:
                fragments.append(f"Revealed: {self._format_card(result.revealed_card)}")
            if result.penalty_card is not None:
                fragments.append(f"Penalty card: {self._format_card(result.penalty_card)}")
            if result.target_player_id is not None:
                fragments.append(f"Target: P{result.target_player_id}")
            if result.target_card_index is not None:
                fragments.append(f"Target idx: {result.target_card_index}")
            if result.penalty_applied:
                fragments.append("Penalty applied")
            if result.wrong_guess_count is not None:
                fragments.append(f"Wrong guesses: {result.wrong_guess_count}")
            if result.wrong_guess_limit_reached:
                fragments.append("Guess limit reached for this player")
            if result.reaction_continues:
                fragments.append("Reaction window remains open")
            if result.cancelled_pending_power:
                fragments.append("Pending power cancelled by this reaction")
            if result.phase_before is not None and result.phase_after is not None:
                fragments.append(f"Phase: {result.phase_before}->{result.phase_after}")
            if result.next_player_id is not None:
                fragments.append(f"Next: P{result.next_player_id}")
            if result.instant_win_player is not None:
                fragments.append(f"Instant winner: P{result.instant_win_player}")
            print(" | ".join(fragments))
        print("")

    def _print_game_over(self) -> None:
        print("=" * 72)
        print("Game over")
        state = self.engine.state
        scores = self.engine.get_scores()
        for player in state.players:
            print(
                f"P{player.id} {player.name} | Hand: {self._format_hand(player, True)} | "
                f"Score: {scores[player.id]}"
            )
        print(f"Winner: {self.engine.get_winner()}")

    def _format_hand(self, player: Player, visible: bool) -> str:
        if visible:
            return "[" + ", ".join(
                f"{idx}:{self._format_card(card)}" for idx, card in enumerate(player.hand)
            ) + "]"
        rendered = []
        for idx, _ in enumerate(player.hand):
            known_card = player.memory.get((player.id, idx))
            rendered.append(
                f"{idx}:{self._format_card(known_card)}" if known_card is not None else f"{idx}:??"
            )
        return "[" + ", ".join(rendered) + "]"

    def _can_show_score(self, player: Player, reveal_full_hand: bool) -> bool:
        if reveal_full_hand:
            return True
        return all((player.id, idx) in player.memory for idx in range(len(player.hand)))

    def _format_card(self, card: object) -> str:
        if card is None:
            return "-"
        suit = getattr(card, "suit").value
        rank = getattr(card, "rank").value
        return f"{rank}{SUIT_MAP.get(suit, suit)}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play Kaboom in the terminal.")
    parser.add_argument("--players", type=int, default=4, help="Number of players.")
    parser.add_argument("--hand-size", type=int, default=4, help="Cards per player.")
    parser.add_argument(
        "--reveal-all",
        action="store_true",
        help="Show every player's hand for debugging.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    app = KaboomCliApp(
        CliConfig(
            num_players=args.players,
            hand_size=args.hand_size,
            reveal_all=args.reveal_all,
        )
    )
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
