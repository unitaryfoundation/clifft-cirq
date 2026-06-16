# justfile
set shell := ["bash", "-lc"]

default:
  @just --list

test:
  uv run pytest

lint:
  uv run ruff check .

build:
  uv build

# Preview changelog for the next release, for example: just changelog-preview v0.1.0
changelog-preview version:
  git-cliff --github-repo unitaryfoundation/clifft-cirq --tag {{version}} --unreleased

# Generate CHANGELOG.md for the next release, for example: just changelog v0.1.0
changelog version:
  git-cliff --github-repo unitaryfoundation/clifft-cirq --unreleased --tag {{version}} --prepend CHANGELOG.md
  @echo "Updated CHANGELOG.md; review, edit, then commit."
