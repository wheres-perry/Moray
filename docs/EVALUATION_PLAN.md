# Evaluation Subsystem Plan (Proposed)

> **Status: planning / not implemented.** Scope is the evaluation subsystem only
> (`EvaluationConfig` and evaluator backends). Search flags are intentionally out of
> scope. Companion to the "Supported Configuration Matrix" in `DEVELOPMENT.md`.

## 1. Goals

- Decouple the evaluation **backend** from its **stackable components**, so that
  combinations are explicit rather than accidental.
- Add lightweight **baseline evaluators** for testing and search sanity checks.
- Add a **Stockfish-distilled PST** source alongside the hand-crafted tables.
- Make exclusivity and stackability machine-checkable via the config registry.

## 2. Composition model

Evaluation config has three layers, each with different composition rules:

| Layer | Composition | Examples |
| --- | --- | --- |
| **Backend** | **Mutually exclusive** — exactly one active | `classic`, `piece_count`, `random_piece`, `psqt_tapered`, `nnue_stockfish`, `nnue_custom` |
| **Components** | **Stackable** — only on hand-crafted backends | `use_mobility`, `use_king_safety`, `use_pawn_structure`, … |
| **Infrastructure** | **Stackable** — cross-cutting, subject to own prerequisites | `use_pawn_hash`, `use_material_hash`, `use_incremental_eval`, … |

`EvaluationConfig.backend` selects layer 1. Layer 2 is **forbidden** unless the backend
is hand-crafted (`classic` / `psqt_tapered`). Layer 3 stacks wherever its own
prerequisites hold.

## 3. Backends (mutually exclusive)

| Backend id | Implementation | Scoring | Deterministic | Status |
| --- | --- | --- | --- | --- |
| `classic` | `CompositeEvaluator` (material + PST + components) | hand-crafted | yes | Supported |
| `piece_count` | `PieceCountEval` (new) | `w * (own_piece_count − opp_piece_count)`, ignores piece types | yes | Proposed |
| `random_piece` | `RandomPieceEval` (new) | `Σ random_value(piece)`, seeded | yes, given `random_seed` | Proposed |
| `psqt_tapered` | Tapered PSQT (PeSTO-style) | mg/eg phase interpolation | yes | Planned |
| `nnue_stockfish` | SF-format NNUE | int8 inference | yes | Proposed |
| `nnue_custom` | Custom NNUE | int8 inference | yes | Proposed |

Notes:

- **`material` is not a separate backend** — it is the degenerate `classic` case with
  all components off. Keeping it as a distinct id would create two code paths for the
  same behaviour.
- **`piece_count`** scores *quantity*, not value. Example: White has 12 pieces, Black
  has 10 — White scores higher, regardless of piece types. This is the simplest
  possible baseline and is useful for verifying that material dominates and that count
  sign conventions are correct.
- **`random_piece`** assigns a seeded pseudorandom value per piece type (optionally
  per piece-square). It is a **test/benchmark backend only** — reproducible for a
  given `random_seed`, but never used for strength.
- NNUE inference must live in C++; a per-node Python/Torch call is not viable.

## 4. PST table sources (mutually exclusive; only for hand-crafted backends)

| Source id | Description | Status |
| --- | --- | --- |
| `handcrafted` | tables in `pst_tables.py` | Supported |
| `stockfish_distilled` | tables fitted to Stockfish evaluations (black-box) | Proposed |
| `pesto` | PeSTO tables (permissively licensed) | Planned |

Rule: `pst_source` is only valid when `backend ∈ {classic, psqt_tapered}`. `handcrafted`
is the default for `classic`; `pesto` is the default for `psqt_tapered`.

### Stockfish distillation method (proposed)

- **Do not copy Stockfish source tables** — Stockfish is GPL-3.0 while this project is
  MIT (see §9).
- Generate a position corpus, query a Stockfish **binary as a black-box oracle** for
  evaluations, then fit PST values via least squares / logistic regression.
- Persist only the fitted numbers plus provenance: `sf_version`, `position_count`,
  `dataset_hash`, `seed`. This makes a table set regenerable and auditable.

## 5. Stackable components (classic / psqt_tapered only)

