#!/usr/bin/env python3
"""
Animated Multi-Language Hello World
====================================
코드가 한 줄씩 타이핑되고, 컴파일/실행 과정이
실시간으로 순차 표시되는 애니메이션 버전

실행: python3 animated_hello.py
브라우저: http://localhost:5050
"""

import subprocess
import shutil
import time
import json
import threading
import queue
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import webbrowser

PORT = 5050
WORKSPACE = Path(__file__).parent / "animated_hello_workspace"

# 이벤트 큐 (실시간 업데이트용)
event_queue = queue.Queue()

# 언어 정의
LANGUAGES = [
    {
        "name": "C",
        "filename": "hello.c",
        "color": "#00b4d8",
        "code": '''#include <stdio.h>

int main(void) {
    // 인사말 메시지 정의
    const char *message = "Hello World";

    // 표준 출력으로 출력
    puts(message);

    return 0;
}''',
        "compile_cmds": [["gcc", "hello.c", "-o", "hello_c"]],
        "run_cmd": ["./hello_c"],
        "syntax": "c",
    },
    {
        "name": "C++",
        "filename": "hello.cpp",
        "color": "#9d4edd",
        "code": '''#include <iostream>
#include <string>

int main() {
    // C++ 문자열 사용
    std::string message = "Hello World";

    // cout으로 출력
    std::cout << message << std::endl;

    return 0;
}''',
        "compile_cmds": [["g++", "hello.cpp", "-o", "hello_cpp"]],
        "run_cmd": ["./hello_cpp"],
        "syntax": "cpp",
    },
    {
        "name": "Rust",
        "filename": "hello.rs",
        "color": "#ff6b35",
        "code": '''fn main() {
    // 불변 문자열 슬라이스
    let message = "Hello World";

    // println! 매크로로 출력
    println!("{}", message);
}''',
        "compile_cmds": [["rustc", "hello.rs", "-o", "hello_rust"]],
        "run_cmd": ["./hello_rust"],
        "syntax": "rust",
    },
    {
        "name": "Assembly",
        "filename": "hello.asm",
        "color": "#ffd60a",
        "code": '''section .data
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
    syscall''',
        "compile_cmds": [
            ["nasm", "-f", "elf64", "hello.asm", "-o", "hello.o"],
            ["ld", "hello.o", "-o", "hello_asm"],
        ],
        "run_cmd": ["./hello_asm"],
        "syntax": "nasm",
    },
]

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>🎬 Animated Multi-Language Hello World</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/vs2015.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            min-height: 100vh;
            color: #c9d1d9;
        }

        .header {
            background: linear-gradient(90deg, #238636, #2ea043);
            padding: 15px;
            text-align: center;
        }

        .header h1 { font-size: 1.6em; color: white; }

        .step-indicator {
            display: flex;
            justify-content: center;
            gap: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.3);
        }

        .step {
            padding: 8px 20px;
            border-radius: 20px;
            background: #21262d;
            color: #8b949e;
            font-size: 0.9em;
            transition: all 0.3s;
        }

        .step.active {
            background: #238636;
            color: white;
            transform: scale(1.05);
        }

        .step.done {
            background: #1f6feb;
            color: white;
        }

        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 12px;
            padding: 12px;
            height: calc(100vh - 180px);
        }

        .lang-panel {
            background: #0d1117;
            border-radius: 10px;
            border: 1px solid #30363d;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .panel-header {
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
        }

        .status-badge {
            font-size: 0.8em;
            padding: 4px 12px;
            border-radius: 12px;
            background: rgba(255,255,255,0.1);
        }

        .code-area {
            flex: 1;
            background: #161b22;
            padding: 15px;
            overflow: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.6;
            min-height: 300px;
        }

        .code-area pre {
            margin: 0;
            white-space: pre-wrap;
        }

        /* 타이핑 커서 효과 */
        .cursor {
            display: inline-block;
            width: 8px;
            height: 18px;
            background: #58a6ff;
            animation: blink 0.8s infinite;
            vertical-align: middle;
            margin-left: 2px;
        }

        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }

        .output-area {
            padding: 12px 15px;
            background: #0d1117;
            border-top: 1px solid #30363d;
            min-height: 120px;
        }

        .output-label {
            font-size: 0.75em;
            color: #8b949e;
            margin-bottom: 5px;
        }

        .output-text {
            font-family: monospace;
            color: #7ee787;
            font-size: 1.1em;
        }

        .output-text.error { color: #f85149; }

        /* 컴파일 명령어 영역 */
        .cmd-area {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 12px;
            margin: 8px 0;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
        }

        .cmd-label {
            color: #8b949e;
            font-size: 0.75em;
            margin-bottom: 4px;
        }

        .cmd-text {
            color: #ff7b72;
            word-break: break-all;
        }

        .cmd-text.running {
            color: #ffa657;
            animation: cmdPulse 1s infinite;
        }

        .cmd-text.done {
            color: #7ee787;
        }

        @keyframes cmdPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .compile-log {
            font-family: monospace;
            font-size: 0.85em;
            color: #58a6ff;
            margin-top: 5px;
        }

        .footer {
            padding: 12px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            background: #161b22;
        }

        .btn {
            padding: 12px 40px;
            font-size: 1em;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-start {
            background: #238636;
            color: white;
        }

        .btn-start:hover:not(:disabled) {
            background: #2ea043;
        }

        .btn-reset {
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .global-status {
            font-size: 1em;
            color: #8b949e;
        }

        /* 진행 표시줄 */
        .progress-bar {
            height: 3px;
            background: #30363d;
            margin-top: 8px;
            border-radius: 2px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            width: 0%;
            transition: width 0.3s;
        }

        /* 타이밍 표시 */
        .timing {
            font-size: 0.8em;
            color: #8b949e;
            margin-top: 8px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Animated Multi-Language Hello World</h1>
    </div>

    <div class="step-indicator">
        <div class="step" id="step1">1️⃣ 코드 작성</div>
        <div class="step" id="step2">2️⃣ 컴파일</div>
        <div class="step" id="step3">3️⃣ 실행</div>
        <div class="step" id="step4">4️⃣ 완료</div>
    </div>

    <div class="main-grid" id="mainGrid"></div>

    <div class="footer">
        <button class="btn btn-start" id="btnStart" onclick="startAnimation()">▶ 시작</button>
        <div class="global-status" id="globalStatus">시작 버튼을 클릭하세요</div>
        <button class="btn btn-reset" id="btnReset" onclick="resetAll()">🔄 리셋</button>
    </div>

    <script>
        const languages = LANGUAGES_JSON;
        let eventSource = null;
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
                    <div class="panel-header" style="background: ${lang.color}; color: white;">
                        <span>${lang.name}</span>
                        <span class="status-badge" id="status-${idx}">대기 중</span>
                    </div>
                    <div class="code-area" id="code-${idx}">
                        <pre><code class="language-${lang.syntax}" id="codeContent-${idx}"></code><span class="cursor" id="cursor-${idx}" style="display:none;"></span></pre>
                    </div>
                    <div class="output-area">
                        <div class="cmd-area" id="cmdArea-${idx}">
                            <div class="cmd-label">$ 실행 명령어:</div>
                            <div class="cmd-text" id="cmdText-${idx}">-</div>
                        </div>
                        <div class="output-label">출력 결과:</div>
                        <div class="output-text" id="output-${idx}">-</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-${idx}" style="background: ${lang.color};"></div>
                        </div>
                        <div class="timing" id="timing-${idx}"></div>
                    </div>
                `;
                grid.appendChild(panel);
            });
        }

        function setStep(stepNum) {
            for (let i = 1; i <= 4; i++) {
                const el = document.getElementById(`step${i}`);
                el.classList.remove('active', 'done');
                if (i < stepNum) el.classList.add('done');
                else if (i === stepNum) el.classList.add('active');
            }
        }

        function updateStatus(idx, text) {
            document.getElementById(`status-${idx}`).textContent = text;
        }

        function appendCode(idx, text) {
            const el = document.getElementById(`codeContent-${idx}`);
            el.textContent += text;
            hljs.highlightElement(el);
        }

        function setCode(idx, text) {
            const el = document.getElementById(`codeContent-${idx}`);
            el.textContent = text;
            hljs.highlightElement(el);
        }

        function showCursor(idx, show) {
            document.getElementById(`cursor-${idx}`).style.display = show ? 'inline-block' : 'none';
        }

        function setOutput(idx, text, isError = false) {
            const el = document.getElementById(`output-${idx}`);
            el.textContent = text;
            el.className = 'output-text' + (isError ? ' error' : '');
        }

        function setCmd(idx, text, status = '') {
            const el = document.getElementById(`cmdText-${idx}`);
            el.textContent = text;
            el.className = 'cmd-text' + (status ? ' ' + status : '');
        }

        function setProgress(idx, percent) {
            document.getElementById(`progress-${idx}`).style.width = percent + '%';
        }

        function setTiming(idx, text) {
            document.getElementById(`timing-${idx}`).textContent = text;
        }

        function startAnimation() {
            if (isRunning) return;
            isRunning = true;

            document.getElementById('btnStart').disabled = true;
            document.getElementById('btnReset').disabled = true;
            document.getElementById('globalStatus').textContent = '🎬 애니메이션 진행 중...';

            // SSE 연결
            eventSource = new EventSource('/events');

            eventSource.onmessage = function(e) {
                const data = JSON.parse(e.data);
                handleEvent(data);
            };

            eventSource.onerror = function() {
                eventSource.close();
                isRunning = false;
                document.getElementById('btnStart').disabled = false;
                document.getElementById('btnReset').disabled = false;
            };

            // 실행 시작 요청
            fetch('/start');
        }

        function handleEvent(data) {
            const { type, lang_idx, payload } = data;

            switch(type) {
                case 'step':
                    setStep(payload.step);
                    document.getElementById('globalStatus').textContent = payload.message;
                    break;

                case 'status':
                    updateStatus(lang_idx, payload.text);
                    break;

                case 'cursor_show':
                    showCursor(lang_idx, true);
                    break;

                case 'cursor_hide':
                    showCursor(lang_idx, false);
                    break;

                case 'code_line':
                    appendCode(lang_idx, payload.line + '\\n');
                    break;

                case 'code_full':
                    setCode(lang_idx, payload.code);
                    break;

                case 'compile_start':
                    setCmd(lang_idx, '$ ' + payload.cmd, 'running');
                    break;

                case 'compile_done':
                    setCmd(lang_idx, '$ ' + payload.cmd + '  ✅ (' + payload.time.toFixed(3) + 's)', 'done');
                    break;

                case 'compile_error':
                    setCmd(lang_idx, '$ ' + payload.cmd + '  ❌ 실패', '');
                    setOutput(lang_idx, payload.error, true);
                    break;

                case 'run_start':
                    setCmd(lang_idx, '$ ' + payload.cmd, 'running');
                    break;

                case 'run_done':
                    setOutput(lang_idx, payload.output || '(출력 없음)');
                    setCmd(lang_idx, '$ ' + payload.cmd + '  ✅ (' + payload.time.toFixed(3) + 's)', 'done');
                    break;

                case 'run_error':
                    setOutput(lang_idx, payload.error, true);
                    setCmd(lang_idx, '$ ' + payload.cmd + '  ❌', '');
                    break;

                case 'progress':
                    setProgress(lang_idx, payload.percent);
                    break;

                case 'timing':
                    setTiming(lang_idx, payload.text);
                    break;

                case 'done':
                    document.getElementById('globalStatus').textContent = '🏁 ' + payload.message;
                    document.getElementById('btnStart').disabled = false;
                    document.getElementById('btnReset').disabled = false;
                    isRunning = false;
                    if (eventSource) eventSource.close();
                    break;
            }
        }

        function resetAll() {
            if (isRunning) return;
            if (eventSource) eventSource.close();

            languages.forEach((_, idx) => {
                document.getElementById(`codeContent-${idx}`).textContent = '';
                document.getElementById(`status-${idx}`).textContent = '대기 중';
                document.getElementById(`output-${idx}`).textContent = '-';
                document.getElementById(`output-${idx}`).className = 'output-text';
                document.getElementById(`cmdText-${idx}`).textContent = '-';
                document.getElementById(`cmdText-${idx}`).className = 'cmd-text';
                document.getElementById(`progress-${idx}`).style.width = '0%';
                document.getElementById(`timing-${idx}`).textContent = '';
                showCursor(idx, false);
            });

            setStep(0);
            document.getElementById('globalStatus').textContent = '시작 버튼을 클릭하세요';
        }

        createPanels();
    </script>
</body>
</html>
'''

class AnimatedHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self._serve_html()
        elif self.path == '/events':
            self._serve_events()
        elif self.path == '/start':
            self._start_animation()
        else:
            self.send_error(404)

    def _serve_html(self):
        lang_json = json.dumps([{
            "name": l["name"],
            "filename": l["filename"],
            "color": l["color"],
            "syntax": l["syntax"],
        } for l in LANGUAGES], ensure_ascii=False)

        html = HTML_TEMPLATE.replace('LANGUAGES_JSON', lang_json)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _serve_events(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        try:
            while True:
                try:
                    event = event_queue.get(timeout=30)
                    data = json.dumps(event, ensure_ascii=False)
                    self.wfile.write(f"data: {data}\n\n".encode('utf-8'))
                    self.wfile.flush()

                    if event.get('type') == 'done':
                        break
                except queue.Empty:
                    # 하트비트
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
        except:
            pass

    def _start_animation(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

        # 애니메이션 스레드 시작
        thread = threading.Thread(target=run_animation)
        thread.daemon = True
        thread.start()

    def log_message(self, format, *args):
        pass

def send_event(event_type, lang_idx=None, payload=None):
    event_queue.put({
        "type": event_type,
        "lang_idx": lang_idx,
        "payload": payload or {}
    })

def run_subprocess(cmd, cwd):
    start = time.time()
    try:
        result = subprocess.run(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, check=True, timeout=30
        )
        return True, time.time() - start, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, time.time() - start, e.stdout or "", e.stderr or str(e)
    except FileNotFoundError:
        return False, time.time() - start, "", f"명령어를 찾을 수 없음: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, time.time() - start, "", "타임아웃"

def run_animation():
    """메인 애니메이션 로직"""

    # 워크스페이스 준비
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    timings = [{} for _ in LANGUAGES]

    # ========== STEP 1: 코드 작성 (타이핑 애니메이션) ==========
    send_event('step', payload={'step': 1, 'message': '📝 Step 1: 코드 작성 중...'})

    for idx, lang in enumerate(LANGUAGES):
        send_event('status', idx, {'text': '작성 중...'})
        send_event('cursor_show', idx)
        send_event('progress', idx, {'percent': 0})

    # 한 줄씩 순차적으로 표시
    code_lines = [lang["code"].split('\n') for lang in LANGUAGES]
    max_lines = max(len(lines) for lines in code_lines)

    for line_num in range(max_lines):
        for idx, lines in enumerate(code_lines):
            if line_num < len(lines):
                send_event('code_line', idx, {'line': lines[line_num]})
                progress = int((line_num + 1) / len(lines) * 30)
                send_event('progress', idx, {'percent': progress})
        time.sleep(0.35)  # 타이핑 속도 (느리게)

    for idx in range(len(LANGUAGES)):
        send_event('cursor_hide', idx)
        send_event('status', idx, {'text': '✅ 작성 완료'})

    time.sleep(0.5)

    # ========== STEP 2: 컴파일 ==========
    send_event('step', payload={'step': 2, 'message': '⚙️ Step 2: 컴파일 중...'})

    for idx, lang in enumerate(LANGUAGES):
        send_event('status', idx, {'text': '컴파일 중...'})
        send_event('progress', idx, {'percent': 30})

        # 소스 파일 작성
        source_path = WORKSPACE / lang["filename"]
        write_start = time.time()
        source_path.write_text(lang["code"], encoding="utf-8")
        timings[idx]['write'] = time.time() - write_start

        # 컴파일
        compile_total = 0.0
        failed = False

        last_cmd_str = ""
        for cmd in lang["compile_cmds"]:
            cmd_str = ' '.join(cmd)
            last_cmd_str = cmd_str
            send_event('compile_start', idx, {'cmd': cmd_str})

            success, elapsed, stdout, stderr = run_subprocess(cmd, WORKSPACE)
            compile_total += elapsed

            if not success:
                send_event('compile_error', idx, {'cmd': cmd_str, 'error': stderr[:100]})
                send_event('status', idx, {'text': '❌ 컴파일 실패'})
                failed = True
                break

            time.sleep(1.0)  # 컴파일 진행 시각화 (느리게)

        timings[idx]['compile'] = compile_total

        if not failed:
            send_event('compile_done', idx, {'cmd': last_cmd_str, 'time': compile_total})
            send_event('status', idx, {'text': '✅ 컴파일 완료'})
            send_event('progress', idx, {'percent': 70})
        else:
            send_event('progress', idx, {'percent': 100})

        time.sleep(0.2)

    time.sleep(0.5)

    # ========== STEP 3: 실행 ==========
    send_event('step', payload={'step': 3, 'message': '🚀 Step 3: 실행 중...'})

    for idx, lang in enumerate(LANGUAGES):
        if timings[idx].get('compile', 0) == 0 and not (WORKSPACE / lang["run_cmd"][0].replace('./', '')).exists():
            # 컴파일 실패한 경우 스킵
            continue

        run_cmd_str = ' '.join(lang["run_cmd"])
        send_event('status', idx, {'text': '실행 중...'})
        send_event('run_start', idx, {'cmd': run_cmd_str})
        send_event('progress', idx, {'percent': 85})

        success, elapsed, stdout, stderr = run_subprocess(lang["run_cmd"], WORKSPACE)
        timings[idx]['run'] = elapsed

        if success:
            send_event('run_done', idx, {'cmd': run_cmd_str, 'output': stdout, 'time': elapsed})
            send_event('status', idx, {'text': '✅ 실행 완료'})
        else:
            send_event('run_error', idx, {'cmd': run_cmd_str, 'error': stderr[:100]})
            send_event('status', idx, {'text': '❌ 실행 실패'})

        send_event('progress', idx, {'percent': 100})

        # 타이밍 표시
        total = sum(timings[idx].values())
        timing_text = f"Write: {timings[idx].get('write', 0):.3f}s | Compile: {timings[idx].get('compile', 0):.3f}s | Run: {timings[idx].get('run', 0):.3f}s | Total: {total:.3f}s"
        send_event('timing', idx, {'text': timing_text})

        time.sleep(0.8)  # 실행 완료 후 대기 (느리게)

    # ========== STEP 4: 완료 ==========
    send_event('step', payload={'step': 4, 'message': '🏁 Step 4: 완료!'})

    # 정리
    try:
        shutil.rmtree(WORKSPACE)
    except:
        pass

    success_count = sum(1 for t in timings if t.get('run', 0) > 0)

    time.sleep(0.5)
    send_event('done', payload={'message': f'완료! 성공: {success_count}/{len(LANGUAGES)}'})

def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   🎬 Animated Multi-Language Hello World                     ║
╠══════════════════════════════════════════════════════════════╣
║   서버 주소: http://localhost:{PORT}                           ║
║   코드가 한 줄씩 타이핑되는 애니메이션 버전!                   ║
║   종료: Ctrl+C                                               ║
╚══════════════════════════════════════════════════════════════╝
""")

    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{PORT}')

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(("", PORT), AnimatedHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n종료...")

if __name__ == "__main__":
    main()
