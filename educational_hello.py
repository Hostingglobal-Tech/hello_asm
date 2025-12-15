#!/usr/bin/env python3

import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

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
    visible_lines: List[str] = field(default_factory=list)
    status: str = "⏳ Waiting"
    stdout: str = ""
    stderr: str = ""
    failed: bool = False
    timings: Dict[str, float] = field(default_factory=dict)

LANGUAGE_COLORS = {
    "Python": "bright_green",
    "C": "cyan",
    "C++": "magenta",
    "Rust": "orange1",
    "Assembly": "yellow",
}

LANGUAGES: List[LanguageSpec] = [
    LanguageSpec(
        name="C",
        filename="hello.c",
        syntax="c",
        code_lines=[
            '#include <stdio.h>  // Bring in standard I/O declarations',
            '',
            'int main(void) {  // Program entry point',
            '    const char *message = "Hello World";  // Immutable greeting text',
            '    puts(message);  // Print the message with a newline',
            '    return 0;  // Signal successful completion to the OS',
            '}  // End of main',
        ],
        compile_cmds=[("gcc", "hello.c", "-o", "hello_c")],
        run_cmd=("./hello_c",),
    ),
    LanguageSpec(
        name="C++",
        filename="hello.cpp",
        syntax="cpp",
        code_lines=[
            '#include <iostream>  // Access std::cout for output',
            '#include <string>   // Use std::string for readable text',
            '',
            'int main() {  // Program entry point',
            '    std::string message = "Hello World";  // Store the greeting',
            '    std::cout << message << std::endl;  // Print with newline',
            '    return 0;  // Indicate successful completion',
            '}  // End of main',
        ],
        compile_cmds=[("g++", "hello.cpp", "-o", "hello_cpp")],
        run_cmd=("./hello_cpp",),
    ),
    LanguageSpec(
        name="Rust",
        filename="hello.rs",
        syntax="rust",
        code_lines=[
            'fn main() {  // Rust entry point',
            '    let message = "Hello World";  // Immutable string slice',
            '    println!("{message}");  // Macro prints with newline',
            '}  // End of main',
        ],
        compile_cmds=[("rustc", "hello.rs", "-o", "hello_rust")],
        run_cmd=("./hello_rust",),
    ),
    LanguageSpec(
        name="Assembly",
        filename="hello.asm",
        syntax="nasm",
        code_lines=[
            'section .data                  ; Define the data segment',
            '    msg db "Hello World", 10    ; Greeting followed by newline',
            '    len equ $ - msg            ; Compute the message length',
            '',
            'section .text                  ; Begin the code segment',
            '    global _start              ; Declare the entry symbol',
            '',
            '_start:                        ; Program entry point',
            '    mov rax, 1                 ; syscall: write',
            '    mov rdi, 1                 ; file descriptor: stdout',
            '    mov rsi, msg               ; pointer to message',
            '    mov rdx, len               ; number of bytes to write',
            '    syscall                    ; perform the write',
            '',
            '    mov rax, 60                ; syscall: exit',
            '    xor rdi, rdi               ; return code 0',
            '    syscall                    ; terminate program',
        ],
        compile_cmds=[
            ("nasm", "-f", "elf64", "hello.asm", "-o", "hello.o"),
            ("ld", "hello.o", "-o", "hello_asm"),
        ],
        run_cmd=("./hello_asm",),
    ),
]

WORKSPACE = Path.cwd() / "educational_hello_workspace"

terminal_size = shutil.get_terminal_size()
console = Console(width=int(terminal_size.columns * 1.8))  # Auto-detect terminal width and multiply by 1.8

def format_timing(value: float) -> str:
    return f"{value:.3f}s"

