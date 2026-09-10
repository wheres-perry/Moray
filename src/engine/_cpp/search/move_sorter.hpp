#pragma once
// ---------------------------------------------------------------------------
// move_sorter.hpp — fast move ordering heuristics
//
// Phase-2 rewrite: dense flat arrays, branch hints, constexpr where
// possible.  The Python-visible dict views (killer_moves, history_table,
// countermove_table) are reconstructed on demand by the bindings so the
// hot path never pays for them.
// ---------------------------------------------------------------------------

#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <vector>

#include "../board/board.hpp"
#include "search_config.hpp"
#include "search_plan.hpp"
#include "static_exchange.hpp"

#if defined(__GNUC__) || defined(__clang__)
#define MS_LIKELY(x) __builtin_expect(!!(x), 1)
#define MS_UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define MS_LIKELY(x) (x)
#define MS_UNLIKELY(x) (x)
#endif

namespace search {

class MoveSorter {
public:
  static constexpr int HASH_MOVE_SCORE = 100'000'000;
  static constexpr int TACTICAL_BASE = 10'000'000;
  static constexpr int KILLER_BASE = 1'000'000;
  static constexpr int COUNTERMOVE_SCORE = 850'000;

  static constexpr int MAX_PLY = 256;
  static constexpr int MAX_KILLER_SLOTS = 8;

  // Centipawn piece values indexed by PieceType.  King is kept at 20000 so
  // MVV-LVA math matches the Python reference exactly.
  static constexpr std::array<int, 6> PIECE_VALUES_CP = {
      100,  // PAWN
      320,  // KNIGHT
      330,  // BISHOP
      500,  // ROOK
      900,  // QUEEN
      20000 // KING
  };

  explicit MoveSorter(const CppSearchConfig &config) noexcept;

  void reset(bool clear_history, bool clear_killers) noexcept;

  [[nodiscard]] std::vector<Move>
  sort_moves(Board &board, const std::vector<Move> &moves, int ply,
             std::optional<Move> hash_move,
             std::optional<Move> previous_move) const;

  [[nodiscard]] std::vector<Move>
  sort_tactical(Board &board, const std::vector<Move> &moves) const;

  [[nodiscard]] int
  score_move(Board &board, const Move &move, int ply,
             std::optional<Move> hash_move,
             std::optional<Move> previous_move) const noexcept;

  [[nodiscard]] int score_tactical_move(Board &board,
                                        const Move &move) const noexcept;

  [[nodiscard]] int mvv_lva(const Board &board,
                            const Move &move) const noexcept;

  [[nodiscard]] int see(Board &board, const Move &move) const;

  void set_telemetry(TelemetrySet *telemetry) noexcept {
    telemetry_ = telemetry;
  }

  void on_beta_cutoff(const Move &move, int ply, int depth,
                      std::optional<Move> previous_move,
                      bool is_tactical) noexcept;

  [[nodiscard]] double history_saturation() const noexcept;

  // Fast path used by the minimax beta-cutoff stats bookkeeping: returns
  // true if the move is currently a killer at the given ply.
  [[nodiscard]] inline bool is_killer(int ply,
                                      const Move &move) const noexcept {
    if (ply < 0 || ply >= MAX_PLY)
      return false;
    const int count = killer_counts_[ply];
    for (int i = 0; i < count; ++i) {
      if (killer_moves_[ply][i] == move) {
        return true;
      }
    }
    return false;
  }

  // Read-only accessors used by the Python binding layer to rebuild the
  // dict-like views exposed for tests.
  [[nodiscard]] const std::array<std::array<Move, MAX_KILLER_SLOTS>, MAX_PLY> &
  killers() const noexcept {
    return killer_moves_;
  }
  [[nodiscard]] const std::array<int, MAX_PLY> &killer_counts() const noexcept {
    return killer_counts_;
  }

  // History table indexed as [from][to][promotion].
  [[nodiscard]] inline int history_get(uint8_t from, uint8_t to,
                                       uint8_t promotion) const noexcept {
    if (MS_UNLIKELY(promotion >= PROMO_SLOTS))
      return 0;
    return history_table_[history_index(from, to, promotion)];
  }
  void history_for_each(
      const std::function<void(uint8_t, uint8_t, uint8_t, int)> &fn) const;

  // Countermove table: keyed by previous move's (from, to, promotion).
  [[nodiscard]] inline std::optional<Move>
  countermove_get(uint8_t from, uint8_t to, uint8_t promotion) const noexcept {
    if (MS_UNLIKELY(promotion >= PROMO_SLOTS))
      return std::nullopt;
    const int idx = history_index(from, to, promotion);
    if (!countermove_present_[idx]) {
      return std::nullopt;
    }
    return countermove_table_[idx];
  }
  void countermove_for_each(const std::function<void(uint8_t, uint8_t, uint8_t,
                                                     const Move &)> &fn) const;

private:
  // Promotion dimension sized at 5 to cover Python's raw promotion byte
  // (0 for no promotion, 1..4 for N/B/R/Q).
  static constexpr int PROMO_SLOTS = 5;
  static constexpr int HISTORY_TABLE_SIZE = 64 * 64 * PROMO_SLOTS;

  [[nodiscard]] static constexpr int history_index(uint8_t from, uint8_t to,
                                                   uint8_t promotion) noexcept {
    return (static_cast<int>(from) * 64 + static_cast<int>(to)) * PROMO_SLOTS +
           static_cast<int>(promotion);
  }

  static constexpr bool is_promotion(const Move &move) noexcept {
    return move.promotion != 0;
  }

  inline FeatureTelemetry *feature_stats(SearchFeature feature) const noexcept {
    if (telemetry_ == nullptr) {
      return nullptr;
    }
    return &(*telemetry_)[feature_index(feature)];
  }

  const CppSearchConfig config_;
  StaticExchangeEvaluator see_service_;
  mutable TelemetrySet *telemetry_ = nullptr;

  // Dense killer storage.  killer_counts_[ply] tracks the occupied slots.
  alignas(64)
      std::array<std::array<Move, MAX_KILLER_SLOTS>, MAX_PLY> killer_moves_{};
  alignas(64) std::array<int, MAX_PLY> killer_counts_{};

  // Dense history/countermove tables keyed by (from, to, promotion).  The
  // extra promotion dimension matches the Python dict key exactly.
  alignas(64) std::array<int, HISTORY_TABLE_SIZE> history_table_{};
  alignas(64) std::array<Move, HISTORY_TABLE_SIZE> countermove_table_{};
  alignas(64) std::array<bool, HISTORY_TABLE_SIZE> history_present_{};
  alignas(64) std::array<bool, HISTORY_TABLE_SIZE> countermove_present_{};
};

} // namespace search
