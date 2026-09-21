"""Custom NNUE evaluation implementation for Moray.

Supports loading Stockfish/NNUE-PyTorch serialized networks (such as
`latent_threats.nnue`) with Full_Threats + PP_3Wide + HalfKAv2_hm^ + LatentThreats
architectures and evaluating positions directly inside the engine.
"""

from __future__ import annotations

import operator
import os
import struct
from functools import reduce
from typing import TYPE_CHECKING, Any

import chess as pychess
import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812

from engine._core import moray_core as core_chess

if TYPE_CHECKING:
    from engine._core.moray_core import Board

_ev = core_chess.evaluators
_IEvaluatorBase: Any = _ev.IEvaluator

# ── LEB128 Decoding ─────────────────────────────────────────────────────────


def decode_leb128(data: bytes, n: int) -> np.ndarray:
    """Decode a stream of signed LEB128 integers."""
    ints = np.empty(n, dtype=np.int32)
    k = 0
    for i in range(n):
        r = 0
        shift = 0
        while True:
            byte = data[k]
            k += 1
            r |= (byte & 0x7F) << shift
            shift += 7
            if (byte & 0x80) == 0:
                ints[i] = r if (byte & 0x40) == 0 else r | ~((1 << shift) - 1)
                break
    return ints


# ── Feature Constants & Tables ──────────────────────────────────────────────

KING_BUCKETS = [
    -1,
    -1,
    -1,
    -1,
    31,
    30,
    29,
    28,
    -1,
    -1,
    -1,
    -1,
    27,
    26,
    25,
    24,
    -1,
    -1,
    -1,
    -1,
    23,
    22,
    21,
    20,
    -1,
    -1,
    -1,
    -1,
    19,
    18,
    17,
    16,
    -1,
    -1,
    -1,
    -1,
    15,
    14,
    13,
    12,
    -1,
    -1,
    -1,
    -1,
    11,
    10,
    9,
    8,
    -1,
    -1,
    -1,
    -1,
    7,
    6,
    5,
    4,
    -1,
    -1,
    -1,
    -1,
    3,
    2,
    1,
    0,
]

INVERSE_KING_BUCKETS = [0] * 32
for _sq, _b in enumerate(KING_BUCKETS):
    if _b >= 0:
        INVERSE_KING_BUCKETS[_b] = _sq

ORIENT_TBL_WHITE = [0 if (sq % 8) < 4 else 7 for sq in range(64)]
ORIENT_TBL_BLACK = [56 if (sq % 8) < 4 else 63 for sq in range(64)]

NUM_VALID_TARGETS = [4, 10, 8, 8, 10, 0]
THREAT_MAP = [
    [-1, 0, -1, 1, -1, -1],
    [0, 1, 2, 3, 4, -1],
    [0, 1, 2, 3, -1, -1],
    [0, 1, 2, 3, -1, -1],
    [0, 1, 2, 3, 4, -1],
    [-1, -1, -1, -1, -1, -1],
]


def pseudo_attacks(pt: int, sq: int) -> int:
    """Return pseudo-legal attack bitboard for sliding/leaping piece on empty board."""
    if pt == pychess.KNIGHT:
        return int(pychess.BB_KNIGHT_ATTACKS[sq])
    if pt == pychess.BISHOP:
        return int(pychess.BB_DIAG_ATTACKS[sq][0])
    if pt == pychess.ROOK:
        return int(pychess.BB_FILE_ATTACKS[sq][0] | pychess.BB_RANK_ATTACKS[sq][0])
    if pt == pychess.QUEEN:
        return int(
            pychess.BB_DIAG_ATTACKS[sq][0]
            | pychess.BB_FILE_ATTACKS[sq][0]
            | pychess.BB_RANK_ATTACKS[sq][0]
        )
    return 0


