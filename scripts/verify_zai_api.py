#!/usr/bin/env python3
"""
独立验证 Z.ai API 调用（仅用标准库，无需 pip install）
优先从 ZAI_API_KEY 环境变量读取密钥，可选读取本地私有配置，
发送一次简单的文本 chat completion 以核实 API Key 与限流情况。
用法: python3 scripts/verify_zai_api.py
"""
import os
import sys
import json
import urllib.request
import urllib.error
import ssl

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.environ.get(
    "SCRAPER_CONFIG_PATH",
    os.path.join(SCRIPT_DIR, "config", "scraper.config.json"),
)


def load_api_key():
    key = os.environ.get("ZAI_API_KEY", "").strip()
    if key:
        return key
    if not os.path.isfile(CONFIG_PATH):
        print("Set ZAI_API_KEY or provide a private config via SCRAPER_CONFIG_PATH")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    key = (cfg.get("zaiApiKey") or cfg.get("llmApiKey") or "").strip()
    if not key:
        print("Set ZAI_API_KEY; do not commit credentials to configuration files")
        sys.exit(1)
    return key


def main():
    api_key = load_api_key()
    print("Config:", CONFIG_PATH)
    print("API Key: configured (value not logged)")

    url = "https://api.z.ai/api/paas/v4/chat/completions"
    payload = {
        "model": "glm-4.7-flash",
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "max_tokens": 64,
        "stream": False,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )

    print("POST", url)
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            code = resp.getcode()
            print("Status:", code)
            for h in ("Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining"):
                v = resp.headers.get(h)
                if v:
                    print("Header %s: %s" % (h, v))
            data = json.loads(resp.read().decode("utf-8"))
            msg = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            print("OK. Reply:", (msg or "")[:200])
            print("usage:", data.get("usage"))
    except urllib.error.HTTPError as e:
        print("Status:", e.code)
        for h in ("Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining"):
            v = e.headers.get(h)
            if v:
                print("Header %s: %s" % (h, v))
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 429:
            print("429 Too Many Requests - 触发限流，请到 Z.ai 控制台查看配额或稍后重试")
        elif e.code == 401:
            print("401 Unauthorized - API Key 无效或已过期，请核对 ZAI_API_KEY 或本地私有配置")
        print("Body:", body[:400])
        sys.exit(2)
    except Exception as e:
        print("Error:", e)
        sys.exit(3)


if __name__ == "__main__":
    main()
