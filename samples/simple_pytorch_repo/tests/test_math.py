import torch


def test_tensor_math() -> None:
    assert torch.ones(1).item() == 1
