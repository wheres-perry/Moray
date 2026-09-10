#pragma once
// Immutable runtime plan compiled from CppSearchConfig at the engine boundary.
// Search code consumes these orthogonal policies and never reads raw use_*
// flags.

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string_view>

#include "search_config.hpp"

namespace search {

[[nodiscard]] inline bool is_finite_number(double value) noexcept {
  constexpr uint64_t EXPONENT_MASK = 0x7ff0'0000'0000'0000ULL;
  return (std::bit_cast<uint64_t>(value) & EXPONENT_MASK) != EXPONENT_MASK;
}

enum class SearchFeature : uint8_t {
  MOVE_ORDERING,
  MVV_LVA,
  HISTORY_HEURISTIC,
  COUNTERMOVE_HEURISTIC,
  SEE_ORDERING,
  KILLER_MOVES,
  HASH_MOVE_ORDERING,
  ALPHA_BETA,
  PVS,
  QUIESCENCE_SEARCH,
  IID,
  NULL_MOVE_PRUNING,
  LMR,
  FUTILITY_PRUNING,
  EXTENDED_FUTILITY_PRUNING,
  REVERSE_FUTILITY_PRUNING,
  DELTA_PRUNING,
  SEE_PRUNING_IN_QS,
  ASPIRATION_WINDOWS,
  CHECK_EXTENSIONS,
  TRANSPOSITION_TABLE,
  TT_AGING,
  COUNT,
};

inline constexpr std::array<std::string_view,
                            static_cast<size_t>(SearchFeature::COUNT)>
    SEARCH_FEATURE_NAMES = {
        "use_move_ordering",
        "use_mvv_lva",
        "use_history_heuristic",
        "use_countermove_heuristic",
        "use_see_ordering",
        "use_killer_moves",
        "use_hash_move_ordering",
        "use_alpha_beta",
        "use_pvs",
        "use_quiescence_search",
        "use_iid",
        "use_null_move_pruning",
        "use_lmr",
        "use_futility_pruning",
        "use_extended_futility_pruning",
        "use_reverse_futility_pruning",
        "use_delta_pruning",
        "use_see_pruning_in_qs",
        "use_aspiration_windows",
        "use_check_extensions",
        "use_transposition_table",
        "use_tt_aging",
};

struct FeatureTelemetry {
  uint64_t considered = 0;
  uint64_t eligible = 0;
  uint64_t applied = 0;
  uint64_t cutoffs = 0;
  uint64_t researches = 0;
};

using TelemetrySet =
    std::array<FeatureTelemetry, static_cast<size_t>(SearchFeature::COUNT)>;

[[nodiscard]] inline constexpr size_t feature_index(SearchFeature feature) {
  return static_cast<size_t>(feature);
}

struct SearchPlan {
  struct GeneralPolicy {
    std::optional<double> max_time;
    std::optional<int> max_depth;
  } general;

  struct OrderingPolicy {
    bool enabled;
    bool mvv_lva;
    bool history;
    int history_max_score;
    bool countermove;
    bool see;
    int see_capture_threshold;
    bool killers;
    int killer_slots_per_ply;
    bool hash_move;
  } ordering;

  struct AlgorithmPolicy {
    bool alpha_beta;
    bool pvs;
    bool quiescence;
    int qs_max_depth;
    bool iid;
    int iid_min_depth;
    int iid_depth_reduction;
  } algorithm;

  struct PruningPolicy {
    bool null_move;
    int nmp_reduction;
    int nmp_min_depth;
    bool lmr;
    int lmr_min_depth;
    int lmr_min_move_number;
    bool futility;
    int futility_margin;
    bool extended_futility;
    int extended_futility_margin;
    bool reverse_futility;
    int rfp_margin_multiplier;
    int rfp_max_depth;
    bool delta;
    int delta_margin;
    bool see_in_qs;
  } pruning;

  struct StatePolicy {
    bool aspiration;
    int aspiration_margin;
    bool check_extensions;
    int max_check_extensions;
    bool transposition_table;
    int tt_size_mb;
    bool tt_aging;
  } state;

  struct RequiredServices {
    bool tt;
    bool zobrist;
    bool move_sorter;
    bool see;
  } services;

  std::array<bool, static_cast<size_t>(SearchFeature::COUNT)> features{};

  [[nodiscard]] bool enabled(SearchFeature feature) const noexcept {
    return features[feature_index(feature)];
  }