| Component | Config key | Depends on | Status |
| --- | --- | --- | --- |
| Material | *(always on in hand-crafted)* | — | Supported |
| Piece-Square Tables (mg/eg) | `evaluation.use_pst` | `pst_source` | Supported |
| Pawn structure | `evaluation.use_pawn_structure` | `use_pst` | Supported |
| Mobility | `evaluation.use_mobility` | — | Supported |
| King safety | `evaluation.use_king_safety` | — | Supported |
| Game-stage interpolation | `evaluation.game_stage_conscious` | phase-aware backend | Supported |
| Bishop pair | `evaluation.use_bishop_pair` | — | Proposed |
| Rook on open/semi-open file | `evaluation.use_rook_open_file` | — | Proposed |
| Space | `evaluation.use_space` | — | Proposed |
| Threats / attacked pieces | `evaluation.use_threats` | — | Proposed |
| Outposts | `evaluation.use_outposts` | `use_pawn_structure` | Proposed |
| Passed-pawn scaling | `evaluation.use_passed_pawn_scaling` | `use_pawn_structure` | Proposed |
| Material imbalance | `evaluation.use_material_imbalance` | — | Proposed |
| Tempo bonus | `evaluation.tempo_cp` | — | Proposed |
| Drawishness / contempt | `evaluation.contempt_cp` | — | Proposed |

## 6. Cross-cutting infrastructure (stackable)

| Mechanism | Config key | Applies to | Status |
| --- | --- | --- | --- |
| Pawn hash table | `evaluation.use_pawn_hash` | hand-crafted; requires `use_pawn_structure` | Proposed |
| Material hash table | `evaluation.use_material_hash` | hand-crafted | Proposed |
| Evaluation cache | `evaluation.use_eval_cache` | any deterministic backend | Proposed |
| Lazy / staged eval | `evaluation.use_lazy_eval` | hand-crafted | Proposed |
| Incremental accumulator | `evaluation.use_incremental_eval` | `classic`, `psqt_tapered`, `nnue_*` | Planned |
| Tuned weights | `evaluation.weights_path` | hand-crafted | Planned |
| Fixed-point (int) eval | `evaluation.use_int_eval` | any | Proposed |
| SIMD / batched eval | `evaluation.use_simd_eval` | any C++ backend | Proposed |

## 7. Exclusivity vs. stackability rules

### Mutually exclusive (must reject if combined)

| Group | Members | Rule |
| --- | --- | --- |
| Backend | `classic`, `piece_count`, `random_piece`, `psqt_tapered`, `nnue_stockfish`, `nnue_custom` | exactly one |
| PST source | `handcrafted`, `stockfish_distilled`, `pesto` | at most one; PST backends only |
| NNUE network | `nnue_stockfish`, `nnue_custom` | implied by backend |

### Stackable (allowed to combine freely, subject to prerequisites)

| Layer | Stacking rule |
| --- | --- |
| Components (§5) | stack on top of `classic` / `psqt_tapered` |
| Infrastructure (§6) | stacks on top of components and hand-crafted backends |

### Invalid combinations (must raise a clear error)

| Combination | Why invalid |
| --- | --- |
| Any component (§5) with `piece_count`, `random_piece`, or `nnue_*` | those backends have no component layer |
| `pst_source` with `piece_count`, `random_piece`, or `nnue_*` | backend does not use PST |
| `game_stage_conscious` with `piece_count` / `random_piece` | not phase-aware |
| `use_pawn_hash` without `use_pawn_structure` | nothing to cache |
| `nnue_path` set on a non-NNUE backend | unused |
| `random_seed` set on a non-`random_piece` backend | unused |
| `piece_count_weight` set on a non-`piece_count` backend | unused |

### Stackability at a glance

| Backend ↓ / Option → | PST source | Components | Infrastructure | NNUE path | Random seed |
| --- | --- | --- | --- | --- | --- |
| `classic` | ✓ (one) | ✓ | ✓ | ✗ | ✗ |
| `psqt_tapered` | ✓ (one) | ✓ | ✓ | ✗ | ✗ |
| `piece_count` | ✗ | ✗ | ✓ (subset) | ✗ | ✗ |
| `random_piece` | ✗ | ✗ | ✗ | ✗ | ✓ (required) |
| `nnue_stockfish` | ✗ | ✗ | ✓ (incremental required) | ✓ (required) | ✗ |
| `nnue_custom` | ✗ | ✗ | ✓ (incremental required) | ✓ (required) | ✗ |

