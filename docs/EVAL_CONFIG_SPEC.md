# Evaluation Configuration Specification

> **Draft v0.4 — planning / not implemented.**
> v0.4: decoupled orthogonal modifiers (`material_mode`, `phase_mode`) with minimal
> backends + aliases. v0.3: tri-state explicit-set semantics; non-composable combinations
> are hard errors. v0.2: selectable PST table sets and custom `piece_values`.
> This document is the authoritative spec for the evaluation config surface. It is
> deliberately standalone; it does not modify `DEVELOPMENT.md`, `TODO.md`, or
> `EVALUATION_PLAN.md`.

## 1. Scope & posture

- **Scope:** `EvaluationConfig` and the evaluator backends only. Search flags are out of
  scope.
- **Project license:** stays **MIT**.
- **Stockfish usage posture:**
  - Stockfish is used **only as a build-time black-box oracle** to fit our own PST
    tables. No Stockfish source is copied, linked, or shipped.
  - Stockfish **NNUE network files** are used at runtime as an evaluation backend. Those
    files are **CC0-1.0** (`official-stockfish/networks`); we ship them with a `NOTICE`.
  - We implement our own NNUE loader + inference. We do **not** copy Stockfish's NNUE
    C++ source (GPL-3.0).

## 2. Configuration surface

### 2.1 Enums

```python
class EvalBackend(Enum):
    """Whole-score mechanism. Deliberately minimal."""

    HANDCRAFTED = "handcrafted"  # composite of orthogonal terms
    NNUE_STOCKFISH = "nnue_stockfish"  # CC0 Stockfish-format net, own inference
    NNUE_CUSTOM = "nnue_custom"  # RESERVED — not scheduled


class MaterialMode(Enum):
    """How the material term is scored — orthogonal to everything else."""

    VALUES = "values"  # piece_values (int or (mg, eg))
    COUNT = "count"  # material_count_weight x piece-count diff
    RANDOM = "random"  # seeded random per piece


class PhaseMode(Enum):
    """Whether terms carrying mg/eg data are interpolated."""

    NONE = "none"  # use mg (or single) values only
    INTERPOLATE = "interpolate"  # mg/eg blend by game phase


class PSTSource(Enum):
    """Origin/family of a bundled table set — metadata, not the selector."""

    HANDCRAFTED = "handcrafted"  # hand-tuned in-repo
    SANE = "sane"  # hand-tuned "sane" values
    PESTO = "pesto"  # permissive third-party tables
    STOCKFISH_DISTILLED = (
        "stockfish_distilled"  # fitted to SF evals, distilled out-of-tree
    )
```

### 2.2 PST table registry

Table sets are hardcoded constants selected by a stable id. `pst_source` is metadata
describing a table's origin; **`pst_table_id` is the selector**.

| `pst_table_id` | `source` | Phase | Provenance | Status |
| --- | --- | --- | --- | --- |
| `handcrafted` | `handcrafted` | single | in-repo | supported |
| `sane` | `sane` | single | hand-tuned, in-repo | proposed |
| `pesto` | `pesto` | tapered | PeSTO (permissive) | planned |
| `sf_distilled_19` | `stockfish_distilled` | tapered | Stockfish 19 oracle + dataset hash (in source) | proposed |
| `sf_distilled_20` | `stockfish_distilled` | tapered | reserved for a future oracle | reserved |

Adding a table set = add one registry entry plus its constant. Renaming or removing an
id is a breaking config change.

### 2.3 Fields

All capability-gated fields are **tri-state**: `None` = unset (resolved per backend), or
an explicit value. Only explicit values can be blocked (see §6.3).

