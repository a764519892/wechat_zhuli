# modules/features/gongyidan.py
import asyncio
from config import zhizaozhiling_modes, is_zhizaozhiling_chazhao
from modules.websocket.server import send_message_to_all_clients
import json



async def buhao_message_api(text, mode):
    if mode == 1:
        desc, result = "指令信息查找", text
    elif mode == 2:
        desc, result = "织造工艺对比信息查找",  text
    else:
        return None,text

    return desc, result  # 返回两个值


async def handle_zhizaozhiling(ferry, sender, content):
    if content == "织造指令":
        reply_text = (
            "请选择查找织造指令内容：\n1. 指令信息\n2. 织造工艺对比信息\n"
            "回复数字1-2选择对应模式，回复'退出'取消织造指令查找。"
        )
        ferry.send_text(reply_text, sender, sender)
        zhizaozhiling_modes[sender] = None
        is_zhizaozhiling_chazhao['start'] = True
        return

    if content in ["1", "2"] and is_zhizaozhiling_chazhao['start']:
        mode = int(content)
        zhizaozhiling_modes[sender] = mode
        mode_desc = {1: "指令信息查找", 2: "织造工艺对比信息查找"}
        ferry.send_text(f"织造指令查找模式已切换为：{mode_desc[mode]}。请发送待查询的内容。", sender, sender)
        return

    if content == "退出" and is_zhizaozhiling_chazhao['start']:
        if sender in zhizaozhiling_modes:
            del zhizaozhiling_modes[sender]
        is_zhizaozhiling_chazhao['start'] = False
        ferry.send_text("织造指令查找功能已退出。", sender, sender)
        return

    if sender in zhizaozhiling_modes and zhizaozhiling_modes[sender] is not None:
        moshi,buhao_text = await buhao_message_api(content, zhizaozhiling_modes[sender])
        data = {"text": "织造指令", "sender": sender, "gongyi": buhao_text, "moshi" : moshi}
        await send_message_to_all_clients(json.dumps(data, ensure_ascii=False), sender, ferry)
