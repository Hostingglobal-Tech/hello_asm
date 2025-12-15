#!/usr/bin/env python3
"""
Web-based Multi-Language Hello World
=====================================
1920x1080 해상도에 최적화된 웹 브라우저 GUI
Flask + HTML/CSS/JavaScript 기반

실행: python3 web_hello.py
브라우저에서: http://localhost:5050
"""

import subprocess
import shutil
import time
import json
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import webbrowser
import os

# ==================== 설정 ====================

PORT = 5050
WORKSPACE = Path(__file__).parent / "web_hello_workspace"

# ==================== 데이터 클래스 ====================

@dataclass
class LanguageSpec:
    name: str
    filename: str
    color: str
    code: str
    compile_cmds: List[List[str]]
    run_cmd: List[str]
    syntax: str

# ==================== 언어 정의 ====================

LANGUAGES = [
    LanguageSpec(
        name="C",
        filename="hello.c",
        color="#00b4d8",
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
        syntax="c",
    ),
    LanguageSpec(
        name="C++",
        filename="hello.cpp",
        color="#9d4edd",
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
        syntax="cpp",
    ),
    LanguageSpec(
        name="Rust",
        filename="hello.rs",
        color="#ff6b35",
        code='''fn main() {
    // 불변 문자열 슬라이스
    let message = "Hello World";

    // println! 매크로로 출력
    println!("{}", message);
}''',
        compile_cmds=[["rustc", "hello.rs", "-o", "hello_rust"]],
        run_cmd=["./hello_rust"],
        syntax="rust",
    ),
    LanguageSpec(
        name="Assembly",
        filename="hello.asm",
        color="#ffd60a",
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
        syntax="nasm",
    ),
]

