#!/bin/bash
# Career Intelligence Assistant - Quick Start Script
# Run this to get up and running quickly

set -e

echo "🚀 Career Intelligence Assistant - Quick Start"
echo "=============================================="
echo ""

OS_NAME="$(uname -s)"
echo "1️⃣  Detecting OS: $OS_NAME"

# Install Ollama (macOS / Linux). Windows users should run in WSL or install Ollama for Windows.
OLLAMA_BIN=""
if command -v ollama >/dev/null 2>&1; then
    OLLAMA_BIN="$(command -v ollama)"
else
    case "$OS_NAME" in
        Darwin)
            echo "2️⃣  Checking Homebrew..."
            BREW_BIN=""
            if [ -x "/opt/homebrew/bin/brew" ]; then
                BREW_BIN="/opt/homebrew/bin/brew"
            elif [ -x "/usr/local/bin/brew" ]; then
                BREW_BIN="/usr/local/bin/brew"
            fi

            if [ -z "$BREW_BIN" ]; then
                echo "Homebrew not found. Installing..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                if [ -x "/opt/homebrew/bin/brew" ]; then
                    BREW_BIN="/opt/homebrew/bin/brew"
                    eval "$(/opt/homebrew/bin/brew shellenv)"
                elif [ -x "/usr/local/bin/brew" ]; then
                    BREW_BIN="/usr/local/bin/brew"
                    eval "$(/usr/local/bin/brew shellenv)"
                fi
            fi
            echo "✅ Homebrew found: $BREW_BIN"

            echo "3️⃣  Installing Ollama..."
            $BREW_BIN install ollama
            # Ensure PATH includes Homebrew bin
            export PATH="$(dirname "$BREW_BIN"):$PATH"
            ;;
        Linux)
            echo "2️⃣  Installing Ollama (Linux)..."
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "❌ Windows detected. Please install Ollama for Windows or run this script in WSL."
            echo "https://ollama.com/download"
            exit 1
            ;;
        *)
            echo "❌ Unsupported OS: $OS_NAME"
            exit 1
            ;;
    esac
fi

if command -v ollama >/dev/null 2>&1; then
    OLLAMA_BIN="$(command -v ollama)"
elif [ -x "/opt/homebrew/opt/ollama/bin/ollama" ]; then
    OLLAMA_BIN="/opt/homebrew/opt/ollama/bin/ollama"
    export PATH="/opt/homebrew/opt/ollama/bin:$PATH"
elif [ -x "/usr/local/opt/ollama/bin/ollama" ]; then
    OLLAMA_BIN="/usr/local/opt/ollama/bin/ollama"
    export PATH="/usr/local/opt/ollama/bin:$PATH"
else
    echo "❌ Ollama is not on PATH. Please restart your terminal and try again."
    exit 1
fi

echo "✅ Ollama found at: $OLLAMA_BIN"

# Check models
echo ""
echo "4️⃣  Checking Ollama server..."
if ! "$OLLAMA_BIN" list >/dev/null 2>&1; then
    echo "Ollama server not running. Starting..."
    case "$OS_NAME" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                brew services start ollama >/dev/null 2>&1 || true
            fi
            ;;
        Linux)
            "$OLLAMA_BIN" serve >/dev/null 2>&1 &
            ;;
    esac
    sleep 2
fi

echo "5️⃣  Checking Ollama models..."
if ! "$OLLAMA_BIN" list | grep -q "llama3.2"; then
    echo "⏳ Installing llama3.2 (this may take a few minutes)..."
    "$OLLAMA_BIN" pull llama3.2
fi
if ! "$OLLAMA_BIN" list | grep -q "mxbai-embed-large"; then
    echo "⏳ Installing mxbai-embed-large..."
    "$OLLAMA_BIN" pull mxbai-embed-large
fi
echo "✅ Models available"

# Activate venv
echo ""
echo "6️⃣  Setting up Python environment..."
if [ ! -d "venv" ]; then
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv venv
    elif command -v python >/dev/null 2>&1; then
        python -m venv venv
    else
        echo "❌ Python not found. Please install Python 3.9+ and retry."
        exit 1
    fi
fi
source venv/bin/activate
echo "✅ Virtual environment activated"

# Install dependencies
echo ""
echo "7️⃣  Installing Python packages..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Create sample jobs directory
echo ""
echo "8️⃣  Setting up directories..."
mkdir -p sample_jobs
echo "✅ Directories ready"

echo ""
echo "=============================================="
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Add job description PDFs to: ./sample_jobs/"
echo "  2. Run: streamlit run app.py"
echo "  3. Upload your resume and analyze fit"
echo ""
echo "📖 Documentation:"
echo "  - README.md              → Full guide"
echo "  - SETUP.md               → Developer workflows"
echo "  - TROUBLESHOOTING.md     → Common issues"
echo "  - .github/copilot-instructions.md → AI agent guide"
echo ""
echo "🧪 Test installation:"
echo "  - python -c 'import langchain, chromadb, streamlit; print(\"✅ OK\")'"
echo "  - pytest test_rag.py -v"
echo ""
