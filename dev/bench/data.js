window.BENCHMARK_DATA = {
  "lastUpdate": 1790014053255,
  "repoUrl": "https://github.com/wheres-perry/Moray",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "d9447913d470949a66258d1c62e605cc1f43a2f4",
          "message": "Update git ignore to exclude output.json",
          "timestamp": "2026-03-21T00:21:15-06:00",
          "tree_id": "9934098fdf0439c15bc9f2a5c7a99130b1545cf3",
          "url": "https://github.com/wheres-perry/ChessEngine/commit/d9447913d470949a66258d1c62e605cc1f43a2f4"
        },
        "date": 1774074436940,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2716.859498483975,
            "unit": "iter/sec",
            "range": "stddev: 0.000029973994677275183",
            "extra": "mean: 368.07203337456593 usec\nrounds: 2427"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 9.01772886035053,
            "unit": "iter/sec",
            "range": "stddev: 0.0005332528104010417",
            "extra": "mean: 110.89266659999453 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.17531715794579675,
            "unit": "iter/sec",
            "range": "stddev: 0.019725407596847825",
            "extra": "mean: 5.703948271333331 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 86.34306757735251,
            "unit": "iter/sec",
            "range": "stddev: 0.00010716437019657106",
            "extra": "mean: 11.581705724135015 msec\nrounds: 87"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 123310.03595914064,
            "unit": "iter/sec",
            "range": "stddev: 2.0916212511700464e-7",
            "extra": "mean: 8.109639999872796 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 75176.69907191866,
            "unit": "iter/sec",
            "range": "stddev: 1.5064872214906174e-7",
            "extra": "mean: 13.301994000073591 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 67639.34296378763,
            "unit": "iter/sec",
            "range": "stddev: 3.4085999456931274e-7",
            "extra": "mean: 14.784295000254133 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 722.1540470935048,
            "unit": "iter/sec",
            "range": "stddev: 0.00009354896890275651",
            "extra": "mean: 1.3847460995680325 msec\nrounds: 693"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 26.962884433062236,
            "unit": "iter/sec",
            "range": "stddev: 0.0008097301715944658",
            "extra": "mean: 37.08802010714355 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 1585.4369201722914,
            "unit": "iter/sec",
            "range": "stddev: 0.00010432742681683432",
            "extra": "mean: 630.7409568154429 usec\nrounds: 1482"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 166.21141846028837,
            "unit": "iter/sec",
            "range": "stddev: 0.0002235891613160499",
            "extra": "mean: 6.016433824243683 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 30.522583212307794,
            "unit": "iter/sec",
            "range": "stddev: 0.00021918342828630057",
            "extra": "mean: 32.76262670968047 msec\nrounds: 31"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "83025aadbddf74487774e243fcfa3cb889e64b1e",
          "message": "Unify dockerfiles and clean up build process",
          "timestamp": "2026-03-21T07:08:03Z",
          "tree_id": "1208f92041dfc77e1748732efaff78ec9a245748",
          "url": "https://github.com/wheres-perry/ChessEngine/commit/83025aadbddf74487774e243fcfa3cb889e64b1e"
        },
        "date": 1774077256984,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2723.559897512401,
            "unit": "iter/sec",
            "range": "stddev: 0.00003862561566851534",
            "extra": "mean: 367.16651648210967 usec\nrounds: 2275"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 9.024067136519854,
            "unit": "iter/sec",
            "range": "stddev: 0.0005629969551564602",
            "extra": "mean: 110.81477839998115 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.1776463670385498,
            "unit": "iter/sec",
            "range": "stddev: 0.031965525618911424",
            "extra": "mean: 5.629160993666687 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 86.46238510331732,
            "unit": "iter/sec",
            "range": "stddev: 0.0003484029498601115",
            "extra": "mean: 11.56572304598191 msec\nrounds: 87"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 119243.60443582115,
            "unit": "iter/sec",
            "range": "stddev: 4.3407821814884584e-7",
            "extra": "mean: 8.386193999513125 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 75549.44847378983,
            "unit": "iter/sec",
            "range": "stddev: 1.45389564621456e-7",
            "extra": "mean: 13.23636400002215 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 67722.00118731389,
            "unit": "iter/sec",
            "range": "stddev: 3.441987379423949e-7",
            "extra": "mean: 14.766249999524916 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 737.4863321786593,
            "unit": "iter/sec",
            "range": "stddev: 0.000041361441280168526",
            "extra": "mean: 1.3559573328577237 msec\nrounds: 703"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 26.949429046053673,
            "unit": "iter/sec",
            "range": "stddev: 0.0002922706826438142",
            "extra": "mean: 37.1065375185169 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 1659.657413969289,
            "unit": "iter/sec",
            "range": "stddev: 0.00008408757462259755",
            "extra": "mean: 602.5339877874967 usec\nrounds: 1474"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 166.9555802991953,
            "unit": "iter/sec",
            "range": "stddev: 0.00007551999208992794",
            "extra": "mean: 5.989617107783608 msec\nrounds: 167"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 29.845328138873132,
            "unit": "iter/sec",
            "range": "stddev: 0.00023688270375431857",
            "extra": "mean: 33.50608160000471 msec\nrounds: 30"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "b4824a339fe953c559de7e0103056d05fd1ff430",
          "message": "Feat/ml extractors and pgn (#6)\n\n* feat: add C++ ML feature extractors and high-performance PGN parser\n\n- Implement zero-copy C++ extractors for CNN, NNUE (HalfKP), and GNN formats\n\n- Add fast, memory-efficient PGN stream parser\n\n- Expose extractors and PGN parser to Python via PyBind11\n\n- Add comprehensive test suites for extractors and PGN parser\n\n- Include rigorous PGN parity tests against `python-chess`\n\n* test: refactor test suite structure, parameterize core tests, and expand uci coverage\n\n- Break monolithic test_core_engine.py into parameterized core tests\n\n- Move tests from unit dumping ground to domain-specific directories\n\n- Add stdin/stdout mock tests to UCI handler covering missing branches\n\n- Remove empty conftest.py files\n\n* style: fix ruff linting and formatting issues in test suite\n\n* Update src/engine/_cpp/extractors/bindings.cpp\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>\n\n* style: fix C++ code formatting to pass clang-format CI check\n\n* style: fix include order in extractors/bindings.cpp\n\n* ci: fix noxfile test paths after directory restructure\n\n* docs: add comprehensive style and naming guides\n\n---------\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>",
          "timestamp": "2026-03-21T03:39:50-06:00",
          "tree_id": "a8db626698439f439182c9caeb75f6b9077913c6",
          "url": "https://github.com/wheres-perry/ChessEngine/commit/b4824a339fe953c559de7e0103056d05fd1ff430"
        },
        "date": 1774086387285,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2682.5266518288313,
            "unit": "iter/sec",
            "range": "stddev: 0.000097193988486751",
            "extra": "mean: 372.78287591970167 usec\nrounds: 2450"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 8.70194211928179,
            "unit": "iter/sec",
            "range": "stddev: 0.011855205375120371",
            "extra": "mean: 114.91687560001083 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.17872875774137625,
            "unit": "iter/sec",
            "range": "stddev: 0.013730558775151844",
            "extra": "mean: 5.59507050033335 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 82.83754287324493,
            "unit": "iter/sec",
            "range": "stddev: 0.0019450459325810613",
            "extra": "mean: 12.071821124996001 msec\nrounds: 88"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 120456.99456448622,
            "unit": "iter/sec",
            "range": "stddev: 6.447071908726987e-7",
            "extra": "mean: 8.301717999984248 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 73063.01187936706,
            "unit": "iter/sec",
            "range": "stddev: 2.843844916416917e-7",
            "extra": "mean: 13.686816000017643 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 68719.64309659223,
            "unit": "iter/sec",
            "range": "stddev: 3.728567235627073e-7",
            "extra": "mean: 14.551880000226447 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 728.0288795383251,
            "unit": "iter/sec",
            "range": "stddev: 0.000047767763698514786",
            "extra": "mean: 1.373571884447968 msec\nrounds: 701"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 27.474815602774065,
            "unit": "iter/sec",
            "range": "stddev: 0.000903166097002389",
            "extra": "mean: 36.396968571429916 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 1633.656724779455,
            "unit": "iter/sec",
            "range": "stddev: 0.0000615724321292324",
            "extra": "mean: 612.1237006721842 usec\nrounds: 1490"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 164.11032797432833,
            "unit": "iter/sec",
            "range": "stddev: 0.00004900633405883705",
            "extra": "mean: 6.093461711662835 msec\nrounds: 163"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 30.680256577670928,
            "unit": "iter/sec",
            "range": "stddev: 0.00016689119370425127",
            "extra": "mean: 32.5942515333395 msec\nrounds: 30"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "0972801128b4287cfe3c26889741ecb39f1d0716",
          "message": "feat(elo): add standalone deterministic Elo estimation subsystem (#7)\n\n* feat(elo): add standalone deterministic Elo estimation subsystem\n\nIntroduce a self-contained elo_tests package with deterministic paired scheduling, simulated engine adapters, JSONL raw game logging, Elo point estimation, normal and paired-bootstrap confidence intervals, sequential stopping, and CLI/config/reporting support.\n\n* fix: resolve style guide issues, runtime errors, and docstring violations\n\n- Fix TypeError in PST tables caused by misplaced string literals.\n- Enable and satisfy strict docstring (pydocstyle) rules project-wide.\n- Move type-only imports into TYPE_CHECKING blocks to resolve TC001/TC003 failures.\n- Resolve undefined name 'Searcher' in Engine initialization.\n- Shorten long lines to comply with 88-character limit.\n- Update TODO.md with project roadmap and maintenance task completion.",
          "timestamp": "2026-03-22T14:51:03-06:00",
          "tree_id": "2216697e688b63ec1dfeecc34f7ce26bf783a457",
          "url": "https://github.com/wheres-perry/ChessEngine/commit/0972801128b4287cfe3c26889741ecb39f1d0716"
        },
        "date": 1774213077415,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2626.736078987747,
            "unit": "iter/sec",
            "range": "stddev: 0.00006316081497294919",
            "extra": "mean: 380.70059950041315 usec\nrounds: 2402"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 8.867772507575618,
            "unit": "iter/sec",
            "range": "stddev: 0.000819593767951151",
            "extra": "mean: 112.76789060000283 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.17395474973961292,
            "unit": "iter/sec",
            "range": "stddev: 0.03986579664873935",
            "extra": "mean: 5.748621417333339 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 85.92101642025122,
            "unit": "iter/sec",
            "range": "stddev: 0.00014858735179540056",
            "extra": "mean: 11.638596022990066 msec\nrounds: 87"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 121311.02278142961,
            "unit": "iter/sec",
            "range": "stddev: 2.03903589211461e-7",
            "extra": "mean: 8.243273999937628 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 73824.69970684049,
            "unit": "iter/sec",
            "range": "stddev: 1.7925088331789914e-7",
            "extra": "mean: 13.545602000021972 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 68457.09348890783,
            "unit": "iter/sec",
            "range": "stddev: 2.1731073231234683e-7",
            "extra": "mean: 14.607690000190132 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 722.8216800624461,
            "unit": "iter/sec",
            "range": "stddev: 0.000045140924822467304",
            "extra": "mean: 1.3834670812773737 msec\nrounds: 689"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 26.606034680080267,
            "unit": "iter/sec",
            "range": "stddev: 0.00015950728406995251",
            "extra": "mean: 37.58545803703294 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 1633.3630033082109,
            "unit": "iter/sec",
            "range": "stddev: 0.00004662776623600035",
            "extra": "mean: 612.2337765546309 usec\nrounds: 1544"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 163.81656587331102,
            "unit": "iter/sec",
            "range": "stddev: 0.00019745633312539835",
            "extra": "mean: 6.104388739130075 msec\nrounds: 161"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 30.25789328719916,
            "unit": "iter/sec",
            "range": "stddev: 0.0006007691400377753",
            "extra": "mean: 33.04922753571406 msec\nrounds: 28"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "1290f91168e2e7651e67efb745bb626817baad8e",
          "message": "fix: update README for test command and fix styling/linting errors",
          "timestamp": "2026-03-23T07:54:49Z",
          "tree_id": "d13c48dd478046d622937729efd160bfa6062505",
          "url": "https://github.com/wheres-perry/ChessEngine/commit/1290f91168e2e7651e67efb745bb626817baad8e"
        },
        "date": 1774252942864,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2457.889190742309,
            "unit": "iter/sec",
            "range": "stddev: 0.000008499215564417949",
            "extra": "mean: 406.85316643505365 usec\nrounds: 2157"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 8.162270561879673,
            "unit": "iter/sec",
            "range": "stddev: 0.001555405789679196",
            "extra": "mean: 122.51492920000828 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.16153136500709606,
            "unit": "iter/sec",
            "range": "stddev: 0.01369415079029391",
            "extra": "mean: 6.190748155666673 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 78.32723376030238,
            "unit": "iter/sec",
            "range": "stddev: 0.00006442775215199348",
            "extra": "mean: 12.766951569618914 msec\nrounds: 79"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 118323.05934276477,
            "unit": "iter/sec",
            "range": "stddev: 8.020973590426798e-8",
            "extra": "mean: 8.45143799995185 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 72730.70032687175,
            "unit": "iter/sec",
            "range": "stddev: 8.940058321740455e-8",
            "extra": "mean: 13.749351999990722 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 58069.6993184382,
            "unit": "iter/sec",
            "range": "stddev: 2.207275741230612e-7",
            "extra": "mean: 17.220684999870173 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 806.1682522203776,
            "unit": "iter/sec",
            "range": "stddev: 0.000037721131338660623",
            "extra": "mean: 1.2404358485288451 msec\nrounds: 713"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 23.070689221409335,
            "unit": "iter/sec",
            "range": "stddev: 0.0009655895836670456",
            "extra": "mean: 43.34504229167161 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 1574.2695379191778,
            "unit": "iter/sec",
            "range": "stddev: 0.0000966389485688487",
            "extra": "mean: 635.2152385046909 usec\nrounds: 1283"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 159.42373024508905,
            "unit": "iter/sec",
            "range": "stddev: 0.0002614180970434234",
            "extra": "mean: 6.272591906252956 msec\nrounds: 160"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 29.640987499809228,
            "unit": "iter/sec",
            "range": "stddev: 0.00022906807454930049",
            "extra": "mean: 33.73706763333833 msec\nrounds: 30"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "8f8fc6abdadf664e914d94753b2131fe9c549aa2",
          "message": "fix(tests): update regex for error message in test_move_ordering_dependencies",
          "timestamp": "2026-04-08T07:16:40Z",
          "tree_id": "eb7d91cb08b7319be49a2f58c310f3d4691e65a8",
          "url": "https://github.com/wheres-perry/ChessEngine/commit/8f8fc6abdadf664e914d94753b2131fe9c549aa2"
        },
        "date": 1775633158088,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2385.880628094128,
            "unit": "iter/sec",
            "range": "stddev: 0.00003894056926129787",
            "extra": "mean: 419.13245290851484 usec\nrounds: 2166"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 8.544097083854734,
            "unit": "iter/sec",
            "range": "stddev: 0.0001607625379713249",
            "extra": "mean: 117.03986859999986 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.16580238695223307,
            "unit": "iter/sec",
            "range": "stddev: 0.03279978931138623",
            "extra": "mean: 6.031276258333335 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 79.91539053925258,
            "unit": "iter/sec",
            "range": "stddev: 0.0003906996176496478",
            "extra": "mean: 12.513234224999792 msec\nrounds: 80"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 125101.0503730913,
            "unit": "iter/sec",
            "range": "stddev: 9.612154451293603e-8",
            "extra": "mean: 7.993538000022228 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 76392.91012690816,
            "unit": "iter/sec",
            "range": "stddev: 2.998098338952998e-7",
            "extra": "mean: 13.090219999980945 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 59028.915314769714,
            "unit": "iter/sec",
            "range": "stddev: 3.872414571241044e-7",
            "extra": "mean: 16.940849999826924 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 770.2617005432666,
            "unit": "iter/sec",
            "range": "stddev: 0.00002699479524568525",
            "extra": "mean: 1.2982600579708152 msec\nrounds: 690"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 23.24557024785893,
            "unit": "iter/sec",
            "range": "stddev: 0.0004911934746427097",
            "extra": "mean: 43.018948958333546 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 1437.5934971636846,
            "unit": "iter/sec",
            "range": "stddev: 0.00005249278088632191",
            "extra": "mean: 695.6069305912698 usec\nrounds: 1167"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 168.12142626322148,
            "unit": "iter/sec",
            "range": "stddev: 0.0005281448330065827",
            "extra": "mean: 5.948081825301298 msec\nrounds: 166"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 27.85349828657778,
            "unit": "iter/sec",
            "range": "stddev: 0.0002345338856687857",
            "extra": "mean: 35.90213300000045 msec\nrounds: 28"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "252ea0ca445a86ca696428f82304a2b8b95a5545",
          "message": "migrate: minimax, evaluators, transposition table and move ordering to C++",
          "timestamp": "2026-04-08T16:10:33Z",
          "tree_id": "d04d31020250bbc1f62d219067c5e7f4c5458adb",
          "url": "https://github.com/wheres-perry/ChessEngine/commit/252ea0ca445a86ca696428f82304a2b8b95a5545"
        },
        "date": 1775664989046,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2599.8797824095127,
            "unit": "iter/sec",
            "range": "stddev: 0.000015322412289496797",
            "extra": "mean: 384.6331691049274 usec\nrounds: 2324"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 8.404122616800965,
            "unit": "iter/sec",
            "range": "stddev: 0.00045223488795473435",
            "extra": "mean: 118.98922060000245 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.16528796518550423,
            "unit": "iter/sec",
            "range": "stddev: 0.0368233568105724",
            "extra": "mean: 6.05004725466667 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 80.31562350434389,
            "unit": "iter/sec",
            "range": "stddev: 0.0005870004891433613",
            "extra": "mean: 12.450877629629742 msec\nrounds: 81"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 109076.5427184687,
            "unit": "iter/sec",
            "range": "stddev: 2.162898633305601e-7",
            "extra": "mean: 9.167874000013398 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 66610.94439112312,
            "unit": "iter/sec",
            "range": "stddev: 1.852825630756331e-7",
            "extra": "mean: 15.012548000044035 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 62926.108073685675,
            "unit": "iter/sec",
            "range": "stddev: 4.278343677807152e-7",
            "extra": "mean: 15.891655000004336 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 734.3591741980081,
            "unit": "iter/sec",
            "range": "stddev: 0.00007509349661636216",
            "extra": "mean: 1.3617314730112788 msec\nrounds: 704"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 24.680503307766905,
            "unit": "iter/sec",
            "range": "stddev: 0.0003289780513318445",
            "extra": "mean: 40.51781227999925 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 1615.518649747758,
            "unit": "iter/sec",
            "range": "stddev: 0.00005272684775549632",
            "extra": "mean: 618.9962586666127 usec\nrounds: 1500"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 147.82658342822592,
            "unit": "iter/sec",
            "range": "stddev: 0.00007561897888763006",
            "extra": "mean: 6.764683163265618 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 36.25294312847355,
            "unit": "iter/sec",
            "range": "stddev: 0.0007347941117441534",
            "extra": "mean: 27.58396736111024 msec\nrounds: 36"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "7414da3c368e7fb06a52843fdc10f769afee97f5",
          "message": "refactor: complete Moray rename, upgrade dependencies, and add elo-test CI pipeline",
          "timestamp": "2026-07-27T09:49:06-06:00",
          "tree_id": "c1712a0c604a9e6f6d06d7876135d9e055999666",
          "url": "https://github.com/wheres-perry/Moray/commit/7414da3c368e7fb06a52843fdc10f769afee97f5"
        },
        "date": 1785167831917,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 5325.481854752378,
            "unit": "iter/sec",
            "range": "stddev: 0.000004660050617972863",
            "extra": "mean: 187.7764354989991 usec\nrounds: 4248"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 16.5347124959059,
            "unit": "iter/sec",
            "range": "stddev: 0.0002824680879804997",
            "extra": "mean: 60.478826000004915 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.3162020253957736,
            "unit": "iter/sec",
            "range": "stddev: 0.03933001371094776",
            "extra": "mean: 3.162535087333334 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 163.14031551713543,
            "unit": "iter/sec",
            "range": "stddev: 0.00011201368645912735",
            "extra": "mean: 6.129692693250707 msec\nrounds: 163"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 211586.29631949458,
            "unit": "iter/sec",
            "range": "stddev: 1.8182677660719378e-7",
            "extra": "mean: 4.72620399995094 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 129752.03866384245,
            "unit": "iter/sec",
            "range": "stddev: 1.10559878249022e-7",
            "extra": "mean: 7.7070080000112275 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 129615.94794028945,
            "unit": "iter/sec",
            "range": "stddev: 2.2513466075454422e-7",
            "extra": "mean: 7.715100000353914 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 1738.0644225452534,
            "unit": "iter/sec",
            "range": "stddev: 0.00002284720618365208",
            "extra": "mean: 575.3526664653671 usec\nrounds: 1652"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 52.51511556962826,
            "unit": "iter/sec",
            "range": "stddev: 0.0004989045824232616",
            "extra": "mean: 19.04213651922996 msec\nrounds: 52"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 4559.427364289956,
            "unit": "iter/sec",
            "range": "stddev: 0.000019994422292489967",
            "extra": "mean: 219.3257881092993 usec\nrounds: 4205"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 290.1019258713062,
            "unit": "iter/sec",
            "range": "stddev: 0.00006718131718172597",
            "extra": "mean: 3.4470643274654296 msec\nrounds: 284"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 60.08666407511269,
            "unit": "iter/sec",
            "range": "stddev: 0.0004830867605830001",
            "extra": "mean: 16.64262803389996 msec\nrounds: 59"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "8a6840124f9e57f35990700bd783665054d5a016",
          "message": "test(uci): add end-to-end test for reported 0000 move issue position with clock time controls",
          "timestamp": "2026-07-27T12:08:48-06:00",
          "tree_id": "21e37efb2b41c446739888e849729fbbd12c1f82",
          "url": "https://github.com/wheres-perry/Moray/commit/8a6840124f9e57f35990700bd783665054d5a016"
        },
        "date": 1785176099168,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 2751.1223934065492,
            "unit": "iter/sec",
            "range": "stddev: 0.00009739764849410592",
            "extra": "mean: 363.48800852940616 usec\nrounds: 1524"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 9.438971490702757,
            "unit": "iter/sec",
            "range": "stddev: 0.00461796394309175",
            "extra": "mean: 105.94374619999485 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.18803786497802902,
            "unit": "iter/sec",
            "range": "stddev: 0.09783281890250434",
            "extra": "mean: 5.318077824999999 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 99.95516221330439,
            "unit": "iter/sec",
            "range": "stddev: 0.00012868593115338635",
            "extra": "mean: 10.004485789998512 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 138142.8789722244,
            "unit": "iter/sec",
            "range": "stddev: 1.3990245596027618e-7",
            "extra": "mean: 7.238881999853675 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 82119.53812675095,
            "unit": "iter/sec",
            "range": "stddev: 1.5360665615158645e-7",
            "extra": "mean: 12.177370000017618 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 78660.25847551883,
            "unit": "iter/sec",
            "range": "stddev: 3.633257782244361e-7",
            "extra": "mean: 12.712900000337868 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 954.3102833861087,
            "unit": "iter/sec",
            "range": "stddev: 0.000027044807979362673",
            "extra": "mean: 1.0478772129037255 msec\nrounds: 930"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 29.642530003791833,
            "unit": "iter/sec",
            "range": "stddev: 0.006560887936111339",
            "extra": "mean: 33.73531206250213 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 2706.8219580903533,
            "unit": "iter/sec",
            "range": "stddev: 0.000019294892016266474",
            "extra": "mean: 369.4369321229735 usec\nrounds: 2534"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 183.8848210272577,
            "unit": "iter/sec",
            "range": "stddev: 0.00007659789706458864",
            "extra": "mean: 5.438186765028134 msec\nrounds: 183"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 37.25212577720561,
            "unit": "iter/sec",
            "range": "stddev: 0.0002399275815679241",
            "extra": "mean: 26.844105648647172 msec\nrounds: 37"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "c7a445a51001156797b055431a617b7a38acf151",
          "message": "docs: add standalone C++ target and GIL release tasks to roadmap",
          "timestamp": "2026-07-27T12:32:27-06:00",
          "tree_id": "4d212a97e836a885c8f26b3ae26709d4083a7d40",
          "url": "https://github.com/wheres-perry/Moray/commit/c7a445a51001156797b055431a617b7a38acf151"
        },
        "date": 1785177471929,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 3144.1087313310863,
            "unit": "iter/sec",
            "range": "stddev: 0.00001581824839577183",
            "extra": "mean: 318.055158218603 usec\nrounds: 2762"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 9.947338610344733,
            "unit": "iter/sec",
            "range": "stddev: 0.0005560116703124704",
            "extra": "mean: 100.52940180000007 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.1923896831546218,
            "unit": "iter/sec",
            "range": "stddev: 0.07217882304229736",
            "extra": "mean: 5.197783912333331 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 101.33332065697682,
            "unit": "iter/sec",
            "range": "stddev: 0.0000992274154595912",
            "extra": "mean: 9.868422287128018 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 137952.99279287673,
            "unit": "iter/sec",
            "range": "stddev: 1.1390414139689224e-7",
            "extra": "mean: 7.248846000038611 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 81147.13484904845,
            "unit": "iter/sec",
            "range": "stddev: 2.1630241595932736e-7",
            "extra": "mean: 12.323293999969565 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 80994.6138586006,
            "unit": "iter/sec",
            "range": "stddev: 7.683068310545083e-8",
            "extra": "mean: 12.346499999935645 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 1019.7664011019563,
            "unit": "iter/sec",
            "range": "stddev: 0.00009663903110407395",
            "extra": "mean: 980.61673626372 usec\nrounds: 1001"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 31.402888242765368,
            "unit": "iter/sec",
            "range": "stddev: 0.0009626512349282724",
            "extra": "mean: 31.84420465625104 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 2720.168618304058,
            "unit": "iter/sec",
            "range": "stddev: 0.00002187798095274003",
            "extra": "mean: 367.62426905118457 usec\nrounds: 2572"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 185.29470748607926,
            "unit": "iter/sec",
            "range": "stddev: 0.0000782598051666912",
            "extra": "mean: 5.396808217391356 msec\nrounds: 184"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 38.19155347924577,
            "unit": "iter/sec",
            "range": "stddev: 0.00019415452695689214",
            "extra": "mean: 26.1838000526327 msec\nrounds: 38"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "a2a48f5ff278a5053b247cb5323a14c6fa37de5d",
          "message": "fix(ci): add explicit write permissions for gh-pages benchmark publishing and PR comments",
          "timestamp": "2026-07-29T23:48:45-06:00",
          "tree_id": "d88c09c78c2510665c894edfd6bc6ed944f7dc02",
          "url": "https://github.com/wheres-perry/Moray/commit/a2a48f5ff278a5053b247cb5323a14c6fa37de5d"
        },
        "date": 1785390895179,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 3102.9883714532248,
            "unit": "iter/sec",
            "range": "stddev: 0.000010343024272298351",
            "extra": "mean: 322.26997986836454 usec\nrounds: 2583"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 9.786465296964167,
            "unit": "iter/sec",
            "range": "stddev: 0.00041062847850393224",
            "extra": "mean: 102.18193899999903 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.19079474436140836,
            "unit": "iter/sec",
            "range": "stddev: 0.07367302376323603",
            "extra": "mean: 5.241234518000003 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 99.82281729433083,
            "unit": "iter/sec",
            "range": "stddev: 0.0002718468684246556",
            "extra": "mean: 10.017749720001063 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 139818.64403304257,
            "unit": "iter/sec",
            "range": "stddev: 1.1710546634794425e-7",
            "extra": "mean: 7.152122000007921 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 81404.5475509909,
            "unit": "iter/sec",
            "range": "stddev: 2.2633546649379834e-7",
            "extra": "mean: 12.284326000013834 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 78897.57989553439,
            "unit": "iter/sec",
            "range": "stddev: 3.3224948193405113e-7",
            "extra": "mean: 12.674660000016047 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 976.2755711206249,
            "unit": "iter/sec",
            "range": "stddev: 0.00008000451470702674",
            "extra": "mean: 1.0243009551618123 msec\nrounds: 959"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 30.773466419985446,
            "unit": "iter/sec",
            "range": "stddev: 0.0007261193563012241",
            "extra": "mean: 32.49552670967747 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 2607.9159053277535,
            "unit": "iter/sec",
            "range": "stddev: 0.000018328835551165666",
            "extra": "mean: 383.44794705883106 usec\nrounds: 2550"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 182.11432587210152,
            "unit": "iter/sec",
            "range": "stddev: 0.00007293872650344422",
            "extra": "mean: 5.491056209945272 msec\nrounds: 181"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 37.20348965796817,
            "unit": "iter/sec",
            "range": "stddev: 0.00017453425628047179",
            "extra": "mean: 26.87919894594678 msec\nrounds: 37"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "16c807811ea8e887fa2dcee09f8acb7942d89e41",
          "message": "Add development status note to README\n\nAdded a note indicating that the project is still in development.",
          "timestamp": "2026-08-05T00:24:23-06:00",
          "tree_id": "b5dc79abe6a1ecd524615ce3680c3d5aff70b496",
          "url": "https://github.com/wheres-perry/Moray/commit/16c807811ea8e887fa2dcee09f8acb7942d89e41"
        },
        "date": 1785911413567,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 3045.7780720356686,
            "unit": "iter/sec",
            "range": "stddev: 0.000028477351597477206",
            "extra": "mean: 328.32333031133896 usec\nrounds: 2537"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 9.714570322330397,
            "unit": "iter/sec",
            "range": "stddev: 0.0006578164585874929",
            "extra": "mean: 102.93816059999585 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 0.18941518683923655,
            "unit": "iter/sec",
            "range": "stddev: 0.08515273718928648",
            "extra": "mean: 5.279407721666668 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 99.9333358568638,
            "unit": "iter/sec",
            "range": "stddev: 0.000259758753705233",
            "extra": "mean: 10.006670861386203 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 137896.07544899546,
            "unit": "iter/sec",
            "range": "stddev: 1.3680532301987057e-7",
            "extra": "mean: 7.251838000058797 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 79789.30516961566,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014231104734368737",
            "extra": "mean: 12.533007999934398 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 76572.25817780585,
            "unit": "iter/sec",
            "range": "stddev: 2.79802879906196e-7",
            "extra": "mean: 13.059559999888393 usec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 1017.176965596555,
            "unit": "iter/sec",
            "range": "stddev: 0.000039230377252133716",
            "extra": "mean: 983.1131001020251 usec\nrounds: 979"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 30.355023226176037,
            "unit": "iter/sec",
            "range": "stddev: 0.00031171406161418786",
            "extra": "mean: 32.943476687498304 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 2640.475444914558,
            "unit": "iter/sec",
            "range": "stddev: 0.000025090565737208872",
            "extra": "mean: 378.71967411246214 usec\nrounds: 2507"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 185.2004606428199,
            "unit": "iter/sec",
            "range": "stddev: 0.00006544415527162758",
            "extra": "mean: 5.399554604394929 msec\nrounds: 182"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 36.89303660924499,
            "unit": "iter/sec",
            "range": "stddev: 0.00022265121970163623",
            "extra": "mean: 27.105386054055824 msec\nrounds: 37"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "committer": {
            "email": "86326912+wheres-perry@users.noreply.github.com",
            "name": "Ethan Perry",
            "username": "wheres-perry"
          },
          "distinct": true,
          "id": "3d75498181b3f6f5eca3f9771e345a885c99900c",
          "message": "feat(eval): integrate Stockfish NNUE and Custom Latent Threats evaluators\n\n- Implement StockfishNNUEEvaluator (SFNNv16 88,944 inputs) and NNUEEvaluator (101,232 inputs with Latent Threats)\n- Wire EvalBackend enum into EvaluationConfig, ConfigSolver, and EvaluatorFactory\n- Add comprehensive test suites with numerical parity benchmarks, feature extractors, and LEB128 decoding\n- Add head-to-head match runner and Stockfish 18 Elo estimation CLI support\n- Update linting, formatting, type hints, and CI gates for PyTorch/NNUE",
          "timestamp": "2026-09-21T11:58:22-06:00",
          "tree_id": "6f4b9e166dfbb87d73643a3f1f9a614fc1069e6b",
          "url": "https://github.com/wheres-perry/Moray/commit/3d75498181b3f6f5eca3f9771e345a885c99900c"
        },
        "date": 1790014052245,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_performance.py::test_full_game_cycle_300_ply",
            "value": 0.0011741649008864842,
            "unit": "iter/sec",
            "range": "stddev: 0.0000045513821440566646",
            "extra": "mean: 851.6691303282945 sec\nrounds: 4069"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_3",
            "value": 0.0000037574127873393897,
            "unit": "iter/sec",
            "range": "stddev: 0.00012950318681890182",
            "extra": "mean: 266140.57507056504 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_perft_traversal_depth_5",
            "value": 7.36583856126281e-8,
            "unit": "iter/sec",
            "range": "stddev: 0.016007878139011233",
            "extra": "mean: 13576186.76655545 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_search_node_expansion_loop",
            "value": 0.00003765353200075617,
            "unit": "iter/sec",
            "range": "stddev: 0.00014319272528721749",
            "extra": "mean: 26557.93352878337 sec\nrounds: 169"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_promotion_heavy_movegen",
            "value": 0.0474271542013107,
            "unit": "iter/sec",
            "range": "stddev: 6.334094055450785e-7",
            "extra": "mean: 21.084967395584613 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_castling_and_ep_movegen",
            "value": 0.030057921064885296,
            "unit": "iter/sec",
            "range": "stddev: 1.2831657935320144e-7",
            "extra": "mean: 33.26910060883201 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_push_pop_precomputed",
            "value": 0.031606771331114364,
            "unit": "iter/sec",
            "range": "stddev: 1.904672066912972e-7",
            "extra": "mean: 31.638789977120485 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_bulk_instantiation_1000",
            "value": 0.00030828125485654313,
            "unit": "iter/sec",
            "range": "stddev: 0.00002517613513920487",
            "extra": "mean: 3243.7911298413005 sec\nrounds: 1371"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_single_move_toggle_50k",
            "value": 0.000012312017298221073,
            "unit": "iter/sec",
            "range": "stddev: 0.00010306017778749362",
            "extra": "mean: 81221.45833441016 sec\nrounds: 56"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_copy_chain_stress",
            "value": 0.0009168662925875445,
            "unit": "iter/sec",
            "range": "stddev: 0.000008185777365991204",
            "extra": "mean: 1090.6715712907699 sec\nrounds: 4045"
          },
          {
            "name": "tests/benchmarks/test_performance.py::test_batch_legal_generation",
            "value": 0.00006506457286446605,
            "unit": "iter/sec",
            "range": "stddev: 0.000027136718244760714",
            "extra": "mean: 15369.347034415616 sec\nrounds: 291"
          },
          {
            "name": "tests/benchmarks/test_search_metrics.py::test_search_metrics_full_suite",
            "value": 0.000012781891981057008,
            "unit": "iter/sec",
            "range": "stddev: 0.00008117409956861924",
            "extra": "mean: 78235.6791531346 sec\nrounds: 57"
          }
        ]
      }
    ]
  }
}