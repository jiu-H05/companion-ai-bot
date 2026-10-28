# 表情包配置与自动收集

本项目使用两个插件实现「机器人有自己的表情包」：

| 插件 | 作用 |
| --- | --- |
| [meme_manager](https://github.com/anka-afk/astrbot_plugin_meme_manager) | 表情包图库、分类、发送策略、自动收集 |
| [astrbot_plugin_sticker_send_as_emoji](https://github.com/YanZephyr14/astrbot_plugin_sticker_send_as_emoji) | 让表情以 QQ 原生小表情形式发送，而不是大图 |

在 AstrBot 面板 → 插件 → 插件市场安装这两个插件，重启后左侧会出现「表情包管理」。

## 一、先让机器人有表情可用

1. 打开「表情包管理」→「资源广场」，下载一个现成表情包
2. 在「图库 / 选择规则」里把它设为默认
3. 聊天时模型会按语境选择分类，插件随机发送该分类的图片

也可以自己新建分类（如 `开心`、`无语`、`安慰`）并上传图片。

## 二、自动收集群友发表情（可选）

自动收集需要一个**支持图片输入**的视觉模型来识别「这是不是表情包、属于什么情绪」。

### 1. 准备视觉模型

本项目默认使用 DeepSeek，其中：

| 模型 | 图片输入 |
| --- | --- |
| `deepseek-chat` | 不支持 |
| `deepseek-flash` | 支持（`input_modalities: text, image`） |

在 AstrBot 的配置文件 `data/cmd_config.json` 的 `provider` 列表中，新增一个只用于识图的模型条目（和聊天模型共用同一个 provider source）：

```json
{
  "id": "deepseek-flash",
  "enable": true,
  "model": "deepseek-flash",
  "provider_source_id": "deepseek",
  "modalities": ["text", "image"],
  "custom_extra_body": {}
}
```

> `provider_source_id` 要填你已有的 DeepSeek source 的 id。
> 也可以在面板「服务提供商」里新建一个模型，把 modalities 选上 image。

### 2. 开启自动收集

编辑 `data/config/meme_manager_config.json` 的 `auto_collect` 段：

```json
{
  "auto_collect": {
    "enabled": true,
    "manual_review": false,
    "vision_provider_id": "deepseek-flash",
    "target_pack_id": "builtin-default",
    "scope": [],
    "sampling_probability": 100,
    "max_images_per_message": 1,
    "cooldown_seconds": 20,
    "daily_recognition_limit": 200,
    "min_meme_confidence": 0.85,
    "min_category_confidence": 0.65
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `vision_provider_id` | 上一步新增的视觉模型 id |
| `target_pack_id` | 收集到哪个表情包（可新建一个专用包） |
| `manual_review` | `true` 先入审核箱；`false` 自动入库 |
| `scope` | 限定收集的会话；空数组表示全部 |
| `sampling_probability` | 采样概率（0-100） |
| `daily_recognition_limit` | 每天最多识别多少张 |
| `min_meme_confidence` | 判定为表情包的最低置信度 |
| `min_category_confidence` | 分类的最低置信度 |

也可以直接在面板「表情包管理 → 自动收集」里改。

### 3. 重启并验证

```bash
cd /opt/deepseek-girl
docker compose restart astrbot
docker logs --tail 100 astrbot 2>&1 | grep -i "自动收集\|auto.collect"
```

看到下面这行即成功：

```
[meme_manager] 自动收集后台任务已启动，视觉模型：deepseek-flash
```

然后往群里或私聊发几张表情包，十几秒后到「表情包管理 → 图库 / 自动收集」查看。

## 三、成本与内容安全

- 自动收集每张图会调用一次视觉模型（成本远低于聊天），建议保留 `daily_recognition_limit` 上限
- 如果群里可能有不合适的图片，把 `manual_review` 设为 `true`，人工审核后再入库
- 收集到的表情会自动参与聊天选图；不想要时在面板删除即可
