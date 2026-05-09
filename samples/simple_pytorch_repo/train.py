import torch


def main() -> None:
    x = torch.ones((2, 2))
    y = x @ x
    print(y)


if __name__ == "__main__":
    main()
