# CLAUDE.md - AI Assistant Development Guide

## Project Overview

**Educational Multi-Language Hello World** is an interactive CLI program demonstrating "Hello World" in 4 programming languages (C, C++, Rust, x86-64 Assembly). It features live code reveal animations, syntax highlighting, and performance metrics.

### Purpose
- Educational tool for comparing programming languages
- Demonstrates compilation and execution workflows
- Provides visual learning experience with animations and metrics

### Technology Stack
- **Python 3**: Main orchestrator and UI framework
- **Rich Library**: Terminal UI, syntax highlighting, progress bars, live displays
- **System Compilers**: gcc (C), g++ (C++), rustc (Rust), nasm+ld (Assembly)

---

## Repository Structure

```
/home/user/hello_asm/
├── educational_hello.py       # Main program with animations and 2x2 layout
├── multi_lang_hello.py        # Simple version without animations
├── README.md                  # User-facing documentation
├── CLAUDE.md                  # This file - AI assistant guide
├── .gitignore                 # Git exclusions (workspace directories)
└── educational_hello_workspace/   # Runtime directory (gitignored)
└── multi_lang_hello_workspace/    # Runtime directory (gitignored)
```

### Key Files

#### educational_hello.py (Main Program)
- **Lines**: 381
- **Features**:
  - 2x2 grid layout (C/C++ top row, Rust/Assembly bottom row)
  - Live code reveal animations (line-by-line)
  - 4-step process: walkthrough → compilation → execution → metrics
  - Rich library integration for beautiful terminal UI
  - Performance timing for write/compile/run operations
  - Monokai theme syntax highlighting
  - Progress bars with time tracking

#### multi_lang_hello.py (Simple Version)
- **Lines**: 215
- **Features**:
  - Basic orchestrator without animations
  - Sequential processing of each language
  - Simple text output with timing
  - Includes Python in addition to the 4 main languages

---

## Code Architecture

### Design Patterns

#### 1. Data Classes (educational_hello.py)
```python
@dataclass
class LanguageSpec:
    name: str
    filename: str
    syntax: str
    code_lines: List[str]
    compile_cmds: List[Sequence[str]]
    run_cmd: Sequence[str]

@dataclass
class LanguageState:
    visible_lines: List[str]
    status: str
    stdout: str
    stderr: str
    failed: bool
    timings: Dict[str, float]
```

**Purpose**: Immutable configuration (LanguageSpec) separated from mutable runtime state (LanguageState)

#### 2. Language Configuration

The `LANGUAGES` list contains specs for:
1. **C** - Uses stdio.h, gcc compiler
2. **C++** - Uses iostream, g++ compiler
3. **Rust** - Uses rustc compiler
4. **Assembly** - Uses nasm assembler + ld linker (x86-64)

**Educational Notes**: Each language's code includes inline comments explaining key concepts (e.g., "// Immutable greeting text", "// syscall: write")

#### 3. Step-Based Execution

The educational version follows a 4-step workflow:
1. **Step 1 - Code Walkthrough**: Reveal code line-by-line with animations
2. **Step 2 - Compilation Progress**: Write files and compile with progress bars
3. **Step 3 - Execution**: Run binaries and capture output
4. **Step 4 - Performance Metrics**: Display timing breakdowns

### Key Functions

#### Subprocess Management
- `run_subprocess(cmd, cwd)`: Execute commands with timing and error handling
- Returns: `(success: bool, elapsed: float, stdout: str, stderr: str)`

#### File Operations
- `write_source_file(spec, workspace)`: Write language source files
- `cleanup_workspace(workspace)`: Remove temporary files

#### UI Rendering
- `build_language_panel(spec, state, step_name)`: Create individual language panels
- `render_layout(step_key, title, caption, states, progress)`: Compose full UI layout

---

## Development Conventions

### Code Style
- **Type Hints**: Use throughout (Python 3.7+ style)
- **Dataclasses**: Prefer over dictionaries for structured data
- **Constants**: UPPER_CASE for module-level constants
- **Functions**: snake_case naming
- **Line Length**: Rich console auto-detects terminal width and multiplies by 1.8x

### Error Handling
- Graceful degradation: failures in one language don't stop others
- Capture both stdout and stderr for diagnostics
- State tracking: `failed: bool` flag in LanguageState
- Detailed error messages displayed in panels

### Terminal UI Patterns
- **Live Display**: Use `rich.live.Live` for animated updates
- **Progress Bars**: Track compilation steps with Rich Progress
- **Panels**: Bordered containers with colored titles
- **Tables**: 2x2 grid layout for language comparison
- **Syntax Highlighting**: Monokai theme for code display

---

## Dependencies

