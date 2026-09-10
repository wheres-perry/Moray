"""UCI Protocol Handler."""

import contextlib
import logging
import sys
from collections.abc import Callable
from typing import ClassVar

from engine.config import EngineConfig
from engine.config_registry import (
    EVALUATION_FEATURES,
    SEARCH_FEATURES,
    SEARCH_PARAMETERS,
)
from engine.config_solver import ConfigSolverError
from engine.factory import STARTING_FEN, create_engine_runtime

_MAX_DEPTH = 100


def _out(msg: str) -> None:
    """Output to stdout with flush."""
    print(msg, flush=True)


def _parse_option_value(current_value: object, value: str) -> bool | int:
    """Parse a UCI value using the current registered field's scalar type."""
    if type(current_value) is bool:
        normalized = value.lower()
        if normalized not in {"true", "false"}:
            raise ValueError("boolean value must be true or false")
        return normalized == "true"
    if type(current_value) is int:
        try:
            return int(value)
        except ValueError as error:
            raise ValueError("value must be an integer") from error
    raise ValueError("unsupported option type")


class UCIHandler:
    """Handles UCI commands and interacts with the engine."""

    def __init__(self) -> None:
        """Initialize the UCI handler with default configuration and runtime."""
        self.config = EngineConfig()
        self.runtime = create_engine_runtime(self.config)

    def _dispatch(self, line: str) -> None:
        """Route a single UCI command line to the appropriate handler."""
        parts = line.strip().split()
        if not parts:
            return

        command = parts[0]
        args = parts[1:]

        if command == "quit":
            sys.exit(0)

        handler = self._commands.get(command)
        if handler is not None:
            handler(self, args)

    def _ponderhit(self, _args: list[str] | None = None) -> None:
        """Handle ponderhit command.

        This is a no-op as pondering is not implemented.

        Args:
            _args: Command arguments (ignored).

        """

    def _uci(self, _args: list[str] | None = None) -> None:
        """Handle uci identification handshake."""
        _out("id name Moray")
        _out("id author wheres-perry")

        for feature_spec in (*SEARCH_FEATURES, *EVALUATION_FEATURES):
            config_obj = getattr(self.config, feature_spec.scope)
            feature_value = bool(getattr(config_obj, feature_spec.name))
            default = "true" if feature_value else "false"
            _out(f"option name {feature_spec.name} type check default {default}")

        for parameter_spec in SEARCH_PARAMETERS:
            name = parameter_spec.uci_name or parameter_spec.name
            parameter_value = int(getattr(self.config.search, parameter_spec.name))
            _out(
                f"option name {name} type spin default {parameter_value} "
                f"min {parameter_spec.minimum} max {parameter_spec.maximum}"
            )
        _out("uciok")

    def _isready(self, _args: list[str] | None = None) -> None:
        """Handle isready command.

        Signals that the engine is ready to receive commands.

        Args:
            _args: Command arguments (ignored).

        """
        _out("readyok")

    def _ucinewgame(self, _args: list[str] | None = None) -> None:
        """Handle ucinewgame command.

        Resets the search state for a new game.

        Args:
            _args: Command arguments (ignored).

        """
        self.runtime.searcher.reset()

    def _position(self, args: list[str] | None = None) -> None:
        """Handle position command."""
        if not args:
            return

        fen_start = STARTING_FEN
        moves_idx = -1

        if args[0] == "startpos":
            fen_start = STARTING_FEN
            if len(args) > 1 and args[1] == "moves":
                moves_idx = 2
        elif args[0] == "fen":
            if "moves" in args:
                try:
                    kw_idx = args.index("moves")
                    fen_parts = args[1:kw_idx]
                    fen_start = " ".join(fen_parts)
                    moves_idx = kw_idx + 1
                except ValueError:
                    pass
            else:
                fen_parts = args[1:]
                fen_start = " ".join(fen_parts)

        self.runtime.board.from_fen(fen_start)

        if moves_idx != -1 and moves_idx < len(args):
            for move in args[moves_idx:]:
                self.runtime.board.push_uci(move)

    def _go(self, args: list[str] | None = None) -> None:
        """Handle go command with time control parsing."""
        if args is None:
            args = []

        depth = 4
        if "depth" in args:
            with contextlib.suppress(ValueError, IndexError):
                idx = args.index("depth")
                depth = int(args[idx + 1])

        max_time: float | None = None
        # Time control allocation is a per-search limit, not persistent config.
        if "movetime" in args:
            with contextlib.suppress(ValueError, IndexError):
                idx = args.index("movetime")
                mtime_ms = int(args[idx + 1])
                max_time = max(0.01, mtime_ms / 1000.0)
        elif "wtime" in args or "btime" in args:
            side_is_white = "b" not in self.runtime.board.fen().split()[1]
            my_time_key = "wtime" if side_is_white else "btime"
            my_inc_key = "winc" if side_is_white else "binc"

            my_time_ms = 30000
            my_inc_ms = 0

            if my_time_key in args:
                with contextlib.suppress(ValueError, IndexError):
                    idx = args.index(my_time_key)
                    my_time_ms = int(args[idx + 1])

            if my_inc_key in args:
                with contextlib.suppress(ValueError, IndexError):
                    idx = args.index(my_inc_key)
                    my_inc_ms = int(args[idx + 1])

            # Allocate time per move: ~1/20th of remaining time + 80% of increment
            time_sec = (my_time_ms / 20.0 + my_inc_ms * 0.8) / 1000.0
            max_time_sec = max(0.01, min(my_time_ms / 1000.0 * 0.95, time_sec))
            max_time = max_time_sec

        if max_time is None:
            _score, best_move = self.runtime.searcher.search(depth)
        else:
            _score, best_move = self.runtime.searcher.search(depth, max_time=max_time)

        if best_move:
            _out(f"bestmove {best_move}")
        else:
            _out("bestmove 0000")

    def _stop(self, _args: list[str] | None = None) -> None:
        """Handle stop command.

        This is a no-op as search is synchronous.

        Args:
            _args: Command arguments (ignored).

        """

    def _setoption(self, args: list[str] | None = None) -> None:
        """Handle setoption command."""
        if not args:
            return
        try:
            name_idx = args.index("name")
        except ValueError:
            return

        if "value" in args:
            value_idx = args.index("value")
            name_parts = args[name_idx + 1 : value_idx]
            value_parts = args[value_idx + 1 :]
            value = " ".join(value_parts)
        else:
            name_parts = args[name_idx + 1 :]
            value = "true"

        name = " ".join(name_parts)

        if name == "Hash":
            name = "tt_size_mb"

        candidate = EngineConfig.from_dict(self.config.to_dict())
        changed = False
        for config_obj in (candidate.search, candidate.evaluation):
            if hasattr(config_obj, name):
                current_value = getattr(config_obj, name)
                try:
                    parsed = _parse_option_value(current_value, value)
                except ValueError as error:
                    _out(f"info string rejected option {name}: {error}")
                    return
                setattr(config_obj, name, parsed)
                changed = True
                break

        if not changed:
            return

        current_fen = self.runtime.board.fen()
        try:
            runtime = create_engine_runtime(candidate, current_fen)
        except (ConfigSolverError, ValueError, OverflowError, RuntimeError) as error:
            _out(f"info string rejected option {name}: {error}")
            return

        self.config = candidate
        self.runtime = runtime

    _CommandHandler = Callable[["UCIHandler", list[str] | None], None]

    _commands: ClassVar[dict[str, _CommandHandler]] = {
        "uci": _uci,
        "isready": _isready,
        "ucinewgame": _ucinewgame,
        "position": _position,
        "go": _go,
        "stop": _stop,
        "setoption": _setoption,
        "ponderhit": _ponderhit,
    }


def main() -> None:
    """Run the UCI command loop.

    Reads UCI commands from stdin and dispatches them to the handler
    until EOF or keyboard interrupt.
    """
    handler = UCIHandler()
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            handler._dispatch(line)
        except KeyboardInterrupt:
            break
        except (ValueError, OSError, RuntimeError):
            logging.exception("Error processing UCI command")
            continue


if __name__ == "__main__":
    main()
