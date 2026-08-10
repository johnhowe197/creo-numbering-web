"""
Web 版启动器：启动本地 FastAPI 服务并自动打开浏览器

环境变量：
- NUMBERING_HOST   监听地址（默认 127.0.0.1）
- NUMBERING_PORT   端口（默认自动选择空闲端口）
- NUMBERING_NO_BROWSER  设为 1 时不自动打开浏览器（供自动化验证）
"""

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn


def find_free_port() -> int:
    """获取一个空闲端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _redirect_stdio() -> None:
    """打包为无窗口程序时 stdout/stderr 为 None，重定向到日志文件防止崩溃"""
    if sys.stdout is not None and sys.stderr is not None:
        return
    if getattr(sys, "frozen", False):
        log_dir = Path(sys.executable).resolve().parent / "logs"
    else:
        log_dir = Path(".").resolve() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = open(log_dir / "error.log", "a", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = log_file
    if sys.stderr is None:
        sys.stderr = log_file


def main():
    _redirect_stdio()
    host = os.environ.get("NUMBERING_HOST", "127.0.0.1")
    port = int(os.environ.get("NUMBERING_PORT", "0") or 0)
    if port <= 0:
        port = find_free_port()
    url = f"http://{host}:{port}/"

    if os.environ.get("NUMBERING_NO_BROWSER") != "1":
        def _open_browser():
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=_open_browser, daemon=True).start()

    print(f"Creo 模型树自动取号器已启动: {url}")
    from app.main import app
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