### Required System Tools
```bash
# Compilers (required for execution)
gcc           # C compiler
g++           # C++ compiler
rustc         # Rust compiler
nasm          # Netwide Assembler (x86-64)
ld            # GNU linker (for assembly)
```

### Python Dependencies
```bash
pip install rich  # Rich library for terminal UI
```

**Version Info**:
- Python 3 (any recent version)
- Rich library (tested with latest versions)

### Installation Check
```bash
# Verify compilers
gcc --version
g++ --version
rustc --version
nasm -version

# Verify Python dependency
python3 -c "import rich; print(rich.__version__)"
```

---

## Workspace Management

### Runtime Directories
- `educational_hello_workspace/`: Created during execution of educational_hello.py
- `multi_lang_hello_workspace/`: Created during execution of multi_lang_hello.py

### Lifecycle
1. **Pre-execution**: Cleanup existing workspace if present
2. **During execution**: Create workspace, write source files, compile, execute
3. **Post-execution**: Cleanup workspace (removed automatically)

### Gitignore
Both workspace directories are gitignored to prevent temporary build artifacts from being committed.

---

## Language-Specific Implementation Notes

### C (hello.c)
```c
#include <stdio.h>
int main(void) {
    const char *message = "Hello World";
    puts(message);
    return 0;
}
```
- Compilation: `gcc hello.c -o hello_c`
- Note: Uses `puts()` for simplicity (auto-adds newline)

### C++ (hello.cpp)
```cpp
#include <iostream>
#include <string>
int main() {
    std::string message = "Hello World";
    std::cout << message << std::endl;
    return 0;
}
```
- Compilation: `g++ hello.cpp -o hello_cpp`
- Note: Uses std::string for modern C++ style

### Rust (hello.rs)
```rust
fn main() {
    let message = "Hello World";
    println!("{message}");
}
```
- Compilation: `rustc hello.rs -o hello_rust`
- Note: Demonstrates Rust's string slice and macro syntax

### x86-64 Assembly (hello.asm)
```nasm
section .data
    msg db "Hello World", 10
    len equ $ - msg

section .text
    global _start

_start:
    mov rax, 1       ; syscall: write
    mov rdi, 1       ; fd: stdout
    mov rsi, msg     ; buffer
    mov rdx, len     ; count
    syscall

    mov rax, 60      ; syscall: exit
    xor rdi, rdi     ; status: 0
    syscall
```
- Compilation: Two steps
  1. `nasm -f elf64 hello.asm -o hello.o` (assemble)
  2. `ld hello.o -o hello_asm` (link)
- Note: Direct Linux syscalls (write=1, exit=60)

---

## Testing & Execution

### Running the Programs

#### Educational Version (Recommended)
```bash
python3 educational_hello.py
```
**Expected Behavior**:
- Animated line-by-line code reveal (~0.3s per line)
- Progress bars during compilation
- 2x2 grid layout with colored panels
- Performance metrics at the end
- Auto-cleanup of workspace

#### Simple Version
```bash
python3 multi_lang_hello.py
```
**Expected Behavior**:
- Sequential processing (Python → C → C++ → Rust → Assembly)
- Simple text output with timestamps
- No animations

### Success Criteria
All languages should output: `Hello World`

### Common Issues

#### Missing Compiler
```
FileNotFoundError: [Errno 2] No such file or directory: 'rustc'
```
**Solution**: Install the missing compiler (see Dependencies section)

#### Rich Library Missing
```
ModuleNotFoundError: No module named 'rich'
```
**Solution**: `pip install rich`

#### Terminal Width Issues
- The program auto-detects terminal width
- Minimum recommended: 120 columns for optimal layout
- Multiplier: 1.8x terminal width for code visibility

---

## Development Workflows

### Git Workflow

#### Current Branch
```bash
# Check current branch
git status

# Current: claude/claude-md-mi4g5vbh9dw3f0gl-01SVNzZW74zqrBmRY8r7mjL7
```

