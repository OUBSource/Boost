#!/bin/bash

set -e

# 1. cd to the right directory
cd "$(dirname "$0")"

# 2. Variables
export DEBUG=${DEBUG:-true}
export COMPOSE_BAKE=true
export DOCKER_BUILDKIT=1

# 3. Start Docker Desktop on macOS if not running
if [[ "$OSTYPE" == "darwin"* ]]; then
  if ! docker info >/dev/null 2>&1; then
    echo "Starting Docker Desktop on macOS..."
    docker desktop start
    
    # Wait for Docker to be ready (max 60 seconds)
    echo "Waiting for Docker to be ready..."
    for i in {1..30}; do
      if docker info >/dev/null 2>&1; then
        break
      fi
      echo "Attempt $i/30: Docker not ready yet..."
      sleep 2
    done
    
    if ! docker info >/dev/null 2>&1; then
      echo "Error: Docker did not start within 60 seconds"
      exit 1
    fi
  fi
fi

# 4. Sanity check (not needed until .env is added)
# if ! [[ -e ./.env ]]; then
#   echo "ERROR: .env file is missing."
#   exit 1
# fi

# 5. Build & run

# 5.1. Development
# Note: in development $NURUN is probably always false,
# in production $NORUN is always true. This is not needed
# but still there for flexibility.
if [[ $DEBUG == "true" && $NORUN != "true" ]]; then
  if [[ $NORUN == "true" ]]; then
    docker compose --profile dev build
  else
    docker compose --profile dev up --build --watch --remove-orphans
  fi
# 5.2. Production
else
  docker compose --profile prod build
  if [[ $NORUN != "true" ]]; then
    cd server/scripts || exit
    chmod +x run.sh
    ./run.sh
  fi
fi