| Field | Type | Default | Applies to | Notes |
| --- | --- | --- | --- | --- |
| `backend` | `EvalBackend` (or alias) | `handcrafted` | always | aliases in §2.4 |
| `material_mode` | `MaterialMode` | `values` | `handcrafted` | see §6.6 |
| `piece_values` | `Mapping[str, int \| tuple[int, int]] \| None` | `None` | `handcrafted`, `values` mode | keys `pawn..queen`; `int` or `(mg, eg)`; partial merge over defaults |
| `material_count_weight` | `int` | `100` | `handcrafted`, `count` mode | `> 0` |
| `random_seed` | `int \| None` | `None` | `handcrafted`, `random` mode | coerced to `0` if omitted |
| `phase_mode` | `PhaseMode` | `interpolate` | `handcrafted` | legacy `game_stage_conscious` alias |
| `use_pst` | `bool` | `True` | `handcrafted` | term toggle |
| `pst_table_id` | `str \| None` | `None` | `handcrafted` and `use_pst` | §2.2 registry |
| `use_pawn_structure` | `bool` | `True` | `handcrafted` | requires `use_pst` |
| `use_mobility` | `bool` | `True` | `handcrafted` | — |
| `use_king_safety` | `bool` | `True` | `handcrafted` | — |
| `use_pawn_hash` | `bool` | `False` | `handcrafted` | requires `use_pawn_structure` |
| `use_material_hash` | `bool` | `False` | `handcrafted` | — |
| `use_eval_cache` | `bool` | `False` | `handcrafted`, `nnue_*` | — |
| `use_lazy_eval` | `bool` | `False` | `handcrafted` | — |
| `use_int_eval` | `bool` | `False` | `handcrafted`, `nnue_*` | — |
| `use_incremental_eval` | `bool` | `False` | all | coerced `True` for `nnue_*` |
| `nnue_path` | `str \| None` | `None` | `nnue_*` | required for `nnue_stockfish` |
| `nnue_layout` | `str \| None` | `None` | `nnue_*` | optional override |

### 2.4 Backends and aliases

`handcrafted` is the **base backend, not an alias**. It is the composite that hosts the
modifiers and terms; the other names are aliases that expand to it plus explicit fields.

| Name | Kind | Expands to / meaning |
| --- | --- | --- |
| `handcrafted` | backend | material (`values`) + `use_pst` + term flags, `phase_mode=interpolate` |
| `nnue_stockfish` | backend | fixed net (`nnue_path`) |
| `nnue_custom` | backend (reserved) | — |
| `classic` | alias | `handcrafted` (identical; kept for familiarity) |
| `material` | alias | `handcrafted`, all terms off, `material_mode=values`, `phase_mode=none` |
| `psqt_tapered` | alias | `handcrafted` + `use_pst=True` + `phase_mode=interpolate` |
| `piece_count` | alias | `handcrafted` + `material_mode=count` + all terms off + `phase_mode=none` |
| `random_piece` | alias | `handcrafted` + `material_mode=random` + all terms off + `phase_mode=none` |

An alias plus a conflicting explicit field (e.g. `psqt_tapered` + `use_pst=False`) is a
contradiction and is **blocked** (§6.6).

## 3. Backend semantics

Backends name the whole-score mechanism only. Everything orthogonal is a modifier.

| Backend | Scoring | Deterministic | Per-node cost | Status |
| --- | --- | --- | --- | --- |
| `handcrafted` | material term (mode-dependent) + enabled terms, phase-aware | yes | low–medium | supported |
| `nnue_stockfish` | int8/int16 NNUE inference over a CC0 net | yes | low | proposed |
| `nnue_custom` | reserved | — | — | not scheduled |

### 3.1 Material modes (`handcrafted`)

| `material_mode` | Score | Uses | Status |
| --- | --- | --- | --- |
| `values` | `Σ piece_values(piece)` (int or mg/eg) | `piece_values` | supported |
| `count` | `material_count_weight × (own_count − opp_count)` | `material_count_weight` | proposed |
| `random` | `Σ random_value(piece; random_seed)` | `random_seed` | proposed |

- `count` example: White 12 pieces vs Black 10 → positive for White, ignoring piece types.
- `random` is a **test/benchmark mode only**, never for strength. A fixed seed must
  reproduce identical scores across runs and processes.

### 3.2 What the aliases mean

Aliases (§2.4) are shorthand; after resolution there is only `handcrafted`:

| Alias | Meaning |
| --- | --- |
| `classic` / `handcrafted` | material (`values`) + PST + components |
| `material` | material (`values`), no other terms |
| `psqt_tapered` | `handcrafted` with a tapered PST |
| `piece_count` | material (`count`), no other terms, no interpolation |
| `random_piece` | material (`random`), no other terms, no interpolation |

- Score convention is unchanged: `IEvaluator.go(board)` returns **centipawns,
  White-relative**; the search negates to side-to-move.

### 3.3 Terms hosted by `handcrafted`

`handcrafted` scores the sum of its enabled terms, by game phase (§6.5). The material term
is always present; the rest are toggles. Any term may carry single or `(mg, eg)` data.