#### Making Changes
1. Develop on the designated claude/* branch
2. Commit with descriptive messages
3. Push to origin: `git push -u origin <branch-name>`

#### Commit History
```
b34703d Add comprehensive README
ada49da Initial commit: Educational multi-language Hello World
```

### Adding New Languages

To add a new language to the educational version:

1. **Define LanguageSpec**:
   ```python
   LanguageSpec(
       name="NewLang",
       filename="hello.ext",
       syntax="lexer_name",  # Pygments lexer name
       code_lines=[...],      # With educational comments
       compile_cmds=[...],    # List of command tuples
       run_cmd=(...),         # Execution command tuple
   )
   ```

2. **Update Layout**: Modify `render_layout()` if changing grid structure

3. **Test Execution**: Ensure compiler is available in environment

4. **Update README**: Document new language and requirements

---

## AI Assistant Guidelines

### When Working on This Project

#### DO:
- ✅ Preserve the existing architecture (LanguageSpec/LanguageState pattern)
- ✅ Maintain type hints for all function signatures
- ✅ Keep educational comments in language code samples
- ✅ Test changes with actual compiler execution
- ✅ Update both README.md and CLAUDE.md for significant changes
- ✅ Use Rich library patterns consistently (Live, Panel, Progress)
- ✅ Handle errors gracefully (don't crash on missing compilers)
- ✅ Maintain workspace cleanup in finally blocks

#### DON'T:
- ❌ Remove or simplify educational comments in code samples
- ❌ Break the 4-step execution model without discussion
- ❌ Add dependencies without documenting them
- ❌ Change terminal width calculations without testing
- ❌ Skip error handling for subprocess calls
- ❌ Commit workspace directories to git
- ❌ Remove timing/metrics features

### Code Modification Patterns

#### Adding a Feature
1. Check if it fits the educational mission
2. Consider impact on visual layout
3. Test with all 4 languages
4. Update documentation
5. Verify workspace cleanup still works

#### Fixing a Bug
1. Reproduce the issue
2. Identify affected language(s)
3. Test fix with `educational_hello.py`
4. Verify simple version (`multi_lang_hello.py`) still works
5. Update error handling if needed

#### Refactoring
1. Preserve external behavior
2. Keep dataclass structure
3. Maintain type safety
4. Run both versions to verify
5. Check that all 4 languages still compile and run

### Testing Checklist

Before committing changes:
- [ ] `python3 educational_hello.py` runs successfully
- [ ] All 4 languages compile without errors
- [ ] All 4 languages output "Hello World"
- [ ] Performance metrics display correctly
- [ ] Workspace cleanup succeeds
- [ ] No new files left in working directory
- [ ] Terminal UI renders correctly (check with different widths)
- [ ] Error handling works (test with missing compiler)

---

## Performance Considerations

### Timing Breakdown

Typical execution times (on modern hardware):
- **Write**: <0.001s per file
- **Compile**:
  - C: 0.1-0.3s
  - C++: 0.2-0.5s
  - Rust: 0.3-1.0s (slower due to LLVM)
  - Assembly: 0.05-0.15s (fast!)
- **Run**: <0.01s per binary
- **Total**: ~2-5s for full execution (including animations)

### Animation Timing
- Line reveal: 0.3s per line (configurable via `time.sleep(0.3)`)
- Live display refresh: 10 FPS (`refresh_per_second=10`)

---

## Future Enhancement Ideas

### Potential Features
- Add more languages (Go, Java, Python, JavaScript/Node.js)
- Interactive mode: let users select languages
- Customizable animations (speed control)
- Export results to HTML/Markdown
- Comparison mode: show ASM output side-by-side
- Educational quiz mode
- Support for custom "Hello World" messages

### Architecture Improvements
- Configuration file for languages (YAML/JSON)
- Plugin system for language support
- Parallel compilation (use multiprocessing)
- Caching compiled binaries

---

## Key Files Reference

### educational_hello.py Line References
- **Lines 21-37**: Core dataclass definitions
- **Lines 39-45**: Language color scheme
- **Lines 47-123**: Language specifications with educational code
- **Lines 133-156**: Subprocess execution with error handling
- **Lines 178-216**: Panel building and UI rendering
- **Lines 218-246**: Layout rendering (2x2 table structure)
- **Lines 248-380**: Main execution loop (4 steps)

### multi_lang_hello.py Line References
- **Lines 11-31**: Assembly source code (direct syscalls)
- **Lines 33-72**: Language dictionaries (includes Python)
- **Lines 94-126**: Command execution with timing
- **Lines 178-191**: Language processing pipeline

---

## Contact & Resources

- **Generated by**: Claude Code (Anthropic)
- **License**: MIT
- **Python Version**: 3.7+
- **Platform**: Linux (x86-64 for assembly)

### External Documentation
- [Rich Library Docs](https://rich.readthedocs.io/)
- [NASM Documentation](https://www.nasm.us/xdoc/2.16.01/html/nasmdoc0.html)
- [Linux Syscall Reference](https://syscalls.w3challs.com/?arch=x86_64)

---

## Changelog

### 2024-11-18
- Initial commit with educational and simple versions
- Comprehensive README added
- CLAUDE.md created for AI assistant guidance

---

**Last Updated**: 2025-11-18
**Document Version**: 1.0
**For AI Assistants**: This document provides comprehensive context for understanding and modifying the codebase. Follow the guidelines above to maintain consistency and educational value.
