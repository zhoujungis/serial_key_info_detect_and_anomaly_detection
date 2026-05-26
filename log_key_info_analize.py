import sys
import json
import os
import re
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMenuBar,
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QFileDialog, QInputDialog,
    QCheckBox, QProgressBar, QGroupBox, QFrame,
    QTreeWidget, QTreeWidgetItem,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction, QActionGroup
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    _bundled_config = os.path.join(sys._MEIPASS, "config")
    _exe_config = os.path.join(BASE_DIR, "config")
    os.makedirs(_exe_config, exist_ok=True)
    if os.path.isdir(_bundled_config):
        for _name in os.listdir(_bundled_config):
            _src = os.path.join(_bundled_config, _name)
            _dst = os.path.join(_exe_config, _name)
            if not os.path.exists(_dst):
                try:
                    if os.path.isdir(_src):
                        shutil.copytree(_src, _dst)
                    else:
                        shutil.copy2(_src, _dst)
                except OSError:
                    pass
else:
    BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "config")
JSON_PATH = os.path.join(CONFIG_DIR, "rules.json")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
TIME_RULES_PATH = os.path.join(CONFIG_DIR, "time_rules.json")
ANOMALY_RULES_PATH = os.path.join(CONFIG_DIR, "anomaly_rules.json")
DEVICE_INFO_PATH = os.path.join(CONFIG_DIR, "device_info.json")


FILES_DIR = os.path.join(BASE_DIR, "files")


def _ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    for old_name, new_path in [
        ("rules.json", JSON_PATH),
        ("config.json", CONFIG_PATH),
    ]:
        old_path = os.path.join(BASE_DIR, old_name)
        if os.path.isfile(old_path) and not os.path.isfile(new_path):
            os.rename(old_path, new_path)


def _clear_files_dir():
    if os.path.isdir(FILES_DIR):
        shutil.rmtree(FILES_DIR)
    os.makedirs(FILES_DIR)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    # 迁移旧路径的文件
    for old_name, new_path in [
        ("rules.json", JSON_PATH),
        ("config.json", CONFIG_PATH),
    ]:
        old_path = os.path.join(BASE_DIR, old_name)
        if os.path.isfile(old_path) and not os.path.isfile(new_path):
            os.rename(old_path, new_path)

DEFAULT_RULES = {
    "RESET": [
        ["enter reset factory", "reset启动"],
        ["play audio file /usr/bin/audio/reset", "reset提示音"],
        ["finish play /usr/bin/audio/reset", "reset提示音播放成功"],
        ["\\[ble\\] trans start", "蓝牙连接打开"],
        ["\\[ble\\] trans stop", "蓝牙关闭连接"],
        ["i:gz_ble_start: i=0", "蓝牙打开"],
        ["i:__gz_ble_disconnect: adv_stop", "蓝牙关"],
        ["i:ble_set_adv_and_scan_rsp: adv_start", "开始广播"],
        ["get ip", "WiFi获取"],
        ["send reset to T41", "reset"],
        ["reset gpio:1", "reset,reset gpio:1"],
        ["reset reason 0", "WiFi唤醒原因,reset reason 0"],
        ["reset reason 1", "WiFi唤醒原因,reset reason 1"],
        ["reset reason 2", "WiFi唤醒原因,reset reason 2"],
        ["mount failed", "TF卡挂载失败"],
        ["by low power", "低电,low power"],
        ["CPU EXCEPTION", "CPU EXCEPTION NO.32"],
        ["Out of memory", "OOM"],
        ["finish play /usr/bin/audio/di", "滴"],
        ["get ip:1", "联网成功"],
        ["gz_ble_stop --------", "蓝牙关闭"],
        ["gz_ble_start \\+\\+\\+\\+\\+\\+\\+\\+", "蓝牙打开"],
        ["gz_ble_start ---", "蓝牙打开"],
    ],
    "绑定解绑": [
        ["\\[ble\\] trans start", "蓝牙打开"],
        ["\\[ble\\] trans stop", "蓝牙关闭"],
        ["play audio file /usr/bin/audio/di", "di"],
        ["play audio file /usr/bin/audio/us/connect_wifi", "配网开始"],
        ["report tp to api-cn\\.fm\\.aosulife\\.com return 0", "联网成功1"],
        ["finish play /usr/bin/audio/us/connect_succ", "联网成功"],
        ["will reboot device", "关/开设备"],
        ["play audio file /usr/bin/audio/us/connect_timeout", "连接超时"],
        ["play audio file /usr/bin/audio/us/connect_pwderr volume 100 times 1", "密码错误"],
        ["bind_success_thread:  wifi_disconnect", "wifi_disconnect"],
        ["dp set del sd when unbind", "解绑"],
        ["station notify unbind", "子站通知解绑"],
        ["handle_dp_from_station, dpid: 232,", "收到子站解绑通知"],
        ["CPU Exception", "CPU Exception"],
        ["reset reason 0", "reset reason 0"],
        ["reset reason 1", "reset reason 1"],
        ["reset reason 2", "reset reason 2"],
        ["Out of memory", "OOM"],
        ["gz_ble_stop --------", "蓝牙关闭"],
        ["gz_ble_start \\+\\+\\+\\+\\+\\+\\+\\+", "蓝牙打开"],
        ["gz_ble_start ---", "蓝牙打开"],
    ],
    "卡刷OTA升级": [
        ["gz_sys_upgrade_ex start updating wifi", "开始WiFi升级"],
        ["gz_sys_upgrade_ex wifi update result: 0", "WiFi升级-成功"],
        ["gz_sys_upgrade_ex wifi update result: -1", "WiFi升级-失败"],
        ["gz_sys_upgrade_ex start updating mcu, length:", "开始MCU升级"],
        ["s_mcu_upgrade_result: 0", "MCU升级-成功"],
        ["s_mcu_upgrade_result: -1", "MCU升级-失败"],
        ["gz_sys_upgrade_ex RV1103B update result: 0", "主控升级-成功"],
        ["gz_sys_upgrade_ex RV1103B update result: -1", "主控升级-失败"],
        ["Out of memory", "OOM异常"],
        ["will reboot device, type:", "will reboot device, type:"],
        ["s_radar_upgrade_result: 0", "雷达升级-成功"],
        ["s_radar_upgrade_result: -1", "雷达升级-失败"],
        ["s_radar_upgrade_result: 255", "雷达升级-失败"],
        ["gz_sys_upgrade_ex start updating AX", "C9X11开始升级"],
        ["gz_sys_upgrade_ex AX update result: 0", "C9X11蓝牙升级成功"],
        ["reboot type: 0", "升级成功重启"],
        ["update error", "升级失败"],
    ],
    "开关机": [
        ["do poweroff", "正常关机"],
        ["power cut 1", "硬关机"],
        ["sd7601_set_bat_turn, 0", "硬关机-电池"],
        ["power cut 0", "软关机"],
        ["do poweron", "正常开机"],
        ["get ip:1", "获取IP"],
        ["power by low power", "低电关机"],
        ["CPU EXCEPTION NO\\.32", "CPU EXCEPTION NO.32"],
        ["play power off audio", "关机音乐"],
        ["play audio file /usr/bin/audio/power_off volume 90 times 1", "播放关机音乐"],
        ["play power on audio", "开机音乐"],
        ["play audio file /usr/bin/audio/power_on volume 90 times 1", "播放开机音乐"],
        ["mmcblk0p1 mounted", "TF卡加载成功"],
        ["mount failed", "TF卡挂载失败"],
        ["not found ssid", "找不到ssid"],
        ["reconnect failed", "重连失败"],
        ["do poweroff 0", "硬关机-1"],
        ["CPU EXCEPTION", "异常"],
        ["i:wifi_connect: \\[H3C_B4AEB0,12345678\\]-->\\[H3C_B4AEB0,12345678\\], status=5", "联网成功"],
        ["finish play /usr/bin/audio/power_off", "C9P关机"],
        ["finish play /usr/bin/audio/power_on", "C9P开机"],
        ["i:version", "WiFi版本"],
        ["reset reason 0", "硬件复位"],
        ["reset reason 1", "看门狗复位"],
        ["reset reason 2", "reset reason 2"],
    ],
    "TF卡": [
        ["mmcblk0p1 mounted", "TF卡加载成功"],
        ["mount failed", "TF卡挂载失败"],
    ],
    "休眠唤醒": [
        ["set busy flag\\[0x02000000\\]", "pir唤醒"],
        ["i:range:", "雷达触发"],
        ["radar event", "radar事件"],
        ["pir event", "pir事件"],
        ["\"w\":0", "无效事件滤除"],
        ["\"w\":1", "有效事件上报"],
        ["reset reason 0", "WiFi唤醒原因,reset reason 0# 硬件复位"],
        ["reset reason 1", "WiFi唤醒原因,reset reason 1## 看门狗复位"],
        ["reset reason 2", "WiFi唤醒原因,reset reason 2"],
        ["verification failed", "wifi-verification failed"],
        ["wait result timeout", "雷达-wait result timeout"],
        ["gz_video_input_catch_jpeg capture jpeg error: -1", "雷达-捕获图片错误"],
        ["Out of memory", "OOM"],
        ["Normal Boot", "Normal Boot"],
        ["by low power", "低电low power"],
        ["CPU EXCEPTION NO\\.32", "CPU EXCEPTION NO.32"],
        ["ROCKIVA_Init failed", "雷达-ROCKIVA_Init failed"],
        ["MIPI_CSI2 ERR2", "雷达-MIPI_CSI2 ERR2"],
        ["RK_MPI_VENC_GetStream Failure:", "雷达-编码获取流失败"],
        ["venc_release 6", "venc_release 6"],
        ["i:host startup time", "pir唤醒时间"],
    ],
}


def load_rules():
    _ensure_config_dir()
    if os.path.isfile(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT_RULES.items():
                if k not in data:
                    data[k] = [list(r) for r in v]
            _normalize_rules(data)
            return data
        except Exception:
            pass
    data = {k: [list(r) for r in v] for k, v in DEFAULT_RULES.items()}
    _normalize_rules(data)
    return data


def save_rules(data):
    _ensure_config_dir()
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_rules(data):
    for k in data:
        rows = data[k]
        for i, row in enumerate(rows):
            if len(row) == 2:
                rows[i] = [row[0], row[1], True, ""]
            elif len(row) == 3:
                rows[i] = [row[0], row[1], row[2], ""]
            elif len(row) >= 4:
                rows[i] = [row[0], row[1], row[2], row[3]]


def load_config():
    _ensure_config_dir()
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"test_selection": ["绑定解绑"], "behaviors": []}


