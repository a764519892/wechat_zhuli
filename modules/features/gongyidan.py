# modules/features/gongyidan.py
import asyncio
from config import gongyidan_modes, is_gongyi_chazhao
from modules.websocket.server import send_message_to_all_clients
import json

async def buhao_chaxun_api(text):
    return text  # 占位，后续扩展

async def buhao_message_api(text, mode):
    if mode == 1:
        desc, result = "布号查找", text
    elif mode == 2:
        desc, result = "品名查找", await buhao_chaxun_api(text)
    else:
        return text

    return f"{result}" if result != text else f"{text}"


async def handle_gongyidan(ferry, sender, content):
    if content == "工艺单":
        reply_text = (
            "请选择查找生成工艺单模式：\n1. 布号查找\n2. 品名查找\n"
            "回复数字1-2选择对应模式，回复'退出'取消工艺单生成功能。"
        )
        ferry.send_text(reply_text, sender, sender)
        gongyidan_modes[sender] = None
        is_gongyi_chazhao['start'] = True
        return

    if content in ["1", "2"] and is_gongyi_chazhao['start']:
        mode = int(content)
        gongyidan_modes[sender] = mode
        mode_desc = {1: "布号查找", 2: "品名查找"}
        ferry.send_text(f"查找工艺单模式已切换为：{mode_desc[mode]}。请发送待查询的内容。", sender, sender)
        return

    if content == "退出" and is_gongyi_chazhao['start']:
        if sender in gongyidan_modes:
            del gongyidan_modes[sender]
        is_gongyi_chazhao['start'] = False
        ferry.send_text("查找工艺单功能已退出。", sender, sender)
        return

    if sender in gongyidan_modes and gongyidan_modes[sender] is not None:
        buhao_text = await buhao_message_api(content, gongyidan_modes[sender])
        data = {"text": "工艺单", "sender": sender, "gongyi": buhao_text}
        await send_message_to_all_clients(json.dumps(data, ensure_ascii=False), sender, ferry)