  [[nodiscard]] static SearchPlan compile(const CppSearchConfig &cfg) {
    validate(cfg);

    SearchPlan plan{
        .general = {.max_time = cfg.max_time, .max_depth = cfg.max_depth},
        .ordering = {.enabled = cfg.use_move_ordering,
                     .mvv_lva = cfg.use_mvv_lva,
                     .history = cfg.use_history_heuristic,
                     .history_max_score = cfg.history_max_score,
                     .countermove = cfg.use_countermove_heuristic,
                     .see = cfg.use_see_ordering,
                     .see_capture_threshold = cfg.see_capture_threshold,
                     .killers = cfg.use_killer_moves,
                     .killer_slots_per_ply = cfg.killer_slots_per_ply,
                     .hash_move = cfg.use_hash_move_ordering},
        .algorithm = {.alpha_beta = cfg.use_alpha_beta,
                      .pvs = cfg.use_pvs,
                      .quiescence = cfg.use_quiescence_search,
                      .qs_max_depth = cfg.qs_max_depth,
                      .iid = cfg.use_iid,
                      .iid_min_depth = cfg.iid_min_depth,
                      .iid_depth_reduction = cfg.iid_depth_reduction},
        .pruning = {.null_move = cfg.use_null_move_pruning,
                    .nmp_reduction = cfg.nmp_reduction_r,
                    .nmp_min_depth = cfg.nmp_min_depth,
                    .lmr = cfg.use_lmr,
                    .lmr_min_depth = cfg.lmr_min_depth,
                    .lmr_min_move_number = cfg.lmr_min_move_number,
                    .futility = cfg.use_futility_pruning,
                    .futility_margin = cfg.futility_margin_standard,
                    .extended_futility = cfg.use_extended_futility_pruning,
                    .extended_futility_margin = cfg.futility_margin_extended,
                    .reverse_futility = cfg.use_reverse_futility_pruning,
                    .rfp_margin_multiplier = cfg.rfp_margin_multiplier,
                    .rfp_max_depth = cfg.rfp_max_depth,
                    .delta = cfg.use_delta_pruning,
                    .delta_margin = cfg.delta_margin,
                    .see_in_qs = cfg.use_see_pruning_in_qs},
        .state = {.aspiration = cfg.use_aspiration_windows,
                  .aspiration_margin = cfg.aspiration_window_margin,
                  .check_extensions = cfg.use_check_extensions,
                  .max_check_extensions = cfg.max_check_extensions,
                  .transposition_table = cfg.use_transposition_table,
                  .tt_size_mb = cfg.tt_size_mb,
                  .tt_aging = cfg.use_tt_aging},
        .services = {.tt = cfg.use_transposition_table,
                     .zobrist = cfg.use_transposition_table,
                     .move_sorter = cfg.use_move_ordering,
                     .see = cfg.use_see_ordering || cfg.use_see_pruning_in_qs},
    };

    plan.features = {
        cfg.use_move_ordering,
        cfg.use_mvv_lva,
        cfg.use_history_heuristic,
        cfg.use_countermove_heuristic,
        cfg.use_see_ordering,
        cfg.use_killer_moves,
        cfg.use_hash_move_ordering,
        cfg.use_alpha_beta,
        cfg.use_pvs,
        cfg.use_quiescence_search,
        cfg.use_iid,
        cfg.use_null_move_pruning,
        cfg.use_lmr,
        cfg.use_futility_pruning,
        cfg.use_extended_futility_pruning,
        cfg.use_reverse_futility_pruning,
        cfg.use_delta_pruning,
        cfg.use_see_pruning_in_qs,
        cfg.use_aspiration_windows,
        cfg.use_check_extensions,
        cfg.use_transposition_table,
        cfg.use_tt_aging,
    };
    return plan;
  }

private:
  static void require(bool condition, const char *message) {
    if (!condition) {
      throw std::invalid_argument(message);
    }
  }

