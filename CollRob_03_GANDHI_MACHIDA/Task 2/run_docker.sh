#!/usr/bin/env bash
# Helper to run the ARGoS container with the Task 2 folder mounted.
#
# Usage:
#   ./run_docker.sh build                       # build the image
#   ./run_docker.sh gui                         # GUI simulation (X11)
#   ./run_docker.sh headless                    # interactive shell, no X11
#   ./run_docker.sh sim <argos-file>            # run argos3 -c on a file
#   ./run_docker.sh experiments                 # run the full sweep
#   ./run_docker.sh plot                        # generate plots

set -e
IMAGE=collrob-argos:tutorial3
HERE="$(cd "$(dirname "$0")" && pwd)"

case "${1:-headless}" in
    build)
        docker build -t "$IMAGE" "$HERE"
        ;;
    gui)
        xhost +local:root >/dev/null 2>&1 || true
        docker run --rm -it \
            -e DISPLAY="$DISPLAY" \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v "$HERE":/work \
            "$IMAGE" argos3 -c task2.argos
        ;;
    sim)
        shift
        xhost +local:root >/dev/null 2>&1 || true
        docker run --rm -it \
            -e DISPLAY="$DISPLAY" \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v "$HERE":/work \
            "$IMAGE" argos3 -c "$@"
        ;;
    headless)
        docker run --rm -it -v "$HERE":/work "$IMAGE" /bin/bash
        ;;
    experiments)
        docker run --rm -v "$HERE":/work "$IMAGE" python3 run_experiments.py
        ;;
    plot)
        docker run --rm -v "$HERE":/work "$IMAGE" python3 plot_results.py
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 {build|gui|sim <file>|headless|experiments|plot}"
        exit 1
        ;;
esac
