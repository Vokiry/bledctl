#!/usr/bin/env bash
set -e

install_system() {
    echo "Installing bledctl system-wide..."
    DEST="/usr/local/bin/bledctl"
    SITE_PKG=$(python3 -c "import site; print(site.getsitepackages()[0])")

    rm -rf "$SITE_PKG/bledctl"
    cp -r "$SCRIPT_DIR/bledctl" "$SITE_PKG/"
    chmod -R 755 "$SITE_PKG/bledctl"

    cat > "$DEST" << WRAPPER
#!/usr/bin/env python3
import sys
import site
sys.path.insert(0, site.getsitepackages()[0])
from bledctl.cli import main
if __name__ == "__main__":
    main()
WRAPPER
    chmod +x "$DEST"

    echo "Installed to $DEST"
    echo "Run 'bledctl --help' to start."
}

install_user() {
    echo "Installing bledctl for current user..."
    DEST="$HOME/.local/bin/bledctl"
    SITE_PKG=$(python3 -c "import site; print(site.getusersitepackages())")

    rm -rf "$SITE_PKG/bledctl"
    mkdir -p "$HOME/.local/bin"
    cp -r "$SCRIPT_DIR/bledctl" "$SITE_PKG/"
    chmod -R 755 "$SITE_PKG/bledctl"

    cat > "$DEST" << WRAPPER
#!/usr/bin/env python3
import sys
import site
sys.path.insert(0, site.getusersitepackages())
from bledctl.cli import main
if __name__ == "__main__":
    main()
WRAPPER
    chmod +x "$DEST"

    echo "Installed to $DEST"
    echo "Add $HOME/.local/bin to your PATH if not already present."
    echo "Run 'bledctl --help' to start."
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" = "--user" ]; then
    install_user
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: ./install.sh [--user]"
    echo "  (no flag)  Install system-wide (requires sudo)"
    echo "  --user     Install for current user only"
else
    if [ -w "/usr/local/bin" ]; then
        install_system
    else
        echo "No write permission to /usr/local/bin."
        echo "Run './install.sh --user' to install for current user."
        exit 1
    fi
fi
