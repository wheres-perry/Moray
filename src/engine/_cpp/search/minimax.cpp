#include "minimax.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

namespace search {

namespace {

constexpr double NEG_INF = -std::numeric_limits<double>::infinity();
constexpr double POS_INF = std::numeric_limits<double>::infinity();

[[nodiscard]] constexpr bool is_finite(double v) noexcept {
  return v != NEG_INF && v != POS_INF;
}

} // namespace

Minimax::Minimax(Board &board, evaluators::IEvaluator &evaluator,
                 TranspositionTable *tt, MoveSorter *sorter,
                 StaticExchangeEvaluator *see, Zobrist *zobrist,
                 const CppSearchConfig &config)
    : board_(board), evaluator_(evaluator), tt_(tt), move_sorter_(sorter),
      see_(see), zobrist_(zobrist), plan_(SearchPlan::compile(config)) {
  if (plan_.services.tt != (tt_ != nullptr) ||
      plan_.services.zobrist != (zobrist_ != nullptr) ||
      plan_.services.move_sorter != (move_sorter_ != nullptr) ||
      plan_.services.see != (see_ != nullptr)) {
    throw std::invalid_argument(
        "Runtime services do not match the resolved search plan");
  }
  if (move_sorter_ != nullptr) {
    move_sorter_->set_telemetry(&stats_.feature_telemetry);
  }
}

void Minimax::reset_state(bool clear_tt, bool clear_history,
                          bool clear_killers) noexcept {
  if (clear_tt && tt_ != nullptr) {
    tt_->clear();
  }
  if (move_sorter_ != nullptr) {
    move_sorter_->reset(clear_history, clear_killers);
  }
  stats_.reset();
  root_best_move_.reset();
}

void Minimax::reset_clock() noexcept {
  start_time_ = Clock::now();
  time_up_ = false;
}

bool Minimax::check_time_limit() noexcept {
  if (!active_max_time_.has_value() || !start_time_.has_value()) {
    return false;
  }
  const auto elapsed =
      std::chrono::duration<double>(Clock::now() - *start_time_);
  if (elapsed.count() >= *active_max_time_) {
    time_up_ = true;
    return true;
  }
  return false;
}

Minimax::Result
Minimax::find_best_move(int depth, std::optional<double> max_time_override) {
  if (depth < 1 || depth > 128) {
    throw std::invalid_argument("Search depth must be between 1 and 128");
  }
  if (max_time_override.has_value() && !is_finite_number(*max_time_override)) {
    throw std::invalid_argument(
        "Search max_time override must be finite and positive");
  }
  if (max_time_override.has_value() && *max_time_override <= 0.0) {
    throw std::invalid_argument(
        "Search max_time override must be finite and positive");
  }
  int target_depth = depth;
  if (plan_.general.max_depth.has_value()) {
    target_depth = std::min(target_depth, *plan_.general.max_depth);
  }
  stats_.reset();
  if (move_sorter_ != nullptr) {
    move_sorter_->set_telemetry(&stats_.feature_telemetry);
  }
  time_up_ = false;
  active_max_time_ = max_time_override.has_value() ? max_time_override
                                                   : plan_.general.max_time;
  start_time_ = Clock::now();
  root_best_move_.reset();

  if (tt_ != nullptr) {
    auto &tt_stats = telemetry(SearchFeature::TRANSPOSITION_TABLE);
    tt_stats.considered += 1;
    tt_stats.eligible += 1;
    tt_stats.applied += 1;
    tt_->increment_age();
    if (plan_.state.tt_aging) {
      auto &age_stats = telemetry(SearchFeature::TT_AGING);
      age_stats.considered += 1;
      age_stats.eligible += 1;
      age_stats.applied += 1;
    }
  }
  if (zobrist_ != nullptr) {
    (void)zobrist_->hash_board(board_);
  }

  const bool root_turn_is_white = board_.get_side_to_move();
  std::optional<double> previous_score;
  std::optional<double> final_relative_score;

  for (int current_depth = 1; current_depth <= target_depth; ++current_depth) {
    if (check_time_limit()) {
      break;
    }

    double alpha = NEG_INF;
    double beta = POS_INF;
    if (plan_.state.aspiration) {
      auto &aspiration_stats = telemetry(SearchFeature::ASPIRATION_WINDOWS);
      aspiration_stats.considered += 1;
      if (previous_score.has_value()) {
        aspiration_stats.eligible += 1;
        aspiration_stats.applied += 1;
        const double margin =
            static_cast<double>(std::max(10, plan_.state.aspiration_margin));
        alpha = *previous_score - margin;
        beta = *previous_score + margin;
      }
    }

    const double relative_score =
        search_with_window(current_depth, alpha, beta);
    if (time_up_) {
      break;
    }

    previous_score = relative_score;
    final_relative_score = relative_score;
    stats_.depth = current_depth;
  }

  Result result;
  if (!final_relative_score.has_value()) {
    return result;
  }

  const std::vector<Move> legal_moves = board_.generate_legal_moves();
  if (legal_moves.empty()) {
    return result;
  }

  // Mandatory safeguard: if search completed without setting a root best move,
  // pick the first legal move as a fallback so the engine never returns nullopt
  // / 0000.
  if (!root_best_move_.has_value()) {
    root_best_move_ = legal_moves[0];
  }

  if (tt_ != nullptr && tt_->max_entries() > 0) {
    stats_.hashfull =
        static_cast<int>((tt_->size() * 1000) / tt_->max_entries());
  }
  if (move_sorter_ != nullptr) {
    stats_.history_saturation = move_sorter_->history_saturation();
  }

  const double white_score =
      root_turn_is_white ? *final_relative_score : -*final_relative_score;
  stats_.score = static_cast<int>(white_score);

  result.score = white_score;
  result.best_move = root_best_move_;
  return result;
}

double Minimax::search_with_window(int depth, double alpha, double beta) {
  const bool use_aspiration = plan_.algorithm.alpha_beta &&
                              plan_.state.aspiration && is_finite(alpha) &&
                              is_finite(beta);

  if (!use_aspiration) {
    const double a = plan_.algorithm.alpha_beta ? alpha : NEG_INF;
    const double b = plan_.algorithm.alpha_beta ? beta : POS_INF;
    return negamax(depth, a, b, 0, std::nullopt,
                   plan_.state.max_check_extensions);
  }

  double current_alpha = alpha;
  double current_beta = beta;

  for (int attempt = 0; attempt < 6; ++attempt) {
    const double score =
        negamax(depth, current_alpha, current_beta, 0, std::nullopt,
                plan_.state.max_check_extensions);
    if (time_up_) {
      return score;
    }
    if (score <= current_alpha) {
      current_alpha -=
          static_cast<double>(std::max(50, plan_.state.aspiration_margin));
      continue;
    }
    if (score >= current_beta) {
      current_beta +=
          static_cast<double>(std::max(50, plan_.state.aspiration_margin));
      continue;
    }
    return score;
  }

  return negamax(depth, NEG_INF, POS_INF, 0, std::nullopt,
                 plan_.state.max_check_extensions);
}

double Minimax::negamax(int depth, double alpha, double beta, int ply,
                        std::optional<Move> previous_move,
                        int extensions_left) {
  stats_.nodes += 1;
  if (ply > stats_.seldepth) {
    stats_.seldepth = ply;
  }

  if (stats_.nodes % TIME_CHECK_INTERVAL == 0 && check_time_limit()) {
    return relative_eval();
  }

  const GameState game_state = board_.is_game_over();
  if (game_state != GameState::ONGOING) {
    return terminal_score(game_state, ply);
  }

  if (depth <= 0) {
    if (plan_.algorithm.quiescence) {
      auto &qs_stats = telemetry(SearchFeature::QUIESCENCE_SEARCH);
      qs_stats.considered += 1;
      qs_stats.eligible += 1;
      qs_stats.applied += 1;
      return quiescence(alpha, beta, ply, 0);
    }
    return relative_eval();
  }

  bool in_check = board_.is_check();
  if (plan_.state.check_extensions) {
    auto &extension_stats = telemetry(SearchFeature::CHECK_EXTENSIONS);
    extension_stats.considered += 1;
    if (in_check && extensions_left > 0) {
      extension_stats.eligible += 1;
      extension_stats.applied += 1;
      depth += 1;
      extensions_left -= 1;
      stats_.check_extensions += 1;
    }
  }

  const auto key_opt = current_hash();
  std::optional<Move> hash_move;
  if (tt_ != nullptr && key_opt.has_value()) {
    auto &tt_stats = telemetry(SearchFeature::TRANSPOSITION_TABLE);
    tt_stats.considered += 1;
    tt_stats.eligible += 1;
    TTEntry *entry = tt_->probe(*key_opt);
    if (entry != nullptr) {
      tt_stats.applied += 1;
      if (entry->has_best_move) {
        hash_move = entry->best_move;
      }
      if (plan_.algorithm.alpha_beta) {
        auto hit_score = tt_->try_get_score(*entry, depth, alpha, beta);
        if (hit_score.has_value()) {
          if (ply == 0) {
            if (entry->has_best_move) {
              root_best_move_ = entry->best_move;
              stats_.tt_hits += 1;
              return *hit_score;
            }
            // If at root and entry has no best move, do not cut off so
            // root_best_move_ is populated.
          } else {
            stats_.tt_hits += 1;
            tt_stats.cutoffs += 1;
            return *hit_score;
          }
        }
      } else if (entry->bound == TTBound::EXACT && entry->depth >= depth) {
        if (ply == 0) {
          if (entry->has_best_move) {
            root_best_move_ = entry->best_move;
            stats_.tt_hits += 1;
            return entry->score;
          }
        } else {
          stats_.tt_hits += 1;
          tt_stats.cutoffs += 1;
          return entry->score;
        }
      }
    }
  }

  const double static_eval = relative_eval();

  if (plan_.pruning.reverse_futility) {
    auto &rfp_stats = telemetry(SearchFeature::REVERSE_FUTILITY_PRUNING);
    rfp_stats.considered += 1;
    if (!in_check && depth <= plan_.pruning.rfp_max_depth && beta < POS_INF) {
      rfp_stats.eligible += 1;
      const double margin =
          static_cast<double>(plan_.pruning.rfp_margin_multiplier * depth);
      if (static_eval - margin >= beta) {
        rfp_stats.applied += 1;
        rfp_stats.cutoffs += 1;
        return beta;
      }
    }
  }

  if (plan_.pruning.null_move) {
    auto &null_stats = telemetry(SearchFeature::NULL_MOVE_PRUNING);
    null_stats.considered += 1;
    if (!in_check && depth >= plan_.pruning.nmp_min_depth &&
        has_non_pawn_material() && beta < POS_INF) {
      null_stats.eligible += 1;
      null_stats.applied += 1;
      const double null_score =
          null_move_search(depth, beta, ply, extensions_left);
      if (null_score >= beta) {
        null_stats.cutoffs += 1;
        stats_.null_move_cuts += 1;
        return beta;
      }
    }
  }

  if (plan_.algorithm.iid) {
    auto &iid_stats = telemetry(SearchFeature::IID);
    iid_stats.considered += 1;
    if (depth >= plan_.algorithm.iid_min_depth && !hash_move.has_value() &&
        tt_ != nullptr && key_opt.has_value()) {
      iid_stats.eligible += 1;
      iid_stats.applied += 1;
      stats_.iid_searches += 1;
      const int shallow_depth = depth - plan_.algorithm.iid_depth_reduction;
      (void)negamax(shallow_depth, alpha, beta, ply, previous_move,
                    extensions_left);
      TTEntry *iid_entry = tt_->probe(*key_opt);
      if (iid_entry != nullptr && iid_entry->has_best_move) {
        hash_move = iid_entry->best_move;
      }
    }
  }

  std::vector<Move> legal_moves = board_.generate_legal_moves();
  if (legal_moves.empty()) {
    return in_check ? -MATE_SCORE + ply : 0.0;
  }

  if (plan_.ordering.enabled) {
    legal_moves = move_sorter_->sort_moves(board_, legal_moves, ply, hash_move,
                                           previous_move);
  }

  const double original_alpha = alpha;
  double best_score = NEG_INF;
  std::optional<Move> best_move;

  for (size_t index = 0; index < legal_moves.size(); ++index) {
    if (time_up_) {
      break;
    }

    const Move &move = legal_moves[index];
    const bool is_tactical = is_tactical_move(move);
    bool prune_move = false;
    if (plan_.pruning.futility) {
      auto &futility_stats = telemetry(SearchFeature::FUTILITY_PRUNING);
      futility_stats.considered += 1;
      if (depth == 1 && !in_check && !is_tactical) {
        futility_stats.eligible += 1;
        if (static_eval + static_cast<double>(plan_.pruning.futility_margin) <=
            alpha) {
          futility_stats.applied += 1;
          prune_move = true;
        }
      }
    }
    if (!prune_move && plan_.pruning.extended_futility) {
      auto &futility_stats =
          telemetry(SearchFeature::EXTENDED_FUTILITY_PRUNING);
      futility_stats.considered += 1;
      if (depth == 2 && !in_check && !is_tactical) {
        futility_stats.eligible += 1;
        if (static_eval +
                static_cast<double>(plan_.pruning.extended_futility_margin) <=
            alpha) {
          futility_stats.applied += 1;
          prune_move = true;
        }
      }
    }
    if (prune_move) {
      continue;
    }

    auto saved_hash = push_move_with_hash(move);
    const bool gives_check = board_.is_check();

    int child_extensions = extensions_left;
    int next_depth = depth - 1;
    if (plan_.state.check_extensions) {
      auto &extension_stats = telemetry(SearchFeature::CHECK_EXTENSIONS);
      extension_stats.considered += 1;
      if (gives_check && child_extensions > 0) {
        extension_stats.eligible += 1;
        extension_stats.applied += 1;
        next_depth += 1;
        child_extensions -= 1;
        stats_.check_extensions += 1;
      }
    }

    const double score = search_child(
        static_cast<int>(index), next_depth, alpha, beta, ply, move, in_check,
        gives_check, is_tactical, child_extensions);

    pop_move_with_hash(saved_hash);

    if (score > best_score) {
      best_score = score;
      best_move = move;
      if (ply == 0) {
        if (!root_best_move_.has_value() || *root_best_move_ != move) {
          stats_.root_move_changes += 1;
        }
        root_best_move_ = move;
      }
    }

    if (plan_.algorithm.alpha_beta) {
      auto &ab_stats = telemetry(SearchFeature::ALPHA_BETA);
      ab_stats.considered += 1;
      ab_stats.eligible += 1;
      ab_stats.applied += 1;
      alpha = std::max(alpha, score);
      if (alpha >= beta) {
        ab_stats.cutoffs += 1;
        stats_.beta_cutoffs += 1;
        if (index == 0) {
          stats_.first_move_cuts += 1;
        }
        if (move_sorter_ != nullptr) {
          if (plan_.ordering.killers && move_sorter_->is_killer(ply, move)) {
            stats_.killer_cuts += 1;
            telemetry(SearchFeature::KILLER_MOVES).cutoffs += 1;
          }
          if (plan_.ordering.history &&
              move_sorter_->history_get(move.from, move.to, move.promotion) >
                  0) {
            stats_.history_cuts += 1;
            telemetry(SearchFeature::HISTORY_HEURISTIC).cutoffs += 1;
          }
          move_sorter_->on_beta_cutoff(move, ply, depth, previous_move,
                                       is_tactical);
        }
        break;
      }
    } else {
      // Keep a best-so-far bound for selective policies such as LMR. It is
      // never passed to children as an alpha-beta pruning window.
      alpha = std::max(alpha, score);
    }
  }

  if (!best_move.has_value()) {
    return static_eval;
  }

  if (tt_ != nullptr && key_opt.has_value()) {
    const TTBound bound = determine_bound(best_score, original_alpha, beta);
    tt_->store(*key_opt, depth, best_score, best_move, bound);
  }

  return best_score;
}

double Minimax::search_child(int index, int next_depth, double alpha,
                             double beta, int ply, const Move &move,
                             bool in_check, bool gives_check, bool is_tactical,
                             int extensions_left) {
  // Depth and window policies are composed independently. This supports all
  // alpha-beta/PVS/LMR combinations instead of hiding one inside another.
  const bool use_alpha_beta = plan_.algorithm.alpha_beta;
  const bool zero_window = use_alpha_beta && plan_.algorithm.pvs && index > 0;
  const bool reduced =
      can_apply_lmr(index, next_depth, in_check, gives_check, is_tactical);

  if (plan_.algorithm.pvs) {
    auto &pvs_stats = telemetry(SearchFeature::PVS);
    pvs_stats.considered += 1;
    if (zero_window) {
      pvs_stats.eligible += 1;
      pvs_stats.applied += 1;
    }
  }

  int initial_depth = next_depth;
  if (plan_.pruning.lmr) {
    auto &lmr_stats = telemetry(SearchFeature::LMR);
    lmr_stats.considered += 1;
    if (reduced) {
      lmr_stats.eligible += 1;
      lmr_stats.applied += 1;
      initial_depth =
          std::max(0, next_depth - lmr_reduction(next_depth, index));
    }
  }

  const double initial_beta = zero_window ? alpha + 1.0 : beta;
  const double child_alpha = use_alpha_beta ? -initial_beta : NEG_INF;
  const double child_beta = use_alpha_beta ? -alpha : POS_INF;
  double score = -negamax(initial_depth, child_alpha, child_beta, ply + 1, move,
                          extensions_left);

  if (reduced && score > alpha) {
    auto &lmr_stats = telemetry(SearchFeature::LMR);
    lmr_stats.researches += 1;
    stats_.lmr_researches += 1;
    score = -negamax(next_depth, child_alpha, child_beta, ply + 1, move,
                     extensions_left);
  }

  if (zero_window && alpha < score && score < beta) {
    auto &pvs_stats = telemetry(SearchFeature::PVS);
    pvs_stats.researches += 1;
    stats_.pvs_researches += 1;
    score = -negamax(next_depth, -beta, -alpha, ply + 1, move, extensions_left);
  }

  return score;
}

double Minimax::quiescence(double alpha, double beta, int ply, int qs_depth) {
  stats_.qsearch_nodes += 1;
  if (ply > stats_.seldepth) {
    stats_.seldepth = ply;
  }

  if (qs_depth >= plan_.algorithm.qs_max_depth) {
    return relative_eval();
  }

  const GameState game_state = board_.is_game_over();
  if (game_state != GameState::ONGOING) {
    return terminal_score(game_state, ply);
  }

  const double stand_pat = relative_eval();
  if (plan_.algorithm.alpha_beta) {
    if (stand_pat >= beta) {
      return beta;
    }
    if (stand_pat > alpha) {
      alpha = stand_pat;
    }
  } else if (stand_pat > alpha) {
    alpha = stand_pat;
  }

  std::vector<Move> tactical;
  for (const auto &move : board_.generate_legal_moves()) {
    if (is_tactical_move(move)) {
      tactical.push_back(move);
    }
  }
  if (tactical.empty()) {
    return alpha;
  }

  if (plan_.ordering.enabled) {
    tactical = move_sorter_->sort_tactical(board_, tactical);
  }

  for (const auto &move : tactical) {
    if (plan_.pruning.delta) {
      auto &delta_stats = telemetry(SearchFeature::DELTA_PRUNING);
      delta_stats.considered += 1;
      const double delta_eval = stand_pat + capture_gain(move) +
                                static_cast<double>(plan_.pruning.delta_margin);
      delta_stats.eligible += 1;
      if (delta_eval < alpha) {
        delta_stats.applied += 1;
        delta_stats.cutoffs += 1;
        stats_.qs_delta_pruning += 1;
        continue;
      }
    }

    if (plan_.pruning.see_in_qs) {
      auto &see_stats = telemetry(SearchFeature::SEE_PRUNING_IN_QS);
      see_stats.considered += 1;
      if (board_.is_capture(move)) {
        see_stats.eligible += 1;
      }
      if (board_.is_capture(move) && see_->evaluate(board_, move) < 0) {
        see_stats.applied += 1;
        see_stats.cutoffs += 1;
        stats_.qs_see_pruning += 1;
        continue;
      }
    }

    auto saved_hash = push_move_with_hash(move);
    const double score = -quiescence(-beta, -alpha, ply + 1, qs_depth + 1);
    pop_move_with_hash(saved_hash);

    if (plan_.algorithm.alpha_beta && score >= beta) {
      return beta;
    }
    if (score > alpha) {
      alpha = score;
    }
  }

  return alpha;
}

double Minimax::null_move_search(int depth, double beta, int ply,
                                 int extensions_left) {
  std::optional<uint64_t> saved_hash;
  std::optional<uint64_t> null_hash;
  if (zobrist_ != nullptr) {
    saved_hash = zobrist_->get_current_hash();
    if (saved_hash.has_value()) {
      null_hash = zobrist_->make_null_move_hash(board_);
    }
  }

  board_.push_null();

  if (zobrist_ != nullptr) {
    if (null_hash.has_value()) {
      zobrist_->set_current_hash(null_hash);
    } else {
      (void)zobrist_->hash_board(board_);
    }
  }

  const int reduction = plan_.pruning.nmp_reduction;
  const double score =
      -negamax(std::max(0, depth - 1 - reduction), -beta, -beta + 1.0, ply + 1,
               std::nullopt, extensions_left);

  (void)board_.pop();
  if (zobrist_ != nullptr && saved_hash.has_value()) {
    zobrist_->set_current_hash(saved_hash);
  }

  return score;
}

bool Minimax::has_non_pawn_material() const noexcept {
  const Color stm = board_.get_side_to_move() ? Color::WHITE : Color::BLACK;
  for (const PieceType pt : {PieceType::KNIGHT, PieceType::BISHOP,
                             PieceType::ROOK, PieceType::QUEEN}) {
    if (board_.get_piece_bb(pt, stm) != 0) {
      return true;
    }
  }
  return false;
}

int Minimax::lmr_reduction(int depth, int move_index) noexcept {
  const double base = 0.75 * std::log(std::max(2, depth)) *
                      std::log(std::max(2, move_index + 1));
  return std::max(1, std::min(3, static_cast<int>(base)));
}

} // namespace search