  static void validate(const CppSearchConfig &cfg) {
    require(!cfg.use_mvv_lva || cfg.use_move_ordering,
            "MVV-LVA requires move ordering");
    require(!cfg.use_see_ordering || cfg.use_move_ordering,
            "SEE ordering requires move ordering");
    require(!cfg.use_history_heuristic ||
                (cfg.use_move_ordering && cfg.use_alpha_beta),
            "History requires move ordering and alpha-beta");
    require(!cfg.use_countermove_heuristic ||
                (cfg.use_move_ordering && cfg.use_alpha_beta),
            "Countermove requires move ordering and alpha-beta");
    require(!cfg.use_killer_moves ||
                (cfg.use_move_ordering && cfg.use_alpha_beta),
            "Killer moves require move ordering and alpha-beta");
    require(!cfg.use_hash_move_ordering ||
                (cfg.use_move_ordering && cfg.use_transposition_table),
            "Hash ordering requires move ordering and TT");
    require(!cfg.use_pvs || cfg.use_alpha_beta, "PVS requires alpha-beta");
    require(!cfg.use_iid || cfg.use_hash_move_ordering,
            "IID requires hash ordering");
    require(!cfg.use_null_move_pruning || cfg.use_alpha_beta,
            "Null-move pruning requires alpha-beta");
    require(!cfg.use_reverse_futility_pruning || cfg.use_alpha_beta,
            "Reverse futility pruning requires alpha-beta");
    require(!cfg.use_delta_pruning || cfg.use_quiescence_search,
            "Delta pruning requires quiescence search");
    require(!cfg.use_see_pruning_in_qs || cfg.use_quiescence_search,
            "QS SEE pruning requires quiescence search");
    require(!cfg.use_aspiration_windows || cfg.use_alpha_beta,
            "Aspiration windows require alpha-beta");
    require(!cfg.use_tt_aging || cfg.use_transposition_table,
            "TT aging requires TT");
    require(!cfg.use_iid || cfg.iid_min_depth > cfg.iid_depth_reduction,
            "IID reduction must be positive and below IID minimum depth");
    require(cfg.killer_slots_per_ply >= 1 && cfg.killer_slots_per_ply <= 8,
            "Killer slots must be between 1 and 8");
    require(cfg.tt_size_mb >= 1 && cfg.tt_size_mb <= 1024,
            "TT size must be between 1 and 1024 MiB");
    require(!cfg.max_time.has_value() || is_finite_number(*cfg.max_time),
            "Search time must be finite and positive");
    require(!cfg.max_time.has_value() || *cfg.max_time > 0.0,
            "Search time must be finite and positive");
    require(!cfg.max_depth.has_value() ||
                (*cfg.max_depth >= 1 && *cfg.max_depth <= 128),
            "Search max depth must be between 1 and 128");
    require(cfg.history_max_score >= 1 && cfg.history_max_score <= 1'000'000,
            "History maximum score is out of range");
    require(cfg.see_capture_threshold >= -1'000'000 &&
                cfg.see_capture_threshold <= 1'000'000,
            "SEE capture threshold is out of range");
    require(cfg.qs_max_depth >= 1 && cfg.qs_max_depth <= 128,
            "Quiescence depth is out of range");
    require(cfg.iid_min_depth >= 2 && cfg.iid_min_depth <= 128,
            "IID minimum depth is out of range");
    require(cfg.iid_depth_reduction >= 1 && cfg.iid_depth_reduction <= 127,
            "IID reduction is out of range");
    require(cfg.nmp_reduction_r >= 1 && cfg.nmp_reduction_r <= 32,
            "NMP reduction is out of range");
    require(cfg.nmp_min_depth >= 1 && cfg.nmp_min_depth <= 128,
            "NMP minimum depth is out of range");
    require(cfg.lmr_min_depth >= 1 && cfg.lmr_min_depth <= 128,
            "LMR minimum depth is out of range");
    require(cfg.lmr_min_move_number >= 1 && cfg.lmr_min_move_number <= 256,
            "LMR minimum move number is out of range");
    require(cfg.futility_margin_standard >= 1 &&
                cfg.futility_margin_standard <= 1'000'000,
            "Futility margin is out of range");
    require(cfg.futility_margin_extended >= 1 &&
                cfg.futility_margin_extended <= 1'000'000,
            "Extended futility margin is out of range");
    require(cfg.rfp_margin_multiplier >= 1 &&
                cfg.rfp_margin_multiplier <= 1'000'000,
            "RFP multiplier is out of range");
    require(cfg.rfp_max_depth >= 1 && cfg.rfp_max_depth <= 128,
            "RFP maximum depth is out of range");
    require(cfg.delta_margin >= 1 && cfg.delta_margin <= 1'000'000,
            "Delta margin is out of range");
    require(cfg.aspiration_window_margin >= 1 &&
                cfg.aspiration_window_margin <= 1'000'000,
            "Aspiration margin is out of range");
    require(cfg.max_check_extensions >= 1 && cfg.max_check_extensions <= 128,
            "Check-extension maximum is out of range");
  }
};

} // namespace search
