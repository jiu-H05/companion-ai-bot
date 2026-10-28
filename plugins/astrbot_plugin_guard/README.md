# astrbot_plugin_guard

AstrBot 守卫插件，为陪伴型机器人提供基础的使用边界。

## 功能

- **群聊额度**：所有群合计每 24 小时最多回复 N 条（默认 20），超限返回固定提示，不调用大模型，节省 token。
- **私聊白名单**：只回复主人和机器人好友，陌生人私聊直接忽略。
- **好友申请自动拒绝**：收到好友申请时自动拒绝（如果 QQ 客户端已经拦截，此逻辑为兜底）。
- **好友豁免**：主人与好友不受群聊额度限制，可正常私聊。

## 安装

把本目录复制到 AstrBot 数据目录的 plugins 下：

```bash
cp -r plugins/astrbot_plugin_guard /opt/deepseek-girl/astrbot/data/plugins/
```

重启 AstrBot：

```bash
cd /opt/deepseek-girl && docker compose restart astrbot
```

## 配置

复制配置模板并按需修改：

```bash
cp config.example.json config.json
```

| 字段 | 说明 |
| --- | --- |
| `master_id` | 主人 QQ 号，私聊必回、不受限额 |
| `daily_limit` | 所有群合计的 24 小时回复上限 |
| `fixed_reply` | 超限后的固定回复 |

修改后重启 AstrBot 生效。计数保存在同目录 `state.json`，删除即清零。

## 说明

- 好友列表每 5 分钟刷新一次；主人用机器人号主动添加的好友，最多 5 分钟后自动获得豁免。
- 仅对 `aiocqhttp`（OneBot v11 / QQ）平台生效。
