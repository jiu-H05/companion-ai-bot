# 陪伴型智能 AI 机器人

基于 **AstrBot + SnowLuma** 的 QQ 智能陪伴机器人：把一个小号变成有固定人设、能群聊也能私聊的 AI 伙伴。

> 本项目是一套可复现的 Docker 部署方案 + 人格提示词 + 使用边界守卫插件。
> 不包含任何账号、密钥、服务器地址等敏感信息，部署时由你自行填写。

## 特性

- **双端对话**：QQ 群聊 @ 回复、私聊回复
- **可定制人格**：温柔知性 / 傲娇 / 元气等风格，一个 JSON 提示词即可切换
- **模型自由**：默认接 DeepSeek，任何 OpenAI 兼容接口都能用
- **表情包**：`meme_manager` 管理表情包库 + `sticker_send_as_emoji` 以 QQ 原生小表情发送
- **使用边界**（自带守卫插件）：
  - 所有群合计每 24 小时最多回复 N 条，超限返回固定提示，不烧 token
  - 私聊只回主人和好友，陌生人私聊直接忽略
  - 好友申请自动拒绝
  - 主人/好友不受额度限制
- **低暴露面**：所有管理面板只绑服务器 `127.0.0.1`，通过 SSH 隧道访问，公网只开 22

## 架构

```
QQ 群 / QQ 私聊
      |
      v
Linux QQ 客户端（SnowLuma 容器内，Xvfb + noVNC 扫码登录）
      |  ptrace hook
      v
SnowLuma（OneBot v11 协议端：WebUI :5099 / HTTP :3000 / WS :3001）
      |  反向 WebSocket  ws://astrbot:6199/ws
      v
AstrBot（机器人框架：WebUI :6185）
      |  HTTPS
      v
DeepSeek API（或任何 OpenAI 兼容模型）
```

- AstrBot 与 SnowLuma 在同一个 Docker 网络里，通过服务名互访
- 6199 / 3000 / 3001 不映射到宿主机
- 6185 / 6081 / 5099 只绑定宿主机回环地址，靠 SSH 隧道访问

## 仓库结构

```
.
├── docker-compose.yml                  # AstrBot + SnowLuma 编排
├── bootstrap.sh                        # 一键初始化：swap / Docker / 随机密码 / 启动
├── .env.example                        # 环境变量模板（复制为 .env）
├── scripts/
│   └── tunnel.ps1                      # Windows 本机 SSH 隧道脚本
├── persona/
│   └── deepseek-girl.md                # 「DeepSeek娘」人格提示词模板
├── plugins/
│   └── astrbot_plugin_guard/           # 使用边界守卫插件（限额/私聊白名单/拒绝好友）
└── docs/
    └── SECURITY.md                     # 安全说明与提交前审计清单
```

## 前置要求

- 一台 Linux 云服务器（推荐 Ubuntu 22.04+，**2 核 4G** 起；2G 内存需依赖 swap，较紧）
- Docker 与 Docker Compose（`bootstrap.sh` 会自动安装）
- 一个可以扫码登录的 QQ 小号
- 一个 DeepSeek API Key（或任意 OpenAI 兼容模型服务的 Key）
- 云安全组只放行 **22（SSH）**

## 快速开始

### 1. 上传代码并初始化

```bash
# 在服务器上
git clone <本仓库地址> /opt/deepseek-girl
cd /opt/deepseek-girl

# 一键初始化：4G swap + Docker + 随机 VNC 密码 + 拉镜像 + 启动
sudo bash bootstrap.sh
```

初始化完成后会生成 `.env`（含随机 VNC 密码），并启动两个容器。

### 2. 建立本机 SSH 隧道

Windows（PowerShell）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\tunnel.ps1 -Server <服务器IP>
```

保持窗口开着，然后在本机浏览器访问：

| 地址 | 用途 |
| --- | --- |
| http://127.0.0.1:6081/vnc.html | noVNC 远程桌面：QQ 扫码登录 |
| http://127.0.0.1:5099 | SnowLuma WebUI |
| http://127.0.0.1:6185 | AstrBot 管理面板 |

Linux / macOS 也可以直接用 ssh 命令：

```bash
ssh -N -L 6185:127.0.0.1:6185 -L 6081:127.0.0.1:6081 -L 5099:127.0.0.1:5099 root@<服务器IP>
```

### 3. 登录 QQ（SnowLuma）

1. 打开 `http://127.0.0.1:6081/vnc.html`，输入 `.env` 里的 `VNC_PASSWD`
2. 在远程桌面里用手机 QQ 扫码登录机器人小号
3. SnowLuma 会自动 hook 注入，WebUI 里能看到账号在线