| Term | Toggle | Depends on | Status |
| --- | --- | --- | --- |
| Material | always on | `material_mode` decides how it is scored | supported |
| Piece-Square Tables | `use_pst` | `pst_table_id` | supported |
| Pawn structure | `use_pawn_structure` | `use_pst` | supported |
| Mobility | `use_mobility` | — | supported |
| King safety | `use_king_safety` | — | supported |
| Bishop pair | `use_bishop_pair` | — | proposed |
| Rook on open/semi-open file | `use_rook_open_file` | — | proposed |
| Space | `use_space` | — | proposed |
| Threats / attacked pieces | `use_threats` | — | proposed |
| Outposts | `use_outposts` | `use_pawn_structure` | proposed |
| Passed-pawn scaling | `use_passed_pawn_scaling` | `use_pawn_structure` | proposed |
| Material imbalance | `use_material_imbalance` | — | proposed |
| Tempo | `tempo_cp` | — | proposed |
| Drawishness / contempt | `contempt_cp` | — | proposed |

Infrastructure flags (`use_pawn_hash`, `use_material_hash`, `use_eval_cache`,
`use_lazy_eval`, `use_int_eval`, `use_incremental_eval`) are **not** terms — they change
*how* terms are computed or cached, and they are also hosted by `handcrafted`.

`handcrafted` is the only mechanism that hosts terms. NNUE backends are whole-score and
host none — that boundary is what makes NNUE a backend rather than a term (§6.1).

## 4. PST sources

### 4.1 Selection

Configs select one **`pst_table_id`** from the §2.2 registry (mutually exclusive). Each
table set is bundled as hardcoded constants; there is no runtime file loading.

- `handcrafted` — existing tables in `pst_tables.py`; the default.
- `sane` — a separate hand-tuned set with "sane" human-readable values.
- `pesto` — permissive third-party tables; a good tapered default.
- `sf_distilled_*` — our own tables fitted to Stockfish evaluations, distilled
  **outside this codebase** (§4.2).

`pst_table_id` applies only when `backend=handcrafted` and `use_pst` is on. Phase handling
is owned by `phase_mode`, not by the table:

| `phase_mode` | Tapered table | Single-phase table |
| --- | --- | --- |
| `none` | `mg` table used for both phases | table used as-is |
| `interpolate` | mg/eg interpolated | same table used for both phases (coerced) |

A PST is **not** required for interpolation: `use_pst=False` + `phase_mode=interpolate`
tapers whatever other terms carry mg/eg data (§6.5).

### 4.2 `stockfish_distilled` tables (distilled out-of-tree, hardcoded in-repo)

Distillation happens **outside this codebase**. The repository ships only the resulting
numbers as hardcoded constants — there is **no runtime file loading** and no data
artifact in the distribution.

**Generation pipeline (external, not runtime)**

1. Build a position corpus (self-play games and/or diverse openings) as EPD.
2. Query a Stockfish binary as a **black-box oracle** for mover-perspective evaluations
   (`go depth N` / `eval`).
3. Fit midgame/endgame PST values by regression (ridge / logistic) with:
   - symmetry constraints (left/right mirror equality),
   - per-piece-type normalization,
   - optional phase weights for interpolation.
4. Emit the fitted tables from the external tooling, then **paste them into this
   codebase** as the `stockfish_distilled` table set.

**In-code representation**

```python
# pst_tables.py (or a generated header) — hardcoded distilled tables.

PST_DISTILLED_SF19 = {
    "mg": {"pawn": (...64 ints...), "knight": (...), "bishop": (...),
           "rook": (...), "queen": (...), "king": (...)},
    "eg": {"pawn": (...64 ints...), "knight": (...), "bishop": (...),
           "rook": (...), "queen": (...), "king": (...)},
}

PST_DISTILLED_PROVENANCE = {
    "sf_version": "sf_19",
    "sf_commit": "0000000000",
    "dataset_sha256": "…",
    "dataset_count": 5000000,
    "fit_method": "ridge",
    "fit_seed": 1234,
}
```

**Rules**

- Tables are module-level constants: 64 entries per piece per phase, mirror-symmetric.
- Provenance is recorded **in source** (constant/docstring) and in `NOTICE`, so a table
  set stays traceable even though distillation is out of tree.
- No Stockfish code or binary is used at runtime; the oracle only produces the numbers.
- Selecting `pst_table_id = sf_distilled_19` switches to this bundled set (one constant
  per version, e.g. `sf_distilled_20` later). There is no runtime path or schema version
  to validate.