def _build_threat_offsets() -> tuple[np.ndarray, int]:
    table = np.zeros((10, 66), dtype=np.int32)
    piece_offset = 0
    piece_tbl = [
        (0, pychess.PAWN),
        (0, pychess.KNIGHT),
        (0, pychess.BISHOP),
        (0, pychess.ROOK),
        (0, pychess.QUEEN),
        (1, pychess.PAWN),
        (1, pychess.KNIGHT),
        (1, pychess.BISHOP),
        (1, pychess.ROOK),
        (1, pychess.QUEEN),
    ]

    for p_idx in range(10):
        c, pt = piece_tbl[p_idx]
        table[p_idx, 65] = piece_offset
        sq_offset = 0
        for sq in range(64):
            table[p_idx, sq] = sq_offset
            if pt == pychess.PAWN:
                if 8 <= sq <= 55:
                    color = pychess.WHITE if c == 0 else pychess.BLACK
                    att = pychess.BB_PAWN_ATTACKS[color][sq]
                    sq_offset += bin(att).count("1")
            else:
                att = pseudo_attacks(pt, sq)
                sq_offset += bin(att).count("1")
        table[p_idx, 64] = sq_offset
        pt_idx = pt - 1
        piece_offset += NUM_VALID_TARGETS[pt_idx] * sq_offset

    return table, piece_offset


THREAT_OFFSETS, TOTAL_THREAT_FEATURES = _build_threat_offsets()


def orient_hm(color_idx: int, sq: int, ksq: int) -> int:
    """Apply horizontal and vertical flip depending on perspective and king square."""
    orient = ORIENT_TBL_WHITE[ksq] if color_idx == 0 else ORIENT_TBL_BLACK[ksq]
    return sq ^ orient


def orient_halfka(is_white_pov: bool, sq: int, ksq: int) -> int:
    """HalfKAv2 horizontal flip when king file < 4 and vertical flip for Black."""
    kfile = ksq % 8
    h = 7 if kfile < 4 else 0
    v = 0 if is_white_pov else 56
    return sq ^ h ^ v


def king_square_hm_index(oriented_k: int) -> int:
    """Return compact 32-bucket index of oriented king square."""
    return (oriented_k >> 3) * 4 + (oriented_k & 7)


# ── Feature Extractor ───────────────────────────────────────────────────────


