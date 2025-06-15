#!/bin/bash
set -e

# Install rust first
curl https://sh.rustup.rs -sSf | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"

# Then install your requirements
pip install -r requirements.txt