# ==================== HTML 템플릿 ====================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1920, height=1080">
    <title>🎓 Educational Multi-Language Hello World</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/vs2015.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/x86asm.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e4e4e4;
        }

        /* 헤더 */
        .header {
            background: linear-gradient(90deg, #007acc, #0099ff);
            padding: 12px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 122, 204, 0.3);
        }

        .header h1 {
            font-size: 1.8em;
            font-weight: 600;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        /* 메인 그리드 */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 15px;
            padding: 15px;
            height: calc(100vh - 140px);
            min-height: 700px;
        }

        /* 언어 패널 */
        .lang-panel {
            background: rgba(30, 30, 30, 0.95);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .lang-panel:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        }

        .panel-header {
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
            font-weight: bold;
            font-size: 1.1em;
        }

        .panel-header .status {
            font-size: 0.85em;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(255,255,255,0.2);
        }

        /* 코드 영역 */
        .code-container {
            flex: 1;
            overflow: auto;
            padding: 12px;
            background: #1e1e1e;
            min-height: 350px;
            max-height: 450px;
        }

        .code-container pre {
            margin: 0;
            font-size: 14px;
            line-height: 1.6;
        }

        .code-container code {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }

        /* 진행 표시줄 */
        .progress-container {
            padding: 8px 15px;
            background: rgba(0,0,0,0.3);
        }

        .progress-bar {
            height: 8px;
            background: #3c3c3c;
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            width: 0%;
            border-radius: 4px;
            transition: width 0.3s ease-out;
        }

        /* 결과 영역 */
        .result-container {
            padding: 12px 15px;
            background: rgba(0,0,0,0.2);
            font-size: 0.9em;
        }

        .result-container .output {
            color: #4ec9b0;
            margin-bottom: 5px;
        }

        .result-container .output.error {
            color: #f14c4c;
        }

        .result-container .timing {
            color: #dcdcaa;
            font-family: monospace;
            font-size: 0.85em;
        }

        /* 푸터 컨트롤 */
        .footer {
            padding: 10px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            background: rgba(0,0,0,0.3);
        }

        .btn {
            padding: 10px 35px;
            font-size: 1em;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .btn-run {
            background: linear-gradient(135deg, #4ec9b0, #3da58a);
            color: white;
        }

        .btn-run:hover:not(:disabled) {
            background: linear-gradient(135deg, #5ed9c0, #4db59a);
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(78, 201, 176, 0.4);
        }

        .btn-reset {
            background: linear-gradient(135deg, #dcdcaa, #bcbc8a);
            color: #1e1e1e;
        }

        .btn-reset:hover:not(:disabled) {
            background: linear-gradient(135deg, #ececa0, #cccc9a);
            transform: scale(1.05);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .global-status {
            font-size: 1.1em;
            min-width: 400px;
            text-align: center;
        }

        /* 애니메이션 */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .running .status {
            animation: pulse 1s infinite;
        }

        /* 성능 차트 영역 */
        .chart-container {
            margin-top: 10px;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }

        .chart-bar {
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 0.8em;
        }

        .chart-label {
            width: 60px;
        }

        .chart-value {
            flex: 1;
            height: 20px;
            background: #3c3c3c;
            border-radius: 4px;
            overflow: hidden;
            margin: 0 10px;
        }

        .chart-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease-out;
        }

        .chart-time {
            width: 70px;
            text-align: right;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 Educational Multi-Language Hello World</h1>
    </div>

    <div class="main-grid" id="mainGrid">
        <!-- 패널들이 JavaScript로 생성됨 -->
    </div>

    <div class="footer">
        <button class="btn btn-run" id="btnRun" onclick="startExecution()">▶ 실행</button>
        <div class="global-status" id="globalStatus">준비됨 - '실행' 버튼을 클릭하세요</div>
        <button class="btn btn-reset" id="btnReset" onclick="resetAll()">🔄 리셋</button>
    </div>

    <script>
        // 언어 데이터
        const languages = LANGUAGES_JSON;

        // 상태 관리
        let states = languages.map(() => ({
            status: '대기 중',
            progress: 0,
            output: '',
            error: '',
            writeTime: 0,
            compileTime: 0,
            runTime: 0,
            totalTime: 0,
            failed: false
        }));

        let isRunning = false;

        // 패널 생성
        function createPanels() {
            const grid = document.getElementById('mainGrid');
            grid.innerHTML = '';

            languages.forEach((lang, idx) => {
                const panel = document.createElement('div');
                panel.className = 'lang-panel';
                panel.id = `panel-${idx}`;
                panel.innerHTML = `
                    <div class="panel-header" style="background: ${lang.color}">
                        <span>${lang.name}</span>
                        <span class="status" id="status-${idx}">⏳ 대기 중</span>
                    </div>
                    <div class="code-container">
                        <pre><code class="language-${lang.syntax}" id="code-${idx}">${escapeHtml(lang.code)}</code></pre>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-${idx}" style="background: ${lang.color}"></div>
                        </div>
                    </div>
                    <div class="result-container">
                        <div class="output" id="output-${idx}">출력: -</div>
                        <div class="timing" id="timing-${idx}">⏱ Write: - | Compile: - | Run: - | Total: -</div>
                    </div>
                `;
                grid.appendChild(panel);
            });

            // 신택스 하이라이팅 적용
            hljs.highlightAll();
        }

        function escapeHtml(text) {
            return text.replace(/&/g, '&amp;')
                       .replace(/</g, '&lt;')
                       .replace(/>/g, '&gt;')
                       .replace(/"/g, '&quot;')
                       .replace(/'/g, '&#039;');
        }

        function updatePanel(idx, state) {
            const statusEl = document.getElementById(`status-${idx}`);
            const progressEl = document.getElementById(`progress-${idx}`);
            const outputEl = document.getElementById(`output-${idx}`);
            const timingEl = document.getElementById(`timing-${idx}`);
            const panelEl = document.getElementById(`panel-${idx}`);

            // 상태 업데이트
            let statusIcon = '⏳';
            if (state.failed) statusIcon = '❌';
            else if (state.progress >= 100) statusIcon = '✅';
            statusEl.textContent = `${statusIcon} ${state.status}`;

            // 진행률 업데이트
            progressEl.style.width = `${state.progress}%`;

            // 출력 업데이트
            if (state.output) {
                outputEl.textContent = `출력: ${state.output}`;
                outputEl.className = 'output';
            } else if (state.error) {
                outputEl.textContent = `에러: ${state.error.substring(0, 80)}...`;
                outputEl.className = 'output error';
            }

            // 타이밍 업데이트
            timingEl.textContent = `⏱ Write: ${state.writeTime.toFixed(3)}s | Compile: ${state.compileTime.toFixed(3)}s | Run: ${state.runTime.toFixed(3)}s | Total: ${state.totalTime.toFixed(3)}s`;

            // 실행 중 애니메이션
            if (state.progress > 0 && state.progress < 100) {
                panelEl.classList.add('running');
            } else {
                panelEl.classList.remove('running');
            }
        }

        async function startExecution() {
            if (isRunning) return;
            isRunning = true;

            document.getElementById('btnRun').disabled = true;
            document.getElementById('btnReset').disabled = true;
            document.getElementById('globalStatus').textContent = '🚀 실행 중...';

            // 상태 초기화
            states = languages.map(() => ({
                status: '준비 중',
                progress: 0,
                output: '',
                error: '',
                writeTime: 0,
                compileTime: 0,
                runTime: 0,
                totalTime: 0,
                failed: false
            }));

            const startTime = performance.now();

            // 모든 언어 병렬 실행
            const promises = languages.map((lang, idx) => executeLanguage(idx));
            await Promise.all(promises);

            const totalTime = (performance.now() - startTime) / 1000;

            // 완료 처리
            const successCount = states.filter(s => !s.failed).length;
            const failCount = states.length - successCount;

            document.getElementById('globalStatus').textContent =
                `🏁 완료! 성공: ${successCount}, 실패: ${failCount} | 총 시간: ${totalTime.toFixed(2)}초`;

            document.getElementById('btnRun').disabled = false;
            document.getElementById('btnReset').disabled = false;
            isRunning = false;
        }

        async function executeLanguage(idx) {
            const state = states[idx];

            try {
                // API 호출
                const response = await fetch(`/execute/${idx}`);
                const result = await response.json();

                // 결과 적용
                state.status = result.status;
                state.progress = result.progress;
                state.output = result.output;
                state.error = result.error;
                state.writeTime = result.write_time;
                state.compileTime = result.compile_time;
                state.runTime = result.run_time;
                state.totalTime = result.total_time;
                state.failed = result.failed;

                updatePanel(idx, state);

            } catch (err) {
                state.status = '통신 오류';
                state.error = err.message;
                state.failed = true;
                state.progress = 100;
                updatePanel(idx, state);
            }
        }

        function resetAll() {
            if (isRunning) return;

            states = languages.map(() => ({
                status: '대기 중',
                progress: 0,
                output: '',
                error: '',
                writeTime: 0,
                compileTime: 0,
                runTime: 0,
                totalTime: 0,
                failed: false
            }));

            states.forEach((state, idx) => updatePanel(idx, state));
            document.getElementById('globalStatus').textContent = "준비됨 - '실행' 버튼을 클릭하세요";
        }

        // 초기화
        createPanels();
    </script>
</body>
</html>
'''

# ==================== HTTP 핸들러 ====================

class HelloHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self._serve_html()
        elif self.path.startswith('/execute/'):
            self._handle_execute()
        else:
            self.send_error(404)

    def _serve_html(self):
        # 언어 데이터를 JSON으로 변환
        lang_json = json.dumps([
            {
                "name": l.name,
                "filename": l.filename,
                "color": l.color,
                "code": l.code,
                "syntax": l.syntax,
            }
            for l in LANGUAGES
        ], ensure_ascii=False)

        html = HTML_TEMPLATE.replace('LANGUAGES_JSON', lang_json)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _handle_execute(self):
        try:
            idx = int(self.path.split('/')[-1])
            result = execute_language(idx)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def log_message(self, format, *args):
        # 로그 출력 억제 (깔끔한 출력을 위해)
        pass

# ==================== 실행 로직 ====================

def run_subprocess(cmd, cwd):
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
        return False, elapsed, "", f"명령어를 찾을 수 없음: {cmd[0]}"
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return False, elapsed, "", "타임아웃 (30초 초과)"

def execute_language(idx):
    """단일 언어 실행"""
    spec = LANGUAGES[idx]
    result = {
        "status": "대기 중",
        "progress": 0,
        "output": "",
        "error": "",
        "write_time": 0.0,
        "compile_time": 0.0,
        "run_time": 0.0,
        "total_time": 0.0,
        "failed": False,
    }

    # 워크스페이스 준비
    if not WORKSPACE.exists():
        WORKSPACE.mkdir(parents=True, exist_ok=True)

    # 1. 소스 파일 작성
    start = time.time()
    source_path = WORKSPACE / spec.filename
    try:
        source_path.write_text(spec.code, encoding="utf-8")
        result["write_time"] = time.time() - start
        result["progress"] = 25
    except OSError as e:
        result["status"] = "파일 작성 실패"
        result["error"] = str(e)
        result["failed"] = True
        result["progress"] = 100
        return result

    # 2. 컴파일
    if spec.compile_cmds:
        result["status"] = "컴파일 중..."
        compile_total = 0.0

        for cmd in spec.compile_cmds:
            success, elapsed, stdout, stderr = run_subprocess(cmd, WORKSPACE)
            compile_total += elapsed

            if not success:
                result["status"] = "컴파일 실패"
                result["error"] = stderr or stdout
                result["failed"] = True
                result["compile_time"] = compile_total
                result["total_time"] = result["write_time"] + result["compile_time"]
                result["progress"] = 100
                return result

        result["compile_time"] = compile_total
        result["progress"] = 70

    # 3. 실행
    result["status"] = "실행 중..."
    success, elapsed, stdout, stderr = run_subprocess(spec.run_cmd, WORKSPACE)
    result["run_time"] = elapsed
    result["total_time"] = result["write_time"] + result["compile_time"] + result["run_time"]

    if success:
        result["status"] = "실행 완료"
        result["output"] = stdout or "(출력 없음)"
        result["progress"] = 100
    else:
        result["status"] = "실행 실패"
        result["error"] = stderr or stdout
        result["failed"] = True
        result["progress"] = 100

    return result

# ==================== 메인 ====================

def main():
    # 워크스페이스 초기화
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   🎓 Educational Multi-Language Hello World - Web Version    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   서버 주소: http://localhost:{PORT}                           ║
║   해상도: 1920x1080 최적화                                    ║
║                                                              ║
║   브라우저에서 위 주소로 접속하세요!                           ║
║   종료: Ctrl+C                                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    # 브라우저 자동 열기 (백그라운드)
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{PORT}')

    threading.Thread(target=open_browser, daemon=True).start()

    # 서버 시작
    with socketserver.TCPServer(("", PORT), HelloHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버를 종료합니다...")
        finally:
            # 정리
            if WORKSPACE.exists():
                shutil.rmtree(WORKSPACE)
            print("✅ 정리 완료")

if __name__ == "__main__":
    main()
