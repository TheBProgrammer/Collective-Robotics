# Build and run docker container
docker compose build
xhost +local:docker   # allow GUI
docker compose run --rm ros2_jazzy bash