---
name: google-user-auth
description: 管理个人 Google OAuth 授权与 token 刷新，统一为 Gmail、Google Analytics、Search Console、Site Verification 和 Indexing API 提供用户 access token。
metadata: {"clawdbot":{"emoji":"🔑","requires":{"bins":["python3"]}}}
allowed-tools: Bash(google-user-auth:*)
---

# google-user-auth

个人 Google OAuth 基础能力，不负责具体业务 API。首次授权使用 `authorize_google_user.py` 获取并保存 `refresh_token`；后续脚本使用 refresh token 换取短期 access token。默认路径和参数已固定，调用方无需传入 OAuth 参数。

## 默认路径和参数

- OAuth Client JSON：`/root/.openclaw/skills/google-user-auth/google-oauth-client.json`
- 用户 token JSON：`/root/.openclaw/skills/google-user-auth/google-user-token.json`
- OAuth 回调端口：`8765`
- 授权 scope：首次授权或重新授权默认申请 Gmail readonly、Analytics readonly、Search Console readonly、Site Verification、Indexing、Search Console 写入和 Analytics 编辑；需要不同范围时可显式传入 `--scopes` 覆盖默认值

## 已配置账号

- 凭证文件：`google-oauth-client.json` 和 `google-user-token.json`（权限 `600`）
- 已授权范围：Gmail readonly、Analytics readonly、Analytics edit、Indexing、Site Verification、Search Console readonly、Search Console write

## 统一流程

1. 首次授权：运行 `scripts/authorize_google_user.py`，在 Google 授权页选择目标个人账号并同意本次 scope；脚本收到回调后自动调用 `scripts/exchange_code.py`。
2. 授权码交换：`exchange_code.py` 使用回调中的一次性 `code` 向 `https://oauth2.googleapis.com/token` 换取 `refresh_token`，保存 `google-user-token.json`；调用方不单独执行该脚本。
3. 后续刷新：业务脚本运行 `scripts/get-token.sh <scope>`；它读取 `refresh_token`，向 Google 换取短期 `access_token`。
4. 业务调用：把 `get-token.sh` 输出的 `access_token` 放入 `Authorization: Bearer`，交给 Gmail、GA、GSC、Site Verification 或 Indexing API。普通查询优先使用 readonly scope；只有需要修改 Search Console 或 Google Analytics 配置时才使用 `webmasters` 或 `analytics.edit`。

## 安全约束

- 不在日志、截图、飞书通知或命令输出中打印 client secret、refresh token 或 access token。
- 个人账号 OAuth 与服务账号 JWT 分开管理，不互换凭证。
- scope 变化或用户撤销授权后，停止并重新走一次明确授权。

## 关键脚本

- `/root/.openclaw/skills/google-user-auth/scripts/authorize_google_user.py`：首次个人 OAuth 授权和 refresh token 保存。
- `/root/.openclaw/skills/google-user-auth/scripts/exchange_code.py`：接收一次性授权码 `code`，向 Google token endpoint 换取并保存用户 Token JSON。
- `/root/.openclaw/skills/google-user-auth/scripts/get-token.sh`：读取 `google-user-token.json`，使用 `refresh_token` 换取并输出短期 access token；不再依赖单独的公共函数脚本。
- `/root/.openclaw/skills/verification/scripts/search_gmail.py`：使用个人 token 搜索验证邮件。
