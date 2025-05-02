# config.py
import queue

WEBSOCKET_HOST = '0.0.0.0'
WEBSOCKET_PORT = 8765
PING_INTERVAL = 60
PING_TIMEOUT = 30

SCREENSHOT_PATH = r"C:\Users\admin\Desktop\桌面\虚拟互通\gong_yidan.bmp"
ZHILING_SCREENSHOT_PATH =r"C:\Users\admin\Desktop\桌面\虚拟互通\zhizaozhiling.jpg"
DAILY_TASK_SOURCE_FILE = r"C:\Users\admin\Desktop\桌面\虚拟互通\测试结果.xls"
DAILY_TASK_TARGET_DIR = r"C:\Users\admin\Desktop\桌面\检测是否有测试报告"
FIND_REPORT_BAT = r"C:\Users\admin\Desktop\桌面\查找报告.bat"
LOG_FILE = r"C:\Users\admin\Desktop\2024-11-07.txt"
HU_TONG = r"C:\Users\admin\Desktop\桌面\虚拟互通"

translation_modes = {}
gongyidan_modes = {}
zhizaozhiling_modes = {}
is_fanyi = {'start': False}
is_gongyi_chazhao = {'start': False}
is_zhizaozhiling_chazhao = {'start': False}
connected_clients = set()
message_queue = queue.Queue()