### 4.3 Material values (`piece_values`)

`piece_values` customizes the material term in `material_mode=values`. Values may be a
single int or an `(mg, eg)` pair, so material can itself be tapered.

- Keys: `pawn`, `knight`, `bishop`, `rook`, `queen`. The king is not valued and is a
  rejected key.
- Partial maps merge over the defaults
  `{pawn: 100, knight: 320, bishop: 330, rook: 500, queen: 900}`.
- Any non-negative int is allowed, including unusual sets such as `{queen: 1, pawn: 10}`,
  and per-phase pairs such as `{queen: (900, 1000)}`.
- Only meaningful with `material_mode=values`; explicitly setting it with `count` or
  `random` mode is **blocked** (§6.6), never ignored. Keys/values are always validated.
- With `phase_mode=none`, a pair's `eg` component is unused and recorded as a note.

```python
piece_values = {"pawn": 100, "knight": 320, "bishop": 330, "rook": 500, "queen": 900}
piece_values = {"queen": (950, 1050), "pawn": (100, 140)}  # tapered material
piece_values = {"queen": 1, "pawn": 10}  # odd but valid
```

## 5. NNUE backend (`nnue_stockfish`)

- **Weights:** a CC0-1.0 `.nnue` file from `official-stockfish/networks`.
- **Inference:** our own implementation in C++ (the search never calls Python/Torch per
  node). Must be incremental: maintain a feature-transformer accumulator updated on
  make/unmake; a full refresh is only a fallback.
- **Layout:** the net's header carries an architecture string (e.g. `HalfKAv2_hm^`). The
  loader must parse it and reject unsupported layouts unless `nnue_layout` overrides it
  to a supported value.
- **Quantization:** follow the standard NNUE scheme (clipped ReLU, int8/int16 feature
  transformer with per-feature scales, int32 accumulation, requantized L1/L2/L3).
- **Provenance:** every shipped net requires a `NOTICE` entry with net filename,
  sha256, source URL, and the CC0 notice.
- **`use_incremental_eval`** is coerced `True` when unset; explicitly setting it `False`
  is **blocked** (§6.6).

### 5.1 Residual licensing note

Stockfish networks are trained on Leela Chess Zero data released under **ODbL**;
Stockfish distributes the resulting nets as CC0. Whether ODbL reaches trained weights is
legally untested. Keep provenance/attribution and confirm with counsel before commercial
or closed distribution. (Not legal advice.)

## 6. Composition rules

**Design goal: try everything that composes — block the rest, never silently.** Backends
name only the whole-score mechanism (§3); every orthogonal concern is a modifier. A field
the backend cannot honor is a **hard error naming the field**, never a silent no-op.
Combinations are widened through documented **coercion**.

| Outcome | Meaning | Behaviour |
| --- | --- | --- |
| **Used** | composes; affects the score | validated per §6.4 |
| **Coerced** | composable after a prerequisite or defined reinterpretation | resolved value in `notes`; not an error |
| **Blocked** | genuinely cannot compose | hard error naming field (+ backend/alias) |

### 6.1 Capability model

Capabilities belong to the two mechanisms; modifiers are orthogonal.

| Capability | `handcrafted` | `nnue_stockfish` | `nnue_custom` |
| --- | --- | --- | --- |
| `HAS_MATERIAL` | yes | built into net | yes |
| `SUPPORTS_MATERIAL_MODES` | yes | — | — |
| `USES_TERMS` | yes | — | — |
| `USES_PST` | via `use_pst` | — | — |
| `SUPPORTS_TAPER` | yes (`phase_mode`) | internal only | internal only |
| `USES_NNUE` | — | yes | yes |
| `REQUIRES_INCREMENTAL` | optional | yes | yes |

`nnue_*` is a **fixed whole-score** mechanism: no terms or modifiers compose with it (only
`nnue_path`, `nnue_layout`, and the coerced `use_incremental_eval`). `nnue_custom` is
reserved: it parses but resolution raises "not implemented".

### 6.2 Mutually exclusive selections

| Group | Members | Rule |
| --- | --- | --- |
| Backend | `handcrafted`, `nnue_stockfish`, `nnue_custom` (aliases in §2.4) | exactly one |
| `material_mode` | `values`, `count`, `random` | exactly one |
| `phase_mode` | `none`, `interpolate` | exactly one |
| PST table | one `pst_table_id` from §2.2 | at most one |

