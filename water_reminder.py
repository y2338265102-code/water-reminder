import atexit
import ctypes
import os
import random
import subprocess
import sys
import time
from pathlib import Path


APP_NAME = "喝水提醒"
INTERVAL_SECONDS = 2 * 60 * 60
MESSAGES = [
    "该喝水啦！💧 保持水分很重要哦",
    "已经2小时没喝水了，快去倒一杯吧~",
    "喝水时间到！你的身体需要补充水分",
    "别忘喝水！健康从一杯水开始",
]

BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / "water_reminder.pid"
STOP_FILE = BASE_DIR / "water_reminder.stop"


def is_windows() -> bool:
    return os.name == "nt"


def remove_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def is_process_running(pid: int) -> bool:
    if pid <= 0:
        return False

    if not is_windows():
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


def ensure_single_instance() -> None:
    if not PID_FILE.exists():
        return

    try:
        existing_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except ValueError:
        remove_file(PID_FILE)
        return

    if is_process_running(existing_pid):
        print(f"{APP_NAME} 已在运行中，PID: {existing_pid}")
        sys.exit(0)

    remove_file(PID_FILE)


def cleanup() -> None:
    if PID_FILE.exists():
        try:
            current_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        except ValueError:
            current_pid = None

        if current_pid == os.getpid():
            remove_file(PID_FILE)

    remove_file(STOP_FILE)


def start_hidden_powershell(script: str) -> None:
    creationflags = subprocess.CREATE_NO_WINDOW if is_windows() else 0
    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def show_windows_notification(message: str) -> None:
    # Prefer Windows toast notifications; fall back to notification area balloons.
    title = APP_NAME.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = (
        message.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
    )
    balloon_title = APP_NAME.replace("'", "''")
    balloon_text = message.replace("'", "''")
    script = f"""
try {{
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
    $template = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{title}</text>
      <text>{text}</text>
    </binding>
  </visual>
</toast>
"@
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Python.WaterReminder')
    $notifier.Show($toast)
}} catch {{
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.BalloonTipTitle = '{balloon_title}'
    $notify.BalloonTipText = '{balloon_text}'
    $notify.Visible = $true
    $notify.ShowBalloonTip(10000)
    Start-Sleep -Seconds 12
    $notify.Dispose()
}}
"""
    start_hidden_powershell(script)


def wait_with_stop_check(seconds: int) -> bool:
    end_time = time.monotonic() + seconds
    while time.monotonic() < end_time:
        if STOP_FILE.exists():
            return True
        time.sleep(min(5, max(0.1, end_time - time.monotonic())))
    return STOP_FILE.exists()


def main() -> None:
    if not is_windows():
        raise RuntimeError("此脚本需要在 Windows 上运行。")

    ensure_single_instance()
    remove_file(STOP_FILE)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(cleanup)

    print(f"{APP_NAME} 已启动，PID: {os.getpid()}。每2小时提醒一次。")

    while True:
        if wait_with_stop_check(INTERVAL_SECONDS):
            break
        message = random.choice(MESSAGES)
        show_windows_notification(message)


if __name__ == "__main__":
    main()
