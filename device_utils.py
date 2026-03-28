"""Cross-platform PyTorch device selection (NVIDIA CUDA, Apple MPS, CPU)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch


def get_torch_device() -> "torch.device":
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
