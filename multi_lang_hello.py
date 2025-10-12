#!/usr/bin/env python3

import shlex
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

ASM_SOURCE = textwrap.dedent(
    """\
    section .data
        msg db "Hello World", 10
        len equ $ - msg

    section .text
        global _start

    _start:
        mov rax, 1
        mov rdi, 1
        mov rsi, msg
        mov rdx, len
        syscall

        mov rax, 60
        xor rdi, rdi
        syscall
    """
)

LANGUAGES = [
    {
        "name": "Python",
        "filename": "hello.py",
        "source": 'print("Hello World")\n',
        "compile_cmds": [],
        "run_cmd": ["python3", "hello.py"],
    },
    {
        "name": "C",
        "filename": "hello.c",
        "source": '#include <stdio.h>\nint main(void){puts("Hello World");return 0;}\n',
        "compile_cmds": [["gcc", "hello.c", "-o", "hello_c"]],
        "run_cmd": ["./hello_c"],
    },
    {
        "name": "C++",
        "filename": "hello.cpp",
        "source": '#include <iostream>\nint main(){std::cout<<"Hello World\\n";}\n',
        "compile_cmds": [["g++", "hello.cpp", "-o", "hello_cpp"]],
        "run_cmd": ["./hello_cpp"],
    },
    {
        "name": "Rust",
        "filename": "hello.rs",
        "source": 'fn main(){println!("Hello World");}\n',
        "compile_cmds": [["rustc", "hello.rs", "-o", "hello_rust"]],
        "run_cmd": ["./hello_rust"],
    },
    {
        "name": "x86-64 Assembly",
        "filename": "hello.asm",
        "source": ASM_SOURCE,
        "compile_cmds": [
            ["nasm", "-f", "elf64", "hello.asm", "-o", "hello.o"],
            ["ld", "hello.o", "-o", "hello_asm"],
        ],
        "run_cmd": ["./hello_asm"],
    },
]


def format_cmd(cmd):
    if isinstance(cmd, (list, tuple)):
        parts = [str(part) for part in cmd]
        try:
            return shlex.join(parts)
        except AttributeError:
            return " ".join(parts)
    return str(cmd)


def print_stream(label, data):
    if not data:
        print(f"    {label}: <empty>")
        return
    print(f"    {label}:")
    for line in data.rstrip().splitlines():
        print(f"      {line}")


def run_command(label, cmd, cwd, show_output=False):
    cmd_list = [str(part) for part in cmd]
    start = time.time()
    try:
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        elapsed = time.time() - start
        print(f"  [{label}] {format_cmd(cmd_list)} ({elapsed:.4f}s)")
        if show_output or result.stdout:
            print_stream("stdout", result.stdout)
        if result.stderr:
            print_stream("stderr", result.stderr)
        return True, elapsed
    except FileNotFoundError as exc:
        elapsed = time.time() - start
        print(f"  [{label} FAILED] {format_cmd(cmd_list)} ({elapsed:.4f}s)")
        print(f"    error: {exc}")
        return False, elapsed
    except subprocess.CalledProcessError as exc:
        elapsed = time.time() - start
        print(f"  [{label} FAILED] {format_cmd(cmd_list)} ({elapsed:.4f}s)")
        if exc.stdout:
            print_stream("stdout", exc.stdout)
        if exc.stderr:
            print_stream("stderr", exc.stderr)
        return False, elapsed


def write_source_file(lang, workspace):
    path = workspace / lang["filename"]
    start = time.time()
    try:
        path.write_text(lang["source"], encoding="utf-8")
        elapsed = time.time() - start
        print(f"  [create] {lang['filename']} ({elapsed:.4f}s)")
        return True
    except OSError as exc:
        elapsed = time.time() - start
        print(f"  [create FAILED] {lang['filename']} ({elapsed:.4f}s)")
        print(f"    error: {exc}")
        return False


def run_compile_steps(lang, workspace):
    success = True
    for cmd in lang.get("compile_cmds", []):
        ok, _ = run_command("compile", cmd, workspace)
        if not ok:
            success = False
            break
    return success


def run_execution(lang, workspace):
    run_command("run", lang["run_cmd"], workspace, show_output=True)


def cleanup_workspace(path, silent=False):
    if not path.exists():
        return True
    try:
        shutil.rmtree(path)
        return True
    except OSError as exc:
        if not silent:
            print(f"Cleanup error for {path}: {exc}")
        return False


def print_header(workspace):
    title = "Multi-language Hello World Orchestrator"
    underline = "=" * len(title)
    print(underline)
    print(title)
    print(underline)
    print(f"Workspace: {workspace}")


def process_language(lang, workspace):
    banner = f" {lang['name']} "
    print(f"\n{banner:-^60}")
    if not write_source_file(lang, workspace):
        return
    compile_cmds = lang.get("compile_cmds") or []
    if compile_cmds:
        if not run_compile_steps(lang, workspace):
            print("  [run] skipped due to compilation failure")
            return
    else:
        print("  [compile] not required")
    run_execution(lang, workspace)


def main():
    workspace = Path.cwd() / "multi_lang_hello_workspace"
    cleanup_workspace(workspace, silent=True)
    workspace.mkdir(parents=True, exist_ok=True)

    print_header(workspace)

    total_start = time.time()
    try:
        for lang in LANGUAGES:
            process_language(lang, workspace)
    finally:
        total_elapsed = time.time() - total_start
        print(f"\nTotal elapsed time: {total_elapsed:.4f}s")
        cleaned = cleanup_workspace(workspace)
        status = "ok" if cleaned else "failed"
        print(f"Workspace cleanup ({workspace}): {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
