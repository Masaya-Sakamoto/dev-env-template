ARG BASE_IMAGE=base_image
ARG OS_CODE_NAME=os_code_name
FROM ${BASE_IMAGE}

# Optional: Install the latest version of cmake
RUN sudo apt-get update && sudo apt-get install ca-certificates gpg wget
RUN echo 'deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ ${OS_CODE_NAME} main' | sudo tee /etc/apt/sources.list.d/kitware.list >/dev/null

RUN apt-get update && \
apt-get -y install \
git \
build-essentials \
cmake

# Optional: Install uv
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Optional: Install Nix
# RUN curl -L https://nixos.org/nix/install | sh -s -- --daemon
