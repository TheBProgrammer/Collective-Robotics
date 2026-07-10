FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake g++ git pkg-config \
        libfreeimage-dev libfreeimageplus-dev \
        freeglut3-dev libxi-dev libxmu-dev \
        liblua5.3-dev lua5.3 \
        qtbase5-dev libqt5opengl5-dev \
        doxygen graphviz libgraphviz-dev asciidoc xmlto \
        python3 python3-pip python3-tk \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pandas matplotlib numpy scipy

ARG ARGOS_REF=3.0.0-beta59
RUN git clone --depth 1 --branch ${ARGOS_REF} https://github.com/ilpincy/argos3.git /tmp/argos3 \
    && mkdir /tmp/argos3/build \
    && cd /tmp/argos3/build \
    && cmake -DCMAKE_BUILD_TYPE=Release ../src \
    && make -j"$(nproc)" \
    && (make man 2>/dev/null || touch argos3.1.gz) \
    && mkdir -p /tmp/argos3/doc/api/standalone /tmp/argos3/doc/api/queryable \
    && touch /tmp/argos3/build/README.html /tmp/argos3/build/RELEASE_NOTES.html /tmp/argos3/build/COMPILING.html \
    && make install \
    && ldconfig \
    && rm -rf /tmp/argos3

# The foraging loop functions are compiled from the mounted work directory by
# `./run_docker.sh loop`, so that editing foraging_loop.cpp does not require
# rebuilding this image.

WORKDIR /work
CMD ["/bin/bash"]
