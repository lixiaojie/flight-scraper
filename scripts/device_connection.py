import os
from appium import webdriver
from appium.options.android import UiAutomator2Options
import subprocess
import time
import json


def _load_scraper_config() -> dict:
    """Load unified scraper config JSON from SCRAPER_CONFIG_PATH, with safe defaults."""
    cfg_path = os.getenv("SCRAPER_CONFIG_PATH")
    default_cfg = {
        "appiumServerUrl": os.getenv("APPIUM_SERVER_URL", "http://appium:4723"),
        "deviceUdid": os.getenv("SCRAPER_DEVICE_UDID", "emulator-5554"),
        "androidPlatformVersion": os.getenv("ANDROID_PLATFORM_VERSION", "16"),
        "adbHost": os.getenv("ANDROID_ADB_SERVER_HOST") or os.getenv("ADB_HOST"),
        "adbPort": int(os.getenv("ANDROID_ADB_SERVER_PORT") or os.getenv("ADB_PORT") or 5037),
        "remoteAdbHost": os.getenv("ANDROID_ADB_SERVER_HOST") or os.getenv("ADB_HOST") or "host.docker.internal",
        "remoteAdbPort": int(os.getenv("ANDROID_ADB_SERVER_PORT") or os.getenv("ADB_PORT") or 5037),
        "outputDir": os.getenv("SCRAPER_OUTPUT_DIR", "/app/results"),
    }
    if not cfg_path:
        return default_cfg
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            file_cfg = json.load(f)
        # file values override defaults when present and truthy (except allow
        # zero for ports)

        def choose(key, cast=None):
            val = file_cfg.get(key)
            if val is None or val == "":
                return default_cfg[key]
            return cast(val) if cast else val
        merged = {
            "appiumServerUrl": choose("appiumServerUrl"),
            "deviceUdid": choose("deviceUdid"),
            "androidPlatformVersion": choose("androidPlatformVersion"),
            "adbHost": choose("adbHost"),
            "adbPort": choose("adbPort", int),
            "remoteAdbHost": choose("remoteAdbHost"),
            "remoteAdbPort": choose("remoteAdbPort", int),
            "outputDir": choose("outputDir"),
        }
        return merged
    except Exception:
        return default_cfg


def connect_device():
    """根据统一配置连接设备并返回 driver。包含多候选 UDID 与重试。"""
    cfg = _load_scraper_config()

    server_url = cfg.get("appiumServerUrl") or "http://appium:4723"
    target_udid = cfg.get("deviceUdid") or "emulator-5554"

    udid_candidates = []
    if target_udid:
        udid_candidates.append(target_udid)
    # 附加常见模拟器/物理设备端口型 UDID 候选
    for c in ("emulator-5554", "emulator-5556"):
        if c not in udid_candidates:
            udid_candidates.append(c)

    caps_base = {
        'platformName': 'Android',
        'appium:automationName': 'UiAutomator2',
        'appium:deviceName': 'Android Emulator',
        'appium:platformVersion': cfg.get('androidPlatformVersion') or '16',
        'appium:noReset': True,
        'appium:fullReset': False,
        'appium:autoGrantPermissions': True,
        'appium:newCommandTimeout': 300,
        'appium:adbExecTimeout': 120000,
        # 进一步提高容忍度
        'appium:uiautomator2ServerInstallTimeout': 120000,
        'appium:uiautomator2ServerLaunchTimeout': 120000,
    }

    adb_host = cfg.get('adbHost')
    adb_port = cfg.get('adbPort')

    # 预检：通过 adb 列表确认设备在线，避免 Appium 立即失败
    def adb_list_devices() -> str:
        env = os.environ.copy()
        args = ['adb']
        if adb_host:
            args += ['-H', str(adb_host)]
        if adb_port:
            args += ['-P', str(adb_port)]
        args += ['devices']
        try:
            out = subprocess.check_output(
                args, stderr=subprocess.STDOUT, env=env, timeout=10)
            return out.decode('utf-8', errors='ignore')
        except Exception as _e:
            return str(_e)

    # 等待设备可见且为 device 状态
    def wait_device_ready(target_udid: str, timeout_sec: int = 30) -> bool:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            listing = adb_list_devices()
            if target_udid and f"{target_udid}\tdevice" in listing:
                return True
            time.sleep(1)
        return False

    last_err = None
    for udid in udid_candidates:
        caps = dict(caps_base)
        caps['appium:udid'] = udid
        # 将远程 adb 服务端信息也传给驱动
        if adb_host:
            caps['appium:adbHost'] = adb_host
        if adb_port:
            try:
                caps['appium:adbPort'] = int(adb_port)
            except Exception:
                caps['appium:adbPort'] = 5037
        # 远程 ADB 中继（如需）
        if cfg.get('remoteAdbHost'):
            caps['appium:remoteAdbHost'] = cfg['remoteAdbHost']
        if cfg.get('remoteAdbPort'):
            try:
                caps['appium:remoteAdbPort'] = int(cfg['remoteAdbPort'])
            except Exception:
                pass
        options = UiAutomator2Options().load_capabilities(caps)
        print(f"🔗 准备连接设备 UDID={udid} via {server_url}")
        # 预检等待
        if not wait_device_ready(udid, timeout_sec=30):
            print(f"⚠️ 预检未发现可用设备: {udid}，继续尝试创建会话...")
        for attempt in range(1, 4):
            try:
                driver = webdriver.Remote(server_url, options=options)
                print("✅ 设备连接成功")
                return driver
            except Exception as e:
                last_err = e
                print(f"⚠️ UDID={udid} 第{attempt}次连接失败: {e}")
                time.sleep(3)
    raise RuntimeError(f"Appium 连接设备失败: {last_err}")
