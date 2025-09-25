#!/bin/bash
# Install pre-commit hook script that runs `make fmt` before commits.

set -e

echo "Preparing to install pre-commit hook..."

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "✗ Not in a git repository"
    exit 1
fi

# Get git hooks directory
GIT_HOOKS_DIR=$(git rev-parse --git-dir)/hooks

# Create hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Check if ruff is available via poetry (optional check)
if poetry run ruff --version >/dev/null 2>&1; then
    echo "✓ ruff available: $(poetry run ruff --version)"
else
    echo "Warning: ruff not available via poetry, but continuing anyway..."
fi

# Path to the pre-commit hook
HOOK_PATH="$GIT_HOOKS_DIR/pre-commit"

# Remove existing hook if it exists
if [ -f "$HOOK_PATH" ]; then
    echo "Removing existing pre-commit hook: $HOOK_PATH"
    rm "$HOOK_PATH"
else
    echo "No existing pre-commit hook found"
fi

# Create the pre-commit hook
echo "Installing pre-commit hook: $HOOK_PATH"
cat > "$HOOK_PATH" << 'EOF'
#!/bin/sh
# Pre-commit hook that runs make fmt
echo "Running make fmt..."
make fmt
if [ $? -ne 0 ]; then
    echo "make fmt failed. Commit aborted."
    exit 1
fi
EOF

# Make it executable
chmod +x "$HOOK_PATH"

echo "✓ Pre-commit hook installation complete!"