#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <stdexcept>
#include <string>

#include "../evaluators/evaluators.hpp"
#include "minimax.hpp"
#include "move_sorter.hpp"
#include "search.hpp"
#include "search_config.hpp"
#include "static_exchange.hpp"
#include "transposition_table.hpp"
#include "zobrist.hpp"

namespace py = pybind11;
using namespace search;

namespace {

// Holders retain the applied CppSearchConfig for introspection and give the
// Minimax binding a single place to reach through to the underlying objects.
struct TTHolder {
  CppSearchConfig config;
  TranspositionTable table;
  explicit TTHolder(CppSearchConfig c) : config(std::move(c)), table(config) {}
};

struct MoveSorterHolder {
  CppSearchConfig config;
  MoveSorter sorter;
  explicit MoveSorterHolder(CppSearchConfig c)
      : config(std::move(c)), sorter(config) {}
};

struct MinimaxHolder {
  CppSearchConfig config;
  Minimax minimax;
  // Keep shared references to the Python wrappers of the dependencies so
  // the holder cannot outlive them.
  py::object tt_ref;
  py::object sorter_ref;
  py::object see_ref;
  py::object zobrist_ref;
  py::object evaluator_ref;

  MinimaxHolder(Board &board, evaluators::IEvaluator &evaluator,
                TranspositionTable *tt, MoveSorter *sorter,
                StaticExchangeEvaluator *see, Zobrist *zobrist,
                CppSearchConfig cfg)
      : config(std::move(cfg)),
        minimax(board, evaluator, tt, sorter, see, zobrist, config) {}
};

TTBound bound_from_string(const std::string &bound) {
  if (bound == "exact")
    return TTBound::EXACT;
  if (bound == "lower")
    return TTBound::LOWER;
  if (bound == "upper")
    return TTBound::UPPER;
  throw std::invalid_argument("Invalid TT bound string: " + bound);
}

const char *bound_to_string(TTBound bound) noexcept {
  switch (bound) {
  case TTBound::EXACT:
    return "exact";
  case TTBound::LOWER:
    return "lower";
  case TTBound::UPPER:
    return "upper";
  }
  return "exact";
}

// Build a CppSearchConfig from a Python SearchConfig object via attribute
// lookups.  This is called in constructors and when a test mutates a
// SearchConfig field and re-enters the TT/sorter/search layer.
CppSearchConfig config_from_py(const py::object &py_config) {
  CppSearchConfig cfg;

  auto get_bool = [&](const char *name, bool fallback) {
    if (py::hasattr(py_config, name)) {
      return py_config.attr(name).cast<bool>();
    }
    return fallback;
  };
  auto get_int = [&](const char *name, int fallback) {
    if (py::hasattr(py_config, name)) {
      return py_config.attr(name).cast<int>();
    }
    return fallback;
  };

  // max_time is Optional[float].
  if (py::hasattr(py_config, "max_time")) {
    py::object mt = py_config.attr("max_time");
    if (!mt.is_none()) {
      cfg.max_time = mt.cast<double>();
    }
  }
  if (py::hasattr(py_config, "max_depth")) {
    py::object depth = py_config.attr("max_depth");
    if (!depth.is_none()) {
      cfg.max_depth = depth.cast<int>();
    }
  }

  cfg.use_move_ordering = get_bool("use_move_ordering", cfg.use_move_ordering);
  cfg.use_mvv_lva = get_bool("use_mvv_lva", cfg.use_mvv_lva);
  cfg.use_history_heuristic =
      get_bool("use_history_heuristic", cfg.use_history_heuristic);
  cfg.history_max_score = get_int("history_max_score", cfg.history_max_score);
  cfg.use_countermove_heuristic =
      get_bool("use_countermove_heuristic", cfg.use_countermove_heuristic);
  cfg.use_see_ordering = get_bool("use_see_ordering", cfg.use_see_ordering);
  cfg.see_capture_threshold =
      get_int("see_capture_threshold", cfg.see_capture_threshold);
  cfg.use_killer_moves = get_bool("use_killer_moves", cfg.use_killer_moves);
  cfg.killer_slots_per_ply =
      get_int("killer_slots_per_ply", cfg.killer_slots_per_ply);
  cfg.use_hash_move_ordering =
      get_bool("use_hash_move_ordering", cfg.use_hash_move_ordering);

  cfg.use_alpha_beta = get_bool("use_alpha_beta", cfg.use_alpha_beta);
  cfg.use_pvs = get_bool("use_pvs", cfg.use_pvs);
  cfg.use_quiescence_search =
      get_bool("use_quiescence_search", cfg.use_quiescence_search);
  cfg.qs_max_depth = get_int("qs_max_depth", cfg.qs_max_depth);
  cfg.use_iid = get_bool("use_iid", cfg.use_iid);
  cfg.iid_min_depth = get_int("iid_min_depth", cfg.iid_min_depth);
  cfg.iid_depth_reduction =
      get_int("iid_depth_reduction", cfg.iid_depth_reduction);

  cfg.use_null_move_pruning =
      get_bool("use_null_move_pruning", cfg.use_null_move_pruning);
  cfg.nmp_reduction_r = get_int("nmp_reduction_r", cfg.nmp_reduction_r);
  cfg.nmp_min_depth = get_int("nmp_min_depth", cfg.nmp_min_depth);
  cfg.use_lmr = get_bool("use_lmr", cfg.use_lmr);
  cfg.lmr_min_depth = get_int("lmr_min_depth", cfg.lmr_min_depth);
  cfg.lmr_min_move_number =
      get_int("lmr_min_move_number", cfg.lmr_min_move_number);
  cfg.use_futility_pruning =
      get_bool("use_futility_pruning", cfg.use_futility_pruning);
  cfg.futility_margin_standard =
      get_int("futility_margin_standard", cfg.futility_margin_standard);
  cfg.use_extended_futility_pruning = get_bool(
      "use_extended_futility_pruning", cfg.use_extended_futility_pruning);
  cfg.futility_margin_extended =
      get_int("futility_margin_extended", cfg.futility_margin_extended);
  cfg.use_reverse_futility_pruning = get_bool("use_reverse_futility_pruning",
                                              cfg.use_reverse_futility_pruning);
  cfg.rfp_margin_multiplier =
      get_int("rfp_margin_multiplier", cfg.rfp_margin_multiplier);
  cfg.rfp_max_depth = get_int("rfp_max_depth", cfg.rfp_max_depth);
  cfg.use_delta_pruning = get_bool("use_delta_pruning", cfg.use_delta_pruning);
  cfg.delta_margin = get_int("delta_margin", cfg.delta_margin);
  cfg.use_see_pruning_in_qs =
      get_bool("use_see_pruning_in_qs", cfg.use_see_pruning_in_qs);

  cfg.use_aspiration_windows =
      get_bool("use_aspiration_windows", cfg.use_aspiration_windows);
  cfg.aspiration_window_margin =
      get_int("aspiration_window_margin", cfg.aspiration_window_margin);
  cfg.use_check_extensions =
      get_bool("use_check_extensions", cfg.use_check_extensions);
  cfg.max_check_extensions =
      get_int("max_check_extensions", cfg.max_check_extensions);
  cfg.use_transposition_table =
      get_bool("use_transposition_table", cfg.use_transposition_table);
  cfg.tt_size_mb = get_int("tt_size_mb", cfg.tt_size_mb);
  cfg.use_tt_aging = get_bool("use_tt_aging", cfg.use_tt_aging);

  return cfg;
}

py::dict config_to_dict(const CppSearchConfig &cfg) {
  py::dict result;
  result["max_time"] =
      cfg.max_time.has_value() ? py::cast(*cfg.max_time) : py::none();
  result["max_depth"] =
      cfg.max_depth.has_value() ? py::cast(*cfg.max_depth) : py::none();
  result["use_move_ordering"] = cfg.use_move_ordering;
  result["use_mvv_lva"] = cfg.use_mvv_lva;
  result["use_history_heuristic"] = cfg.use_history_heuristic;
  result["history_max_score"] = cfg.history_max_score;
  result["use_countermove_heuristic"] = cfg.use_countermove_heuristic;
  result["use_see_ordering"] = cfg.use_see_ordering;
  result["see_capture_threshold"] = cfg.see_capture_threshold;
  result["use_killer_moves"] = cfg.use_killer_moves;
  result["killer_slots_per_ply"] = cfg.killer_slots_per_ply;
  result["use_hash_move_ordering"] = cfg.use_hash_move_ordering;
  result["use_alpha_beta"] = cfg.use_alpha_beta;
  result["use_pvs"] = cfg.use_pvs;
  result["use_quiescence_search"] = cfg.use_quiescence_search;
  result["qs_max_depth"] = cfg.qs_max_depth;
  result["use_iid"] = cfg.use_iid;
  result["iid_min_depth"] = cfg.iid_min_depth;
  result["iid_depth_reduction"] = cfg.iid_depth_reduction;
  result["use_null_move_pruning"] = cfg.use_null_move_pruning;
  result["nmp_reduction_r"] = cfg.nmp_reduction_r;
  result["nmp_min_depth"] = cfg.nmp_min_depth;
  result["use_lmr"] = cfg.use_lmr;
  result["lmr_min_depth"] = cfg.lmr_min_depth;
  result["lmr_min_move_number"] = cfg.lmr_min_move_number;
  result["use_futility_pruning"] = cfg.use_futility_pruning;
  result["futility_margin_standard"] = cfg.futility_margin_standard;
  result["use_extended_futility_pruning"] = cfg.use_extended_futility_pruning;
  result["futility_margin_extended"] = cfg.futility_margin_extended;
  result["use_reverse_futility_pruning"] = cfg.use_reverse_futility_pruning;
  result["rfp_margin_multiplier"] = cfg.rfp_margin_multiplier;
  result["rfp_max_depth"] = cfg.rfp_max_depth;
  result["use_delta_pruning"] = cfg.use_delta_pruning;
  result["delta_margin"] = cfg.delta_margin;
  result["use_see_pruning_in_qs"] = cfg.use_see_pruning_in_qs;
  result["use_aspiration_windows"] = cfg.use_aspiration_windows;
  result["aspiration_window_margin"] = cfg.aspiration_window_margin;
  result["use_check_extensions"] = cfg.use_check_extensions;
  result["max_check_extensions"] = cfg.max_check_extensions;
  result["use_transposition_table"] = cfg.use_transposition_table;
  result["tt_size_mb"] = cfg.tt_size_mb;
  result["use_tt_aging"] = cfg.use_tt_aging;
  return result;
}

} // namespace

