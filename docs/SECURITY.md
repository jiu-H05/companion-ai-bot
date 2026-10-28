# 安全说明与审计

## 原则

本仓库**不包含任何真实凭据**：

- 不包含 DeepSeek / OpenAI 等 API Key
- 不包含 QQ 账号 Cookie、OneBot access token
- 不包含 SSH 私钥
- 不包含服务器公网 IP、实例信息
- 不包含 AstrBot 面板密码哈希、JWT secret
- 不包含真实 QQ 号（配置中为占位符）

运行时密钥通过服务器上的 `.env`、AstrBot 面板配置、SnowLuma 配置保存，均已在 `.gitignore` 中排除。

## 部署时的安全建议

1. **面板不暴露公网**：`docker-compose.yml` 里 6185 / 6081 / 5099 均绑定 `127.0.0.1`，只通过 SSH 隧道访问；云安全组只放行 22。
2. **使用 SSH 密钥登录**，不要把密码写进脚本；私钥保存在本机，权限设为仅当前用户可读。
3. **API Key 只填在面板/服务器端**，不要写进 README、脚本或提交记录。
4. **定期轮换**：如果怀疑泄露，立即到 DeepSeek 控制台吊销旧 Key 并重新生成。
5. **QQ 账号风控**：使用小号、绑定手机、不要频繁异地登录；机器人协议端属于第三方实现，请遵守 QQ 用户协议。
6. **备份**：`/opt/deepseek-girl` 与 Docker 卷包含登录态，定期备份但不要上传到公开仓库。

## 提交前检查

```bash
git status
git diff --cached
grep -rniE "sk-[a-zA-Z0-9]{10,}|ghp_|gho_|Bearer |accessToken|password|passwd" . --exclude-dir=.git
```

发现任何密钥被误提交：立即删除仓库中的文件并轮换对应密钥，仅删除提交记录不足以消除风险。