def save_config(data):
    _ensure_config_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_time_rules():
    _ensure_config_dir()
    if os.path.isfile(TIME_RULES_PATH):
        try:
            with open(TIME_RULES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_time_rules(data):
    _ensure_config_dir()
    with open(TIME_RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_anomaly_rules():
    _ensure_config_dir()
    if os.path.isfile(ANOMALY_RULES_PATH):
        try:
            with open(ANOMALY_RULES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for row in data:
                if len(row) == 3:
                    row.append(True)
            return data
        except Exception:
            pass
    return []


def save_anomaly_rules(data):
    _ensure_config_dir()
    with open(ANOMALY_RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


DEFAULT_DEVICE_INFO = [
    ["设备SN", "", ""],
    ["主控版本", "", ""],
    ["Wi-Fi版本", "", ""],
]


def load_device_info():
    _ensure_config_dir()
    if os.path.isfile(DEVICE_INFO_PATH):
        try:
            with open(DEVICE_INFO_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for i, row in enumerate(data):
                if len(row) == 2:
                    data[i] = [row[0], row[1], ""]
            return data
        except Exception:
            pass
    return [list(r) for r in DEFAULT_DEVICE_INFO]


def save_device_info(data):
    _ensure_config_dir()
    with open(DEVICE_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_file_bytes(path):
    """Read file as bytes once, then try to decode — avoids multiple full-file reads."""
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ["utf-8", "gbk", "utf-16", "latin-1"]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def _read_file_lines(path):
    """Read file as list of lines with auto encoding detection (single I/O)."""
    content = _read_file_bytes(path)
    if content is None:
        return None
    return content.split("\n")


# Single combined timestamp regex — replaces the 7 separate patterns above.
# Groups are ordered by priority (most specific first); use m.lastindex to
# find which one matched.  This turns ~7 regex calls per extraction into 1.
_TIMESTAMP_RE = re.compile(
    r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\]'   # [2024-01-15 10:30:45.123456]
    r'|(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)'       # 2024-01-15 10:30:45.123456
    r'|(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'            # 2024-01-15 10:30:45
    r'|\[(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\]'        # [YY/MM/DD HH:MM:SS]
    r'|(\d{2}:\d{2}:\d{2}\.\d+)'                           # HH:MM:SS.micro
    r'|(\d{2}:\d{2}:\d{2})'                                 # HH:MM:SS
)
_TS_PARSE_RE = re.compile(r'^(\d+):(\d{2}):(\d{2})(?:\.(\d+))?$')
_REF_HMS_RE = re.compile(r'^(\d+):(\d{2}):(\d{2})$')
_REF_HM_RE = re.compile(r'^(\d+):(\d{2})$')
_REF_VAL_RE = re.compile(r'^([\d.]+)\s*(ms|s|m|h)?$')


class ReorderableTable(QTableWidget):
    """支持手动排序的表格"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)


class RuleDialog(QDialog):
    def __init__(self, parent=None, selected_tests=None):
        super().__init__(parent)
        self.setWindowTitle("关键字配置")
        self.setMinimumSize(950, 600)
        self.resize(1050, 680)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        self.selected_tests = selected_tests or []
        self.tables = {}
        rules_data = load_rules()
        if self.selected_tests:
            self.rule_names = [n for n in self.selected_tests if n in rules_data]
        else:
            self.rule_names = list(rules_data.keys())
        if not self.rule_names:
            self.rule_names = list(rules_data.keys())
        # 设备信息始终放最后
        self.rule_names.append("设备信息")
        self.device_info = load_device_info()

        for name in self.rule_names:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(12, 12, 12, 12)

            is_device = (name == "设备信息")

            if is_device:
                hint = QLabel("名称不可编辑，第二列为匹配正则，第三列为提取结果")
                hint.setStyleSheet("color: gray")
                page_layout.addWidget(hint)

                table = ReorderableTable()
                table.setColumnCount(3)
                table.setHorizontalHeaderLabels(["名称", "正则表达式", "提取信息"])
                table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
                table.verticalHeader().hide()
                table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                table.setFont(QFont("Microsoft YaHei UI", 10))

                table.setRowCount(len(self.device_info))
                for i, row_data in enumerate(self.device_info):
                    nm = row_data[0]
                    pat = row_data[1] if len(row_data) >= 2 else ""
                    info = row_data[2] if len(row_data) >= 3 else ""
                    item = QTableWidgetItem(nm)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(i, 0, item)
                    table.setItem(i, 1, QTableWidgetItem(pat))
                    table.setItem(i, 2, QTableWidgetItem(info))

                page_layout.addWidget(table)
            else:
                hint = QLabel("第一列为关键字，可直接编辑匹配规则")
                hint.setStyleSheet("color: gray")
                page_layout.addWidget(hint)

                table = ReorderableTable()
                table.setColumnCount(3)
                table.setHorizontalHeaderLabels(["关键字", "含义", "选择"])
                table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
                table.verticalHeader().hide()
                table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                table.setFont(QFont("Microsoft YaHei UI", 10))

                rows = rules_data.get(name, [])
                table.setRowCount(len(rows))
                auto_check = name in self.selected_tests
                for i, row_data in enumerate(rows):
                    kw = row_data[0]
                    meaning = row_data[1] if len(row_data) >= 2 else ""
                    checked = row_data[2] if len(row_data) >= 3 else auto_check
                    table.setItem(i, 0, QTableWidgetItem(kw))
                    table.setItem(i, 1, QTableWidgetItem(meaning))
                    cb = QTableWidgetItem()
                    cb.setFlags(cb.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    cb.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
                    table.setItem(i, 2, cb)

                page_layout.addWidget(table)

                btn_row = QHBoxLayout()
                add_btn = QPushButton("＋ 添加行")
                del_btn = QPushButton("－ 删除选中行")
                btn_row.addWidget(add_btn)
                btn_row.addWidget(del_btn)
                btn_row.addStretch()
                page_layout.addLayout(btn_row)

                add_btn.clicked.connect(lambda checked, t=table: self.add_row(t))
                del_btn.clicked.connect(lambda checked, t=table: self.del_row(t))

            tabs.addTab(page, f"  {name}  ")
            self.tables[name] = table

        bottom = QHBoxLayout()
        bottom.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(100)
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        bottom.addWidget(save_btn)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

        save_btn.clicked.connect(self.save)
        close_btn.clicked.connect(self.close)

    def add_row(self, table):
        cur = table.currentRow()
        row = cur + 1 if cur >= 0 else table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(""))
        table.setItem(row, 1, QTableWidgetItem(""))
        cb = QTableWidgetItem()
        cb.setFlags(cb.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        cb.setCheckState(Qt.CheckState.Unchecked)
        table.setItem(row, 2, cb)
        table.selectRow(row)

    def del_row(self, table):
        row = table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要删除的行")
            return
        table.removeRow(row)

    def save(self):
        existing = load_rules()
        data = {k: list(v) for k, v in existing.items()}
        for name, table in self.tables.items():
            if name == "设备信息":
                rows = []
                for r in range(table.rowCount()):
                    nm = table.item(r, 0).text().strip() if table.item(r, 0) else ""
                    pat = table.item(r, 1).text().strip() if table.item(r, 1) else ""
                    info = table.item(r, 2).text().strip() if table.item(r, 2) else ""
                    rows.append([nm, pat, info])
                save_device_info(rows)
            else:
                rows = []
                for r in range(table.rowCount()):
                    kw = table.item(r, 0)
                    meaning = table.item(r, 1)
                    kw_text = kw.text().strip() if kw else ""
                    meaning_text = meaning.text().strip() if meaning else ""
                    cb_item = table.item(r, 2)
                    checked = cb_item.checkState() == Qt.CheckState.Checked if cb_item else True
                    if kw_text:
                        phase = ""
                        if name in existing:
                            for er in existing[name]:
                                if er[0] == kw_text and len(er) >= 4:
                                    phase = er[3]
                                    break
                        rows.append([kw_text, meaning_text, checked, phase])
            data[name] = rows

        save_rules(data)
        QMessageBox.information(self, "成功", f"已保存到 {JSON_PATH}")


class TimeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("时间配置")
        self.setMinimumSize(800, 400)
        self.resize(900, 500)

        config = load_config()
        self.test_names = config.get("test_selection", [])
        all_rules = load_time_rules()
        time_rules = [r for r in all_rules if r[0] in self.test_names]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        hint = QLabel("可增删行。第二、三列填写正则匹配规则，第四列填写参考时间，第五列勾选时多匹配取最短")
        hint.setStyleSheet("color: gray")
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["测试选择", "开始时间打印", "结束时间打印", "参考时间", "取最短"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setFont(QFont("Microsoft YaHei UI", 10))

        self._load_rows(time_rules)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("＋ 添加行")
        del_btn = QPushButton("－ 删除选中行")
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        bottom = QHBoxLayout()
        bottom.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(100)
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        bottom.addWidget(save_btn)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.del_row)
        save_btn.clicked.connect(self.save)
        close_btn.clicked.connect(self.close)

    def _load_rows(self, time_rules):
        self.table.setRowCount(len(time_rules))
        for i, rule in enumerate(time_rules):
            name = rule[0] if len(rule) >= 1 else ""
            start = rule[1] if len(rule) >= 2 else ""
            end = rule[2] if len(rule) >= 3 else ""
            ref = rule[3] if len(rule) >= 4 else ""
            use_min = rule[4] if len(rule) >= 5 else False
            item = QTableWidgetItem(name)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QTableWidgetItem(start))
            self.table.setItem(i, 2, QTableWidgetItem(end))
            self.table.setItem(i, 3, QTableWidgetItem(ref))
            cb = QTableWidgetItem()
            cb.setFlags(cb.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            cb.setCheckState(Qt.CheckState.Checked if use_min else Qt.CheckState.Unchecked)
            self.table.setItem(i, 4, cb)

    def _sort_by_test(self):
        rows = []
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 0).text().strip()
            start = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
            end = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
            ref = self.table.item(r, 3).text().strip() if self.table.item(r, 3) else ""
            cb = self.table.item(r, 4)
            use_min = cb.checkState() == Qt.CheckState.Checked if cb else False
            rows.append([name, start, end, ref, use_min])
        order = {n: i for i, n in enumerate(self.test_names)}
        rows.sort(key=lambda r: order.get(r[0], 999))
        self.table.setRowCount(0)
        self._load_rows(rows)

    def add_row(self):
        if not self.test_names:
            QMessageBox.warning(self, "提示", "没有可选的测试项目，请先在配置中选择")
            return
        if len(self.test_names) == 1:
            name = self.test_names[0]
        else:
            name, ok = QInputDialog.getItem(self, "选择测试", "请选择测试项目:", self.test_names, 0, False)
            if not ok:
                return
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem(name)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, item)
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.setItem(row, 2, QTableWidgetItem(""))
        self.table.setItem(row, 3, QTableWidgetItem(""))
        cb = QTableWidgetItem()
        cb.setFlags(cb.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        cb.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 4, cb)
        self._sort_by_test()
        # 选中新增的行
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).text().strip() == name:
                self.table.selectRow(r)

    def del_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要删除的行")
            return
        self.table.removeRow(row)

    def save(self):
        all_rules = load_time_rules()
        merged = [r for r in all_rules if r[0] not in self.test_names]
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 0).text().strip()
            start = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
            end = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
            ref = self.table.item(r, 3).text().strip() if self.table.item(r, 3) else ""
            cb = self.table.item(r, 4)
            use_min = cb.checkState() == Qt.CheckState.Checked if cb else False
            merged.append([name, start, end, ref, use_min])
        save_time_rules(merged)
        QMessageBox.information(self, "成功", "时间配置已保存")

class AnomalyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("异常配置")
        self.setMinimumSize(900, 400)
        self.resize(1050, 550)

        self.all_test_names = ["RESET", "绑定解绑", "卡刷OTA升级", "开关机", "休眠唤醒", "TF卡", "通用"]
        config = load_config()
        selected = set(config.get("test_selection", []) + ["通用"])
        anomaly_rules = [r for r in load_anomaly_rules() if r[0] in selected]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        hint = QLabel("可增删行。第一列为测试选择，第二列为关键字，第三列为含义，第四列勾选启用，第五列勾选仅显示次数")
        hint.setStyleSheet("color: gray")
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["测试选择", "关键字", "含义", "启用", "仅显示次数"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setFont(QFont("Microsoft YaHei UI", 10))

        self._load_rows(anomaly_rules)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("＋ 添加行")
        del_btn = QPushButton("－ 删除选中行")
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        bottom = QHBoxLayout()
        bottom.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(100)
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        bottom.addWidget(save_btn)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.del_row)
        save_btn.clicked.connect(self.save)
        close_btn.clicked.connect(self.close)

    def _load_rows(self, anomaly_rules):
        self.table.setRowCount(len(anomaly_rules))
        for i, rule in enumerate(anomaly_rules):
            test = rule[0] if len(rule) >= 1 else "通用"
            pattern = rule[1] if len(rule) >= 2 else ""
            meaning = rule[2] if len(rule) >= 3 else ""
            enabled = rule[3] if len(rule) >= 4 else True
            count_only = rule[4] if len(rule) >= 5 else False
            item = QTableWidgetItem(test)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QTableWidgetItem(pattern))
            self.table.setItem(i, 2, QTableWidgetItem(meaning))
            cb = QTableWidgetItem()
            cb.setFlags(cb.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            cb.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
            self.table.setItem(i, 3, cb)
            cb2 = QTableWidgetItem()
            cb2.setFlags(cb2.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            cb2.setCheckState(Qt.CheckState.Checked if count_only else Qt.CheckState.Unchecked)
            self.table.setItem(i, 4, cb2)

    def _sort_by_test(self):
        rows = []
        for r in range(self.table.rowCount()):
            test = self.table.item(r, 0).text().strip()
            pattern = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
            meaning = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
            cb = self.table.item(r, 3)
            enabled = cb.checkState() == Qt.CheckState.Checked if cb else True
            cb2 = self.table.item(r, 4)
            count_only = cb2.checkState() == Qt.CheckState.Checked if cb2 else False
            rows.append([test, pattern, meaning, enabled, count_only])
        order = {n: i for i, n in enumerate(self.all_test_names)}
        rows.sort(key=lambda r: order.get(r[0], 999))
        self.table.setRowCount(0)
        self._load_rows(rows)

    def add_row(self):
        all_items = self.all_test_names
        if len(all_items) == 1:
            name = all_items[0]
        else:
            name, ok = QInputDialog.getItem(self, "选择测试", "请选择测试项目:", all_items, 0, False)
            if not ok:
                return
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem(name)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, item)
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.setItem(row, 2, QTableWidgetItem(""))
        cb = QTableWidgetItem()
        cb.setFlags(cb.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        cb.setCheckState(Qt.CheckState.Checked)
        self.table.setItem(row, 3, cb)
        cb2 = QTableWidgetItem()
        cb2.setFlags(cb2.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        cb2.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 4, cb2)
        self._sort_by_test()
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).text().strip() == name:
                self.table.selectRow(r)

    def del_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要删除的行")
            return
        self.table.removeRow(row)

    def save(self):
        all_rules = load_anomaly_rules()
        merged = [r for r in all_rules if r[0] not in self.all_test_names]
        for r in range(self.table.rowCount()):
            test = self.table.item(r, 0).text().strip()
            pattern = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
            meaning = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
            cb = self.table.item(r, 3)
            enabled = cb.checkState() == Qt.CheckState.Checked if cb else True
            cb2 = self.table.item(r, 4)
            count_only = cb2.checkState() == Qt.CheckState.Checked if cb2 else False
            if pattern:
                merged.append([test, pattern, meaning, enabled, count_only])
        save_anomaly_rules(merged)
        QMessageBox.information(self, "成功", "异常配置已保存")


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置")
        self.setFixedSize(300, 340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("测试选择")
        title.setFont(QFont("Microsoft YaHei UI", 13))
        layout.addWidget(title)

        group = QGroupBox()
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 12px 8px;
                background: #fafafa;
            }
        """)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)

        self.checkboxes = {}
        items = ["RESET", "绑定解绑", "卡刷OTA升级", "开关机", "休眠唤醒", "TF卡"]
        config = load_config()
        saved_selection = config.get("test_selection", [])
        for item in items:
            cb = QCheckBox(item)
            cb.setFont(QFont("Microsoft YaHei UI", 10))
            cb.setChecked(item in saved_selection)
            cb.setStyleSheet("padding: 2px 4px;")
            group_layout.addWidget(cb)
            self.checkboxes[item] = cb

        layout.addWidget(group)
        layout.addStretch()

        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        bottom.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setFixedSize(100, 32)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4a9eff; color: white; border: none;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #3a8eef; }
        """)
        quit_btn = QPushButton("取消")
        quit_btn.setFixedSize(100, 32)
        bottom.addWidget(save_btn)
        bottom.addWidget(quit_btn)
        layout.addLayout(bottom)

        save_btn.clicked.connect(self.save)
        quit_btn.clicked.connect(self.close)

    def save(self):
        checked = [name for name, cb in self.checkboxes.items() if cb.isChecked()]
        if not checked:
            QMessageBox.warning(self, "提示", "请至少选择一个测试项")
            return

        save_config({"test_selection": checked})

        lines = ["测试选择:"]
        for name in checked:
            lines.append(f"  ✔ {name}")
        QMessageBox.information(self, "已保存", "\n".join(lines))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日志关键信息分析")
        self.resize(900, 650)

        self.current_file = None
        self.current_folder = None
        self.current_multi_folder = None
        self.raw_content = ""
        self.raw_lines = []
        self._last_sections = []
        self._realtime_file_size = 0
        self.run_mode = "offline"
        self.realtime_running = False
        self.realtime_interval_min = 30
        self.last_analysis = None
        self.last_update = None

        self.realtime_timer = QTimer(self)
        self.realtime_timer.timeout.connect(self._refresh_realtime)

        self._build_menu()
        self._build_central()

        new_shortcut = QAction("新建", self)
        new_shortcut.setShortcut("Ctrl+N")
        new_shortcut.triggered.connect(self.new_file)
        self.addAction(new_shortcut)

        open_shortcut = QAction("打开", self)
        open_shortcut.setShortcut("Ctrl+O")
        open_shortcut.triggered.connect(self.open_file)
        self.addAction(open_shortcut)

        open_folder_shortcut = QAction("打开文件夹", self)
        open_folder_shortcut.setShortcut("Ctrl+D")
        open_folder_shortcut.triggered.connect(self.open_folder)
        self.addAction(open_folder_shortcut)

        multi_folder_shortcut = QAction("打开多设备文件夹", self)
        multi_folder_shortcut.setShortcut("Ctrl+Shift+D")
        multi_folder_shortcut.triggered.connect(self.open_multi_device_folder)
        self.addAction(multi_folder_shortcut)

        saveas_shortcut = QAction("另存为", self)
        saveas_shortcut.setShortcut("Ctrl+Shift+S")
        saveas_shortcut.triggered.connect(self.save_as_file)
        self.addAction(saveas_shortcut)

    def _build_menu(self):
        menubar = self.menuBar()
        menubar_font = QFont("Microsoft YaHei UI", 9)

        file_menu = menubar.addMenu("文件")
        file_menu.setFont(menubar_font)

        open_act = QAction("打开    Ctrl+O", self)
        open_act.triggered.connect(self.open_file)
        file_menu.addAction(open_act)

        open_folder_act = QAction("打开文件夹    Ctrl+D", self)
        open_folder_act.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_act)

        multi_folder_act = QAction("打开多设备文件夹    Ctrl+Shift+D", self)
        multi_folder_act.triggered.connect(self.open_multi_device_folder)
        file_menu.addAction(multi_folder_act)

        saveas_act = QAction("导出PDF    Ctrl+Shift+S", self)
        saveas_act.triggered.connect(self.save_as_file)
        file_menu.addAction(saveas_act)

        config_menu = menubar.addMenu("配置")
        config_menu.setFont(menubar_font)

        self.test_items = ["RESET", "绑定解绑", "卡刷OTA升级", "开关机", "休眠唤醒", "TF卡"]
        self.test_actions = {}

        config = load_config()
        saved_selection = config.get("test_selection", [])

        for item in self.test_items:
            is_checked = item in saved_selection
            label = f"● {item}" if is_checked else f"  {item}"
            action = QAction(label, self)
            action.setData(item)
            action.triggered.connect(lambda checked=False, a=action: self._toggle_test(a))
            config_menu.addAction(action)
            self.test_actions[item] = action

        keyword_menu = menubar.addMenu("关键字")
        keyword_menu.setFont(menubar_font)
        keyword_act = QAction("打开关键字", self)
        keyword_act.triggered.connect(self.open_rule)
        keyword_menu.addAction(keyword_act)

        time_menu = menubar.addMenu("时间")
        time_menu.setFont(menubar_font)
        time_act = QAction("打开时间配置", self)
        time_act.triggered.connect(self.open_time)
        time_menu.addAction(time_act)

        anomaly_menu = menubar.addMenu("异常")
        anomaly_menu.setFont(menubar_font)
        anomaly_act = QAction("打开异常配置", self)
        anomaly_act.triggered.connect(self.open_anomaly)
        anomaly_menu.addAction(anomaly_act)

        calc_menu = menubar.addMenu("计算")
        calc_menu.setFont(menubar_font)

        runall_act = QAction("我全都要", self)
        runall_act.triggered.connect(self.run_all)
        calc_menu.addAction(runall_act)

        calc_menu.addSeparator()

        keyprint_act = QAction("关键打印", self)
        keyprint_act.triggered.connect(self.run_match)
        calc_menu.addAction(keyprint_act)

        keytime_act = QAction("关键时间", self)
        keytime_act.triggered.connect(self.run_keytime)
        calc_menu.addAction(keytime_act)

        anomaly_calc_act = QAction("异常检测", self)
        anomaly_calc_act.triggered.connect(self.run_anomaly)
        calc_menu.addAction(anomaly_calc_act)

        verinfo_act = QAction("升级版本", self)
        verinfo_act.triggered.connect(self.run_upgrade_version)
        calc_menu.addAction(verinfo_act)

        mode_menu = menubar.addMenu("模式")
        mode_menu.setFont(menubar_font)

        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusive(True)

        self.act_offline = QAction("离线", self)
        self.act_offline.setCheckable(True)
        self.act_offline.setChecked(True)
        self.act_offline.triggered.connect(lambda: self._on_mode_changed("offline"))
        self.mode_group.addAction(self.act_offline)
        mode_menu.addAction(self.act_offline)

        self.act_realtime = QAction("实时", self)
        self.act_realtime.setCheckable(True)
        self.act_realtime.triggered.connect(lambda: self._on_mode_changed("realtime"))
        self.mode_group.addAction(self.act_realtime)
        mode_menu.addAction(self.act_realtime)

        mode_menu.addSeparator()

        self.interval_menu = mode_menu.addMenu("刷新间隔")
        self.interval_group = QActionGroup(self)
        self.interval_group.setExclusive(True)
        self.interval_actions = []
        for minutes in [30, 60, 90, 120, 180, 240, 360, 720, 1440]:
            act = QAction(self._fmt_interval(minutes), self)
            act.setCheckable(True)
            act.setData(minutes)
            if minutes == self.realtime_interval_min:
                act.setChecked(True)
            act.triggered.connect(lambda checked=False, m=minutes: self._set_interval(m))
            self.interval_group.addAction(act)
            self.interval_menu.addAction(act)
            self.interval_actions.append(act)

        mode_menu.addSeparator()

        self.act_listen = QAction("▶  开始监听", self)
        self.act_listen.triggered.connect(self._toggle_realtime)
        mode_menu.addAction(self.act_listen)
        self._refresh_mode_ui()

        help_menu = menubar.addMenu("帮助")
        help_menu.setFont(menubar_font)

        ver_act = QAction("版本", self)
        ver_act.triggered.connect(lambda: self._show_info_dialog(
            "版本信息", "BigBoom",
            "V0.99", "日志关键信息分析工具"
        ))
        help_menu.addAction(ver_act)

        about_act = QAction("关于", self)
        about_act.triggered.connect(lambda: self._show_info_dialog(
            "关于", "联系我们",
            "zhoujun@glazero.com", "深圳致翎科技有限公司"
        ))
        help_menu.addAction(about_act)

        copyright_act = QAction("版权", self)
        copyright_act.triggered.connect(lambda: self._show_info_dialog(
            "版权声明", "© 2025",
            "深圳致翎科技有限公司",
            "本软件受中华人民共和国著作权法及国际版权条约保护。\n未经许可，不得复制、分发或反向工程。"
        ))
        help_menu.addAction(copyright_act)

    def _show_info_dialog(self, title, brand, line1, line2):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(340)
        dlg.setMaximumWidth(460)
        dlg.setStyleSheet("QDialog { background: #ffffff; }")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(30, 22, 30, 18)
        layout.setSpacing(0)

        # ── Icon + Brand ──
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_lbl = QLabel("●")
        icon_lbl.setStyleSheet(
            "color: #0969da; font-size: 18px; background: transparent;"
        )
        icon_lbl.setFixedWidth(24)
        header_row.addWidget(icon_lbl)

        brand_lbl = QLabel(brand)
        brand_lbl.setStyleSheet(
            "color: #1f2328; font-size: 18px; font-weight: 700; background: transparent;"
        )
        header_row.addWidget(brand_lbl, 1)
        layout.addLayout(header_row)

        sub_lbl = QLabel(line1)
        sub_lbl.setStyleSheet(
            "color: #6e7781; font-size: 12px; background: transparent; "
            "padding-left: 34px; padding-bottom: 4px;"
        )
        layout.addWidget(sub_lbl)

        # ── Divider ──
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #e1e4e8; margin: 10px 0 12px 0; max-height: 1px;")
        layout.addWidget(div)

        # ── Body ──
        body_text = QLabel(line2)
        body_text.setWordWrap(True)
        body_text.setStyleSheet(
            "color: #57606a; font-size: 13px; line-height: 1.7;"
            "background: transparent;"
        )
        layout.addWidget(body_text)

        layout.addSpacing(16)

        # ── Button ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(88, 32)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #f6f8fa; color: #1f2328;
                border: 1px solid #d0d7de; border-radius: 6px;
                font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background: #eaecef; }
            QPushButton:pressed { background: #d0d7de; }
        """)
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    def _build_central(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.path_label = QLabel("未打开文件，请点击 文件→打开 或 Ctrl+O 选择日志文件")
        self.path_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.path_label.setTextFormat(Qt.TextFormat.RichText)
        self.path_label.setStyleSheet(
            "padding: 5px 14px; background: #eaecef; "
            "border-bottom: 1px solid #c8ccd1; color: #555a63;"
        )
        layout.addWidget(self.path_label)

        self.output = QTreeWidget()
        self.output.setHeaderHidden(True)
        self.output.setFont(QFont("Consolas", 11))
        self.output.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        self.output.setIndentation(16)
        layout.addWidget(self.output)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(22)
        self.progress.setTextVisible(True)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.setCentralWidget(central)

    @staticmethod
    def _fmt_interval(minutes):
        if minutes < 60:
            return f"{minutes} 分钟"
        if minutes % 60 == 0:
            return f"{minutes // 60} 小时"
        return f"{minutes / 60:.1f} 小时"

    def _refresh_mode_ui(self):
        """同步「模式」菜单里各 QAction 的勾选/文字状态"""
        if hasattr(self, "act_offline"):
            self.act_offline.setChecked(self.run_mode == "offline")
            self.act_realtime.setChecked(self.run_mode == "realtime")
        if hasattr(self, "interval_menu"):
            self.interval_menu.setEnabled(self.run_mode == "realtime")
        if hasattr(self, "act_listen"):
            if self.realtime_running:
                self.act_listen.setText("■  停止监听")
            else:
                self.act_listen.setText("▶  开始监听")
            self.act_listen.setEnabled(
                self.run_mode == "realtime" or self.realtime_running
            )
        if hasattr(self, "interval_actions"):
            for act in self.interval_actions:
                act.setChecked(act.data() == self.realtime_interval_min)
        self._update_path_label()

    def _update_path_label(self):
        if not hasattr(self, "path_label"):
            return
        if not self.current_file and not self.current_folder:
            if self.raw_content:
                return
            self.path_label.setText("未打开文件，请点击 文件→打开 或 Ctrl+O 选择日志文件")
            self.path_label.setStyleSheet(
                "padding: 5px 14px; background: #eaecef; "
                "border-bottom: 1px solid #c8ccd1; color: #555a63;"
            )
            return

        if self.current_file:
            try:
                size_mb = os.path.getsize(self.current_file) / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB"
            except OSError:
                size_str = "-"
            lines_str = f"{len(self.raw_lines)} 行" if self.raw_lines else ""
            meta = " · ".join(filter(None, [self.current_file, size_str, lines_str]))
        else:
            meta = f"文件夹: {self.current_folder}  ·  {len(self.raw_lines)} 行"

        if self.realtime_running:
            every = self._fmt_interval(self.realtime_interval_min)
            updated = (
                f"上次刷新 {self.last_update.strftime('%H:%M:%S')}"
                if self.last_update else "等待首次刷新"
            )
            self.path_label.setText(
                f'<span style="color:#1a7f37;">●</span>&nbsp;'
                f'<b>LIVE</b>&nbsp;·&nbsp;每 {every}&nbsp;·&nbsp;{updated}'
                f'&nbsp;&nbsp;<span style="color:#8a8f97;">|</span>&nbsp;&nbsp;'
                f'<span style="color:#555a63;">{meta}</span>'
            )
            self.path_label.setStyleSheet(
                "padding: 5px 14px; background: #ecfdf3; "
                "border-bottom: 1px solid #b7e4c7; color: #1f2937;"
            )
        else:
            self.path_label.setText(meta)
            self.path_label.setStyleSheet(
                "padding: 5px 14px; background: #eaecef; "
                "border-bottom: 1px solid #c8ccd1; color: #1f2937;"
            )

    def _on_mode_changed(self, mode):
        if mode == self.run_mode:
            self._refresh_mode_ui()
            return
        if mode == "offline" and self.realtime_running:
            self._stop_realtime()
        self.run_mode = mode
        self._refresh_mode_ui()

    def _set_interval(self, minutes):
        self.realtime_interval_min = minutes
        if self.realtime_running:
            self.realtime_timer.start(minutes * 60 * 1000)
        self._refresh_mode_ui()

    def _toggle_realtime(self):
        if self.realtime_running:
            self._stop_realtime()
        else:
            self._start_realtime()

    def _start_realtime(self):
        if self.run_mode != "realtime":
            QMessageBox.information(
                self, "提示", "当前是离线模式，请先在 模式→实时 切换到实时模式"
            )
            return
        if not self.current_file and not self.current_folder:
            QMessageBox.information(
                self, "提示", "请先用 文件→打开 选择日志文件，或用 文件→打开文件夹 选择目录"
            )
            return
        self.realtime_timer.start(self.realtime_interval_min * 60 * 1000)
        self.realtime_running = True
        self.last_update = None

        self.last_analysis = self.run_all
        self._refresh_mode_ui()
        self._refresh_realtime()

    def _stop_realtime(self):
        self.realtime_timer.stop()
        self.realtime_running = False
        self._refresh_mode_ui()

    def _refresh_realtime(self):
        if self.current_folder:
            self._refresh_realtime_folder()
        else:
            self._refresh_realtime_file()

    def _refresh_realtime_file(self):
        if not self.current_file or not os.path.isfile(self.current_file):
            return

        try:
            current_size = os.path.getsize(self.current_file)
        except OSError:
            return

        prev_size = getattr(self, '_realtime_file_size', 0)

        if current_size < prev_size:
            # File truncated/rotated — full re-read
            prev_size = 0
            self.raw_content = ""
            self.raw_lines = []

        if current_size == prev_size:
            self._rerun_analysis()
            self.last_update = datetime.now()
            self._update_path_label()
            return  # No new data

        with open(self.current_file, "rb") as f:
            f.seek(prev_size)
            new_bytes = f.read()

        new_content = None
        for enc in ["utf-8", "gbk", "utf-16", "latin-1"]:
            try:
                new_content = new_bytes.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if new_content is None:
            return

        self.raw_content += new_content
        new_lines = new_content.split("\n")
        # Merge partial line at the boundary
        if self.raw_lines and new_lines:
            self.raw_lines[-1] += new_lines[0]
            self.raw_lines.extend(new_lines[1:])
        else:
            self.raw_lines.extend(new_lines)

        self._realtime_file_size = current_size
        self._extract_device_info(self.raw_content)
        self._rerun_analysis()
        self.last_update = datetime.now()
        self._update_path_label()

    def _refresh_realtime_folder(self):
        if not self.current_folder or not os.path.isdir(self.current_folder):
            return
        merged, file_count, total_lines = self._merge_folder_files(self.current_folder)
        if merged is None:
            return
        self.raw_content = "\n".join(merged)
        self.raw_lines = merged
        self._extract_device_info(self.raw_content)
        self._rerun_analysis()
        self.last_update = datetime.now()
        self._update_path_label()

    def _rerun_analysis(self):
        if self.last_analysis is not None:
            try:
                self.last_analysis(silent=True)
            except TypeError:
                self.last_analysis()

    def _show_sections(self, sections):
        """sections: list of (title, lines) — title is bold collapsible header"""
        self._last_sections = sections
        self.output.clear()
        for title, lines in sections:
            parent = QTreeWidgetItem(self.output)
            parent.setText(0, title)
            f = parent.font(0)
            f.setBold(True)
            parent.setFont(0, f)
            for line in lines:
                child = QTreeWidgetItem(parent)
                child.setText(0, line)
        self.output.expandAll()

    def _show_plain(self, text):
        self._last_sections = [("分析结果", text.split("\n"))] if text else []
        self.output.clear()
        if text:
            item = QTreeWidgetItem(self.output)
            item.setText(0, text)

    def _get_plain_text(self):
        lines = []

        def walk(item):
            lines.append(item.text(0))
            for i in range(item.childCount()):
                walk(item.child(i))

        for i in range(self.output.topLevelItemCount()):
            walk(self.output.topLevelItem(i))
        return "\n".join(lines)

    def new_file(self):
        if self._get_plain_text().strip():
            reply = QMessageBox.question(
                self, "确认", "当前内容未保存，是否新建？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
        if self.realtime_running:
            self._stop_realtime()
        self.output.clear()
        self.current_file = None
        self.current_folder = None
        self.current_multi_folder = None
        self.raw_content = ""
        self.raw_lines = []
        self.last_analysis = None
        self._realtime_file_size = 0
        self._update_path_label()
        self.setWindowTitle("日志关键信息分析 - 未命名")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "日志文件 (*.log *.txt)"
        )
        if not path:
            return

        content = _read_file_bytes(path)
        if content is None:
            QMessageBox.critical(self, "错误", "无法识别文件编码")
            return

        self.raw_content = content
        self.raw_lines = content.split("\n")
        self.output.clear()
        self.current_file = path
        self.current_folder = None
        self.last_analysis = None
        self._realtime_file_size = os.path.getsize(path)
        self.setWindowTitle(f"日志关键信息分析 - {os.path.basename(path)}")
        self.progress.setValue(0)
        self._update_path_label()

        # 自动提取设备信息
        self._extract_device_info(content)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "打开文件夹")
        if not folder:
            return

        merged, file_count, total_lines = self._merge_folder_files(folder)
        if merged is None:
            return

        self.progress.setMaximum(1)
        self.progress.setFormat("拼接文本中…")
        QApplication.processEvents()
        self.raw_content = "\n".join(merged)
        self.raw_lines = merged
        self.progress.setValue(1)
        QApplication.processEvents()
        self.output.clear()
        self.current_file = None
        self.current_folder = folder
        self.last_analysis = None
        self.path_label.setText(
            f"文件夹: {folder}  ·  {file_count} 个文件  ·  {total_lines} 行"
        )
        self.path_label.setStyleSheet(
            "padding: 5px 14px; background: #eaecef; "
            "border-bottom: 1px solid #c8ccd1; color: #1f2937;"
        )
        self.setWindowTitle(f"日志关键信息分析 - {os.path.basename(folder)}")
        self.progress.setValue(0)
        self.progress.setFormat("%p%")

        self._extract_device_info(self.raw_content)

    def open_multi_device_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "打开多设备文件夹")
        if not folder:
            return

        subdirs = [os.path.join(folder, d) for d in os.listdir(folder)
                   if os.path.isdir(os.path.join(folder, d))]
        subdirs.sort()

        if not subdirs:
            QMessageBox.information(self, "提示", "所选文件夹中没有子文件夹")
            return

        if self.realtime_running:
            self._stop_realtime()

        saved_content = self.raw_content
        saved_lines = self.raw_lines
        saved_file = self.current_file
        saved_folder = self.current_folder

        self.current_file = None
        self.current_folder = None

        all_sections = []
        total_devices = len(subdirs)

        for di, subdir in enumerate(subdirs):
            device_name = os.path.basename(subdir)
            self.progress.setFormat(f"处理设备 {di + 1}/{total_devices}: {device_name} … %p%")
            self.progress.setValue(0)
            QApplication.processEvents()

            merged, file_count, total_lines = self._merge_folder_files(subdir)
            if merged is None:
                continue

            self.raw_content = "\n".join(merged)
            self.raw_lines = merged
            self._extract_device_info(self.raw_content)

            device_sections = self._run_device_analysis(device_name, file_count, total_lines)
            all_sections.extend(device_sections)

        self.raw_content = saved_content
        self.raw_lines = saved_lines
        self.current_file = saved_file
        self.current_folder = saved_folder
        self.current_multi_folder = folder

        self.progress.setFormat("%p%")
        self.progress.setValue(0)
        self._last_sections = all_sections
        self._show_sections(all_sections)
        self.path_label.setText(
            f"多设备文件夹: {folder}  ·  {total_devices} 个设备"
        )
        self.path_label.setStyleSheet(
            "padding: 5px 14px; background: #eaecef; "
            "border-bottom: 1px solid #c8ccd1; color: #1f2937;"
        )
        self.setWindowTitle(f"日志关键信息分析 - 多设备 {os.path.basename(folder)}")
        QMessageBox.information(self, "完成", f"已完成 {total_devices} 个设备的分析")

    def _run_device_analysis(self, device_name, file_count, total_lines):
        sections = []

        def _clean(secs):
            return [(t, l) for t, l in secs if "设备信息" not in t and "异常检测" not in t]

        # 设备头部：文件夹名 + 设备信息
        device_info = load_device_info()
        header_lines = [f"文件夹: {device_name}", f"文件: {file_count} 个, {total_lines} 行"]
        for row in device_info:
            nm = row[0]
            info = row[2] if len(row) >= 3 else ""
            if info:
                header_lines.append(f"{nm}: {info}")
        sections.append((f"▍设备: {device_name}", header_lines))

        # 关键打印
        self.progress.setFormat(f"{device_name} - 关键打印… %p%")
        QApplication.processEvents()
        self.run_match(silent=True)
        if self._last_sections:
            sections.append((f"▍{device_name} - 关键打印", []))
            sections.extend(_clean(self._last_sections))

        # 关键时间
        self.progress.setFormat(f"{device_name} - 关键时间… %p%")
        QApplication.processEvents()
        self.run_keytime(silent=True)
        if self._last_sections:
            sections.append((f"▍{device_name} - 关键时间", []))
            sections.extend(_clean(self._last_sections))

        # 异常检测
        self.progress.setFormat(f"{device_name} - 异常检测… %p%")
        QApplication.processEvents()
        self.run_anomaly(silent=True)
        if self._last_sections:
            sections.append((f"▍{device_name} - 异常检测", []))
            sections.extend(_clean(self._last_sections))

        return sections

    def _extract_device_info(self, content):
        device_info = load_device_info()
        updated = False
        for i, row in enumerate(device_info):
            pat = row[1] if len(row) >= 2 else ""
            if not pat:
                continue
            try:
                m = re.search(pat, content)
                if m:
                    extracted = m.group(1) if m.lastindex else m.group(0)
                    device_info[i][2] = extracted
                    updated = True
            except re.error:
                continue
        if updated:
            save_device_info(device_info)

    def _merge_folder_files(self, folder):
        """合并文件夹内所有 .log/.txt 文件，返回 (merged_lines, file_count, total_lines) 或 (None, 0, 0)"""
        import glob
        import heapq
        import itertools

        files = sorted(glob.glob(os.path.join(folder, "*.log")) +
                       glob.glob(os.path.join(folder, "*.txt")))
        if not files:
            QMessageBox.information(self, "提示", "所选文件夹中没有 .log 或 .txt 文件")
            return None, 0, 0

        # ------------------------------------------------------------------
        # 时间戳解析：用字符串切片代替 datetime.strptime + 正则，快 50~100 倍。
        # ISO 格式 "YYYY-MM-DD HH:MM:SS.ffffff" 天然可按字符串字典序比较。
        # ------------------------------------------------------------------
        def _sort_key(line):
            start = line.find('[')
            if start == -1:
                return '~~~~~~~~'
            end = line.find(']', start + 1)
            if end == -1:
                return '~~~~~~~~'
            ts = line[start + 1:end]
            if len(ts) < 19:
                return '~~~~~~~~'
            if len(ts) > 19 and ts[19] == '.':
                us = ts[20:]
                if len(us) < 6:
                    ts = ts[:20] + us + '0' * (6 - len(us))
                elif len(us) > 6:
                    ts = ts[:26]
            elif len(ts) == 19:
                ts = ts + '.000000'
            return ts

        def _file_iter(filepath):
            lines = _read_file_lines(filepath)
            if lines is None:
                return None
            return ((_sort_key(l), l) for l in lines), len(lines)

        # ------------------------------------------------------------------
        # 同类型文件（CPU/CPU、WiFi/WiFi）时间区间不重叠，可直接拼接。
        # 只需跨类型做 k 路归并（通常 k=2），堆深极小，每次比较 O(1)。
        # ------------------------------------------------------------------
        file_count = len(files)
        self.progress.setMaximum(file_count)

        # 逐个文件读取并分组。同类型文件时间区间不重叠，可直接拼接。
        cpu_iters, wifi_iters, other_iters = [], [], []
        total_lines = 0

        for fi, f in enumerate(files):
            self.progress.setValue(fi)
            QApplication.processEvents()
            result = _file_iter(f)
            if result is None:
                continue
            it, lc = result
            total_lines += lc
            name = os.path.basename(f).lower()
            if 'cpu' in name:
                cpu_iters.append(it)
            elif 'wifi' in name:
                wifi_iters.append(it)
            else:
                other_iters.append(it)

        self.progress.setValue(file_count)
        QApplication.processEvents()

        merge_sources = []
        if cpu_iters:
            merge_sources.append(itertools.chain(*cpu_iters))
        if wifi_iters:
            merge_sources.append(itertools.chain(*wifi_iters))
        merge_sources.extend(other_iters)

        if not merge_sources:
            QMessageBox.information(self, "提示", "没有可读取的内容")
            self.progress.setValue(0)
            return None, 0, 0

        # k 路归并（通常 k=2：CPU 流 + WiFi 流），带进度
        self.progress.setMaximum(total_lines)
        self.progress.setFormat("合并排序中… %p%")
        QApplication.processEvents()

        merged = []
        for li, (_, line) in enumerate(heapq.merge(*merge_sources, key=lambda x: x[0])):
            merged.append(line)
            if li % 5000 == 0:
                self.progress.setValue(li)
                QApplication.processEvents()

        self.progress.setValue(total_lines)
        self.progress.setFormat("%p%")
        return merged, file_count, len(merged)

    def save_file(self):
        if self.current_file:
            self._write_pdf(self.current_file)
        else:
            self.save_as_file()

    def save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出PDF", "", "PDF文件 (*.pdf)"
        )
        if not path:
            return
        self._write_pdf(path)
        self.current_file = path
        self.path_label.setText(path)
        self.setWindowTitle(f"日志关键信息分析 - {os.path.basename(path)}")

    def _register_chinese_font(self):
        font_name = "ChineseFont"
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/STSONG.TTF",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, fp, subfontIndex=0))
                    return font_name
                except Exception:
                    continue
        return None

    def _write_pdf(self, path):
        font_name = self._register_chinese_font()
        if font_name is None:
            QMessageBox.critical(self, "错误", "无法加载中文字体，请确认系统字体存在")
            return

        try:
            page_w, page_h = A4
            doc = SimpleDocTemplate(
                path, pagesize=A4,
                topMargin=28 * mm, bottomMargin=25 * mm,
                leftMargin=22 * mm, rightMargin=22 * mm,
                title="日志关键信息分析报告",
                author="BigBoom",
            )

            style_title = ParagraphStyle(
                "CNTitle", fontName=font_name, fontSize=18,
                leading=24, spaceAfter=4 * mm, alignment=TA_CENTER,
                textColor=colors.HexColor("#1a1a2e"),
            )
            style_h1 = ParagraphStyle(
                "CNH1", fontName=font_name, fontSize=12,
                leading=18, spaceBefore=6 * mm, spaceAfter=2 * mm,
                textColor=colors.HexColor("#2c3e6b"),
            )
            style_h2 = ParagraphStyle(
                "CNH2", fontName=font_name, fontSize=10,
                leading=16, spaceBefore=4 * mm, spaceAfter=1 * mm,
                textColor=colors.HexColor("#4a5568"),
            )
            style_body = ParagraphStyle(
                "CNBody", fontName=font_name, fontSize=9,
                leading=15, textColor=colors.HexColor("#333333"),
            )
            style_header = ParagraphStyle(
                "CNHeader", fontName=font_name, fontSize=8,
                leading=10, textColor=colors.HexColor("#b0b7c3"),
            )

            def on_page(canvas, doc):
                cw, ch = page_w, page_h
                canvas.saveState()

                # ── Watermark ──
                canvas.setFont(font_name, 48)
                canvas.setFillColor(colors.HexColor("#f0f0f5"))
                canvas.drawCentredString(cw / 2, ch / 2, "BigBoom")

                # ── Page header ──
                canvas.setFont(font_name, 7)
                canvas.setFillColor(colors.HexColor("#c0c5ce"))
                canvas.drawString(22 * mm, ch - 16 * mm, "BigBoom V0.99  ·  日志关键信息分析报告")
                canvas.drawRightString(cw - 22 * mm, ch - 16 * mm,
                    datetime.now().strftime("%Y-%m-%d %H:%M"))

                # ── Header line ──
                canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
                canvas.setLineWidth(0.3)
                canvas.line(22 * mm, ch - 20 * mm, cw - 22 * mm, ch - 20 * mm)

                # ── Footer ──
                canvas.setFont(font_name, 7)
                canvas.setFillColor(colors.HexColor("#b0b7c3"))
                canvas.drawCentredString(cw / 2, 12 * mm,
                    f"第 {canvas.getPageNumber()} 页  ·  BigBoom 日志分析工具  ·  深圳致翎科技")
                canvas.restoreState()

            story = []
            story.append(Paragraph("日志关键信息分析报告", style_title))
            story.append(HRFlowable(
                width="100%", thickness=0.8, color=colors.HexColor("#4a5568"),
                spaceAfter=4 * mm,
            ))

            symbol_map = {"✓": "[OK]", "✔": "[OK]", "✘": "[FAIL]"}
            for title, lines in self._last_sections:
                # Section divider (▍ prefix)
                if title.startswith("▍"):
                    story.append(HRFlowable(
                        width="100%", thickness=1.2, color=colors.HexColor("#2c3e6b"),
                        spaceBefore=3 * mm, spaceAfter=1 * mm,
                    ))
                    story.append(Paragraph(title[1:], style_h1))
                    continue
                # Spacer
                if not title and not lines:
                    story.append(Spacer(1, 2 * mm))
                    continue
                # Normal section
                if not lines:
                    story.append(Paragraph(title, style_h1))
                else:
                    story.append(Paragraph(title, style_h1))
                    for line in lines:
                        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        for old, new in symbol_map.items():
                            escaped = escaped.replace(old, new)
                        story.append(Paragraph(f"  {escaped}", style_body))
                    story.append(Spacer(1, 2 * mm))

            doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
            QMessageBox.information(self, "成功", "PDF 已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存 PDF 失败: {e}")

    def _extract_timestamp(self, line):
        if not line:
            return "--:--:--"
        m = _TIMESTAMP_RE.search(line)
        if m:
            return m.group(m.lastindex)
        return "--:--:--"

    def run_all(self, silent=False):
        if not self.raw_content:
            if not silent:
                QMessageBox.information(self, "提示", "请先打开一个日志文件或文件夹")
            return
        self.last_analysis = self.run_all

        def _clean(sections):
            return [(t, l) for t, l in sections if "设备信息" not in t and "异常检测" not in t]

        all_sections = []

        # ── 1. 关键打印 ──
        self.progress.setFormat("关键打印… %p%")
        self.progress.setValue(0)
        QApplication.processEvents()
        self.run_match(silent=True)
        if self._last_sections:
            all_sections.append(("▍关键打印", []))
            all_sections.extend(_clean(self._last_sections))

        # ── 2. 关键时间 ──
        self.progress.setFormat("关键时间… %p%")
        self.progress.setValue(0)
        QApplication.processEvents()
        self.run_keytime(silent=True)
        if self._last_sections:
            all_sections.append(("▍关键时间", []))
            all_sections.extend(_clean(self._last_sections))

        # ── 3. 异常检测 ──
        self.progress.setFormat("异常检测… %p%")
        self.progress.setValue(0)
        QApplication.processEvents()
        self.run_anomaly(silent=True)
        if self._last_sections:
            all_sections.append(("▍异常检测", []))
            all_sections.extend(_clean(self._last_sections))

        self.progress.setFormat("%p%")
        self._last_sections = all_sections
        self._show_sections(all_sections)

    def run_match(self, silent=False):
        if not self.raw_content:
            if not silent:
                QMessageBox.information(self, "提示", "请先打开一个日志文件")
            return
        self.last_analysis = self.run_match

        lines = self.raw_lines
        total = len(lines)
        if total == 0:
            if not silent:
                QMessageBox.information(self, "提示", "日志文件为空")
            return

        rules_data = load_rules()
        config = load_config()
        selected_tests = config.get("test_selection", [])

        if not selected_tests:
            if not silent:
                QMessageBox.information(self, "提示", "请先在配置中选择测试项目")
            return

        test_keywords = {}
        for test_name in selected_tests:
            if test_name not in rules_data:
                continue
            kws = []
            for rule in rules_data[test_name]:
                checked = rule[2] if len(rule) >= 3 else True
                if not checked:
                    continue
                pattern = rule[0]
                meaning = rule[1] if len(rule) >= 2 else ""
                phase = rule[3] if len(rule) >= 4 else ""
                try:
                    cre = re.compile(pattern)
                    kws.append((cre, pattern, meaning, phase))
                except re.error:
                    continue
            if kws:
                test_keywords[test_name] = kws

        if not test_keywords:
            if not silent:
                QMessageBox.information(self, "提示", "没有启用的关键字规则")
            return

        _clear_files_dir()

        states = {}
        for tn in test_keywords:
            states[tn] = {
                'start': -1,
                'seen': {},
                'incomplete': [],
                'complete_list': [],
                'total': 0,
                'complete': 0,
                'cycle_no': 0,
            }

        match_counts = {}

        self.progress.setMaximum(total)
        self.progress.setValue(0)
        self.progress.setFormat("关键打印… %p%")

        for line_idx, line in enumerate(lines):
            if not line:
                continue
            for tn, kws in test_keywords.items():
                state = states[tn]
                first_cre, first_pat, first_meaning, _ = kws[0]

                if first_cre.search(line):
                    match_counts[(tn, first_pat, first_meaning)] = match_counts.get((tn, first_pat, first_meaning), 0) + 1

                    if state['start'] >= 0:
                        if len(state['seen']) == 1 and 0 in state['seen']:
                            state['seen'][0] = line_idx
                        else:
                            state['cycle_no'] += 1
                            state['total'] += 1
                            missing = [m for i, (_, _, m, _) in enumerate(kws) if i not in state['seen']]
                            if missing:
                                state['incomplete'].append((
                                    state['cycle_no'], state['start'], line_idx,
                                    missing, state['seen'].copy()
                                ))
                            else:
                                state['complete'] += 1
                                state['complete_list'].append((
                                    state['cycle_no'], state['start'], line_idx,
                                    state['seen'].copy()
                                ))
                            state['start'] = line_idx
                            state['seen'] = {0: line_idx}
                    else:
                        state['start'] = line_idx
                        state['seen'] = {0: line_idx}

                elif state['start'] >= 0:
                    for kw_idx, (cre, pat, meaning, phase) in enumerate(kws):
                        if kw_idx == 0:
                            continue
                        if kw_idx in state['seen']:
                            continue
                        if not cre.search(line):
                            continue
                        if phase:
                            seen_meanings = {kws[i][2] for i in state['seen']}
                            if phase.startswith("before:"):
                                if phase[7:] in seen_meanings:
                                    continue
                            elif phase.startswith("after:"):
                                if phase[6:] not in seen_meanings:
                                    continue
                        match_counts[(tn, pat, meaning)] = match_counts.get((tn, pat, meaning), 0) + 1
                        state['seen'][kw_idx] = line_idx
                        break

            if line_idx % 5000 == 0:
                self.progress.setValue(line_idx)
                QApplication.processEvents()

        for tn, kws in test_keywords.items():
            state = states[tn]
            if state['start'] >= 0:
                state['cycle_no'] += 1
                state['total'] += 1
                missing = [m for i, (_, _, m, _) in enumerate(kws) if i not in state['seen']]
                if missing:
                    state['incomplete'].append((
                        state['cycle_no'], state['start'], total,
                        missing, state['seen'].copy()
                    ))
                else:
                    state['complete'] += 1
                    state['complete_list'].append((
                        state['cycle_no'], state['start'], total,
                        state['seen'].copy()
                    ))

        self.progress.setValue(total)

        sections = []

        # 设备信息
        device_info = load_device_info()
        has_device = any(row[2] for row in device_info if len(row) >= 3)
        if has_device:
            dev_lines = []
            for row in device_info:
                nm = row[0]
                info = row[2] if len(row) >= 3 else ""
                if info:
                    dev_lines.append(f"{nm}: {info}")
            sections.append(("设备信息", dev_lines))

        # 总结
        summary_lines = []
        any_incomplete = False
        for tn, state in states.items():
            kws = test_keywords[tn]
            incomplete_nums = [r[0] for r in state['incomplete']]
            summary_lines.append(f"【{tn}】")
            summary_lines.append(f"  共触发循环: {state['total']} 次")
            summary_lines.append(f"  完整循环: {state['complete']} 次")
            if state['total'] > 0:
                rate = state['complete'] / state['total'] * 100
                summary_lines.append(f"  压测成功率: {rate:.1f}%")
            if state['incomplete']:
                any_incomplete = True
                nums_str = ", ".join(f"第{n}个循环" for n in incomplete_nums)
                summary_lines.append(f"  不完整循环: {len(state['incomplete'])} 次 ({nums_str})")
            else:
                summary_lines.append("  不完整循环: 0 次")
        if not any_incomplete:
            summary_lines.append("✓ 所有测试项目的所有循环均完整")
        sections.append(("总结", summary_lines))

        # 详细结果 (不完整循环详情)
        detail_lines = []
        for tn, state in states.items():
            kws = test_keywords[tn]
            if not state['incomplete']:
                continue
            detail_lines.append(f"【{tn}】")
            for cycle_no, start, end, missing, seen in state['incomplete']:
                start_ts = self._extract_full_ts(lines[start]) if start < len(lines) else ""
                end_idx = min(end, total - 1)
                end_ts = self._extract_full_ts(lines[end_idx]) if end_idx < len(lines) else ""
                end_display = end if end < total else total
                detail_lines.append(f"  第{cycle_no}个循环 [{start_ts}] ~ [{end_ts}]")
                for kw_idx, ln in sorted(seen.items(), key=lambda x: x[1]):
                    meaning = kws[kw_idx][2]
                    ts = self._extract_full_ts(lines[ln]) if ln < len(lines) else ""
                    detail_lines.append(f"    ✔ [{ts}] {meaning}")
                for meaning in missing:
                    detail_lines.append(f"    ✘ {meaning}")
        if detail_lines:
            sections.append(("不完整循环详情", detail_lines))

        # 关键字匹配次数统计
        kw_lines = []
        for tn, kws in test_keywords.items():
            kw_lines.append(f"【{tn}】")
            for cre, pat, meaning, _ in kws:
                cnt = match_counts.get((tn, pat, meaning), 0)
                kw_lines.append(f"  {meaning}: {cnt}次")
        sections.append(("关键字匹配次数统计", kw_lines))

        self._last_sections = sections
        self._show_sections(sections)

        # 保存完整循环到 files/测试名/
        file_count = 0
        for tn, state in states.items():
            test_dir = os.path.join(FILES_DIR, tn)
            os.makedirs(test_dir, exist_ok=True)
            for cycle_no, start, end, seen in state['complete_list']:
                end_idx = min(end, total - 1)
                cycle_lines = lines[start:end_idx + 1]
                filepath = os.path.join(test_dir, f"第{cycle_no}个循环.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(cycle_lines))
                file_count += 1
        if file_count:
            self._last_sections = sections + [("文件保存", [f"✓ 已保存 {file_count} 个完整循环到 files/ 目录"])]
            self._show_sections(self._last_sections)

    def run_keytime(self, silent=False):
        if not self.raw_content:
            if not silent:
                QMessageBox.information(self, "提示", "请先打开一个日志文件")
            return
        self.last_analysis = self.run_keytime

        all_time_rules = load_time_rules()
        config = load_config()
        selected_tests = config.get("test_selection", [])

        time_rules = [r for r in all_time_rules if r[0] in selected_tests]
        if not time_rules:
            if not silent:
                QMessageBox.information(self, "提示", "没有配置时间规则，请先在时间配置中添加")
            return

        # Pre-compile regex for each rule (same rule applies to many cycle files)
        compiled_rules = {}  # id(rule) -> (start_re, end_re) or None if invalid
        for rule in time_rules:
            if not rule[1] or not rule[2]:
                compiled_rules[id(rule)] = None
                continue
            try:
                compiled_rules[id(rule)] = (re.compile(rule[1]), re.compile(rule[2]))
            except re.error:
                compiled_rules[id(rule)] = None

        # 先收集所有要处理的任务
        tasks = []  # [(test_name, cycle_file, rule, file_lines)]
        for test_name in selected_tests:
            test_dir = os.path.join(FILES_DIR, test_name)
            if not os.path.isdir(test_dir):
                continue
            test_rules = [r for r in time_rules if r[0] == test_name]
            if not test_rules:
                continue
            for cf in sorted(os.listdir(test_dir)):
                filepath = os.path.join(test_dir, cf)
                with open(filepath, "r", encoding="utf-8") as f:
                    file_lines = f.read().split("\n")
                for rule in test_rules:
                    if compiled_rules.get(id(rule)):
                        tasks.append((test_name, cf, rule, file_lines))

        if not tasks:
            if not silent:
                QMessageBox.information(self, "提示", "没有可用的完整循环文件，请先执行关键打印")
            return

        self.progress.setMaximum(len(tasks))
        self.progress.setValue(0)
        self.progress.setFormat("关键时间… %p%")

        # 先收集所有失败项，按 (test_name, rule) 分组
        from collections import OrderedDict
        grouped = OrderedDict()  # (test_name, start_pat, end_pat) -> [fail_lines, ...]
        total_pass = 0
        total_fail = 0
        rule_stats = {}
        rule_elapsed = {}

        for task_idx, (test_name, cf, rule, file_lines) in enumerate(tasks):
            self.progress.setValue(task_idx)

            name, start_pat, end_pat, ref_time_str = rule[0], rule[1], rule[2], rule[3]
            start_re, end_re = compiled_rules[id(rule)]
            use_min = rule[4] if len(rule) >= 5 else False

            # 收集所有起止匹配行，end 保留捕获组值用于动态参考
            start_matches = []
            end_matches = []
            for i, line in enumerate(file_lines):
                if start_re.search(line):
                    ts = self._parse_ts(self._extract_timestamp(line))
                    if ts is not None:
                        start_matches.append((i, ts))
                m = end_re.search(line)
                if m:
                    ts = self._parse_ts(self._extract_timestamp(line))
                    if ts is not None:
                        cap = m.group(1) if m.lastindex else None
                        end_matches.append((i, ts, cap))

            if not start_matches or not end_matches:
                continue

            rkey = (test_name, start_pat, end_pat)
            if rkey not in rule_stats:
                rule_stats[rkey] = {"pass": 0, "fail": 0}

            group_key = (test_name, start_pat, end_pat)
            if group_key not in grouped:
                grouped[group_key] = []

            if use_min:
                # 第一个结束 − 最后一个开始（必须在结束之前）
                first_end = end_matches[0]
                last_start = max(
                    (s for s in start_matches if s[0] < first_end[0]),
                    key=lambda x: x[0], default=None
                )
                if last_start is None:
                    continue
                pairs_to_check = [(last_start[1], last_start[0], first_end[1], first_end[0], first_end[2])]
            else:
                # 顺序配对：S1→E1, S2→E2, ...
                pairs_to_check = []
                si, ei = 0, 0
                while si < len(start_matches) and ei < len(end_matches):
                    if start_matches[si][0] < end_matches[ei][0]:
                        pairs_to_check.append((
                            start_matches[si][1], start_matches[si][0],
                            end_matches[ei][1], end_matches[ei][0],
                            end_matches[ei][2]
                        ))
                        si += 1
                        ei += 1
                    else:
                        ei += 1

            if not pairs_to_check:
                continue

            for start_ts, start_line, end_ts, end_line, cap_val in pairs_to_check:
                elapsed = end_ts - start_ts
                if elapsed < 0:
                    elapsed = 0
                if group_key not in rule_elapsed:
                    rule_elapsed[group_key] = []
                rule_elapsed[group_key].append(elapsed)
                ref_seconds = self._parse_dynamic_ref(ref_time_str, cap_val)

                if ref_seconds is None or elapsed <= ref_seconds:
                    total_pass += 1
                    rule_stats[rkey]["pass"] += 1
                    continue

                total_fail += 1
                rule_stats[rkey]["fail"] += 1
                start_ts_str = self._extract_full_ts(file_lines[start_line])
                end_ts_str = self._extract_full_ts(file_lines[end_line])
                ref_display = ref_time_str if ref_time_str else "-"
                grouped[group_key].append(
                    (start_ts, f"{start_ts_str} → {end_ts_str}  "
                     f"耗时: {elapsed:.1f}s  参考: {ref_display}")
                )

        self.progress.setValue(len(tasks))

        # 组装输出
        sections = []

        # 设备信息
        device_info = load_device_info()
        has_device = any(row[2] for row in device_info if len(row) >= 3)
        if has_device:
            dev_lines = []
            for row in device_info:
                nm = row[0]
                info = row[2] if len(row) >= 3 else ""
                if info:
                    dev_lines.append(f"{nm}: {info}")
            sections.append(("设备信息", dev_lines))

        # 总结
        from collections import OrderedDict
        test_summary = OrderedDict()
        for (test_name, start_pat, end_pat), st in rule_stats.items():
            if test_name not in test_summary:
                test_summary[test_name] = []
            status = "✓" if st["fail"] == 0 else "✘"
            avg_str = ""
            gkey = (test_name, start_pat, end_pat)
            if gkey in rule_elapsed and rule_elapsed[gkey]:
                avg_s = sum(rule_elapsed[gkey]) / len(rule_elapsed[gkey])
                avg_str = f"  平均耗时: {avg_s:.1f}s"
            test_summary[test_name].append(
                f"{status} {start_pat} → {end_pat}  "
                f"通过: {st['pass']}  超时: {st['fail']}{avg_str}"
            )
        summary_lines = []
        for test_name in selected_tests:
            if test_name in test_summary:
                summary_lines.append(f"【{test_name}】")
                summary_lines.extend(test_summary[test_name])
        summary_lines.append(f"合计: 通过 {total_pass} 次, 超时 {total_fail} 次")
        sections.append((f"总结  (通过 {total_pass} / 超时 {total_fail})", summary_lines))

        # 详细结果
        detail_lines = []
        if total_pass == 0 and total_fail == 0:
            detail_lines.append("无可用时间数据")
        else:
            current_test = None
            for (test_name, start_pat, end_pat), fails in grouped.items():
                if not fails:
                    continue
                if test_name != current_test:
                    current_test = test_name
                    detail_lines.append(f"【{test_name}】")
                detail_lines.append(f"  规则: {start_pat} → {end_pat}")
                fails.sort(key=lambda x: x[0] if x[0] is not None else 0)
                for idx, (_, line) in enumerate(fails, 1):
                    detail_lines.append(f"    {idx}. {line}")
        sections.append((f"详细结果  ({len(detail_lines)} 条)", detail_lines))

        self._last_sections = sections
        self._show_sections(sections)

    def _extract_full_ts(self, line):
        m = _TIMESTAMP_RE.search(line)
        if m:
            return m.group(m.lastindex)
        return "--:--:--"

    def run_upgrade_version(self, silent=False):
        if not self.raw_content:
            if not silent:
                QMessageBox.information(self, "提示", "请先打开一个日志文件")
            return
        self.last_analysis = self.run_upgrade_version

        full_versions = []
        wifi_versions = []

        for line in self.raw_lines:
            m = re.search(r"get full version (\S+)", line)
            if m:
                ts = self._extract_full_ts(line)
                full_versions.append((ts, m.group(1)))
            m = re.search(r"get wifi ver (\S+)", line)
            if m:
                ts = self._extract_full_ts(line)
                wifi_versions.append((ts, m.group(1)))

        sections = []

        def build_section(title, items):
            slines = []
            if not items:
                slines.append("(无)")
            else:
                prev = None
                for i, (ts, v) in enumerate(items, 1):
                    mark = "  +" if v == prev else ""
                    idx = f"{i:>3}."
                    slines.append(f"{idx} {ts}  {v}{mark}")
                    prev = v
            sections.append((f"{title}  ({len(items)} 条)", slines))

        build_section("主控版本", full_versions)
        build_section("Wi-Fi版本", wifi_versions)

        self._show_sections(sections)

    def run_anomaly(self, silent=False):
        if not self.raw_content:
            if not silent:
                QMessageBox.information(self, "提示", "请先打开一个日志文件或文件夹")
            return
        self.last_analysis = self.run_anomaly

        all_rules = load_anomaly_rules()
        config = load_config()
        selected_tests = config.get("test_selection", [])
        active_tests = set(selected_tests + ["通用"])
        rules = [r for r in all_rules if r[0] in active_tests and (r[3] if len(r) >= 4 else True)]
        if not rules:
            if not silent:
                QMessageBox.information(self, "提示", "没有启用的异常规则")
            return

        keywords = [(r[1], r[2]) for r in rules if r[1]]
        if not keywords:
            return

        count_only_map = {r[2]: (r[4] if len(r) >= 5 else False) for r in rules if r[1]}

        # 将所有关键字编译成一个正则交替式，作为快速预过滤器。
        # 只有命中关键字的行才进入逐关键字检查，避免每行都做 O(M) 次 substring。
        combined_re = re.compile('|'.join(re.escape(kw) for kw, _ in keywords))

        lines = self.raw_lines
        total = len(lines)
        self.progress.setMaximum(total)
        self.progress.setValue(0)
        self.progress.setFormat("异常检测… %p%")

        from collections import OrderedDict
        results = OrderedDict()

        for line_idx, line in enumerate(lines):
            if not line:
                continue
            if combined_re.search(line):
                ts = None
                for keyword, meaning in keywords:
                    if keyword in line:
                        if ts is None:
                            ts = self._extract_full_ts(line)
                        results.setdefault(meaning, []).append((ts, line_idx, keyword))
            if line_idx % 5000 == 0:
                self.progress.setValue(line_idx)
                QApplication.processEvents()

        self.progress.setValue(total)

        test_label = "、".join(selected_tests) if selected_tests else "全部"
        lines_found = sum(len(v) for v in results.values())

        sections = []

        # 标题
        sections.append((f"异常检测 — 测试项: {test_label}  规则: {len(keywords)} 条  命中: {lines_found} 次", []))

        # 设备信息
        device_info = load_device_info()
        has_device = any(row[2] for row in device_info if len(row) >= 3)
        if has_device:
            dev_lines = []
            for row in device_info:
                nm = row[0]
                info = row[2] if len(row) >= 3 else ""
                if info:
                    dev_lines.append(f"{nm}: {info}")
            sections.append(("设备信息", dev_lines))

        # 总结
        summary_lines = []
        total_matches = 0
        for meaning, matches in results.items():
            summary_lines.append(f"  {meaning}: {len(matches)} 次匹配")
            total_matches += len(matches)
        summary_lines.insert(0, f"合计命中: {total_matches} 次")
        sections.append(("总结", summary_lines))

        # 详细结果
        detail_lines = []
        for meaning, matches in results.items():
            if count_only_map.get(meaning, False):
                detail_lines.append(f"【{meaning}】 ({len(matches)} 条)")
                kw_counts = {}
                for _, _, kw in matches:
                    kw_counts[kw] = kw_counts.get(kw, 0) + 1
                for kw, cnt in kw_counts.items():
                    snippet = kw if len(kw) <= 80 else kw[:77] + "..."
                    detail_lines.append(f"  {snippet}: {cnt}次")
            else:
                detail_lines.append(f"【{meaning}】 ({len(matches)} 条)")
                for i, (ts, line_idx, keyword) in enumerate(matches, 1):
                    snippet = keyword if len(keyword) <= 120 else keyword[:117] + "..."
                    detail_lines.append(f"  {i:>4}. [{ts}] 行{line_idx + 1}  {snippet}")
        if not detail_lines:
            detail_lines.append("未匹配到任何异常规则")
        sections.append(("详细结果", detail_lines))

        self._last_sections = sections
        self._show_sections(sections)

    def run_merge(self):
        path1, _ = QFileDialog.getOpenFileName(
            self, "选择第一个日志文件", "", "日志文件 (*.log *.txt)"
        )
        if not path1:
            return
        path2, _ = QFileDialog.getOpenFileName(
            self, "选择第二个日志文件", "", "日志文件 (*.log *.txt)"
        )
        if not path2:
            return

        lines1 = _read_file_lines(path1)
        lines2 = _read_file_lines(path2)
        if lines1 is None or lines2 is None:
            QMessageBox.critical(self, "错误", "无法识别文件编码")
            return

        import heapq

        def _sort_key(line):
            start = line.find('[')
            if start == -1:
                return '~~~~~~~~'
            end = line.find(']', start + 1)
            if end == -1:
                return '~~~~~~~~'
            ts = line[start + 1:end]
            if len(ts) < 19:
                return '~~~~~~~~'
            if len(ts) > 19 and ts[19] == '.':
                us = ts[20:]
                if len(us) < 6:
                    ts = ts[:20] + us + '0' * (6 - len(us))
                elif len(us) > 6:
                    ts = ts[:26]
            elif len(ts) == 19:
                ts = ts + '.000000'
            return ts

        total = len(lines1) + len(lines2)
        self.progress.setMaximum(total)

        # 每个文件内部已有序，2 路归并
        it1 = ((_sort_key(l), l) for l in lines1)
        it2 = ((_sort_key(l), l) for l in lines2)
        merged = [line for _, line in heapq.merge(it1, it2, key=lambda x: x[0])]

        self.progress.setValue(total)

        self.raw_content = "\n".join(merged)
        self.raw_lines = merged
        self._show_plain(self.raw_content)
        self.current_file = None
        self.path_label.setText(f"合并: {os.path.basename(path1)} + {os.path.basename(path2)}")
        self.setWindowTitle("日志关键信息分析 - 合并日志")
        self.progress.setValue(0)
        QMessageBox.information(self, "完成",
            f"合并完成，共 {len(merged)} 行。\n可通过 文件→另存为 保存")

    def run_merge_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含日志文件的文件夹")
        if not folder:
            return

        merged, file_count, total_lines = self._merge_folder_files(folder)
        if merged is None:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并文件", "", "日志文件 (*.log *.txt)"
        )
        if not save_path:
            self.progress.setValue(0)
            return

        with open(save_path, "w", encoding="utf-8") as f:
            f.write("\n".join(merged))

        self.progress.setValue(0)
        QMessageBox.information(self, "完成",
            f"已合并 {file_count} 个文件，共 {total_lines} 行。\n保存至: {save_path}")

    def _parse_ts(self, ts_str):
        if not ts_str or ts_str == "--:--:--":
            return None
        ts_str = ts_str.strip("[]")
        for fmt in ["%Y-%m-%d %H:%M:%S", "%y/%m/%d %H:%M:%S", "%m/%d/%y %H:%M:%S"]:
            try:
                return datetime.strptime(ts_str, fmt).timestamp()
            except ValueError:
                continue
        m = _TS_PARSE_RE.match(ts_str)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + float("0." + (m.group(4) or "0"))
        return None

    def _parse_dynamic_ref(self, ref_str, cap_val):
        if cap_val is not None and ref_str and ',' in ref_str:
            for pair in ref_str.split(','):
                pair = pair.strip()
                if ':' in pair:
                    k, v = pair.split(':', 1)
                    if k.strip() == cap_val:
                        return self._parse_ref(v.strip())
        return self._parse_ref(ref_str)

    def _parse_ref(self, ref_str):
        if not ref_str or not ref_str.strip():
            return None
        ref = ref_str.strip().lower()
        m = _REF_HMS_RE.match(ref)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        m = _REF_HM_RE.match(ref)
        if m:
            return int(m.group(1)) * 60 + int(m.group(2))
        m = _REF_VAL_RE.match(ref)
        if m:
            val = float(m.group(1))
            unit = m.group(2) or "s"
            if unit == "ms":
                return val / 1000
            elif unit == "h":
                return val * 3600
            elif unit == "m":
                return val * 60
            return val
        try:
            return float(ref)
        except ValueError:
            return None

    def show_raw(self):
        if self.raw_content:
            self._show_plain(self.raw_content)

    def open_time(self):
        dlg = TimeDialog(self)
        dlg.exec()

    def open_anomaly(self):
        dlg = AnomalyDialog(self)
        dlg.exec()

    def _toggle_test(self, action):
        item = action.data()
        config = load_config()
        selected = config.get("test_selection", [])

        if item in selected:
            selected.remove(item)
            action.setText(f"  {item}")
        else:
            selected.append(item)
            action.setText(f"● {item}")

        save_config({"test_selection": selected})

    def open_config(self):
        dlg = ConfigDialog(self)
        dlg.exec()

    def open_rule(self):
        config = load_config()
        selected = config.get("test_selection", [])
        dlg = RuleDialog(self, selected_tests=selected)
        dlg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 9))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
