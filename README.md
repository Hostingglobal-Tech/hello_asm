# Educational Multi-Language Hello World

An interactive CLI program that demonstrates "Hello World" in 4 programming languages (C, C++, Rust, x86-64 Assembly) with live code reveal animations, syntax highlighting, and performance metrics.

## ✨ Features

- **2x2 Grid Layout**: Displays all 4 languages simultaneously
  - Top row: C, C++
  - Bottom row: Rust, Assembly
- **Live Code Reveal**: Line-by-line animation showing code as it's being "written" (0.3s per line)
- **Syntax Highlighting**: Beautiful Monokai theme using Rich library with Pygments
- **Performance Metrics**: Real-time tracking of write, compile, and execution times
- **4-Step Process**:
  1. **Code Walkthrough** - Line-by-line reveal with educational comments
  2. **Compilation Progress** - Live progress bars with time tracking
  3. **Execution** - Run all binaries and capture output
  4. **Performance Metrics** - Detailed timing breakdown for each language

## 🎯 Project Versions

This project includes two versions:

1. **educational_hello.py** (Recommended) - Full-featured with animations and 2x2 layout
2. **multi_lang_hello.py** - Simple version with sequential processing and includes Python

## 📋 Requirements

### System Compilers

```bash
# Install C/C++ compilers and assembler
sudo apt-get update
sudo apt-get install -y gcc g++ nasm

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Python Dependencies

```bash
# Python 3 (usually pre-installed)
python3 --version

# Install Rich library for terminal UI
pip install rich
```

### Verify Installation

```bash
gcc --version      # GNU C Compiler
g++ --version      # GNU C++ Compiler
rustc --version    # Rust Compiler
nasm -version      # Netwide Assembler
python3 -c "import rich; print(rich.__version__)"  # Rich library
```

## 🚀 Usage

### Educational Version (Recommended)

```bash
python3 educational_hello.py
```

**What you'll see:**
- Animated line-by-line code reveal (~5 seconds)
- 2x2 grid layout with colored panels
- Live compilation progress bars
- Execution results for all 4 languages
- Performance metrics dashboard

**Expected output:**
```
Step 1 • Code Walkthrough ✍️
Step 2 • Compilation Progress ⚙️
Step 3 • Execution 🎬
Step 4 • Performance Metrics ⏱

🏁 Total elapsed time: ~7.0s
🧹 Workspace cleanup successful
```

### Simple Version

```bash
python3 multi_lang_hello.py
```

**Features:**
- Sequential processing (Python → C → C++ → Rust → Assembly)
- Simple text output with timing
- No animations or special UI
- Includes Python as a bonus language

## 📸 Output Example

The educational version displays:

```
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃         C            ┃        C++           ┃
┣━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━┫
┃ Syntax-highlighted   ┃ Syntax-highlighted   ┃
┃ code with comments   ┃ code with comments   ┃
┃ ✅ Execution success ┃ ✅ Execution success ┃
┃ stdout: Hello World  ┃ stdout: Hello World  ┃
┃ ⏱ write: 0.001s     ┃ ⏱ write: 0.000s     ┃
┃    compile: 0.187s   ┃    compile: 1.134s   ┃
┃    run: 0.006s       ┃    run: 0.008s       ┃
┃    total: 0.193s     ┃    total: 1.142s     ┃
┗━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━┛
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃        Rust          ┃      Assembly        ┃
┗━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━┛
```

## 💻 Implementation Details

### Languages

| Language | Compiler | Key Features | Compilation Steps |
|----------|----------|--------------|-------------------|
| **C** | gcc | `stdio.h`, `puts()` | 1 step: gcc hello.c -o hello_c |
| **C++** | g++ | `iostream`, `std::string` | 1 step: g++ hello.cpp -o hello_cpp |
| **Rust** | rustc | `println!()` macro, immutable bindings | 1 step: rustc hello.rs -o hello_rust |
| **Assembly** | nasm+ld | Direct Linux syscalls (write=1, exit=60) | 2 steps: nasm → ld |

### Code Structure

Each language demonstrates:
- ✅ Basic "Hello World" output
- ✅ Educational inline comments explaining key concepts
- ✅ Proper exit codes (return 0 or exit syscall)
- ✅ Modern best practices for each language

### Performance Benchmarks

Based on actual execution (your mileage may vary):

| Language | Write Time | Compile Time | Run Time | Total Time |
|----------|-----------|--------------|----------|------------|
| C | <0.001s | ~0.19s | ~0.006s | **~0.19s** ⚡ |
| C++ | <0.001s | ~1.13s | ~0.008s | **~1.14s** |
| Rust | <0.001s | ~0.40s | ~0.007s | **~0.41s** 🦀 |
| Assembly | <0.001s | ~0.05s | ~0.005s | **~0.05s** 🚀 |

**Key Insights:**
- Assembly is fastest (when nasm is installed)
- C is very fast to compile and execute
- Rust is 3x faster to compile than C++
- C++ has the longest compile time (LLVM overhead)

### Terminal Width

The program auto-detects terminal width and multiplies it by 1.8x for better code visibility.
**Recommended**: At least 120 columns for optimal layout.

## 🛠️ Technical Stack

- **Python 3.7+**: Main orchestrator and control flow
- **Rich 14.2.0+**: Terminal UI, syntax highlighting, progress bars, live displays
- **GCC**: C compilation
- **G++**: C++ compilation
- **rustc**: Rust compilation
- **NASM + ld**: x86-64 assembly compilation and linking
- **Pygments**: Syntax highlighting (via Rich)
- **Dataclasses**: Type-safe configuration and state management

## 🎓 Educational Value

This project is perfect for:
- **Learning multiple programming languages** side-by-side
- **Understanding compilation workflows** (interpreted vs compiled)
- **Comparing language performance** in real-time
- **Teaching systems programming** (especially assembly syscalls)
- **Demonstrating Rich library capabilities** for Python CLI apps

## 🐛 Troubleshooting

### Rich library not found
```bash
pip install rich
# or
pip3 install rich
```

### Compiler not found
```bash
# For C/C++
sudo apt-get install build-essential

# For Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# For Assembly
sudo apt-get install nasm
```

### Terminal too narrow
The program requires at least 80 columns. Resize your terminal or run:
```bash
stty size  # Check current terminal size
```

## 📁 Project Structure

```
hello_asm/
├── educational_hello.py       # Main program (381 lines)
├── multi_lang_hello.py        # Simple version (215 lines)
├── README.md                  # This file
├── CLAUDE.md                  # AI assistant development guide
├── .gitignore                 # Excludes workspace directories
└── *_workspace/               # Auto-generated (gitignored)
```

## 🤝 Contributing

Contributions are welcome! Some ideas:
- Add more languages (Go, Java, JavaScript, Python, etc.)
- Improve animations and UI
- Add interactive mode for language selection
- Export results to HTML/Markdown
- Add educational quiz mode

## 📄 License

MIT License - Feel free to use, modify, and distribute!

## 👤 Author

Generated with [Claude Code](https://claude.com/claude-code) by Anthropic

## 🔗 Resources

- [Rich Library Documentation](https://rich.readthedocs.io/)
- [NASM Documentation](https://www.nasm.us/doc/)
- [Linux Syscall Reference](https://syscalls.w3challs.com/?arch=x86_64)
- [Rust Book](https://doc.rust-lang.org/book/)

---

⭐ If you find this project useful, please consider starring it on GitHub!