def extract_features(  # noqa: C901, PLR0912
    board: pychess.Board,
    is_white_pov: bool,
    include_latent_threats: bool = True,
) -> list[int]:
    """Extract active indices for NNUE features."""
    features: list[int] = []
    persp_c = 0 if is_white_pov else 1
    opp_persp_c = 1 - persp_c

    ksq = board.king(pychess.WHITE if is_white_pov else pychess.BLACK)
    if ksq is None:
        return features

    # 1. Full_Threats (inputs: 59808, offset: 0)
    # Order: White then Black
    colors_order = (0, 1) if is_white_pov else (1, 0)
    pieces_bb = int(board.occupied)
    white_k = board.king(pychess.WHITE)
    black_k = board.king(pychess.BLACK)
    kings_bb = (
        (1 << white_k) | (1 << black_k)
        if white_k is not None and black_k is not None
        else 0
    )
    non_king_pieces = pieces_bb & ~kings_bb
    all_pawns = int(board.pawns)

    for c in colors_order:
        pawn_bb = int(
            board.pieces(pychess.PAWN, pychess.WHITE if c == 0 else pychess.BLACK)
        )
        diag_targets = non_king_pieces & ~all_pawns

        if c == 0:  # White
            # right: +9, left: +7
            right_targets = ((pawn_bb & ~pychess.BB_FILE_H) << 9) & diag_targets
            left_targets = ((pawn_bb & ~pychess.BB_FILE_A) << 7) & diag_targets
            shifts = [(right_targets, 9), (left_targets, 7)]
        else:  # Black
            # right: -7, left: -9
            right_targets = ((pawn_bb & ~pychess.BB_FILE_H) >> 7) & diag_targets
            left_targets = ((pawn_bb & ~pychess.BB_FILE_A) >> 9) & diag_targets
            shifts = [(right_targets, -7), (left_targets, -9)]

        attkr_pt_idx = 0  # PAWN
        for targets, delta in shifts:
            temp = targets
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                temp &= temp - 1
                from_sq = to_sq - delta
                attkd_piece = board.piece_at(to_sq)
                if attkd_piece is None:
                    continue
                attkd_pt_idx = attkd_piece.piece_type - 1
                slot = THREAT_MAP[attkr_pt_idx][attkd_pt_idx]
                if slot >= 0:
                    attkr_from_o = orient_hm(persp_c, from_sq, ksq)
                    attkd_to_o = orient_hm(persp_c, to_sq, ksq)
                    attkr_c = c
                    attkd_c = 0 if attkd_piece.color == pychess.WHITE else 1
                    if persp_c == 1:
                        attkr_c ^= 1
                        attkd_c ^= 1
                    attacker_key = attkr_c * 5 + attkr_pt_idx
                    enemy = attkr_c != attkd_c
                    if not (
                        attkr_pt_idx == attkd_pt_idx
                        and (enemy or attkr_pt_idx != 0)
                        and attkr_from_o < attkd_to_o
                    ):
                        attacks = pychess.BB_PAWN_ATTACKS[
                            pychess.WHITE if attkr_c == 0 else pychess.BLACK
                        ][attkr_from_o]
                        rank_below = ((1 << attkd_to_o) - 1) & attacks
                        idx = int(
                            THREAT_OFFSETS[attacker_key, 65]
                            + (attkd_c * (NUM_VALID_TARGETS[attkr_pt_idx] // 2) + slot)
                            * THREAT_OFFSETS[attacker_key, 64]
                            + THREAT_OFFSETS[attacker_key, attkr_from_o]
                            + bin(rank_below).count("1")
                        )
                        features.append(idx)

        # Knights, Bishops, Rooks, Queens
        for pt in (pychess.KNIGHT, pychess.BISHOP, pychess.ROOK, pychess.QUEEN):
            pt_idx = pt - 1
            attkr_bb = int(board.pieces(pt, pychess.WHITE if c == 0 else pychess.BLACK))
            temp_attkr = attkr_bb
            while temp_attkr:
                from_sq = (temp_attkr & -temp_attkr).bit_length() - 1
                temp_attkr &= temp_attkr - 1
                att = int(board.attacks(from_sq)) & non_king_pieces
                temp_att = att
                while temp_att:
                    to_sq = (temp_att & -temp_att).bit_length() - 1
                    temp_att &= temp_att - 1
                    attkd_piece = board.piece_at(to_sq)
                    if attkd_piece is None:
                        continue
                    attkd_pt_idx = attkd_piece.piece_type - 1
                    slot = THREAT_MAP[pt_idx][attkd_pt_idx]
                    if slot < 0:
                        continue
                    attkr_from_o = orient_hm(persp_c, from_sq, ksq)
                    attkd_to_o = orient_hm(persp_c, to_sq, ksq)
                    attkr_c = c
                    attkd_c = 0 if attkd_piece.color == pychess.WHITE else 1
                    if persp_c == 1:
                        attkr_c ^= 1
                        attkd_c ^= 1
                    enemy = attkr_c != attkd_c
                    if (
                        pt_idx == attkd_pt_idx
                        and (enemy or pt_idx != 0)
                        and attkr_from_o < attkd_to_o
                    ):
                        continue
                    attacker_key = attkr_c * 5 + pt_idx
                    attacks = pseudo_attacks(pt, attkr_from_o)
                    rank_below = ((1 << attkd_to_o) - 1) & attacks
                    idx = int(
                        THREAT_OFFSETS[attacker_key, 65]
                        + (attkd_c * (NUM_VALID_TARGETS[pt_idx] // 2) + slot)
                        * THREAT_OFFSETS[attacker_key, 64]
                        + THREAT_OFFSETS[attacker_key, attkr_from_o]
                        + bin(rank_below).count("1")
                    )
                    features.append(idx)

    # 2. PP_3Wide (inputs: 4560, offset: 59808)
    pp_offset = 59808
    for c in colors_order:
        pawn_bb = int(
            board.pieces(pychess.PAWN, pychess.WHITE if c == 0 else pychess.BLACK)
        )
        temp = pawn_bb
        while temp:
            from_sq = (temp & -temp).bit_length() - 1
            temp &= temp - 1
            f = from_sq % 8
            file_mask = pychess.BB_FILES[f]
            if f > 0:
                file_mask |= pychess.BB_FILES[f - 1]
            if f < 7:
                file_mask |= pychess.BB_FILES[f + 1]
            targets_mask = (
                file_mask & ~pychess.BB_RANK_1 & ~pychess.BB_RANK_8 & ~(1 << from_sq)
            ) & all_pawns

            temp_tgt = targets_mask
            while temp_tgt:
                to_sq = (temp_tgt & -temp_tgt).bit_length() - 1
                temp_tgt &= temp_tgt - 1
                if from_sq >= to_sq:
                    continue
                paired_color = 0 if board.color_at(to_sq) == pychess.WHITE else 1

                from_o = orient_hm(persp_c, from_sq, ksq)
                to_o = orient_hm(persp_c, to_sq, ksq)
                c_o = c ^ persp_c
                paired_c_o = paired_color ^ persp_c

                if 8 <= from_o <= 55 and 8 <= to_o <= 55:
                    id_a = 48 * c_o + (from_o - 8)
                    id_b = 48 * paired_c_o + (to_o - 8)
                    hi = max(id_a, id_b)
                    lo = min(id_a, id_b)
                    idx = pp_offset + hi * (hi - 1) // 2 + lo
                    features.append(idx)

    # 3. HalfKAv2_hm^ (inputs: 24576, offset: 64368)
    halfka_offset = 64368
    o_ksq = orient_halfka(is_white_pov, ksq, ksq)
    k_bucket = KING_BUCKETS[o_ksq]

    for sq, piece in board.piece_map().items():
        pt_idx = piece.piece_type - 1
        p_idx = pt_idx * 2 + (1 if piece.color != (persp_c == 0) else 0)
        o_sq = orient_halfka(is_white_pov, sq, ksq)
        idx = halfka_offset + o_sq + p_idx * 64 + k_bucket * 768
        features.append(idx)

    # 4. LatentThreats (inputs: 12288, offset: 88944)
    lt_offset = 88944
    ksq_us = ksq
    ksq_them = board.king(pychess.BLACK if is_white_pov else pychess.WHITE)
    us_color = pychess.WHITE if is_white_pov else pychess.BLACK
    them_color = pychess.BLACK if is_white_pov else pychess.WHITE

    if include_latent_threats and ksq_them is not None:

        def get_slider_blockers(
            attacker_color: pychess.Color, target_k: int
        ) -> tuple[int, int]:
            bishops = int(board.pieces(pychess.BISHOP, attacker_color))
            rooks = int(board.pieces(pychess.ROOK, attacker_color))
            queens = int(board.pieces(pychess.QUEEN, attacker_color))
            occupied = int(board.occupied)

            diag_snipers = pseudo_attacks(pychess.BISHOP, target_k) & (bishops | queens)
            orth_snipers = pseudo_attacks(pychess.ROOK, target_k) & (rooks | queens)
            snipers = diag_snipers | orth_snipers

            all_blockers = 0
            pinners = 0
            temp_snipers = snipers
            while temp_snipers:
                sniper_sq = (temp_snipers & -temp_snipers).bit_length() - 1
                temp_snipers &= temp_snipers - 1
                blockers = pychess.between(sniper_sq, target_k) & occupied
                if blockers and (blockers & (blockers - 1)) == 0:
                    all_blockers |= blockers
                    pinners |= 1 << sniper_sq
            return all_blockers, pinners

        # 1. Process Absolute Pins against OUR King (K_target = 0)
        pinned_us, pinners_them = get_slider_blockers(them_color, ksq_us)
        temp_pinned = pinned_us
        while temp_pinned:
            p_sq = (temp_pinned & -temp_pinned).bit_length() - 1
            temp_pinned &= temp_pinned - 1
            line_pinners = pychess.ray(ksq_us, p_sq) & pinners_them
            if not line_pinners:
                continue
            s_sq = (line_pinners & -line_pinners).bit_length() - 1
            pinner_pt = board.piece_type_at(s_sq)
            if pinner_pt is None:
                continue
            type_idx = (
                0
                if pinner_pt == pychess.BISHOP
                else (1 if pinner_pt == pychess.ROOK else 2)
            )

            oriented_k = orient_hm(persp_c, ksq_us, ksq_us)
            oriented_p = orient_hm(persp_c, p_sq, ksq_us)
            s_k = king_square_hm_index(oriented_k)
            s_p = oriented_p
            idx = (
                lt_offset + (0 * 3 * 32 * 64) + (type_idx * 32 * 64) + (s_k * 64) + s_p
            )
            features.append(idx)

        # 2. Process Skewers / X-Rays against OPPONENT King (K_target = 1)
        pinned_them, pinners_us = get_slider_blockers(us_color, ksq_them)
        temp_pinned = pinned_them
        while temp_pinned:
            p_sq = (temp_pinned & -temp_pinned).bit_length() - 1
            temp_pinned &= temp_pinned - 1
            line_pinners = pychess.ray(ksq_them, p_sq) & pinners_us
            if not line_pinners:
                continue
            s_sq = (line_pinners & -line_pinners).bit_length() - 1
            pinner_pt = board.piece_type_at(s_sq)
            if pinner_pt is None:
                continue
            type_idx = (
                0
                if pinner_pt == pychess.BISHOP
                else (1 if pinner_pt == pychess.ROOK else 2)
            )

            oriented_k = orient_hm(opp_persp_c, ksq_them, ksq_them)
            oriented_p = orient_hm(opp_persp_c, p_sq, ksq_them)
            s_k = king_square_hm_index(oriented_k)
            s_p = oriented_p
            idx = (
                lt_offset + (1 * 3 * 32 * 64) + (type_idx * 32 * 64) + (s_k * 64) + s_p
            )
            features.append(idx)

    return features


# ── NNUE Evaluator Class ────────────────────────────────────────────────────


class NNUEEvaluator(_IEvaluatorBase):  # type: ignore[misc]
    """Custom NNUE Evaluator loading weights directly from `.nnue` binary."""

    VERSION = 0x6A448AFA

    def __init__(
        self, net_path: str = "latent_threats.nnue", device: str = "cpu"
    ) -> None:
        """Initialize the NNUE evaluator, loading weights from binary."""
        super().__init__()
        self.device = torch.device(device)
        self.net_path = net_path

        if not os.path.isabs(net_path):
            candidates = [
                net_path,
                os.path.join(os.getcwd(), net_path),
                os.path.join(
                    os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    ),
                    net_path,
                ),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    self.net_path = c
                    break

        if not os.path.isfile(self.net_path):
            raise FileNotFoundError(f"NNUE network file not found at: {self.net_path}")

        self._load_network(self.net_path)

    def _load_network(self, file_path: str) -> None:
        """Parse the LEB128-compressed .nnue binary."""
        with open(file_path, "rb") as f:
            v = struct.unpack("<I", f.read(4))[0]
            if v != self.VERSION:
                raise ValueError(f"Unsupported NNUE version: 0x{v:08X}")
            _net_hash = struct.unpack("<I", f.read(4))[0]
            desc_len = struct.unpack("<I", f.read(4))[0]
            self.description = f.read(desc_len).decode("utf-8")
            _ft_hash = struct.unpack("<I", f.read(4))[0]

            def read_tensor(dtype: Any, shape: tuple[int, ...]) -> np.ndarray:
                pos = f.tell()
                magic = f.read(17)
                count = reduce(operator.mul, shape, 1)
                if magic == b"COMPRESSED_LEB128":
                    byte_len = struct.unpack("<I", f.read(4))[0]
                    raw_bytes = f.read(byte_len)
                    arr = decode_leb128(raw_bytes, count).astype(np.float32)
                else:
                    f.seek(pos)
                    arr = np.fromfile(f, dtype, count).astype(np.float32)
                return arr.reshape(shape)

            # Feature Transformer Biases (1024 int16s, 8 PSQT zeros)
            bias_l1 = read_tensor(np.int16, (1024,)) / 256.0
            bias = np.zeros(1032, dtype=np.float32)
            bias[:1024] = bias_l1

            # Features:
            # Full_Threats (59808)
            ft_w = read_tensor(np.int8, (59808, 1024)) / 256.0
            ft_p = read_tensor(np.int32, (59808, 8)) / 9600.0
            w_full = np.concatenate([ft_w, ft_p], axis=1)

            # PP_3Wide (4560)
            pp_w = read_tensor(np.int8, (4560, 1024)) / 256.0
            pp_p = read_tensor(np.int32, (4560, 8)) / 9600.0
            w_pp = np.concatenate([pp_w, pp_p], axis=1)

            # HalfKAv2_hm^ (stored as 22528, expand to 24576)
            hk_w = read_tensor(np.int16, (22528, 1024)) / 256.0
            hk_p = read_tensor(np.int32, (22528, 8)) / 9600.0
            w_hk_export = np.concatenate([hk_w, hk_p], axis=1)

            w_hk = np.zeros((24576, 1032), dtype=np.float32)
            for b in range(32):
                src_offset = b * 704
                dst_offset = b * 768
                w_hk[dst_offset : dst_offset + 640] = w_hk_export[
                    src_offset : src_offset + 640
                ]
                src_king = src_offset + 10 * 64
                ksq = INVERSE_KING_BUCKETS[b]
                w_hk[dst_offset + 10 * 64 + ksq] = w_hk_export[src_king + ksq]
                w_hk[dst_offset + 11 * 64 : dst_offset + 12 * 64] = w_hk_export[
                    src_king : src_king + 64
                ]
                w_hk[dst_offset + 11 * 64 + ksq] = 0.0

            # LatentThreats (12288)
            lt_w = read_tensor(np.int8, (12288, 1024)) / 256.0
            lt_p = read_tensor(np.int32, (12288, 8)) / 9600.0
            w_lt = np.concatenate([lt_w, lt_p], axis=1)

            merged_weights = np.concatenate([w_full, w_pp, w_hk, w_lt], axis=0)
            self.ft_weights = torch.from_numpy(merged_weights).to(self.device)
            self.ft_bias = torch.from_numpy(bias).to(self.device)

            # Layer Stacks (8 buckets)
            self.l1_weights = []
            self.l1_biases = []
            self.l2_weights = []
            self.l2_biases = []
            self.out_weights = []
            self.out_biases = []

            for _b in range(8):
                _fc_h = struct.unpack("<I", f.read(4))[0]
                b_l1 = read_tensor(np.int32, (32,)) / 16384.0
                w_l1 = read_tensor(np.int8, (32, 1024)) / 128.0

                b_l2 = read_tensor(np.int32, (32,)) / 8192.0
                w_l2 = read_tensor(np.int8, (32, 64)) / 64.0

                b_out = read_tensor(np.int32, (1,)) / 16384.0
                w_out = read_tensor(np.int8, (1, 128)) / 128.0

                self.l1_weights.append(torch.from_numpy(w_l1).to(self.device))
                self.l1_biases.append(torch.from_numpy(b_l1).to(self.device))
                self.l2_weights.append(torch.from_numpy(w_l2).to(self.device))
                self.l2_biases.append(torch.from_numpy(b_l2).to(self.device))
                self.out_weights.append(torch.from_numpy(w_out).to(self.device))
                self.out_biases.append(torch.from_numpy(b_out).to(self.device))

    def _extract_features(self, board: pychess.Board, is_white_pov: bool) -> list[int]:
        """Return active feature indices for *board* from the given perspective.

        Override in subclasses to plug in a different feature set without
        duplicating the quantized forward pass.
        """
        return extract_features(board, is_white_pov)

    @torch.no_grad()
    def evaluate_board(self, board: pychess.Board) -> float:
        """Evaluate a position from White's perspective in centipawns."""
        w_indices = self._extract_features(board, is_white_pov=True)
        b_indices = self._extract_features(board, is_white_pov=False)

        if not w_indices or not b_indices:
            return 0.0

        w_idx_tensor = torch.tensor(w_indices, dtype=torch.long, device=self.device)
        b_idx_tensor = torch.tensor(b_indices, dtype=torch.long, device=self.device)

        wp = self.ft_weights[w_idx_tensor].sum(dim=0) + self.ft_bias
        bp = self.ft_weights[b_idx_tensor].sum(dim=0) + self.ft_bias

        w, wpsqt = wp[:1024], wp[1024:]
        b, bpsqt = bp[:1024], bp[1024:]

        num_pieces = bin(int(board.occupied)).count("1")
        bucket = min(7, max(0, (num_pieces - 1) // 4))
        w_psqt_val = wpsqt[bucket]
        b_psqt_val = bpsqt[bucket]

        is_white_stm = board.turn == pychess.WHITE
        l0_ = torch.cat([w, b], dim=0) if is_white_stm else torch.cat([b, w], dim=0)

        l0_ = torch.clamp(l0_, 0.0, 255.0 / 256.0)

        # Pairwise multiplication
        l0_out = torch.cat(
            [l0_[:512] * l0_[512:1024], l0_[1024:1536] * l0_[1536:2048]], dim=0
        )
        l0_out = torch.floor(l0_out * 128.0 + 1e-5) / 128.0

        # L1
        l1c = F.linear(l0_out, self.l1_weights[bucket], self.l1_biases[bucket])
        l1_skip = l1c[-2] - l1c[-1]
        l1_sqr = torch.floor(torch.pow(l1c, 2.0) * 128.0 + 1e-5) / 128.0
        l1x = torch.floor(l1c * 128.0 + 1e-5) / 128.0
        l1_act = torch.clamp(torch.cat([l1_sqr, l1x], dim=0), 0.0, 127.0 / 128.0)

        # L2
        l2c = F.linear(l1_act, self.l2_weights[bucket], self.l2_biases[bucket])
        l2_sqr = torch.floor(torch.pow(l2c, 2.0) * 128.0 + 1e-5) / 128.0
        l2x = torch.floor(l2c * 128.0 + 1e-5) / 128.0
        l2_act = torch.clamp(torch.cat([l2_sqr, l2x], dim=0), 0.0, 127.0 / 128.0)

        # Output
        l3_in = torch.cat([l1_act, l2_act], dim=0)
        l3c = F.linear(l3_in, self.out_weights[bucket], self.out_biases[bucket])

        l3x = l3c[0] + l1_skip
        fwd_out_int = torch.round(l3x * 32768.0).to(torch.int64)
        output_value_int = torch.div(fwd_out_int * 9600, 32768, rounding_mode="trunc")
        l3x = output_value_int.to(torch.float32) / 9600.0

        us_val = 1.0 if is_white_stm else 0.0
        x = l3x + (w_psqt_val - b_psqt_val) * (us_val - 0.5)

        stm_score = float(x.item() * 600.0)
        # Return White-perspective score
        return stm_score if is_white_stm else -stm_score

    def go(self, board: Board | pychess.Board) -> float:
        """Fulfill the IEvaluator contract."""
        pyc_board = (
            board if isinstance(board, pychess.Board) else pychess.Board(board.fen())
        )
        return self.evaluate_board(pyc_board)


CustomNNUEEvaluator = NNUEEvaluator
