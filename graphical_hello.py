#!/usr/bin/env python3
"""
Graphical Multi-Language Hello World
=====================================
1920x1080 해상도에 최적화된 GUI 버전
4개 언어(C, C++, Rust, Assembly)를 시각적으로 비교

Features:
- 2x2 그리드 레이아웃
- 실시간 컴파일/실행 진행 표시
- 성능 메트릭 차트
- 다크 테마 UI
"""

import subprocess
import shutil
import time
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont

# ==================== 설정 ====================

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1000

# 다크 테마 색상
COLORS = {
    "bg": "#1e1e1e",
    "panel_bg": "#252526",
    "text": "#d4d4d4",
    "accent": "#007acc",
    "success": "#4ec9b0",
    "error": "#f14c4c",
    "warning": "#dcdcaa",
    "c_color": "#00b4d8",
    "cpp_color": "#9d4edd",
    "rust_color": "#ff6b35",
    "asm_color": "#ffd60a",
    "progress_bg": "#3c3c3c",
    "code_bg": "#1e1e1e",
}

# 신택스 하이라이팅 색상
SYNTAX_COLORS = {
    "keyword": "#569cd6",
    "string": "#ce9178",
    "comment": "#6a9955",
    "function": "#dcdcaa",
    "type": "#4ec9b0",
    "number": "#b5cea8",
    "preprocessor": "#c586c0",
}

# ==================== 데이터 클래스 ====================

@dataclass
class LanguageSpec:
    name: str
    filename: str
    color: str
    code: str
    compile_cmds: List[List[str]]
    run_cmd: List[str]
    keywords: List[str]

@dataclass
class LanguageState:
    status: str = "대기 중"
    progress: float = 0.0
    output: str = ""
    error: str = ""
    write_time: float = 0.0
    compile_time: float = 0.0
    run_time: float = 0.0
    total_time: float = 0.0
    failed: bool = False

# ==================== 언어 정의 ====================

LANGUAGES = [
    LanguageSpec(
        name="C",
        filename="hello.c",
        color=COLORS["c_color"],
        code='''#include <stdio.h>

int main(void) {
    // 인사말 메시지 정의
    const char *message = "Hello World";

    // 표준 출력으로 출력
    puts(message);

    return 0;  // 성공적 종료
}''',
        compile_cmds=[["gcc", "hello.c", "-o", "hello_c"]],
        run_cmd=["./hello_c"],
        keywords=["int", "void", "const", "char", "return", "#include"],
    ),
    LanguageSpec(
        name="C++",
        filename="hello.cpp",
        color=COLORS["cpp_color"],
        code='''#include <iostream>
#include <string>

int main() {
    // C++ 문자열 사용
    std::string message = "Hello World";

    // cout으로 출력
    std::cout << message << std::endl;

    return 0;  // 성공적 종료
}''',
        compile_cmds=[["g++", "hello.cpp", "-o", "hello_cpp"]],
        run_cmd=["./hello_cpp"],
        keywords=["int", "return", "std", "#include"],
    ),
    LanguageSpec(
        name="Rust",
        filename="hello.rs",
        color=COLORS["rust_color"],
        code='''fn main() {
    // 불변 문자열 슬라이스
    let message = "Hello World";

    // println! 매크로로 출력
    println!("{}", message);
}''',
        compile_cmds=[["rustc", "hello.rs", "-o", "hello_rust"]],
        run_cmd=["./hello_rust"],
        keywords=["fn", "let", "println"],
    ),
    LanguageSpec(
        name="Assembly",
        filename="hello.asm",
        color=COLORS["asm_color"],
        code='''section .data
    msg db "Hello World", 10
    len equ $ - msg

section .text
    global _start

_start:
    ; write(1, msg, len)
    mov rax, 1      ; syscall: write
    mov rdi, 1      ; stdout
    mov rsi, msg    ; buffer
    mov rdx, len    ; length
    syscall

    ; exit(0)
    mov rax, 60     ; syscall: exit
    xor rdi, rdi    ; status: 0
    syscall''',
        compile_cmds=[
            ["nasm", "-f", "elf64", "hello.asm", "-o", "hello.o"],
            ["ld", "hello.o", "-o", "hello_asm"],
        ],
        run_cmd=["./hello_asm"],
        keywords=["section", "global", "mov", "syscall", "db", "equ", "xor"],
    ),
]

# ==================== 메인 애플리케이션 ====================

class GraphicalHelloApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎓 Educational Multi-Language Hello World")
        self.root.configure(bg=COLORS["bg"])

        # 화면 크기 설정
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # 창 크기 조정 (화면에 맞게)
        width = min(WINDOW_WIDTH, screen_width - 50)
        height = min(WINDOW_HEIGHT, screen_height - 100)

        # 중앙 배치
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(True, True)

        # 워크스페이스 설정
        self.workspace = Path.cwd() / "graphical_hello_workspace"

        # 상태 관리
        self.states: List[LanguageState] = [LanguageState() for _ in LANGUAGES]
        self.panels: List[Dict] = []
        self.running = False

        # 폰트 설정
        self.code_font = tkfont.Font(family="Consolas", size=11)
        self.title_font = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.status_font = tkfont.Font(family="Segoe UI", size=10)

        # UI 구성
        self._create_header()
        self._create_main_content()
        self._create_footer()

    def _create_header(self):
        """헤더 영역 생성"""
        header = tk.Frame(self.root, bg=COLORS["accent"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="🎓 Educational Multi-Language Hello World",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg=COLORS["accent"],
        )
        title.pack(pady=15)

    def _create_main_content(self):
        """메인 콘텐츠 영역 (2x2 그리드)"""
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 그리드 설정
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # 4개 언어 패널 생성
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, (spec, pos) in enumerate(zip(LANGUAGES, positions)):
            panel = self._create_language_panel(main, spec, i)
            panel.grid(row=pos[0], column=pos[1], sticky="nsew", padx=5, pady=5)

    def _create_language_panel(self, parent: tk.Frame, spec: LanguageSpec, index: int) -> tk.Frame:
        """언어별 패널 생성"""
        panel = tk.Frame(parent, bg=COLORS["panel_bg"], relief=tk.RIDGE, bd=2)

        # 제목 바
        title_bar = tk.Frame(panel, bg=spec.color, height=40)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)

        title_label = tk.Label(
            title_bar,
            text=f"  {spec.name}",
            font=self.title_font,
            fg="white",
            bg=spec.color,
            anchor="w",
        )
        title_label.pack(side=tk.LEFT, pady=8)

        # 상태 라벨
        status_label = tk.Label(
            title_bar,
            text="⏳ 대기 중",
            font=self.status_font,
            fg="white",
            bg=spec.color,
        )
        status_label.pack(side=tk.RIGHT, padx=10, pady=8)

        # 코드 영역
        code_frame = tk.Frame(panel, bg=COLORS["code_bg"])
        code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        code_text = scrolledtext.ScrolledText(
            code_frame,
            font=self.code_font,
            bg=COLORS["code_bg"],
            fg=COLORS["text"],
            insertbackground="white",
            relief=tk.FLAT,
            wrap=tk.NONE,
            height=12,
        )
        code_text.pack(fill=tk.BOTH, expand=True)
        code_text.insert(tk.END, spec.code)
        code_text.config(state=tk.DISABLED)

        # 신택스 하이라이팅 적용
        self._apply_syntax_highlighting(code_text, spec)

        # 진행 표시줄
        progress_frame = tk.Frame(panel, bg=COLORS["panel_bg"], height=30)
        progress_frame.pack(fill=tk.X, padx=5, pady=2)
        progress_frame.pack_propagate(False)

        style = ttk.Style()
        style.configure(
            f"{spec.name}.Horizontal.TProgressbar",
            troughcolor=COLORS["progress_bg"],
            background=spec.color,
        )

        progress_bar = ttk.Progressbar(
            progress_frame,
            style=f"{spec.name}.Horizontal.TProgressbar",
            orient=tk.HORIZONTAL,
            mode="determinate",
            maximum=100,
        )
        progress_bar.pack(fill=tk.X, expand=True)

        # 결과/타이밍 영역
        result_frame = tk.Frame(panel, bg=COLORS["panel_bg"], height=80)
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        result_frame.pack_propagate(False)

        output_label = tk.Label(
            result_frame,
            text="출력: -",
            font=self.status_font,
            fg=COLORS["text"],
            bg=COLORS["panel_bg"],
            anchor="w",
        )
        output_label.pack(anchor="w")

        timing_label = tk.Label(
            result_frame,
            text="⏱ Write: - | Compile: - | Run: - | Total: -",
            font=self.status_font,
            fg=COLORS["warning"],
            bg=COLORS["panel_bg"],
            anchor="w",
        )
        timing_label.pack(anchor="w", pady=2)

        # 패널 정보 저장
        self.panels.append({
            "frame": panel,
            "status_label": status_label,
            "code_text": code_text,
            "progress_bar": progress_bar,
            "output_label": output_label,
            "timing_label": timing_label,
        })

        return panel

    def _apply_syntax_highlighting(self, text_widget: scrolledtext.ScrolledText, spec: LanguageSpec):
        """신택스 하이라이팅 적용"""
        text_widget.config(state=tk.NORMAL)

        # 태그 설정
        text_widget.tag_configure("keyword", foreground=SYNTAX_COLORS["keyword"])
        text_widget.tag_configure("string", foreground=SYNTAX_COLORS["string"])
        text_widget.tag_configure("comment", foreground=SYNTAX_COLORS["comment"])
        text_widget.tag_configure("preprocessor", foreground=SYNTAX_COLORS["preprocessor"])
        text_widget.tag_configure("number", foreground=SYNTAX_COLORS["number"])

        content = text_widget.get("1.0", tk.END)

        # 키워드 하이라이팅
        for keyword in spec.keywords:
            start = "1.0"
            while True:
                pos = text_widget.search(keyword, start, tk.END, regexp=False)
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                text_widget.tag_add("keyword", pos, end)
                start = end

        # 문자열 하이라이팅 ("...")
        start = "1.0"
        while True:
            pos = text_widget.search('"', start, tk.END)
            if not pos:
                break
            end_pos = text_widget.search('"', f"{pos}+1c", tk.END)
            if end_pos:
                text_widget.tag_add("string", pos, f"{end_pos}+1c")
                start = f"{end_pos}+1c"
            else:
                break

        # 주석 하이라이팅 (// 또는 ;)
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for comment_char in ['//', ';']:
                if comment_char in line:
                    col = line.index(comment_char)
                    text_widget.tag_add("comment", f"{line_num}.{col}", f"{line_num}.end")
                    break

        # #include, section 등 전처리기
        for prep in ["#include", "section"]:
            start = "1.0"
            while True:
                pos = text_widget.search(prep, start, tk.END)
                if not pos:
                    break
                end = f"{pos}+{len(prep)}c"
                text_widget.tag_add("preprocessor", pos, end)
                start = end

        text_widget.config(state=tk.DISABLED)

    def _create_footer(self):
        """푸터 영역 (컨트롤 버튼)"""
        footer = tk.Frame(self.root, bg=COLORS["bg"], height=60)
        footer.pack(fill=tk.X, pady=10)

        # 버튼 스타일
        btn_style = {
            "font": ("Segoe UI", 12, "bold"),
            "relief": tk.FLAT,
            "cursor": "hand2",
            "width": 15,
            "height": 2,
        }

        # 실행 버튼
        self.run_btn = tk.Button(
            footer,
            text="▶ 실행",
            bg=COLORS["success"],
            fg="white",
            command=self._start_execution,
            **btn_style,
        )
        self.run_btn.pack(side=tk.LEFT, padx=20)

        # 상태 라벨
        self.global_status = tk.Label(
            footer,
            text="준비됨 - '실행' 버튼을 클릭하세요",
            font=("Segoe UI", 11),
            fg=COLORS["text"],
            bg=COLORS["bg"],
        )
        self.global_status.pack(side=tk.LEFT, expand=True)

        # 리셋 버튼
        self.reset_btn = tk.Button(
            footer,
            text="🔄 리셋",
            bg=COLORS["warning"],
            fg="black",
            command=self._reset,
            **btn_style,
        )
        self.reset_btn.pack(side=tk.RIGHT, padx=20)

    def _update_panel(self, index: int, state: LanguageState):
        """패널 UI 업데이트"""
        panel = self.panels[index]
        spec = LANGUAGES[index]

        # 상태 라벨 업데이트
        status_text = state.status
        if state.failed:
            status_text = f"❌ {status_text}"
            panel["status_label"].config(fg=COLORS["error"])
        elif "완료" in status_text or "성공" in status_text:
            status_text = f"✅ {status_text}"
            panel["status_label"].config(fg=COLORS["success"])
        else:
            status_text = f"⏳ {status_text}"
        panel["status_label"].config(text=status_text)

        # 진행 표시줄 업데이트
        panel["progress_bar"]["value"] = state.progress

        # 출력 라벨 업데이트
        if state.output:
            panel["output_label"].config(text=f"출력: {state.output}", fg=COLORS["success"])
        elif state.error:
            panel["output_label"].config(text=f"에러: {state.error[:50]}...", fg=COLORS["error"])

        # 타이밍 라벨 업데이트
        timing_text = f"⏱ Write: {state.write_time:.3f}s | Compile: {state.compile_time:.3f}s | Run: {state.run_time:.3f}s | Total: {state.total_time:.3f}s"
        panel["timing_label"].config(text=timing_text)

    def _run_subprocess(self, cmd: List[str], cwd: Path) -> tuple:
        """서브프로세스 실행"""
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=30,
            )
            elapsed = time.time() - start
            return True, elapsed, result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start
            return False, elapsed, e.stdout or "", e.stderr or str(e)
        except FileNotFoundError as e:
            elapsed = time.time() - start
            return False, elapsed, "", str(e)
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            return False, elapsed, "", "타임아웃 (30초 초과)"

    def _execute_language(self, index: int):
        """단일 언어 실행"""
        spec = LANGUAGES[index]
        state = self.states[index]

        # 1. 소스 파일 작성
        state.status = "소스 파일 작성 중..."
        state.progress = 10
        self.root.after(0, lambda: self._update_panel(index, state))

        start = time.time()
        source_path = self.workspace / spec.filename
        try:
            source_path.write_text(spec.code, encoding="utf-8")
            state.write_time = time.time() - start
        except OSError as e:
            state.status = "파일 작성 실패"
            state.error = str(e)
            state.failed = True
            self.root.after(0, lambda: self._update_panel(index, state))
            return

        state.progress = 25
        self.root.after(0, lambda: self._update_panel(index, state))

        # 2. 컴파일
        if spec.compile_cmds:
            state.status = "컴파일 중..."
            state.progress = 40
            self.root.after(0, lambda: self._update_panel(index, state))

            compile_total = 0.0
            for i, cmd in enumerate(spec.compile_cmds):
                success, elapsed, stdout, stderr = self._run_subprocess(cmd, self.workspace)
                compile_total += elapsed

                if not success:
                    state.status = "컴파일 실패"
                    state.error = stderr or stdout
                    state.failed = True
                    state.compile_time = compile_total
                    state.total_time = state.write_time + state.compile_time
                    self.root.after(0, lambda: self._update_panel(index, state))
                    return

                state.progress = 40 + (30 * (i + 1) / len(spec.compile_cmds))
                self.root.after(0, lambda: self._update_panel(index, state))

            state.compile_time = compile_total

        state.progress = 70
        self.root.after(0, lambda: self._update_panel(index, state))

        # 3. 실행
        state.status = "실행 중..."
        state.progress = 85
        self.root.after(0, lambda: self._update_panel(index, state))

        success, elapsed, stdout, stderr = self._run_subprocess(spec.run_cmd, self.workspace)
        state.run_time = elapsed
        state.total_time = state.write_time + state.compile_time + state.run_time

        if success:
            state.status = "실행 완료"
            state.output = stdout or "(출력 없음)"
            state.progress = 100
        else:
            state.status = "실행 실패"
            state.error = stderr or stdout
            state.failed = True
            state.progress = 100

        self.root.after(0, lambda: self._update_panel(index, state))

    def _start_execution(self):
        """모든 언어 실행 시작"""
        if self.running:
            return

        self.running = True
        self.run_btn.config(state=tk.DISABLED)
        self.global_status.config(text="🚀 실행 중...")

        # 워크스페이스 초기화
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

        # 상태 초기화
        self.states = [LanguageState() for _ in LANGUAGES]

        def run_all():
            total_start = time.time()
            threads = []

            # 병렬 실행
            for i in range(len(LANGUAGES)):
                t = threading.Thread(target=self._execute_language, args=(i,))
                threads.append(t)
                t.start()

            # 모든 스레드 완료 대기
            for t in threads:
                t.join()

            total_elapsed = time.time() - total_start

            # 정리
            try:
                shutil.rmtree(self.workspace)
                cleanup_status = "✅ 정리 완료"
            except:
                cleanup_status = "⚠️ 정리 실패"

            # UI 업데이트
            self.root.after(0, lambda: self._finish_execution(total_elapsed, cleanup_status))

        thread = threading.Thread(target=run_all)
        thread.start()

    def _finish_execution(self, total_time: float, cleanup_status: str):
        """실행 완료 처리"""
        self.running = False
        self.run_btn.config(state=tk.NORMAL)

        # 성공/실패 카운트
        success_count = sum(1 for s in self.states if not s.failed)
        fail_count = len(self.states) - success_count

        status_text = f"🏁 완료! 성공: {success_count}, 실패: {fail_count} | 총 시간: {total_time:.2f}초 | {cleanup_status}"
        self.global_status.config(text=status_text)

    def _reset(self):
        """리셋"""
        if self.running:
            return

        self.states = [LanguageState() for _ in LANGUAGES]

        for i, panel in enumerate(self.panels):
            spec = LANGUAGES[i]
            panel["status_label"].config(text="⏳ 대기 중", fg="white")
            panel["progress_bar"]["value"] = 0
            panel["output_label"].config(text="출력: -", fg=COLORS["text"])
            panel["timing_label"].config(text="⏱ Write: - | Compile: - | Run: - | Total: -")

        self.global_status.config(text="준비됨 - '실행' 버튼을 클릭하세요")

# ==================== 메인 ====================

def main():
    root = tk.Tk()
    app = GraphicalHelloApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
