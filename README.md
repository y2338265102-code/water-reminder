# Python 喝水提醒工具

## 启动

后台运行，不显示控制台窗口：

```powershell
pythonw water_reminder.py
```

调试运行，可以看到启动信息：

```powershell
python water_reminder.py
```

启动后脚本会常驻后台，每隔 2 小时弹出一次 Windows 原生通知区域提醒。

## 停止

```powershell
python stop.py
```

## 文件

- `water_reminder.py`：主提醒程序
- `stop.py`：停止提醒程序
- `water_reminder.pid`：运行时自动生成，记录后台进程
- `water_reminder.stop`：停止时临时生成
