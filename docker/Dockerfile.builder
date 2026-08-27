ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG CUDA_ARCH

WORKDIR /build

# Mitsuba/Dr.Jit のコンパイル時にターゲットGPUアーキテクチャを明示し、最適化
ENV CMAKE_ARGS="-DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCH}"

# Submoduleのソースをコピー
COPY third_party/sionna-rt /build/sionna-rt

# 依存関係を含めず、Sionna-RT本体のみをコンパイルしてWheel(.whl)を生成
RUN cd sionna-rt && \
    uv pip install --system build && \
    python -m build --wheel --outdir /wheels

# ※ このイメージは実行には使いません。「/wheels」ディレクトリを取り出すためだけの箱です。