### 6.3 Explicit-set semantics (resolves the default contradiction)

Capability-gated fields are **tri-state**: unset (`None`) / on / off.

- **Unset** → resolved to the backend default. No error.
- **Explicitly set** → must be consistent with the capabilities (§6.1/§6.4):
  - consistent, including redundant-consistent (e.g. `use_pst=True` on `psqt_tapered`) →
    **Used**;
  - prerequisite missing → **Coerced** (auto-satisfied and recorded);
  - capability absent, or value contradicts the backend/alias → **Blocked**.

Aliases expand to explicit fields before this check; an alias plus a conflicting field is a
contradiction (e.g. `psqt_tapered` + `use_pst=False`). Because only *explicit* settings are
checked, defaults never force a "must be off" rule — and nothing is silently ignored.

### 6.4 Field applicability

| Field | Composes when | Explicit value that blocks |
| --- | --- | --- |
| `backend` | always | unknown; alias conflict; reserved member |
| `material_mode` | `SUPPORTS_MATERIAL_MODES` | set on `nnue_*` |
| `piece_values` | mode `values` | set on `nnue_*`; set with `count`/`random`; invalid key/value |
| `material_count_weight` | mode `count` | set on `nnue_*`; set outside `count`; `<= 0` |
| `random_seed` | mode `random` | set on `nnue_*`; set outside `random` |
| `phase_mode` | `SUPPORTS_TAPER` | set on `nnue_*` |
| `use_pst` | `USES_TERMS` | set on `nnue_*`; `False` while `pst_table_id` is set |
| `pst_table_id` | `USES_TERMS` and `use_pst` | set on `nnue_*`; unknown id; set while `use_pst=False` |
| `use_pawn_structure` | `USES_TERMS` (coerces `use_pst=True` if unset) | set on `nnue_*`; `use_pst=False` while true |
| `use_mobility`, `use_king_safety` | `USES_TERMS` | set on `nnue_*` |
| `use_pawn_hash` | `USES_TERMS` (coerces `use_pawn_structure` if unset) | `use_pawn_structure=False` while true |
| `use_material_hash`, `use_lazy_eval` | `USES_TERMS` | set on `nnue_*` |
| `use_eval_cache`, `use_int_eval` | `handcrafted` or `nnue_*` | malformed value |
| `use_incremental_eval` | all | `False` on `nnue_*` |
| `nnue_path` | `USES_NNUE` | set on `handcrafted`; missing on `nnue_stockfish` |
| `nnue_layout` | `USES_NNUE` | set on `handcrafted`; unsupported layout |

### 6.5 Phase resolution (interpolation is orthogonal to PST)

| `phase_mode` | Term carries mg/eg | Term is single-valued | PST table phase |
| --- | --- | --- | --- |
| `none` | `mg` used; `eg` unused (noted) | value used | `mg`/single used |
| `interpolate` | mg/eg blended by phase | value used unchanged | tapered → blend; single → same both phases (coerced) |

Consequences that make "try everything" work:

- Tapered PST **without** the alias: `use_pst=True` + `phase_mode=interpolate`.
- Tapered evaluation **without PST**: `use_pst=False` + `phase_mode=interpolate` with
  tapered `piece_values` and/or tapered components.
- Count/random material **with** other terms: e.g. `material_mode=count` + `use_pst` /
  components — previously impossible.

### 6.6 Blocked combinations (hard errors — never silent)

| Blocked when explicitly set | Reason |
| --- | --- |
| any term/modifier field on `nnue_*` | NNUE is a fixed whole-score mechanism |
| `piece_values` / `material_count_weight` / `random_seed` outside their `material_mode` | mode-specific input |
| `pst_table_id` while `use_pst=False` | contradiction |
| `use_pawn_structure=True` with `use_pst=False` | contradiction |
| `use_pawn_hash=True` with `use_pawn_structure=False` | contradiction |
| alias + conflicting field (e.g. `psqt_tapered` + `use_pst=False`) | alias expansion contradicts the field |
| unknown `pst_table_id` | not in §2.2 registry |
| reserved selection (`nnue_custom`, `sf_distilled_20`) | not implemented |
| missing `nnue_path` on `nnue_stockfish` | no weights to load |
| `nnue_path`/`nnue_layout` unreadable or unsupported layout | cannot infer |
| `piece_values` invalid key / negative / `bool` value | invalid valuation |
| `material_count_weight <= 0` | meaningless scale |
| unknown/unparseable enum, malformed type, out-of-range value | malformed config |

