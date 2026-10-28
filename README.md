# 陪伴型智能 AI 机器人

[![AstrBot](https://img.shields.io/badge/AstrBot-4.x-27a7d8)](https://github.com/AstrBotDevs/AstrBot)
[![SnowLuma](https://img.shields.io/badge/SnowLuma-OneBot%20v11-7b61ff)](https://github.com/SnowLuma/SnowLuma)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

把一个小号变成 **有固定人设、能群聊也能私聊** 的 QQ 智能陪伴机器人。

基于 **AstrBot + SnowLuma**，一套 Docker Compose 即可私有化部署。带着完整的人格提示词、表情包方案和使用边界插件，也带着一份不泄露任何密钥的部署模板。

---

## 为什么做这个

市面上的 QQ 机器人方案很多，但真正落到「陪伴」这件事上，通常缺三样东西：

1. **稳定的人设**——不是每次对话都换一种语气；
2. **可控的成本**——群里被疯狂 @ 时不会一夜烧掉几百块 token；
3. **清晰的边界**——陌生人不能随便私聊，好友申请不能来者不拒。

这个项目把这三件事做成了一套可以直接复用的部署方案：

- 人格由系统提示词固定，换风格只需改一段文字；
- 群聊默认 24 小时限额，超限回固定提示、不调用大模型；
- 私聊白名单 + 好友申请自动拒绝 + 面板不暴露公网。

---

## 功能特性

| 能力 | 说明 |
| --- | --- |
| 群聊 / 私聊 | QQ 群内 @ 回复，私聊直接对话 |
| 人格系统 | 温柔知性、傲娇、元气……一份提示词即可切换 |
| 模型自由 | 默认 DeepSeek，任何 OpenAI 兼容接口都能接 |
| 表情包 | `meme_manager` 管理图库，`sticker_send_as_emoji` 以 QQ 原生小表情发送，支持自动收集群友表情 |
| 使用边界 | 群聊 24h 限额、私聊白名单、好友申请自动拒绝（自带插件） |
| 低成本运行 | 2 核 4G 云服务器即可，2G 内存靠 swap 也能跑 |
| 低暴露面 | 管理面板只绑 `127.0.0.1`，SSH 隧道访问，公网只开 22 |

---

## 架构

```
QQ 群 / QQ 私聊
      │
      ▼
Linux QQ 客户端（SnowLuma 容器内，Xvfb + noVNC 扫码登录）
      │  ptrace hook
      ▼
SnowLuma（OneBot v11 协议端：WebUI :5099 / HTTP :3000 / WS :3001）
      │  反向 WebSocket  ws://astrbot:6199/ws
      ▼
AstrBot（机器人框架：WebUI :6185）
      │  HTTPS
      ▼
DeepSeek API（或任意 OpenAI 兼容模型）
```

- 两个容器在同一个 Docker 网络里，通过服务名互访；
- 6199 / 3000 / 3001 不映射到宿主机；
- 6185 / 6081 / 5099 只绑定宿主机回环地址，靠 SSH 隧道访问。

---

## 快速开始

### 环境要求

- Linux 云服务器（推荐 Ubuntu 22.04+，**2 核 4G** 起）
- Docker / Docker Compose（`bootstrap.sh` 会自动安装）
- 一个可以扫码登录的 QQ 小号
- 一个 DeepSeek API Key（或任意 OpenAI 兼容服务）
- 云安全组只放行 **22（SSH）**

### 1. 部署

```bash
git clone https://github.com/jiu-H05/companion-ai-bot.git /opt/deepseek-girl
cd /opt/deepseek-girl

# 一键初始化：4G swap + Docker + 随机 VNC 密码 + 拉镜像 + 启动
sudo bash bootstrap.sh
```

完成后会生成 `.env`（含随机 VNC 密码），并启动 AstrBot / SnowLuma 两个容器。

### 2. 建立 SSH 隧道

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\tunnel.ps1 -Server <服务器IP>
```

Linux / macOS：

```bash
ssh -N -L 6185:127.0.0.1:6185 -L 6081:127.0.0.1:6081 -L 5099:127.0.0.1:5099 root@<服务器IP>
```

| 地址 | 用途 |
| --- | --- |
| http://127.0.0.1:6081/vnc.html | noVNC 远程桌面：QQ 扫码登录 |
| http://127.0.0.1:5099 | SnowLuma WebUI |
| http://127.0.0.1:6185 | AstrBot 管理面板 |

### 3. 登录 QQ

1. 打开 `http://127.0.0.1:6081/vnc.html`，输入 `.env` 里的 `VNC_PASSWD`；
2. 在远程桌面里用手机 QQ 扫码登录机器人小号；
3. SnowLuma 会自动 hook 注入，WebUI 里看到账号在线即可。

### 4. 让 SnowLuma 连到 AstrBot

SnowLuma WebUI → 网络配置 → 新建「反向 WebSocket」：

- 启用：勾选
- URL：`ws://astrbot:6199/ws`
- 重连间隔：1000
- 保存

### 5. 配置 AstrBot

打开 `http://127.0.0.1:6185`，用户名 `astrbot`，初始密码在日志里：

```bash
docker logs astrbot 2>&1 | grep -i "password\|密码" | tail -n 5
```

在面板里完成三件事：

1. **机器人 → 创建机器人 → OneBot v11**：反向 WS 主机 `0.0.0.0`、端口 `6199`、Token 留空；
2. **服务提供商 → 新增 OpenAI 兼容**：API Base 填 `https://api.deepseek.com/v1`，填入你的 Key，模型 `deepseek-chat`；
3. **人格 → 新建**：粘贴 [persona/deepseek-girl.md](persona/deepseek-girl.md) 的内容，设为默认人格。

日志出现 `aiocqhttp(OneBot v11) 适配器已连接` 即表示链路打通。

### 6. 安装表情包（可选）

AstrBot 面板 → 插件 → 插件市场，安装：

- `meme_manager`：表情包库管理，可从资源广场下载表情包；
- `astrbot_plugin_sticker_send_as_emoji`：让表情以 QQ 原生小表情形式发送。

安装后到「表情包管理 → 资源广场」下载一个现成表情包即可使用。

想让机器人**自动收集群友发表情**，需要额外配置一个支持图片输入的视觉模型（本项目用 `deepseek-flash`），完整步骤见 [docs/MEME.md](docs/MEME.md)。

### 7. 安装使用边界插件

```bash
cp -r plugins/astrbot_plugin_guard /opt/deepseek-girl/astrbot/data/plugins/
cd /opt/deepseek-girl/astrbot/data/plugins/astrbot_plugin_guard
cp config.example.json config.json
# 编辑 config.json：master_id 改成你的 QQ 号，按需调整 daily_limit / fixed_reply
docker compose -f /opt/deepseek-girl/docker-compose.yml restart astrbot
```

| 字段 | 说明 |
| --- | --- |
| `master_id` | 主人 QQ：私聊必回、不受限额 |
| `daily_limit` | 所有群合计 24 小时回复上限（默认 20） |
| `fixed_reply` | 超限后的固定提示 |

---

## 目录结构

```
.
├── docker-compose.yml                  # AstrBot + SnowLuma 编排
├── bootstrap.sh                        # 一键初始化：swap / Docker / 随机密码 / 启动
├── .env.example                        # 环境变量模板（复制为 .env）
├── scripts/
│   └── tunnel.ps1                      # Windows 本机 SSH 隧道
├── persona/
│   └── deepseek-girl.md                # 「DeepSeek娘」人格提示词
├── plugins/
│   └── astrbot_plugin_guard/           # 使用边界插件
└── docs/
    └── SECURITY.md                     # 安全说明与提交前审计清单
```

---

## 常用运维

```bash
cd /opt/deepseek-girl
docker compose ps                  # 查看状态
docker compose logs -f --tail=100  # 查看日志
docker compose restart             # 重启
docker compose pull && docker compose up -d   # 升级镜像
```

忘记 AstrBot 面板密码：

```bash
docker exec -it astrbot astrbot password
```

备份登录态与配置：

```bash
docker run --rm -v deepseek-girl-snowluma-data:/data -v /opt/backup:/backup alpine \
  tar czf /backup/snowluma-data-$(date +%F).tar.gz -C /data .
```

---

## 安全设计

- 仓库内**不包含任何真实凭据**：API Key、SSH 私钥、QQ 号、服务器 IP、面板密码均已排除或替换为占位符；
- `.gitignore` 已排除 `.env`、私钥、数据库、运行时数据与日志；
- 所有管理面板只监听 `127.0.0.1`，通过 SSH 隧道访问，公网只开 22；
- 详细说明与提交前自检命令见 [docs/SECURITY.md](docs/SECURITY.md)。

---

## 常见问题

**拉镜像失败？**
`bootstrap.sh` 会自动切换 DaoCloud 镜像；仍失败可手动修改 `docker-compose.yml` 的 image 前缀。

**QQ 重启后掉登录？**
登录态保存在 Docker 卷里，但 QQ 客户端重启后可能需要在 noVNC 里重新扫码或点登录。

**内存不足 / 容器被杀？**
`dmesg | grep -i oom` 确认；2G 机器建议升到 4G，或确认 swap 已生效。

**AstrBot 连不上 SnowLuma？**
确认 SnowLuma 反向 WS 地址是 `ws://astrbot:6199/ws`，AstrBot 平台端口是 6199。

**群聊不回复？**
确认机器人被 @，或消息以配置的唤醒前缀开头；到 AstrBot 日志确认有没有收到事件。

---

## 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot)：机器人框架
- [SnowLuma](https://github.com/SnowLuma/SnowLuma)：QQ 协议端
- [meme_manager](https://github.com/anka-afk/astrbot_plugin_meme_manager)：表情包管理
- [astrbot_plugin_sticker_send_as_emoji](https://github.com/YanZephyr14/astrbot_plugin_sticker_send_as_emoji)：表情发送

## 免责声明

本项目仅供学习与技术研究，与腾讯 / QQ 无隶属关系。使用第三方 QQ 协议端可能违反平台用户协议，请使用小号并自行承担风险。

## License

[MIT](LICENSE)。第三方组件（AstrBot、SnowLuma 及插件）遵循各自许可证。
