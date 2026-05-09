FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "train.py"]
