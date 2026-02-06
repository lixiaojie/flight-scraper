# Z.ai API 配置与验证

## 配置位置

- **API Key**：`scripts/config/scraper.config.json`
  - 字段：`llmApiKey` 或 `zaiApiKey`（二选一，优先 `zaiApiKey`）
  - 类型：`llmApiType` 设为 `zai` 时使用 Z.ai 视觉接口

## 调用说明（与官方一致）

- **端点**：`POST https://api.z.ai/api/paas/v4/chat/completions`
- **鉴权**：`Authorization: Bearer <API Key>`
- **视觉模型**：`glm-4.6v-flash`（航班截图解析）
- 参考：[Z.ai Chat Completion](https://docs.z.ai/api-reference/llm/chat-completion)

## 429 Too Many Requests

429 表示**请求过于频繁，触发限流**。处理方式：

1. 在 [Z.ai 控制台](https://z.ai/manage-apikey/rate-limits) 查看该 Key 的配额与限速。
2. 本仓库已在 `scripts/parser_llm_vision.py` 中对 429 做**最多 3 次重试**（指数退避），若仍失败需稍后再跑任务或升级配额。
3. 单独验证 Key 与当前限流情况见下方。

## 单独验证请求

不跑抓取任务，仅验证 Key 是否有效、是否被限流：

```bash
# 在项目根目录
python3 scripts/verify_zai_api.py
```

或在 Docker 内（使用容器内配置路径）：

```bash
docker exec -it <web容器名> python3 /app/scripts/verify_zai_api.py
```

脚本会：

- 从 `SCRAPER_CONFIG_PATH` 指向的 JSON 中读取 `llmApiKey`（未设置时默认 `scripts/config/scraper.config.json`）
- 发送一次**仅文本**的 chat completion（不传图片）
- 输出状态码、限流相关响应头（如有）、以及 401/429 时的简要说明

若返回 **200**：Key 有效，可正常调用。  
若返回 **429**：当前被限流，需等一段时间或到控制台查看/调整配额。  
若返回 **401**：Key 无效或已过期，请在 Z.ai 控制台核对并更新 `scraper.config.json` 中的 `llmApiKey`。