### 6.7 Coercions (composable; recorded in `notes`)

| Trigger | Coercion |
| --- | --- |
| `use_pawn_structure` on, `use_pst` unset | `use_pst = True` |
| `use_pawn_hash` on, `use_pawn_structure` unset | `use_pawn_structure = True` (cascades to `use_pst`) |
| `random_seed` omitted in `random` mode | `random_seed = 0` |
| `pst_table_id` omitted with `use_pst` | default table (`handcrafted`) |
| single-phase table + `phase_mode=interpolate` | table used for both phases |
| `nnue_*` with `use_incremental_eval` unset | `use_incremental_eval = True` |
| alias without conflicting fields | expanded to explicit fields |

### 6.8 Stackability at a glance

`used` = composes · `coerced` = auto-satisfied/reinterpreted · `blocked` = explicit set is a
hard error.

| Field ↓ / Backend → | `handcrafted` | `nnue_stockfish` |
| --- | --- | --- |
| `material_mode` / `piece_values` / `material_count_weight` / `random_seed` | used (mode-gated) | blocked |
| `phase_mode` | used | blocked |
| `use_pst` / `pst_table_id` | used | blocked |
| term flags (pawn structure, mobility, king safety, …) | used | blocked |
| `use_pawn_hash` / `use_material_hash` / `use_lazy_eval` | used | blocked |
| `use_eval_cache` / `use_int_eval` | used | used |
| `use_incremental_eval` | used (optional) | coerced `True` |
| `nnue_path` / `nnue_layout` | blocked | used (path required) |

## 7. Validation & resolution rules (for the config registry)

Resolution is a pure function `resolve(raw) -> (effective, notes)`. It never mutates the
raw config and is idempotent: `resolve(resolve(c)) == resolve(c)`.

### 7.1 Resolution order

1. Parse and type-check; unknown enum members or malformed values → **Blocked**.
2. Expand aliases (§2.4) into explicit fields; a conflicting explicit field → **Blocked**.
3. Determine which fields were **explicitly set** (tri-state awareness, §6.3).
4. Read the backend capability set (§6.1).
5. For each explicitly-set field, apply §6.4:
   - capability absent, or value contradicts the backend/alias → **Blocked**;
   - prerequisite missing → **Coerced** (recorded in `notes`);
   - otherwise → **Used**.
6. Resolve unset defaults and mode-gated fields (§6.6/§6.7).
7. Resolve `pst_table_id` default; validate registry membership.
8. Resolve `material_mode` and `phase_mode` behaviour (§3.1/§6.5).
9. Enforce dependency closure transitively (`use_pawn_hash → use_pawn_structure →
   use_pst`) by coercion, never by rejection.
10. Emit `notes` entries: `coerced`, `defaulted`, `eg-unused`.

### 7.2 Ordering guarantee

Capability checks (§6.4) run **before** default resolution. Blocked combinations are
detected from what the user actually specified, never from a default value. This is what
makes the old "must be default/off" contradiction structurally impossible.

### 7.3 Blocked ⇒ hard error

Every row of §6.6 raises an error naming the offending field and backend. No explicitly
set field is ever silently dropped; a coerced field is always reported in `notes`.

### 7.4 Invariants (assertable in tests)

- `resolve` is idempotent and deterministic.
- Every explicitly-set field ends as **Used** or **Coerced**; nothing is dropped without a
  `notes` entry.
- Every accepted config builds an engine and completes a depth-2 search returning a legal
  move.
- Every blocked config raises an error naming the offending field.

## 8. Serialization

```json
{
  "search_depth": 12,
  "search": { "use_alpha_beta": true },
  "evaluation": {
    "backend": "handcrafted",
    "material_mode": "values",
    "piece_values": {"queen": [950, 1050], "pawn": [100, 140]},
    "phase_mode": "interpolate",
    "pst_table_id": "sf_distilled_19",
    "use_mobility": true,
    "use_pawn_hash": true
  }
}
```

```json
{
  "search_depth": 8,
  "evaluation": {
    "backend": "handcrafted",
    "material_mode": "count",
    "material_count_weight": 100,
    "phase_mode": "none",
    "use_pst": true,
    "pst_table_id": "handcrafted"
  }
}
```

