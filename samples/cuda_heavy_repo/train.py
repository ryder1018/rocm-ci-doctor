import os

import torch


def main() -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    device = torch.device("cuda")
    model_input = torch.ones((1024, 1024)).cuda()
    result = model_input.to("cuda") @ model_input
    print(torch.cuda.get_device_name(device))
    print(result.sum().item())


if __name__ == "__main__":
    main()
