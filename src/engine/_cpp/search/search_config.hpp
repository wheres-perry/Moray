#pragma once
// ---------------------------------------------------------------------------
// search_config.hpp — Plain-old-data mirror of Python SearchConfig
//
// Constructed from a py::object via from_py_config() in bindings.cpp and
// consumed by TranspositionTable, MoveSorter, and Minimax.  Keeping this a
// POD means each consumer can copy it cheaply and avoid reaching back into
// Python mid-search.
// ---------------------------------------------------------------------------

#include <cstdint>
#include <limits>
#include <optional>

namespace search {

struct CppSearchConfig {
  // General
  std::optional<double> max_time;
  std::optional<int> max_depth;

  // Move ordering
  bool use_move_ordering = true;
  bool use_mvv_lva = true;
  bool use_history_heuristic = true;
  int history_max_score = 16384;
  bool use_countermove_heuristic = true;
  bool use_see_ordering = true;
  int see_capture_threshold = 0;
  bool use_killer_moves = true;
  int killer_slots_per_ply = 2;
  bool use_hash_move_ordering = true;

  // Algorithms
  bool use_alpha_beta = true;
  bool use_pvs = true;
  bool use_quiescence_search = true;
  int qs_max_depth = 16;
  bool use_iid = true;
  int iid_min_depth = 5;
  int iid_depth_reduction = 2;

  // Pruning
  bool use_null_move_pruning = true;
  int nmp_reduction_r = 3;
  int nmp_min_depth = 3;
  bool use_lmr = true;
  int lmr_min_depth = 3;
  int lmr_min_move_number = 4;
  bool use_futility_pruning = true;
  int futility_margin_standard = 300;
  bool use_extended_futility_pruning = true;
  int futility_margin_extended = 500;
  bool use_reverse_futility_pruning = true;
  int rfp_margin_multiplier = 120;
  int rfp_max_depth = 8;
  bool use_delta_pruning = true;
  int delta_margin = 200;
  bool use_see_pruning_in_qs = true;

  // State evaluation & hashing
  bool use_aspiration_windows = true;
  int aspiration_window_margin = 50;
  bool use_check_extensions = true;
  int max_check_extensions = 16;
  bool use_transposition_table = true;
  int tt_size_mb = 64;
  bool use_tt_aging = true;
};

} // namespace search
