import ctypes
import os
import signal
import subprocess
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / "water_reminder.pid"
STOP_FILE = BASE_DIR / "water_reminder.stop"


def remove_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def is_process_running(pid: int) -> bool:
    if pid <= 0:
        return False

    process_query_limited_information = 0x1000
    still_active = 259

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False

    exit_code = ctypes.c_ulong()
    try:
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def main() -> None:
    if not PID_FILE.exists():
        print("喝水提醒未在运行。")
        remove_file(STOP_FILE)
        return

    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except ValueError:
        remove_file(PID_FILE)
        remove_file(STOP_FILE)
        print("已清理无效状态文件。")
        return

    STOP_FILE.write_text("stop", encoding="utf-8")

    for _ in range(10):
        if not is_process_running(pid):
            remove_file(PID_FILE)
            remove_file(STOP_FILE)
            print("喝水提醒已停止。")
            return
        time.sleep(0.5)

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    time.sleep(1)
    if is_process_running(pid):
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    remove_file(PID_FILE)
    remove_file(STOP_FILE)
    print("喝水提醒已停止。")


if __name__ == "__main__":
    main()
