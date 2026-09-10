"""Test the UCI protocol handler (engine.uci.UCIHandler)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from engine.uci import _MAX_DEPTH, UCIHandler, main

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handler() -> UCIHandler:
    """Return a fresh UCIHandler with no engine instantiated yet."""
    return UCIHandler()


def _dispatch_and_capture(handler: UCIHandler, *lines: str) -> list[str]:
    """Send one or more UCI lines and return all emitted output lines."""
    captured: list[str] = []

    with patch("engine.uci._out", side_effect=captured.append):
        for line in lines:
            handler._dispatch(line)
    return captured


# ---------------------------------------------------------------------------
# Core dispatch and loop
# ---------------------------------------------------------------------------


def test_dispatch_empty_line() -> None:
    """Ignore empty lines."""
    h = _handler()
    h._dispatch("")
    h._dispatch("   ")


def test_dispatch_quit() -> None:
    """Call sys.exit on quit command."""
    h = _handler()
    with patch("sys.exit") as mock_exit:
        h._dispatch("quit")
        mock_exit.assert_called_once_with(0)


def test_main_loop() -> None:
    """Test the main loop handling normal input and EOF."""
    inputs = ["isready\n", "uci\n", ""]
    with (
        patch("sys.stdin.readline", side_effect=inputs),
        patch("engine.uci._out") as mock_out,
    ):
        main()
        assert mock_out.call_count >= 2


def test_main_loop_keyboard_interrupt() -> None:
    """Test main loop exits gracefully on KeyboardInterrupt."""
    with patch("sys.stdin.readline", side_effect=KeyboardInterrupt):
        main()


def test_main_loop_value_error() -> None:
    """Test main loop catches ValueError and continues."""
    inputs = ["bad_command\n", ""]
    with (
        patch("sys.stdin.readline", side_effect=inputs),
        patch.object(UCIHandler, "_dispatch", side_effect=[ValueError("test"), None]),
        patch("logging.exception") as mock_log,
    ):
        main()
        mock_log.assert_called_once()


# ---------------------------------------------------------------------------
# uci & isready
# ---------------------------------------------------------------------------


def test_uci_sends_id_and_uciok() -> None:
    """Emit id name, id author, at least one option, and 'uciok' on 'uci' command."""
    output = _dispatch_and_capture(_handler(), "uci")
    assert any(line.startswith("id name ") for line in output)
    assert any(line.startswith("id author ") for line in output)
    assert any(line.startswith("option ") for line in output)
    assert output[-1] == "uciok"


def test_isready_sends_readyok() -> None:
    """Emit 'readyok' on 'isready' command."""
    output = _dispatch_and_capture(_handler(), "isready")
    assert output == ["readyok"]


def test_ucinewgame() -> None:
    """Reset the searcher on 'ucinewgame' command."""
    h = _handler()
    h.runtime.searcher = MagicMock()
    h._dispatch("ucinewgame")
    h.runtime.searcher.reset.assert_called_once()


def test_ponderhit() -> None:
    """Handle 'ponderhit' as a no-op."""
    h = _handler()
    h._dispatch("ponderhit")


def test_stop() -> None:
    """Handle 'stop' as a no-op."""
    h = _handler()
    h._dispatch("stop")


# ---------------------------------------------------------------------------
# position command
# ---------------------------------------------------------------------------


def test_position_empty() -> None:
    """Do nothing when 'position' has no args."""
    h = _handler()
    h.runtime.board = MagicMock()
    h._dispatch("position")
    h.runtime.board.from_fen.assert_not_called()


def test_position_startpos() -> None:
    """Set board to initial state on 'position startpos'."""
    h = _handler()
    h.runtime.board = MagicMock()
    _dispatch_and_capture(h, "position startpos")
    h.runtime.board.from_fen.assert_called()


def test_position_fen() -> None:
    """Set board to specific FEN on 'position fen ...'."""
    h = _handler()
    h.runtime.board = MagicMock()
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    _dispatch_and_capture(h, f"position fen {fen}")
    h.runtime.board.from_fen.assert_called_with(fen)


def test_position_fen_with_moves() -> None:
    """Set board to FEN and apply moves on 'position fen ... moves ...'."""
    h = _handler()
    h.runtime.board = MagicMock()
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    _dispatch_and_capture(h, f"position fen {fen} moves e7e5")
    h.runtime.board.from_fen.assert_called_with(fen)
    h.runtime.board.push_uci.assert_called_with("e7e5")


def test_position_fen_with_moves_bad_index() -> None:
    """Handle 'position fen moves' without actual fen string gracefully."""
    h = _handler()
    h.runtime.board = MagicMock()
    _dispatch_and_capture(h, "position fen moves e2e4")
    h.runtime.board.from_fen.assert_called_with("")
    h.runtime.board.push_uci.assert_called_with("e2e4")


def test_position_moves() -> None:
    """Apply moves on 'position startpos moves ...'."""
    h = _handler()
    h.runtime.board = MagicMock()
    _dispatch_and_capture(h, "position startpos moves e2e4 e7e5")
    h.runtime.board.from_fen.assert_called_once()
    assert h.runtime.board.push_uci.call_count == 2
    h.runtime.board.push_uci.assert_any_call("e2e4")
    h.runtime.board.push_uci.assert_any_call("e7e5")


# ---------------------------------------------------------------------------
# go command
# ---------------------------------------------------------------------------


def test_go_no_args() -> None:
    """Use default depth on 'go' without args."""
    h = _handler()
    h.runtime.searcher = MagicMock()
    h.runtime.searcher.search.return_value = (0.0, "e2e4")
    _dispatch_and_capture(h, "go")
    h.runtime.searcher.search.assert_called_with(4)


def test_go_depth() -> None:
    """Call search with depth X on 'go depth X'."""
    h = _handler()
    h.runtime.searcher = MagicMock()
    h.runtime.searcher.search.return_value = (0.0, "e2e4")
    _dispatch_and_capture(h, "go depth 5")
    h.runtime.searcher.search.assert_called_with(5)


def test_go_depth_invalid() -> None:
    """Fall back to default depth gracefully on 'go depth invalid'."""
    h = _handler()
    h.runtime.searcher = MagicMock()
    h.runtime.searcher.search.return_value = (0.0, "e2e4")
    _dispatch_and_capture(h, "go depth abc")
    h.runtime.searcher.search.assert_called_with(4)


def test_go_depth_missing_value() -> None:
    """Fall back to default depth gracefully on 'go depth' without a value."""
    h = _handler()
    h.runtime.searcher = MagicMock()
    h.runtime.searcher.search.return_value = (0.0, "e2e4")
    _dispatch_and_capture(h, "go depth")
    h.runtime.searcher.search.assert_called_with(4)


def test_go_no_best_move() -> None:
    """Output bestmove 0000 if no move found."""
    h = _handler()
    h.runtime.searcher = MagicMock()
    h.runtime.searcher.search.return_value = (0.0, None)
    output = _dispatch_and_capture(h, "go depth 1")
    assert output == ["bestmove 0000"]


# ---------------------------------------------------------------------------
# setoption command
# ---------------------------------------------------------------------------


def test_setoption_no_args() -> None:
    """Do nothing when 'setoption' has no args."""
    h = _handler()
    h._dispatch("setoption")


def test_setoption_no_name() -> None:
    """Do nothing when 'setoption' lacks the 'name' keyword."""
    h = _handler()
    h._dispatch("setoption value 64")


def test_setoption_hash() -> None:
    """Update config when setting Hash option."""
    h = _handler()
    _dispatch_and_capture(h, "setoption name Hash value 64")
    assert h.config.search.tt_size_mb == 64


def test_setoption_hash_invalid_value() -> None:
    """Handle invalid Hash option value gracefully without crashing."""
    h = _handler()
    h.config.search.tt_size_mb = 16
    _dispatch_and_capture(h, "setoption name Hash value abc")
    assert h.config.search.tt_size_mb == 16


def test_setoption_hash_no_value() -> None:
    """Assume default behavior when setting Hash without 'value' keyword."""
    h = _handler()
    h.config.search.tt_size_mb = 16
    _dispatch_and_capture(h, "setoption name Hash")
    assert h.config.search.tt_size_mb == 16


def test_setoption_rebuilds_effective_runtime() -> None:
    """A valid option change is installed into a new compiled search plan."""
    h = _handler()
    previous_searcher = h.runtime.searcher

    output = _dispatch_and_capture(h, "setoption name use_pvs value false")

    assert output == []
    assert h.runtime.searcher is not previous_searcher
    assert h.runtime.searcher.engine.effective_features["use_pvs"] is False


def test_invalid_setoption_preserves_active_runtime() -> None:
    """An invalid partial reconfiguration never changes requested or applied state."""
    h = _handler()
    previous_runtime = h.runtime

    output = _dispatch_and_capture(h, "setoption name use_alpha_beta value false")

    assert output
    assert output[0].startswith("info string rejected option")
    assert h.config.search.use_alpha_beta is True
    assert h.runtime is previous_runtime


def test_go_passes_allocated_time_as_per_search_limit() -> None:
    """UCI clock allocation does not mutate persistent optimization config."""
    h = _handler()
    h.runtime.searcher = MagicMock()
    h.runtime.searcher.search.return_value = (0.0, "e2e4")
    original = h.config.search.max_time

    _dispatch_and_capture(h, "go movetime 50")

    h.runtime.searcher.search.assert_called_once_with(4, max_time=0.05)
    assert h.config.search.max_time == original
