#include "static_exchange.hpp"

#include <algorithm>
#include <limits>

namespace search {

namespace {

[[nodiscard]] inline int piece_value(PieceType type) noexcept {
  return StaticExchangeEvaluator::PIECE_VALUES_CP[static_cast<int>(type)];
}

} // namespace

int StaticExchangeEvaluator::evaluate(Board &board, const Move &move) const {
  if (!board.is_capture(move)) {
    return 0;
  }

  Board simulation = board;
  int gains[32];
  int depth = 0;

  int gain = 0;
  auto victim = simulation.piece_at(move.to);
  if (!victim && simulation.is_en_passant(move)) {
    gain = PIECE_VALUES_CP[0];
  } else if (victim) {
    gain = piece_value(victim->type);
  }
  gains[0] = gain;

  simulation.push(move);
  const uint8_t target = move.to;

  while (depth < 31) {
    Move best_attacker{};
    bool found = false;
    int lowest_value = std::numeric_limits<int>::max();

    for (const auto &reply : simulation.generate_legal_moves()) {
      if (reply.to != target || !simulation.is_capture(reply)) {
        continue;
      }
      auto attacker = simulation.piece_at(reply.from);
      const int value = attacker ? piece_value(attacker->type) : 0;
      if (value < lowest_value) {
        lowest_value = value;
        best_attacker = reply;
        found = true;
      }
    }

    if (!found) {
      break;
    }

    auto captured = simulation.piece_at(target);
    const int captured_value = captured ? piece_value(captured->type) : 0;
    ++depth;
    gains[depth] = captured_value - gains[depth - 1];
    simulation.push(best_attacker);
  }

  while (depth > 0) {
    gains[depth - 1] = -std::max(-gains[depth - 1], gains[depth]);
    --depth;
  }
  return gains[0];
}

} // namespace search