### 4. 配置 SnowLuma 反向连接 AstrBot

SnowLuma WebUI → 网络配置 → 新建「反向 WebSocket」：

- 启用：勾选
- URL：`ws://astrbot:6199/ws`
- 重连间隔：1000
- 保存

### 5. 配置 AstrBot

打开 `http://127.0.0.1:6185`，首次登录用户名 `astrbot`，初始密码在启动日志里：

```bash
docker logs astrbot 2>&1 | grep -i "密码\|password" | tail -n 5
```

然后在面板完成：

1. **机器人 → 创建机器人 → OneBot v11**：反向 WS 主机 `0.0.0.0`、端口 `6199`、Token 留空
2. **服务提供商 → 新增 OpenAI 兼容**：API Base `https://api.deepseek.com/v1`、填入你的 Key、模型 `deepseek-chat`
3. **人格 → 新建**：粘贴 `persona/deepseek-girl.md` 的内容，设为默认人格
4. 日志出现 `aiocqhttp(OneBot v11) 适配器已连接` 即成功

### 6. 安装表情包插件（可选）

AstrBot 面板 → 插件 → 插件市场，安装：

- `meme_manager`：表情包库管理（左侧会出现「表情包管理」页面，可从资源广场下载表情包）
- `astrbot_plugin_sticker_send_as_emoji`：让表情以 QQ 原生小表情形式发送

### 7. 安装使用边界守卫插件

```bash
# 在服务器上
cp -r plugins/astrbot_plugin_guard /opt/deepseek-girl/astrbot/data/plugins/
cd /opt/deepseek-girl/astrbot/data/plugins/astrbot_plugin_guard
cp config.example.json config.json
# 编辑 config.json：把 master_id 改成你的 QQ 号，按需调整 daily_limit / fixed_reply
docker compose -f /opt/deepseek-girl/docker-compose.yml restart astrbot
```

配置项：

| 字段 | 说明 |
| --- | --- |
| `master_id` | 主人 QQ：私聊必回、不受限额 |
| `daily_limit` | 所有群合计 24 小时回复上限（默认 20） |
| `fixed_reply` | 超限后的固定提示 |

## 运维

```bash
cd /opt/deepseek-girl
docker compose ps                  # 状态
docker compose logs -f --tail=100  # 日志
docker compose restart             # 重启
docker compose pull && docker compose up -d   # 升级镜像
```

忘记 AstrBot 面板密码：

```bash
docker exec -it astrbot astrbot password
```

备份（登录态、配置都在 Docker 卷里）：

```bash
docker run --rm -v deepseek-girl-snowluma-data:/data -v /opt/backup:/backup alpine \
  tar czf /backup/snowluma-data-$(date +%F).tar.gz -C /data .
```

## 常见问题

- **拉镜像失败**：`bootstrap.sh` 会自动切 DaoCloud 镜像；仍失败可手动改 `docker-compose.yml` 的 image 前缀
- **QQ 重启后掉登录**：登录态在 Docker 卷里，但 QQ 客户端重启后可能需要在 noVNC 里重新扫码/点登录
- **内存不足 / 容器被杀**：`dmesg | grep -i oom` 确认；2G 机器建议升到 4G
- **AstrBot 连不上 SnowLuma**：确认 SnowLuma 的反向 WS 地址是 `ws://astrbot:6199/ws`，AstrBot 平台端口是 6199
- **群聊不回复**：确认机器人已被 @，或消息以配置的唤醒前缀开头；检查 AstrBot 日志有没有收到事件

## 安全

- 本仓库不含任何真实密钥、账号、IP，详见 [docs/SECURITY.md](docs/SECURITY.md)
- 管理面板不要暴露公网；如需公网访问，至少加反向代理 + 强密码 + IP 白名单
- 第三方 QQ 协议端存在账号风控风险，请使用小号并遵守 QQ 用户协议

## 免责声明

本项目仅供学习与技术研究，与腾讯 / QQ 无隶属关系。使用第三方协议端可能违反平台用户协议，风险自负。
