#pragma once

#include <array>

#include "../board/board.hpp"

namespace search {

// Shared SEE service. It is deliberately independent of move ordering so
// quiescence pruning and future features can request it directly.
class StaticExchangeEvaluator {
public:
  static constexpr std::array<int, 6> PIECE_VALUES_CP = {100, 320, 330,
                                                         500, 900, 20000};

  [[nodiscard]] int evaluate(Board &board, const Move &move) const;
};

} // namespace search