```json
{
  "search_depth": 6,
  "evaluation": { "backend": "psqt_tapered", "pst_table_id": "pesto" }
}
```

```json
{
  "search_depth": 12,
  "evaluation": { "backend": "nnue_stockfish", "nnue_path": "nets/nn-1a298aa575a0.nnue" }
}
```

The second and third examples were impossible under the bundled-backend model: count
material **with** PST, and a tapered PST expressed without a dedicated backend.

## 9. Compatibility & migration

- `backend` omitted → `handcrafted` (current behaviour preserved).
- Old names remain loadable as aliases (§2.4): `classic` is `handcrafted`; `psqt_tapered`,
  `piece_count`, and `random_piece` expand to explicit fields.
- `game_stage_conscious` → **deprecated alias** for `phase_mode` (`true` →
  `interpolate`, `false` → `none`).
- `piece_count_weight` → renamed `material_count_weight`.
- Existing component flags keep their names, defaults, and meaning.
- `pst_table_id = None` with `use_pst` resolves to the `handcrafted` table set.
- `nnue_custom` is reserved so adding it later is not a breaking enum change.

## 10. Testing requirements

- **Determinism:** `material_mode=random` with a fixed `random_seed` reproduces identical
  evals across runs/processes.
- **Sign convention:** `material_mode=count` is `> 0` when the side to move has more
  pieces, `< 0` when fewer, `0` when equal (White-relative).
- **PST registry:** each bundled `pst_table_id` resolves; unknown ids are rejected; every
  table has 64 entries per piece per phase and is mirror-symmetric; provenance constants
  are populated.
- **Piece values:** partial maps merge with defaults; `int` and `(mg, eg)` forms both
  parse; `king` keys, unknown keys, negative values, and `bool` values are rejected;
  odd-but-valid maps (e.g. `{queen: 1, pawn: 10}`) change the material term
  deterministically.
- **Phase orthogonality:** tapered evaluation works with `use_pst=False`; tapered PST works
  without the `psqt_tapered` alias; a single-phase table under `interpolate` is coerced and
  noted.
- **Material orthogonality:** `material_mode=count` composes with PST and components.
- **NNUE differential:** incremental accumulator equals a full accumulator refresh after
  every make/unmake in the randomised-game parity tests.
- **NNUE reset:** accumulator is invalidated on `set_fen` and on TT/history clears.
- **Stacking:** every allowed modifier/term combination builds and returns a finite score.
- **Blocking:** every row in §6.6 is rejected with a message naming the offending field; no
  explicitly-set field is ever silently ignored.
- **Resolution:** `resolve` is idempotent and deterministic; every field ends as Used,
  Coerced, or Blocked; alias expansion is pure sugar (an aliased config resolves
  identically to its expansion); coerced/defaulted fields appear in `notes`.

## 11. Non-goals / open questions

- **Non-goal:** training or shipping a custom NNUE (`nnue_custom` reserved).
- **Non-goal:** GPU/batched NNUE inference.
- **Non-goal:** changing any `SearchConfig` flag (see §12).
- **Open:** naming for hand-tuned table sets — `sane` vs a versioned `handcrafted_v2`?
- **Open:** should `nnue_layout` be settable at all, or strictly header-derived?
- **Open:** default `material_count_weight` (100 cp/piece vs. tuned)?
- **Open:** should `material_mode=random` also act as a stackable noise modifier on other
  modes, or remain a full replacement mode? (Current spec: replacement only.)
- **Open:** which components carry mg/eg data next, now that `phase_mode` can consume it?

## 12. Composability principle (reuse beyond evaluation)

The rule applied throughout this document is:

> A **backend** names the whole-score mechanism. Every orthogonal concern is a **modifier**.
> Bundles become **aliases**. Contradictions **block**; prerequisites **coerce**; nothing is
> silently ignored.

The same audit applied to `SearchConfig` surfaces two known bundles (found while reviewing
the engine; **out of scope for this document**):

- **LMR is nested inside the PVS branch** in `minimax.cpp`, so `use_lmr=True` has no effect
  when `use_pvs=False`. LMR is orthogonal to PVS and should be applied independently or
  declared a hard dependency — not silently inert.
- **SEE pruning in QS** requires the move sorter, which is only built when
  `use_move_ordering=True`; the config accepts the combination and silently does nothing.

Both are the same class of bug this spec removes for evaluation: a modifier whose effect
vanishes because it was bundled into another feature's code path.
