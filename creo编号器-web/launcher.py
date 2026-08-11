"""
Web 版启动器：启动本地 FastAPI 服务并打开浏览器

- 单实例：重复启动时检测已有实例，直接复用（不新增进程）
- 系统托盘：右下角图标，菜单含「打开取号器 / 退出」

环境变量：
- NUMBERING_HOST      监听地址（默认 127.0.0.1）
- NUMBERING_PORT      端口（默认 8000；被占用时自动换空闲端口）
- NUMBERING_NO_BROWSER 设为 1 时不自动打开浏览器（供自动化验证）
"""

import json
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn


def find_free_port() -> int:
    """获取一个空闲端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _redirect_stdio() -> None:
    """无窗口模式下 stdout/stderr 为 None，重定向到日志文件防止崩溃"""
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


def _probe_existing(url: str) -> bool:
    """探测是否已有取号器实例在运行（响应为合法 JSON 列表）"""
    try:
        with urllib.request.urlopen(url + "api/projects", timeout=1.5) as r:
            if r.status == 200:
                return isinstance(json.loads(r.read().decode("utf-8")), list)
    except Exception:
        return False
    return False


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def _load_tray_icon():
    """加载托盘图标（优先 app_icon.png，缺失时程序化生成）"""
    from PIL import Image
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parent
    for name in ("app_icon.png", "app_icon.ico"):
        p = base / name
        if p.exists():
            try:
                return Image.open(p)
            except Exception:
                pass
    from PIL import Image as _I, ImageDraw
    img = _I.new("RGBA", (64, 64), (37, 99, 235, 255))
    ImageDraw.Draw(img).ellipse((14, 14, 50, 50), fill=(255, 255, 255, 255))
    return img


def _run_tray(server, url: str) -> None:
    """运行系统托盘（打开 / 退出）；托盘不可用时保持服务驻留"""
    try:
        import pystray
    except Exception as e:
        print(f"托盘不可用，服务保持驻留: {e}")
        while not server.should_exit:
            time.sleep(1)
        return

    image = _load_tray_icon()

    def _open(_icon=None, _item=None):
        webbrowser.open(url)

    def _quit(_icon=None, _item=None):
        server.should_exit = True
        if _icon:
            _icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("打开取号器", _open, default=True),
        pystray.MenuItem("退出", _quit),
    )
    icon = pystray.Icon("creo_numbering_web", image, "Creo模型树自动取号器", menu)
    icon.run()


def main():
    _redirect_stdio()
    host = os.environ.get("NUMBERING_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("NUMBERING_PORT", "8000") or "8000")
    except ValueError:
        port = 8000
    default_url = f"http://{host}:{port}/"

    # 单实例：已有实例在运行 → 打开浏览器复用，不新增进程
    if _probe_existing(default_url):
        print(f"检测到取号器已在运行，打开现有实例: {default_url}")
        if os.environ.get("NUMBERING_NO_BROWSER") != "1":
            webbrowser.open(default_url)
        return

    # 默认端口被其他程序占用（非取号器）→ 换空闲端口
    if port == 8000 and _port_in_use(host, port):
        port = find_free_port()
    url = f"http://{host}:{port}/"

    if os.environ.get("NUMBERING_NO_BROWSER") != "1":
        def _open_browser():
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=_open_browser, daemon=True).start()

    print(f"Creo 模型树自动取号器已启动: {url}")

    from app.main import app
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()

    _run_tray(server, url)


if __name__ == "__main__":
    main()