void init_search_bindings(py::module_ &m) {
  py::class_<Zobrist>(m, "Zobrist")
      .def(py::init<std::optional<uint64_t>>(), py::arg("seed") = py::none())
      .def("hash_board", &Zobrist::hash_board, "Compute full hash from scratch",
           py::arg("board"))
      .def("make_move_hash", &Zobrist::make_move_hash,
           "Fast incremental hash update", py::arg("board"), py::arg("move"))
      .def("make_null_move_hash", &Zobrist::make_null_move_hash,
           "O(1) incremental hash for null move", py::arg("board"))
      .def("get_current_hash", &Zobrist::get_current_hash, "Get current hash")
      .def("set_current_hash", &Zobrist::set_current_hash, "Set current hash",
           py::arg("hash_val"))
      .def("invalidate_hash", &Zobrist::invalidate_hash, "Invalidate hash");

  py::class_<StaticExchangeEvaluator>(m, "StaticExchangeEvaluator")
      .def(py::init<>())
      .def("evaluate", &StaticExchangeEvaluator::evaluate, py::arg("board"),
           py::arg("move"));

  // ── Transposition table ───────────────────────────────────────────
  py::class_<TTEntry>(m, "TTEntry")
      .def_readwrite("key", &TTEntry::key)
      .def_readwrite("depth", &TTEntry::depth)
      .def_readwrite("score", &TTEntry::score)
      .def_readwrite("age", &TTEntry::age)
      .def_property(
          "best_move",
          [](const TTEntry &e) -> py::object {
            if (!e.has_best_move)
              return py::none();
            return py::cast(e.best_move);
          },
          [](TTEntry &e, py::object value) {
            if (value.is_none()) {
              e.has_best_move = false;
            } else {
              e.best_move = value.cast<Move>();
              e.has_best_move = true;
            }
          })
      .def_property(
          "bound",
          [](const TTEntry &e) {
            return std::string(bound_to_string(e.bound));
          },
          [](TTEntry &e, const std::string &s) {
            e.bound = bound_from_string(s);
          });

  py::class_<TTHolder>(m, "TranspositionTable")
      .def(py::init([](py::object py_config) {
             return std::make_unique<TTHolder>(config_from_py(py_config));
           }),
           py::arg("config"))
      .def("increment_age", [](TTHolder &h) { h.table.increment_age(); })
      .def("clear", [](TTHolder &h) { h.table.clear(); })
      .def("size", [](const TTHolder &h) { return h.table.size(); })
      .def_property(
          "max_entries",
          [](const TTHolder &h) { return h.table.max_entries(); },
          [](TTHolder &h, int value) { h.table.set_max_entries(value); })
      .def_property_readonly(
          "current_age",
          [](const TTHolder &h) { return h.table.current_age(); })
      .def(
          "probe",
          [](TTHolder &h, uint64_t key) -> py::object {
            TTEntry *entry = h.table.probe(key);
            if (entry == nullptr)
              return py::none();
            // Return a copy — tests only read entry fields, and returning by
            // value keeps binding lifetime management simple.
            return py::cast(*entry);
          },
          py::arg("key"))
      .def(
          "try_get_score",
          [](const TTHolder &h, const TTEntry &entry, int depth, double alpha,
             double beta) -> py::object {
            auto result = h.table.try_get_score(entry, depth, alpha, beta);
            if (!result.has_value())
              return py::none();
            return py::float_(*result);
          },
          py::arg("entry"), py::arg("depth"), py::arg("alpha"), py::arg("beta"))
      .def(
          "store",
          [](TTHolder &h, uint64_t key, int depth, double score,
             py::object best_move, const std::string &bound) {
            std::optional<Move> bm;
            if (!best_move.is_none()) {
              bm = best_move.cast<Move>();
            }
            h.table.store(key, depth, score, bm, bound_from_string(bound));
          },
          py::arg("key"), py::arg("depth"), py::arg("score"),
          py::arg("best_move"), py::arg("bound"));

  py::class_<SearchStats>(m, "SearchStats")
      .def_readonly("nodes", &SearchStats::nodes)
      .def_readonly("depth", &SearchStats::depth)
      .def_readonly("seldepth", &SearchStats::seldepth)
      .def_readonly("tt_hits", &SearchStats::tt_hits)
      .def_readonly("hashfull", &SearchStats::hashfull)
      .def_readonly("beta_cutoffs", &SearchStats::beta_cutoffs)
      .def_readonly("first_move_cuts", &SearchStats::first_move_cuts)
      .def_readonly("killer_cuts", &SearchStats::killer_cuts)
      .def_readonly("history_cuts", &SearchStats::history_cuts)
      .def_readonly("qsearch_nodes", &SearchStats::qsearch_nodes)
      .def_readonly("null_move_cuts", &SearchStats::null_move_cuts)
      .def_readonly("pvs_researches", &SearchStats::pvs_researches)
      .def_readonly("root_move_changes", &SearchStats::root_move_changes)
      .def_readonly("score", &SearchStats::score)
      .def_readonly("best_move", &SearchStats::best_move)
      .def("__repr__", [](const SearchStats &s) {
        return "<SearchStats nodes=" + std::to_string(s.nodes) +
               " depth=" + std::to_string(s.depth) + ">";
      });

  py::class_<Search>(m, "Search")
      .def(py::init<Board &>(), py::keep_alive<1, 2>())
      .def("search", &Search::search, "Run a fixed depth search",
           py::arg("depth"))
      .def("get_stats", &Search::get_stats,
           "Get statistics from the last search")
      .def("reset_stats", &Search::reset_stats, "Reset search statistics");

  // ── Move sorter ───────────────────────────────────────────────────
  auto build_killer_dict = [](const MoveSorterHolder &h) {
    py::dict result;
    const auto &killers = h.sorter.killers();
    const auto &counts = h.sorter.killer_counts();
    for (int ply = 0; ply < MoveSorter::MAX_PLY; ++ply) {
      const int c = counts[ply];
      if (c <= 0) {
        continue;
      }
      py::list moves;
      for (int slot = 0; slot < c; ++slot) {
        moves.append(py::cast(killers[ply][slot]));
      }
      result[py::cast(ply)] = moves;
    }
    return result;
  };

  auto build_history_dict = [](const MoveSorterHolder &h) {
    py::dict result;
    h.sorter.history_for_each(
        [&](uint8_t from, uint8_t to, uint8_t promo, int score) {
          py::tuple key =
              py::make_tuple(static_cast<int>(from), static_cast<int>(to),
                             static_cast<int>(promo));
          result[key] = score;
        });
    return result;
  };

  auto build_countermove_dict = [](const MoveSorterHolder &h) {
    py::dict result;
    h.sorter.countermove_for_each(
        [&](uint8_t from, uint8_t to, uint8_t promo, const Move &m) {
          py::tuple key =
              py::make_tuple(static_cast<int>(from), static_cast<int>(to),
                             static_cast<int>(promo));
          result[key] = py::cast(m);
        });
    return result;
  };

  py::class_<MoveSorterHolder>(m, "MoveSorter")
      .def(py::init([](py::object py_config) {
             return std::make_unique<MoveSorterHolder>(
                 config_from_py(py_config));
           }),
           py::arg("config"))
      .def(
          "reset",
          [](MoveSorterHolder &h, bool clear_history, bool clear_killers) {
            h.sorter.reset(clear_history, clear_killers);
          },
          py::arg("clear_history") = true, py::arg("clear_killers") = true)
      .def(
          "sort_moves",
          [](MoveSorterHolder &h, Board &board, const std::vector<Move> &moves,
             int ply, py::object hash_move, py::object previous_move) {
            std::optional<Move> hm;
            if (!hash_move.is_none())
              hm = hash_move.cast<Move>();
            std::optional<Move> pm;
            if (!previous_move.is_none())
              pm = previous_move.cast<Move>();
            return h.sorter.sort_moves(board, moves, ply, hm, pm);
          },
          py::arg("board"), py::arg("moves"), py::arg("ply"),
          py::arg("hash_move"), py::arg("previous_move"))
      .def(
          "sort_tactical",
          [](MoveSorterHolder &h, Board &board,
             const std::vector<Move> &moves) {
            return h.sorter.sort_tactical(board, moves);
          },
          py::arg("board"), py::arg("moves"))
      .def(
          "see",
          [](MoveSorterHolder &h, Board &board, const Move &move) {
            return h.sorter.see(board, move);
          },
          py::arg("board"), py::arg("move"))
      .def(
          "on_beta_cutoff",
          [](MoveSorterHolder &h, const Move &move, int ply, int depth,
             py::object previous_move, bool is_tactical) {
            std::optional<Move> pm;
            if (!previous_move.is_none())
              pm = previous_move.cast<Move>();
            h.sorter.on_beta_cutoff(move, ply, depth, pm, is_tactical);
          },
          py::arg("move"), py::arg("ply"), py::arg("depth"),
          py::arg("previous_move"), py::arg("is_tactical"))
      .def("history_saturation",
           [](const MoveSorterHolder &h) {
             return h.sorter.history_saturation();
           })
      .def_property_readonly("killer_moves", build_killer_dict)
      .def_property_readonly("history_table", build_history_dict)
      .def_property_readonly("countermove_table", build_countermove_dict);

  // ── MinimaxStats ─────────────────────────────────────────────────
  py::class_<MinimaxStats>(m, "MinimaxStats")
      .def(py::init<>())
      .def_readwrite("nodes", &MinimaxStats::nodes)
      .def_readwrite("depth", &MinimaxStats::depth)
      .def_readwrite("seldepth", &MinimaxStats::seldepth)
      .def_readwrite("tt_hits", &MinimaxStats::tt_hits)
      .def_readwrite("hashfull", &MinimaxStats::hashfull)
      .def_readwrite("beta_cutoffs", &MinimaxStats::beta_cutoffs)
      .def_readwrite("first_move_cuts", &MinimaxStats::first_move_cuts)
      .def_readwrite("killer_cuts", &MinimaxStats::killer_cuts)
      .def_readwrite("history_cuts", &MinimaxStats::history_cuts)
      .def_readwrite("qsearch_nodes", &MinimaxStats::qsearch_nodes)
      .def_readwrite("null_move_cuts", &MinimaxStats::null_move_cuts)
      .def_readwrite("pvs_researches", &MinimaxStats::pvs_researches)
      .def_readwrite("lmr_researches", &MinimaxStats::lmr_researches)
      .def_readwrite("qs_see_pruning", &MinimaxStats::qs_see_pruning)
      .def_readwrite("qs_delta_pruning", &MinimaxStats::qs_delta_pruning)
      .def_readwrite("check_extensions", &MinimaxStats::check_extensions)
      .def_readwrite("iid_searches", &MinimaxStats::iid_searches)
      .def_readwrite("root_move_changes", &MinimaxStats::root_move_changes)
      .def_readwrite("history_saturation", &MinimaxStats::history_saturation)
      .def_readwrite("score", &MinimaxStats::score)
      .def("reset", &MinimaxStats::reset);

  // ── Minimax ──────────────────────────────────────────────────────
  // The Python wrapper is responsible for constructing the TT, move sorter,
  // and Zobrist holders; this binding stitches them together via raw
  // pointers while holding Python references to keep them alive.
  py::class_<MinimaxHolder>(m, "CppMinimax")
      .def(
          py::init([](Board &board, py::object evaluator_obj, py::object tt_obj,
                      py::object sorter_obj, py::object see_obj,
                      py::object zobrist_obj, py::object py_config) {
            auto &evaluator = evaluator_obj.cast<evaluators::IEvaluator &>();
            TranspositionTable *tt_ptr = nullptr;
            MoveSorter *sorter_ptr = nullptr;
            StaticExchangeEvaluator *see_ptr = nullptr;
            Zobrist *zobrist_ptr = nullptr;
            if (!tt_obj.is_none()) {
              tt_ptr = &tt_obj.cast<TTHolder &>().table;
            }
            if (!sorter_obj.is_none()) {
              sorter_ptr = &sorter_obj.cast<MoveSorterHolder &>().sorter;
            }
            if (!see_obj.is_none()) {
              see_ptr = &see_obj.cast<StaticExchangeEvaluator &>();
            }
            if (!zobrist_obj.is_none()) {
              zobrist_ptr = &zobrist_obj.cast<Zobrist &>();
            }
            auto holder = std::make_unique<MinimaxHolder>(
                board, evaluator, tt_ptr, sorter_ptr, see_ptr, zobrist_ptr,
                config_from_py(py_config));
            holder->tt_ref = std::move(tt_obj);
            holder->sorter_ref = std::move(sorter_obj);
            holder->see_ref = std::move(see_obj);
            holder->zobrist_ref = std::move(zobrist_obj);
            holder->evaluator_ref = std::move(evaluator_obj);
            return holder;
          }),
          py::keep_alive<1, 2>(), py::arg("board"), py::arg("evaluator"),
          py::arg("tt"), py::arg("sorter"), py::arg("see"), py::arg("zobrist"),
          py::arg("config"))
      .def(
          "find_best_move",
          [](MinimaxHolder &h, int depth,
             std::optional<double> max_time) -> py::tuple {
            Minimax::Result result = h.minimax.find_best_move(depth, max_time);
            py::object score =
                result.score.has_value() ? py::cast(*result.score) : py::none();
            py::object best_move = result.best_move.has_value()
                                       ? py::cast(*result.best_move)
                                       : py::none();
            return py::make_tuple(score, best_move);
          },
          py::arg("depth"), py::arg("max_time") = py::none())
      .def(
          "reset_state",
          [](MinimaxHolder &h, bool clear_tt, bool clear_history,
             bool clear_killers) {
            h.minimax.reset_state(clear_tt, clear_history, clear_killers);
          },
          py::arg("clear_tt") = true, py::arg("clear_history") = true,
          py::arg("clear_killers") = true)
      .def_property_readonly(
          "stats",
          [](const MinimaxHolder &h) -> const MinimaxStats & {
            return h.minimax.stats();
          },
          py::return_value_policy::reference_internal)
      .def_property_readonly("effective_features",
                             [](const MinimaxHolder &h) {
                               py::dict result;
                               const SearchPlan &plan = h.minimax.plan();
                               for (size_t index = 0;
                                    index < SEARCH_FEATURE_NAMES.size();
                                    ++index) {
                                 result[py::str(SEARCH_FEATURE_NAMES[index])] =
                                     plan.features[index];
                               }
                               return result;
                             })
      .def_property_readonly(
          "effective_config",
          [](const MinimaxHolder &h) { return config_to_dict(h.config); })
      .def_property_readonly(
          "feature_stats",
          [](const MinimaxHolder &h) {
            py::dict result;
            const auto &values = h.minimax.stats().feature_telemetry;
            for (size_t index = 0; index < SEARCH_FEATURE_NAMES.size();
                 ++index) {
              const auto &stats = values[index];
              py::dict item;
              item["considered"] = stats.considered;
              item["eligible"] = stats.eligible;
              item["applied"] = stats.applied;
              item["cutoffs"] = stats.cutoffs;
              item["researches"] = stats.researches;
              result[py::str(SEARCH_FEATURE_NAMES[index])] = std::move(item);
            }
            return result;
          })
      .def_property_readonly(
          "node_count",
          [](const MinimaxHolder &h) { return h.minimax.node_count(); })
      .def_property_readonly("root_best_move",
                             [](const MinimaxHolder &h) -> py::object {
                               auto move = h.minimax.root_best_move();
                               if (!move.has_value())
                                 return py::none();
                               return py::cast(*move);
                             })
      .def_property(
          "time_up", [](const MinimaxHolder &h) { return h.minimax.time_up(); },
          [](MinimaxHolder &h, bool value) { h.minimax.set_time_up(value); })
      .def("check_time_limit",
           [](MinimaxHolder &h) { return h.minimax.check_time_limit(); })
      .def("reset_clock", [](MinimaxHolder &h) { h.minimax.reset_clock(); });
}
