# -*- coding: utf-8 -*-
# 此文件由 page_capture.py 分拆而来

import time
import os
import re
import subprocess
import json
import glob
from datetime import datetime, date, timedelta
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from lxml import etree
from io import StringIO

def tprint(*args, **kwargs):
    """带时间戳的打印函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}]", *args, **kwargs)


def wait_step(driver, seconds=2):
    """步骤间等待"""
    print(f"⏳ 等待 {seconds} 秒...")
    time.sleep(seconds)


def parse_bounds(bounds_str):
    """解析bounds字符串，返回(x1, y1, x2, y2)"""
    try:
        match = re.search(
            r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            return tuple(map(int, match.groups()))
    except BaseException:
        pass
    return None


def _get_adb_config():
    """获取ADB配置信息"""
    # 尝试从device_connection导入配置函数
    try:
        from device_connection import _load_scraper_config
        cfg = _load_scraper_config()
        return cfg.get('adbHost'), cfg.get('adbPort')
    except Exception:
        # 如果导入失败，直接从环境变量读取
        adb_host = os.getenv("ANDROID_ADB_SERVER_HOST") or os.getenv("ADB_HOST")
        adb_port = os.getenv("ANDROID_ADB_SERVER_PORT") or os.getenv("ADB_PORT")
        if adb_port:
            try:
                adb_port = int(adb_port)
            except Exception:
                adb_port = 5037
        else:
            adb_port = 5037
        return adb_host, adb_port


def _check_adb_available():
    """检查adb命令是否可用"""
    try:
        result = subprocess.run(
            ['which', 'adb'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, result.stdout.strip()
        return False, None
    except Exception:
        return False, None


def _run_adb_command(args, adb_host=None, adb_port=None, timeout=30):
    """执行adb命令"""
    # 首先检查adb是否可用
    adb_available, adb_path = _check_adb_available()
    if not adb_available:
        return False, "", "adb command not found. Please install android-tools-adb in the container."
    
    env = os.environ.copy()
    cmd = ['adb']
    if adb_host:
        cmd += ['-H', str(adb_host)]
    if adb_port:
        cmd += ['-P', str(adb_port)]
    cmd.extend(args)
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=timeout,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)


def check_app_installed(package_name="com.MobileTicket", adb_host=None, adb_port=None):
    """检查应用是否已安装"""
    tprint(f"🔍 检查应用是否已安装: {package_name}")
    
    success, stdout, stderr = _run_adb_command(
        ['shell', 'pm', 'list', 'packages', package_name],
        adb_host=adb_host,
        adb_port=adb_port
    )
    
    if not success:
        tprint(f"⚠️ 检查应用安装状态失败: {stderr}")
        return False
    
    installed = package_name in stdout
    if installed:
        tprint(f"✅ 应用 {package_name} 已安装")
    else:
        tprint(f"❌ 应用 {package_name} 未安装")
    
    return installed


def _extract_version_from_filename(filename):
    """从文件名中提取版本号，例如：12306v5.9.4.5.apk -> (5, 9, 4, 5)"""
    try:
        # 匹配类似 12306v5.9.4.5.apk 或 12306-5.9.4.5.apk 的模式
        import re
        # 查找版本号模式：v数字.数字.数字.数字 或 数字.数字.数字.数字
        version_pattern = r'[vV]?(\d+)\.(\d+)\.(\d+)\.(\d+)'
        match = re.search(version_pattern, filename)
        if match:
            return tuple(int(x) for x in match.groups())
        # 如果没有找到4段版本号，尝试3段
        version_pattern_3 = r'[vV]?(\d+)\.(\d+)\.(\d+)'
        match = re.search(version_pattern_3, filename)
        if match:
            return tuple(int(x) for x in match.groups()) + (0,)
        # 如果还没有，尝试2段
        version_pattern_2 = r'[vV]?(\d+)\.(\d+)'
        match = re.search(version_pattern_2, filename)
        if match:
            return tuple(int(x) for x in match.groups()) + (0, 0)
    except Exception:
        pass
    return None


def _find_latest_apk(apk_files):
    """从APK文件列表中选择版本最新的文件"""
    if not apk_files:
        return None
    
    if len(apk_files) == 1:
        return apk_files[0]
    
    # 提取每个文件的版本号并排序
    apk_with_versions = []
    for apk_path in apk_files:
        filename = os.path.basename(apk_path)
        version = _extract_version_from_filename(filename)
        if version:
            apk_with_versions.append((version, apk_path, filename))
        else:
            # 如果没有版本号，使用文件修改时间作为备选
            try:
                mtime = os.path.getmtime(apk_path)
                apk_with_versions.append(((-1, -1, -1, -1, mtime), apk_path, filename))
            except Exception:
                apk_with_versions.append(((-1, -1, -1, -1, 0), apk_path, filename))
    
    if not apk_with_versions:
        return apk_files[0]
    
    # 按版本号降序排序（最新版本在前）
    apk_with_versions.sort(key=lambda x: x[0], reverse=True)
    latest_version, latest_path, latest_filename = apk_with_versions[0]
    
    if latest_version[0] >= 0:
        tprint(f"📦 找到 {len(apk_files)} 个APK文件，选择最新版本: {latest_filename} (版本: {'.'.join(map(str, latest_version[:4]))})")
    else:
        tprint(f"📦 找到 {len(apk_files)} 个APK文件，选择最新修改的: {latest_filename}")
    
    return latest_path


def _find_assets_directory():
    """查找assets目录，支持多种路径（本地和Docker环境）"""
    possible_paths = []
    
    # 优先检查Docker环境中的常见路径（/app/assets）
    # 因为脚本通常在Docker容器中运行，且assets目录会被挂载到/app/assets
    if os.path.exists("/app"):
        possible_paths.append("/app/assets")
    
    # 方法1: 从当前工作目录查找（Docker环境可能是/app）
    cwd = os.getcwd()
    if cwd:
        possible_paths.append(os.path.join(cwd, "assets"))
        # 如果当前在/app/scripts或/app，则assets在/app/assets
        if cwd.startswith("/app"):
            possible_paths.append("/app/assets")
    
    # 方法2: 从脚本目录向上查找（本地开发环境）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    possible_paths.append(os.path.join(project_root, "assets"))
    
    # 方法3: 从环境变量或配置中获取项目根目录
    project_root_env = os.getenv("PROJECT_ROOT") or os.getenv("SCRAPER_PROJECT_ROOT")
    if project_root_env:
        possible_paths.append(os.path.join(project_root_env, "assets"))
    
    # 方法4: 尝试常见的项目根目录路径
    for base in ["/app", "/workspace", os.path.expanduser("~/Downloads/flight-scraper")]:
        possible_paths.append(os.path.join(base, "assets"))
    
    # 去重并检查每个路径
    checked_paths = []
    debug_info = []
    for path in possible_paths:
        if path and path not in checked_paths:
            checked_paths.append(path)
            exists = os.path.exists(path)
            is_dir = os.path.isdir(path) if exists else False
            debug_info.append(f"   - {path} (exists: {exists}, is_dir: {is_dir})")
            if is_dir:
                tprint(f"✅ 找到assets目录: {path}")
                # 验证目录中是否有文件
                try:
                    files = os.listdir(path)
                    apk_files = [f for f in files if f.lower().endswith('.apk')]
                    if apk_files:
                        tprint(f"📦 assets目录中包含 {len(apk_files)} 个APK文件")
                    else:
                        tprint(f"⚠️ assets目录存在但未找到APK文件")
                except Exception as e:
                    tprint(f"⚠️ 无法列出assets目录内容: {e}")
                return path
    
    # 如果都没找到，输出调试信息
    tprint(f"❌ 未找到assets目录，检查过的路径:")
    for info in debug_info:
        tprint(info)
    
    # 返回最可能的路径（用于错误提示）
    return possible_paths[0] if possible_paths else None


def install_apk_from_assets(apk_path=None, adb_host=None, adb_port=None):
    """从assets文件夹安装APK，自动选择最新版本"""
    # 如果没有指定路径，尝试在assets文件夹中查找apk文件
    if not apk_path:
        # 查找assets目录
        assets_dir = _find_assets_directory()
        
        if not assets_dir or not os.path.isdir(assets_dir):
            tprint(f"❌ 未找到assets目录，尝试过的路径:")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            tprint(f"   - {os.path.join(project_root, 'assets')}")
            tprint(f"   - {os.path.join(os.getcwd(), 'assets')}")
            tprint(f"   - /app/assets")
            return False
        
        # 查找所有apk文件
        apk_files = glob.glob(os.path.join(assets_dir, "*.apk"))
        apk_files.extend(glob.glob(os.path.join(assets_dir, "*.APK")))  # 也查找大写扩展名
        
        if not apk_files:
            tprint(f"❌ assets文件夹中未找到APK文件 (搜索目录: {assets_dir})")
            return False
        
        # 选择最新版本的APK
        apk_path = _find_latest_apk(apk_files)
        if not apk_path:
            tprint(f"❌ 无法确定要安装的APK文件")
            return False
        
        tprint(f"📦 准备安装APK: {os.path.basename(apk_path)}")
    
    if not os.path.exists(apk_path):
        tprint(f"❌ APK文件不存在: {apk_path}")
        return False
    
    tprint(f"📥 开始安装APK: {apk_path}")
    
    success, stdout, stderr = _run_adb_command(
        ['install', '-r', apk_path],
        adb_host=adb_host,
        adb_port=adb_port,
        timeout=120  # 安装可能需要更长时间
    )
    
    if success and "Success" in stdout:
        tprint(f"✅ APK安装成功")
        return True
    else:
        tprint(f"❌ APK安装失败: {stderr or stdout}")
        return False


def check_and_install_12306_app(adb_host=None, adb_port=None):
    """检查12306应用是否安装，如果未安装则从assets文件夹安装"""
    tprint("=" * 50)
    tprint("📱 步骤1: 检查并安装12306应用")
    tprint("=" * 50)
    
    # 首先检查adb是否可用
    adb_available, adb_path = _check_adb_available()
    if not adb_available:
        tprint("⚠️ adb命令不可用，无法检查/安装应用")
        tprint("⚠️ 建议：在容器中安装android-tools-adb，或通过Appium连接后检查应用")
        tprint("⚠️ 继续执行，假设应用已安装或稍后通过Appium处理...")
        return True  # 返回True，允许继续执行，后续通过Appium处理
    
    # 如果没有提供adb信息，从配置中获取
    if adb_host is None or adb_port is None:
        cfg_host, cfg_port = _get_adb_config()
        if adb_host is None:
            adb_host = cfg_host
        if adb_port is None:
            adb_port = cfg_port
    
    package_name = "com.MobileTicket"
    
    # 检查应用是否已安装
    if check_app_installed(package_name, adb_host=adb_host, adb_port=adb_port):
        tprint("✅ 12306应用已安装，跳过安装步骤")
        return True
    
    # 应用未安装，尝试从assets文件夹安装
    tprint("📦 应用未安装，开始从assets文件夹安装...")
    
    if install_apk_from_assets(adb_host=adb_host, adb_port=adb_port):
        # 再次检查确认安装成功
        time.sleep(2)  # 等待安装完成
        if check_app_installed(package_name, adb_host=adb_host, adb_port=adb_port):
            tprint("✅ 12306应用安装并验证成功")
            return True
        else:
            tprint("⚠️ 安装完成但验证失败，请手动检查")
            return False
    else:
        tprint("❌ 12306应用安装失败")
        return False
