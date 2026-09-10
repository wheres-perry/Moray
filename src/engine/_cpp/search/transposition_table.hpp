#pragma once
// ---------------------------------------------------------------------------
// transposition_table.hpp — high-performance contiguous TT
//
// Storage model:
//   • Power-of-two capacity ⇒ mask-based indexing (no modulo).
//   • Single-entry buckets with a depth/age replacement policy (no eviction
//     scan, no rehashing, no allocations on the hot path).
//   • Entries are trivially-copyable PODs packed into an aligned vector.
//
// Layout is tuned for cache locality: probe() touches exactly one 32-byte
// slot, which is the critical-path cost during alpha-beta search.
// ---------------------------------------------------------------------------

#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <optional>

#include "../board/board.hpp"
#include "search_config.hpp"

#if defined(__GNUC__) || defined(__clang__)
#define TT_LIKELY(x) __builtin_expect(!!(x), 1)
#define TT_UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define TT_LIKELY(x) (x)
#define TT_UNLIKELY(x) (x)
#endif

namespace search {

// EMPTY = 0 so zero-initialized (calloc-backed) storage starts out marked
// as empty without a per-entry construction pass.
enum class TTBound : uint8_t {
  EMPTY = 0,
  EXACT = 1,
  LOWER = 2,
  UPPER = 3,
};

// Packed TT entry.  We keep it ≤ 32 B so a cache line holds two entries.
// The ``score`` is still stored as double to preserve Python parity for
// corner cases like math.inf sentinels; an int16 specialization is a good
// follow-up once the Python wrapper no longer round-trips infinities.
struct TTEntry {
  uint64_t key; // full Zobrist key (collision detection).
  double score;
  Move best_move;
  int16_t depth;
  uint16_t age;
  TTBound bound;
  bool has_best_move;

  [[nodiscard]] constexpr bool is_occupied() const noexcept {
    return bound != TTBound::EMPTY;
  }
};

static_assert(sizeof(TTEntry) <= 32, "TTEntry should fit in 32 bytes");

class TranspositionTable {
public:
  static constexpr int ESTIMATED_ENTRY_SIZE_BYTES =
      static_cast<int>(sizeof(TTEntry));

  explicit TranspositionTable(const CppSearchConfig &config);

  inline void increment_age() noexcept {
    if (config_.use_tt_aging) {
      ++current_age_;
    }
  }

  inline void clear() noexcept {
    // Single memset pass — zero bytes match TTBound::EMPTY, so every slot
    // is marked free without touching enum fields individually.
    if (table_ != nullptr && capacity_ > 0) {
      std::memset(table_.get(), 0, capacity_ * sizeof(TTEntry));
    }
    size_ = 0;
  }

  [[nodiscard]] inline size_t size() const noexcept { return size_; }

  [[nodiscard]] inline int max_entries() const noexcept { return max_entries_; }

  void set_max_entries(int value) noexcept;

  [[nodiscard]] inline int current_age() const noexcept { return current_age_; }

  // Pointer to the stored entry, or nullptr on miss.  Updates the entry's
  // age on hit when aging is enabled.
  [[nodiscard]] inline TTEntry *probe(uint64_t key) noexcept {
    TTEntry &slot = table_[bucket_index(key)];
    if (TT_LIKELY(slot.is_occupied() && slot.key == key)) {
      if (config_.use_tt_aging) {
        slot.age = static_cast<uint16_t>(current_age_);
      }
      return &slot;
    }
    return nullptr;
  }

  // Non-owning iteration over the backing array (used by bindings/tests).
  [[nodiscard]] inline const TTEntry *data() const noexcept {
    return table_.get();
  }
  [[nodiscard]] inline size_t capacity() const noexcept { return capacity_; }

  [[nodiscard]] inline std::optional<double>
  try_get_score(const TTEntry &entry, int depth, double alpha,
                double beta) const noexcept {
    if (TT_UNLIKELY(entry.depth < depth)) {
      return std::nullopt;
    }
    switch (entry.bound) {
    case TTBound::EXACT:
      return entry.score;
    case TTBound::LOWER:
      if (entry.score >= beta) {
        return entry.score;
      }
      break;
    case TTBound::UPPER:
      if (entry.score <= alpha) {
        return entry.score;
      }
      break;
    case TTBound::EMPTY:
      break;
    }
    return std::nullopt;
  }

  void store(uint64_t key, int depth, double score,
             std::optional<Move> best_move, TTBound bound) noexcept;

private:
  [[nodiscard]] inline size_t bucket_index(uint64_t key) const noexcept {
    return static_cast<size_t>(key) & mask_;
  }

  struct FreeDeleter {
    void operator()(TTEntry *p) const noexcept { std::free(p); }
  };

  const CppSearchConfig config_;
  std::unique_ptr<TTEntry[], FreeDeleter> table_;
  size_t capacity_ = 0;
  size_t mask_ = 0;
  int max_entries_ = 0;
  size_t size_ = 0;
  int current_age_ = 0;
};

} // namespace search
