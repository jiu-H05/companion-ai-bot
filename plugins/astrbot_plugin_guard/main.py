# -*- coding: utf-8 -*-
"""群聊每日额度 / 私聊白名单 / 好友申请自动拒绝。"""
import json
import os
import time

from astrbot.api import logger, star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.platform.message_type import MessageType

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "state.json")

DEFAULTS = {
    "master_id": "123456789",
    "daily_limit": 20,
    "fixed_reply": "今天的聊天额度用完啦，明天再来找我吧～",
}


class Guard(star.Star):
    def __init__(self, context: star.Context) -> None:
        super().__init__(context)
        self.cfg = dict(DEFAULTS)
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.cfg.update(json.load(f))
        except Exception as e:
            logger.warning(f"[guard] 读取配置失败: {e}")
        self.friend_ids = set()
        self.last_friend_refresh = 0.0
        self.timestamps = []
        self._load_state()

    def _load_state(self) -> None:
        try:
            if os.path.exists(STATE_PATH):
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.timestamps = [float(x) for x in data.get("timestamps", [])]
        except Exception as e:
            logger.warning(f"[guard] 读取状态失败: {e}")

    def _save_state(self) -> None:
        try:
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump({"timestamps": self.timestamps}, f)
        except Exception as e:
            logger.warning(f"[guard] 保存状态失败: {e}")

    def _prune(self) -> None:
        now = time.time()
        window = 24 * 3600
        self.timestamps = [t for t in self.timestamps if now - t < window]

    async def _refresh_friends(self, event: AstrMessageEvent) -> None:
        now = time.time()
        if now - self.last_friend_refresh < 300 and self.friend_ids:
            return
        bot = getattr(event, "bot", None)
        if bot is None:
            return
        try:
            data = await bot.call_action("get_friend_list")
            if isinstance(data, dict):
                data = data.get("data", [])
            ids = set()
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("user_id"):
                        ids.add(str(item["user_id"]))
            if ids:
                self.friend_ids = ids
                self.last_friend_refresh = now
                logger.info(f"[guard] 好友列表已刷新: {len(ids)} 个")
        except Exception as e:
            logger.warning(f"[guard] 获取好友列表失败: {e}")

    def _is_exempt(self, sender_id: str) -> bool:
        if self.cfg.get("debug_force_count"):
            return False
        return sender_id == str(self.cfg.get("master_id")) or sender_id in self.friend_ids

    @filter.event_message_type(filter.EventMessageType.ALL, priority=-100)
    async def guard(self, event: AstrMessageEvent):
        if event.get_platform_name() != "aiocqhttp":
            return

        raw = getattr(getattr(event, "message_obj", None), "raw_message", None)
        if raw is not None and hasattr(raw, "get"):
            if raw.get("post_type") == "request" and raw.get("request_type") == "friend":
                flag = raw.get("flag")
                bot = getattr(event, "bot", None)
                if bot is not None and flag:
                    try:
                        await bot.call_action("set_friend_add_request", flag=flag, approve=False)
                        logger.info(f"[guard] 已自动拒绝好友申请: {raw.get('user_id')}")
                    except Exception as e:
                        logger.warning(f"[guard] 拒绝好友申请失败: {e}")
                event.stop_event()
                return

        sender_id = str(event.get_sender_id())
        message_type = event.get_message_type()

        if message_type == MessageType.FRIEND_MESSAGE:
            await self._refresh_friends(event)
            if not self._is_exempt(sender_id):
                logger.info(f"[guard] 已忽略陌生私聊: {sender_id}")
                event.stop_event()
            return

        if message_type == MessageType.GROUP_MESSAGE:
            if not event.is_at_or_wake_command:
                return
            await self._refresh_friends(event)
            if self._is_exempt(sender_id):
                return
            self._prune()
            limit = int(self.cfg.get("daily_limit", 20))
            if len(self.timestamps) >= limit:
                logger.info(f"[guard] 24h 群聊额度已用完 {len(self.timestamps)}/{limit}，返回固定提示")
                event.set_result(event.plain_result(str(self.cfg.get("fixed_reply"))))
                event.stop_event()
                return
            self.timestamps.append(time.time())
            self._save_state()
            return
