# Every toolchain the skill's evaluation fixtures need, so the evals run the same way
# on any machine and stay sandboxed in the container (see SECURITY.md).
# Base: the dev container project's Ubuntu image (non-root user "vscode").
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG SWIFT_VERSION=6.2

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
       openjdk-21-jdk-headless \
       ruby-full \
       python3 python3-pip python3-venv \
       build-essential clang gdb \
       curl ca-certificates git jq unzip \
       binutils libc6-dev libcurl4-openssl-dev libedit2 libgcc-13-dev libpython3-dev \
       libsqlite3-0 libstdc++-13-dev libxml2-dev libncurses-dev libz3-dev pkg-config tzdata zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
