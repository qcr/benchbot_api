# Use an official Python runtime as a parent image
FROM nvidia/cuda:8.0-cudnn5-devel-ubuntu16.04
# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    libcurl4-openssl-dev \
    libjsoncpp-dev \
    libopencv-dev \
    python \
    python-pip \
    python3 \
    python3-pip \
    wget \
    git \
    && apt-get clean

RUN mkdir build && cd build && cmake -DCMAKE_INSTALL_PREFIX=/usr .. && make && make install && cd .. && rm -rf build
RUN cd python && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    python setup.py install && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    python3 setup.py install

WORKDIR /
RUN rm -rf /app