def run_subprocess(cmd: Sequence[str], cwd: Path) -> Tuple[bool, float, str, str]:
    start = time.time()
    try:
        result = subprocess.run(
            tuple(str(part) for part in cmd),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        elapsed = time.time() - start
        stdout_text = result.stdout.strip()
        stderr_text = result.stderr.strip()
        return True, elapsed, stdout_text, stderr_text
    except FileNotFoundError as exc:
        elapsed = time.time() - start
        return False, elapsed, "", str(exc)
    except subprocess.CalledProcessError as exc:
        elapsed = time.time() - start
        stdout_text = (exc.stdout or "").strip()
        stderr_text = (exc.stderr or "").strip()
        return False, elapsed, stdout_text, stderr_text

def write_source_file(spec: LanguageSpec, workspace: Path) -> Tuple[bool, float, str]:
    start = time.time()
    path = workspace / spec.filename
    try:
        source = "\n".join(spec.code_lines) + "\n"
        path.write_text(source, encoding="utf-8")
        elapsed = time.time() - start
        return True, elapsed, ""
    except OSError as exc:
        elapsed = time.time() - start
        return False, elapsed, str(exc)

def cleanup_workspace(workspace: Path) -> bool:
    if not workspace.exists():
        return True
    try:
        shutil.rmtree(workspace)
        return True
    except OSError:
        return False

def build_language_panel(spec: LanguageSpec, state: LanguageState, step_name: str) -> Panel:
    code_text = "\n".join(state.visible_lines)
    if code_text:
        syntax = Syntax(
            code_text,
            spec.syntax,
            theme="monokai",
            line_numbers=True,
            word_wrap=False,  # Disable word wrap for better readability
        )
        code_renderable = syntax
    else:
        code_renderable = Align.center(Text("… awaiting reveal …", style="dim"), vertical="middle")
    status_lines: List[Text] = []
    status_lines.append(Text(state.status, style="bold"))
    if state.stdout:
        status_lines.append(Text(f"stdout: {state.stdout}", style="green"))
    if state.stderr:
        status_lines.append(Text(f"stderr: {state.stderr}", style="red"))
    if step_name == "Step 4":
        timing_parts = []
        for label in ("write", "compile", "run"):
            if label in state.timings:
                timing_parts.append(f"{label}: {format_timing(state.timings[label])}")
        if timing_parts:
            status_lines.append(Text(" ⏱  " + " | ".join(timing_parts), style="cyan"))
        if "total" in state.timings:
            status_lines.append(Text(f" total: {format_timing(state.timings['total'])}", style="yellow"))
    body = Group(
        code_renderable,
        Rule(style="dim"),
        *(Align.left(line) for line in status_lines),
    )
    panel = Panel(
        body,
        title=f"[bold]{spec.name}[/bold]",
        border_style=LANGUAGE_COLORS.get(spec.name, "white"),
    )
    return panel

def render_layout(step_key: str, step_title: str, step_caption: str, states: List[LanguageState], progress: Optional[Progress] = None) -> Group:
    header = Panel(
        Text(step_title, justify="center", style="bold white on blue"),
        subtitle=step_caption,
        subtitle_align="left",
    )

    # Build all panels
    panels = [build_language_panel(spec, state, step_key) for spec, state in zip(LANGUAGES, states)]

    renderables = [header]

    # First table: C and C++ (top row)
    table1 = Table(expand=True, show_header=True, header_style="bold")
    table1.add_column(LANGUAGES[0].name, justify="center", ratio=1)  # C
    table1.add_column(LANGUAGES[1].name, justify="center", ratio=1)  # C++
    table1.add_row(panels[0], panels[1])
    renderables.append(table1)

    # Second table: Rust and Assembly (bottom row)
    table2 = Table(expand=True, show_header=True, header_style="bold")
    table2.add_column(LANGUAGES[2].name, justify="center", ratio=1)  # Rust
    table2.add_column(LANGUAGES[3].name, justify="center", ratio=1)  # Assembly
    table2.add_row(panels[2], panels[3])
    renderables.append(table2)

    if progress is not None:
        renderables.append(progress)
    return Group(*renderables)

def main() -> int:
    total_start = time.time()
    states = [LanguageState() for _ in LANGUAGES]
    cleanup_workspace(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    step_key = "Step 1"
    step_title = "Step 1 • Code Walkthrough ✍️"
    step_caption = "Revealing each language line-by-line with helpful notes."
    with Live(
        render_layout(step_key, step_title, step_caption, states),
        console=console,
        refresh_per_second=10,
    ) as live:
        max_lines = max(len(spec.code_lines) for spec in LANGUAGES)
        for line_index in range(max_lines):
            for spec_index, spec in enumerate(LANGUAGES):
                if line_index < len(spec.code_lines):
                    states[spec_index].visible_lines.append(spec.code_lines[line_index])
                    states[spec_index].status = f"📝 Revealed line {line_index + 1} / {len(spec.code_lines)}"
            live.update(render_layout(step_key, step_title, step_caption, states))
            time.sleep(0.3)
        for state in states:
            state.status = "✅ Source ready"
        live.update(render_layout(step_key, step_title, step_caption, states))
        step_key = "Step 2"
        step_title = "Step 2 • Compilation Progress ⚙️"
        step_caption = "Writing files and compiling each language with live progress."
        progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(bar_width=None, pulse_style="magenta"),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        progress.start()
        task_meta: List[Tuple[int, int]] = []
        for spec in LANGUAGES:
            total_steps = 1 + len(spec.compile_cmds)
            task_id = progress.add_task(f"📦 {spec.name}", total=total_steps)
            task_meta.append((task_id, total_steps))
        live.update(render_layout(step_key, step_title, step_caption, states, progress))
        for index, spec in enumerate(LANGUAGES):
            state = states[index]
            task_id, total_steps = task_meta[index]
            state.status = "🗂️ Writing source file"
            live.update(render_layout(step_key, step_title, step_caption, states, progress))
            ok, elapsed, error_message = write_source_file(spec, WORKSPACE)
            state.timings["write"] = elapsed
            progress.advance(task_id)
            if not ok:
                state.status = f"❌ Write failed: {error_message}"
                state.stderr = error_message
                state.failed = True
                progress.update(task_id, completed=total_steps)
                live.update(render_layout(step_key, step_title, step_caption, states, progress))
                continue
            if not spec.compile_cmds:
                state.timings["compile"] = 0.0
                state.status = "✅ Ready to interpret"
                live.update(render_layout(step_key, step_title, step_caption, states, progress))
                progress.update(task_id, completed=total_steps)
                continue
            compile_time = 0.0
            for cmd_index, cmd in enumerate(spec.compile_cmds, start=1):
                state.status = f"⚙️ Compiling ({cmd_index}/{len(spec.compile_cmds)})"
                live.update(render_layout(step_key, step_title, step_caption, states, progress))
                ok, elapsed, stdout_text, stderr_text = run_subprocess(cmd, WORKSPACE)
                compile_time += elapsed
                if not ok:
                    state.status = "❌ Compilation error"
                    state.stderr = stderr_text or stdout_text
                    state.failed = True
                    progress.update(task_id, completed=total_steps)
                    live.update(render_layout(step_key, step_title, step_caption, states, progress))
                    break
                progress.advance(task_id)
                if stdout_text:
                    state.stdout = stdout_text
                if stderr_text:
                    state.stderr = stderr_text
            if state.failed:
                state.timings["compile"] = compile_time
                continue
            state.timings["compile"] = compile_time
            state.status = "✅ Compilation complete"
            progress.update(task_id, completed=total_steps)
            live.update(render_layout(step_key, step_title, step_caption, states, progress))
        progress.refresh()
        progress.stop()
        step_key = "Step 3"
        step_title = "Step 3 • Execution 🎬"
        step_caption = "Running each hello-world and capturing the output."
        live.update(render_layout(step_key, step_title, step_caption, states))
        for index, spec in enumerate(LANGUAGES):
            state = states[index]
            if state.failed:
                state.status = "⛔ Skipped due to earlier error"
                continue
            state.status = "🚀 Executing binary"
            live.update(render_layout(step_key, step_title, step_caption, states))
            ok, elapsed, stdout_text, stderr_text = run_subprocess(spec.run_cmd, WORKSPACE)
            state.timings["run"] = elapsed
            if ok:
                state.status = "✅ Execution succeeded"
                state.stdout = stdout_text or "<no output>"
                state.stderr = stderr_text
            else:
                state.status = "❌ Execution error"
                state.stderr = stderr_text or stdout_text or "Execution failed"
                state.failed = True
            live.update(render_layout(step_key, step_title, step_caption, states))
        step_key = "Step 4"
        step_title = "Step 4 • Performance Metrics ⏱"
        step_caption = "Reviewing time spent writing, compiling, and running each language."
        for state in states:
            total = sum(state.timings.values())
            if total:
                state.timings["total"] = total
            if not state.failed and "compile" not in state.timings:
                state.timings.setdefault("compile", 0.0)
        live.update(render_layout(step_key, step_title, step_caption, states))
    total_elapsed = time.time() - total_start
    cleaned = cleanup_workspace(WORKSPACE)
    console.print()
    console.print(f"🏁 Total elapsed time: {format_timing(total_elapsed)}")
    if cleaned:
        console.print(f"🧹 Workspace cleanup successful: {WORKSPACE}")
    else:
        console.print(f"⚠️ Failed to delete workspace: {WORKSPACE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
