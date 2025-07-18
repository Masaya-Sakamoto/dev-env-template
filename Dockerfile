ARG BASE_IMAGE=base_image
ARG OS_CODE_NAME=os_code_name
FROM ${BASE_IMAGE}

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    gpg \
    wget \
    git \
    build-essential \
    cmake

# # Kitwareリポジトリのセットアップ
# RUN wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | gpg --dearmor - | tee /usr/share/keyrings/kitware-archive-keyring.gpg >/dev/null
# RUN echo "deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ ${OS_CODE_NAME} main" | tee /etc/apt/sources.list.d/kitware.list >/dev/null
# RUN apt-get install kitware-archive-keyring
# RUN apt-get update && apt-get install cmake

COPY scripts/ /tmp/scripts/
RUN chown -R root:root /tmp/scripts/*
RUN chmod +x /tmp/scripts/post-create.sh

RUN mkdir -p /workspace/app && chown -R vscode:vscode /workspace/app

# 再びvscodeユーザーに戻す
USER vscode