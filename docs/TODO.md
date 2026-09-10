# Moray Development Roadmap

## Core Testing & Stability
- [ ] Setup Elo tests with configs and games (simulated and real)
- [ ] Set up Mate in N tests (M1 through M12+)
- [ ] Set up draw tests (stalemate, threefold repetition, fifty-move rule, insufficient material)
- [ ] Set up "Best Move" tactical tests:
    - [ ] En passant is the only/best move
    - [ ] Castling is the only/best move
    - [ ] Promotion (specifically under-promotion) is the only/best move
- [x] Fix broken benchmark in nox: `pytest --benchmark-only --benchmark-json=output.json --benchmark-autosave tests/benchmarks`
- [x] Fix ASAN/UBSAN sanitizer session in nox (`exit code -6` in `tests_all`)

## Engine & Search Improvements
- [ ] Implement and evaluate different evaluators (see `docs/EVALUATION_PLAN.md`):
    - [ ] Simple Hand-Coded Evaluation (current)
    - [ ] PeSTO-style tapered evaluation
    - [ ] Piece-count baseline (`piece_count`) for search sanity testing
    - [ ] Random-piece baseline (`random_piece`, seeded) for search sanity testing
    - [ ] Stockfish-distilled PST source (`pst_source=stockfish_distilled`, black-box distillation)
    - [ ] Stockfish NNUE (HalfKAv2_hm, SF-format network loader)
    - [ ] Custom NNUE (own architecture + training pipeline)
- [ ] Static Exchange Evaluation (SEE) for better move ordering and pruning
- [ ] Syzygy Tablebase Integration in the search loop
- [ ] Refine Null Move Pruning (NMP) with adaptive reduction
- [ ] Implement Aspiration Windows and Principal Variation Search (PVS) optimizations
- [ ] Internal Iterative Deepening (IID) for nodes without hash moves

## Configuration & Tooling
- [x] Dependency Resolution with z3 solver for config validation
- [ ] Expand UCI options support (e.g., MultiPV, Hash size, Threads)
- [x] Automated Elo regression testing in CI with Stockfish 18 & `elo-test` PR label
- [ ] Release Python GIL during C++ search (`py::call_guard<py::gil_scoped_release>()`) for non-blocking multi-threading
- [ ] Optional Standalone C++ UCI Executable Target (`moray_uci`) in `CMakeLists.txt` for single-binary distribution

## Proposed Future Ideas
- [ ] **Multi-threading (Lazy SMP)**: Parallelize search across multiple CPU cores.
- [ ] **Search Visualization Tool**: A CLI or web-based tool to visualize the search tree and pruning decisions. (Planned for later)
- [ ] **Game Database Analysis**: Script to analyze PGN databases to identify engine weaknesses.