## 8. Proposed config schema

```python
class EvalBackend(Enum):
    CLASSIC = "classic"
    PIECE_COUNT = "piece_count"
    RANDOM_PIECE = "random_piece"
    PSQT_TAPERED = "psqt_tapered"
    NNUE_STOCKFISH = "nnue_stockfish"
    NNUE_CUSTOM = "nnue_custom"


class PSTSource(Enum):
    HANDCRAFTED = "handcrafted"
    STOCKFISH_DISTILLED = "stockfish_distilled"
    PESTO = "pesto"


@dataclass
class EvaluationConfig:
    backend: EvalBackend = EvalBackend.CLASSIC
    pst_source: PSTSource | None = None
    # baseline backends
    piece_count_weight: int = 100
    random_seed: int | None = None
    # NNUE
    nnue_path: str | None = None
    # ...existing component + infrastructure flags...
```

## 9. Licensing notes (Stockfish, PSTs, and NNUE networks)

### The two Stockfish artifacts have different licenses

| Artifact | License | Usable in this MIT project? |
| --- | --- | --- |
| Stockfish **source code** (incl. its NNUE loader/inference) | GPL-3.0 | No — copying/linking forces the combined work to GPL-3.0 |
| Stockfish **NNUE networks** (`official-stockfish/networks`) | CC0-1.0 | Yes — public-domain dedication, no copyleft |
| Stockfish **classical PST/eval source tables** | GPL-3.0 | No — do not copy values out of the source |

### Option A — stay MIT (use a CC0 network with your own inference)

- Implement your own NNUE loader + incremental inference from the public format
  description; vendor a network file from `official-stockfish/networks` (CC0-1.0).
- Do **not** copy any Stockfish `.cpp`/`.h` code.
- Add a `NOTICE` entry with network name, sha256, source URL, and the CC0 notice. CC0
  requires no attribution, but record provenance so a table/net set can be regenerated.
- For a strong hand-crafted PST without GPL entanglement, use **PeSTO** (permissive).

### Option B — switch the project to GPL-3.0

- Legitimate: as copyright holder you can relicense your own MIT code, and MIT is
  GPL-compatible (include it in a GPL-3.0 work, preserving its notice).
- Then you may reuse Stockfish's NNUE inference/loader source directly — a large time
  saving — and ship Stockfish networks.
- Cost: the entire distributed work becomes GPL-3.0 (source availability, no
  proprietary/closed distribution, anti-tivoization). Usually fine for a chess engine.
- If external contributors wrote MIT code, it can be included under the combined GPL
  distribution while retaining its MIT notice.

### Residual risk

Stockfish networks are trained on Leela Chess Zero data released under **ODbL**.
Stockfish distributes the resulting networks as CC0, but whether ODbL reaches trained
weights is legally untested. Keep provenance/attribution and flag for legal review
before commercial or otherwise high-stakes distribution.

> Not legal advice — have counsel confirm before changing the license or shipping
> Stockfish-derived artifacts.

## 10. Testing plan

- **Determinism:** `random_piece` with a fixed seed reproduces identical evals across
  runs and processes.
- **Sign convention:** `piece_count` returns > 0 when the side to move has more
  pieces, < 0 when fewer, 0 when equal (White-relative, matching `IEvaluator.go`).
- **Stacking:** every allowed component/infrastructure combination builds and returns
  a finite score.
- **Exclusivity:** each invalid combination in §7 is rejected with a message naming the
  offending key.
- **Differential:** incremental accumulator (when added) matches `go(board)` after every
  make/unmake in the randomised-game parity tests.

## 11. Open questions

1. Is `random_piece` a standalone backend, a stackable **noise modifier**, or both?
2. Should `piece_count` be a distinct backend or a flag on `classic`
   (e.g. `use_material_values=False`)?
3. Default `piece_count_weight` — 100 cp/piece, or tuned?
4. Should `random_piece` be forbidden in strength/parity tests but allowed in
   benchmarks? Policy needs to be explicit.
5. Naming: `piece_count` vs `material_count` (the latter risks confusion with
   material *values*).
