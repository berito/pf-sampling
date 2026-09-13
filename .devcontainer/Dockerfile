# syntax=docker/dockerfile:1
#
# Layers are ordered from rarely changed and slow to often changed and fast, so a change only rebuilds
# the layers after it:
#   1. system packages            (rare, slow)
#   2. heavy Python packages      (rare, slow)   requirements-base.txt
#   3. LaTeX for the report       (rare, slow)
#   4. light Python packages      (often, fast)  requirements.txt   (add new libraries here)
#   5. environment settings       (instant)
# Download caches are kept between builds, so even a rebuilt layer doesn't download everything again.

FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# 1. System packages. The C/C++ toolchain is for gmapping (2000s-era C++ with its own makefiles).
#    New system tools: add a separate RUN line below this one, so this layer stays cached.
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        make \
        cmake \
        pkg-config \
        gdb \
        ffmpeg \
        libx11-6 \
        libgl1 \
        libglib2.0-0

# 2. Heavy Python packages that rarely change.
COPY requirements-base.txt /tmp/requirements-base.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -r /tmp/requirements-base.txt

# 3. LaTeX, to build report/ (make -C report). Large, so it sits before the layers that change often.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        latexmk \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        lmodern \
        texlive-science \
        texlive-bibtex-extra \
        biber

# 4. Light Python packages. Adding a library here rebuilds only this layer and the settings below.
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -r /tmp/requirements.txt

# 5. Environment settings (no files, instant to rebuild).
# Non-interactive matplotlib backend so demos run headless (MPLBACKEND=TkAgg plus an X socket shows windows).
ENV MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    # keep Python from writing __pycache__ into vendor/, so upstream code stays untouched
    PYTHONDONTWRITEBYTECODE=1
