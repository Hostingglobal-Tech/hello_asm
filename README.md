# Educational Multi-Language Hello World

An interactive CLI program that demonstrates "Hello World" in 4 programming languages (C, C++, Rust, x86-64 Assembly) with live code reveal animations, syntax highlighting, and performance metrics.

## Features

- **2x2 Layout**: Displays code in a grid format
  - Top row: C, C++
  - Bottom row: Rust, Assembly
- **Live Code Reveal**: Line-by-line animation showing code as it's being "written"
- **Syntax Highlighting**: Beautiful Monokai theme using Rich library
- **Performance Metrics**: Tracks time for write, compile, and run operations
- **4-Step Process**:
  1. Code Walkthrough (line-by-line reveal)
  2. Compilation Progress (with progress bars)
  3. Execution
  4. Performance Metrics

## Requirements

```bash
# Install required compilers
sudo apt-get update
sudo apt-get install gcc g++ nasm

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Python dependencies
pip install rich
```

## Usage

### Educational Version (Recommended)

```bash
python3 educational_hello.py
```

Features a beautiful 2x2 layout with live animations and detailed comments.

### Simple Version

```bash
python3 multi_lang_hello.py
```

Basic orchestrator without animations.

## Screenshots

The program displays:
- Syntax-highlighted code with educational comments
- Real-time compilation progress bars
- Execution output for each language
- Performance timing breakdown

## Implementation Details

### Languages

1. **C**: Uses `stdio.h` and `puts()` for output
2. **C++**: Uses `iostream` and `std::cout` with `std::string`
3. **Rust**: Uses `println!()` macro with string slices
4. **Assembly**: Direct x86-64 syscalls (write and exit)

### Terminal Width

The program auto-detects terminal width and multiplies it by 1.8x for better code visibility.

## Technical Stack

- **Python 3**: Main orchestrator
- **Rich Library**: Terminal UI, syntax highlighting, progress bars
- **GCC/G++**: C/C++ compilation
- **rustc**: Rust compilation
- **NASM + ld**: Assembly compilation and linking

## License

MIT License

## Author

Generated with [Claude Code](https://claude.com/claude-code)
