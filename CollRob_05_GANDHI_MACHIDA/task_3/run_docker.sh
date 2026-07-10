#!/usr/bin/env bash
# Helper to run the Task 3 foraging experiment in the ARGoS container.
#
# Usage:
#   ./run_docker.sh build         # build the ARGoS image
#   ./run_docker.sh loop          # compile the foraging loop functions (.so)
#   ./run_docker.sh gui           # watch one simulation (needs X11)
#   ./run_docker.sh experiments   # run the full N = 1..10 sweep
#   ./run_docker.sh plot          # generate the figures from data/
#   ./run_docker.sh shell         # interactive shell inside the container

set -e
IMAGE=collrob-argos:tutorial3
HERE="$(cd "$(dirname "$0")" && pwd)"

# A function, not a string: the repository path may contain spaces.
run() {
    docker run --rm -v "$HERE":/work -e ARGOS_PLUGIN_PATH=/work "$IMAGE" "$@"
}

# The loop functions must exist before any simulation can start.
ensure_loop() {
    if [ ! -f "$HERE/libforaging_loop.so" ]; then
        echo "libforaging_loop.so missing -- compiling it first"
        "$0" loop
    fi
}

case "${1:-shell}" in
    build)
        docker build -t "$IMAGE" "$HERE"
        ;;
    loop)
        run bash -c '
            cd /work && g++ -std=c++11 -shared -fPIC -O2 \
                foraging_loop.cpp -o libforaging_loop.so \
                -I/usr/local/include -I/usr/include/lua5.3 \
                -L/usr/local/lib/argos3 \
                -largos3core_simulator -largos3plugin_simulator_entities'
        # the container runs as root; hand the artifact back to the caller
        run chown "$(id -u):$(id -g)" /work/libforaging_loop.so
        echo "built libforaging_loop.so"
        ;;
    gui)
        ensure_loop
        xhost +local:root >/dev/null 2>&1 || true
        docker run --rm -it \
            -e DISPLAY="$DISPLAY" -e ARGOS_PLUGIN_PATH=/work \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v "$HERE":/work \
            "$IMAGE" argos3 -c task3.argos
        ;;
    experiments)
        ensure_loop
        run python3 run_experiments.py
        run chown -R "$(id -u):$(id -g)" /work/data
        ;;
    plot)
        run python3 plot_results.py
        run chown -R "$(id -u):$(id -g)" /work/plots
        ;;
    shell)
        docker run --rm -it -v "$HERE":/work -e ARGOS_PLUGIN_PATH=/work "$IMAGE" /bin/bash
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 {build|loop|gui|experiments|plot|shell}"
        exit 1
        ;;
esac
