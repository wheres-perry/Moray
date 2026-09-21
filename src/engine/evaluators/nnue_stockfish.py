"""Stockfish NNUE evaluator for Moray.

Supports loading official Stockfish NNUE networks (such as SFNNv16,
e.g. `nn-134a887f4c8f.nnue` / `stockfish.nnue`) with Full_Threats + PP_3Wide +
HalfKAv2_hm^ architecture (88,944 inputs) and evaluating positions directly inside
the engine.
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

from engine.evaluators.nnue import (
    INVERSE_KING_BUCKETS,
    NNUEEvaluator,
    decode_leb128,
    extract_features,
)

if TYPE_CHECKING:
    from engine._core.moray_core import Board


def extract_sfnnv16_features(board: pychess.Board, is_white_pov: bool) -> list[int]:
    """Extract active feature indices for SFNNv16.

    Feature components: Full_Threats (59,808) + PP_3Wide (4,560) + HalfKAv2_hm^
    (24,576) = 88,944 total input dimensions.

    Args:
        board: A python-chess Board.
        is_white_pov: Whether to evaluate from White's perspective.

    Returns:
        List of active feature indices in [0, 88944).

    """
    return extract_features(board, is_white_pov, include_latent_threats=False)


class StockfishNNUEEvaluator(NNUEEvaluator):
    """Stockfish NNUE Evaluator loading SFNNv16 weights directly from binary."""

    VERSION: int = 0x6A448AFA
    FT_HASH: int = 0xCB685313

    def __init__(
        self,
        net_path: str = "models/stockfish.nnue",
        device: str = "cpu",
    ) -> None:
        """Initialize the Stockfish NNUE evaluator and load weights from binary.

        Args:
            net_path: Path to the .nnue network binary.
            device: PyTorch compute device ('cpu' or 'cuda').

        Raises:
            FileNotFoundError: If the network file is not found.
            ValueError: If the file header or version is unsupported.

        """
        super().__init__(net_path=net_path, device=device)

    def _load_network(self, file_path: str) -> None:
        """Parse the LEB128-compressed SFNNv16 .nnue binary."""
        with open(file_path, "rb") as f:
            v = struct.unpack("<I", f.read(4))[0]
            if v != self.VERSION:
                raise ValueError(
                    f"Unsupported NNUE version: 0x{v:08X} "
                    f"(expected 0x{self.VERSION:08X})"
                )
            _net_hash = struct.unpack("<I", f.read(4))[0]
            desc_len = struct.unpack("<I", f.read(4))[0]
            self.description = f.read(desc_len).decode("utf-8")
            ft_hash = struct.unpack("<I", f.read(4))[0]
            if ft_hash != self.FT_HASH:
                raise ValueError(
                    f"Unsupported FT hash: 0x{ft_hash:08X} "
                    f"(expected SFNNv16 hash 0x{self.FT_HASH:08X})"
                )

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

            # SFNNv16 Features:
            # 1. Full_Threats (59808)
            ft_w = read_tensor(np.int8, (59808, 1024)) / 256.0
            ft_p = read_tensor(np.int32, (59808, 8)) / 9600.0
            w_full = np.concatenate([ft_w, ft_p], axis=1)

            # 2. PP_3Wide (4560)
            pp_w = read_tensor(np.int8, (4560, 1024)) / 256.0
            pp_p = read_tensor(np.int32, (4560, 8)) / 9600.0
            w_pp = np.concatenate([pp_w, pp_p], axis=1)

            # 3. HalfKAv2_hm^ (stored as 22528, expand to 24576)
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

            # Merged feature weights for SFNNv16 (88,944 rows)
            merged_weights = np.concatenate([w_full, w_pp, w_hk], axis=0)
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
        """Extract active SFNNv16 feature indices for *board*."""
        return extract_sfnnv16_features(board, is_white_pov)

    def go(self, board: Board | pychess.Board) -> float:
        """Fulfill the IEvaluator contract."""
        pyc_board = (
            board if isinstance(board, pychess.Board) else pychess.Board(board.fen())
        )
        return self.evaluate_board(pyc_board)
