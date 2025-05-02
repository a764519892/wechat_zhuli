# modules/features/translation.py
import asyncio
import requests
from config import translation_modes, is_fanyi

async def translate(text, source_language, target_language, secret):
    url = f"https://aotuman.a764519892.workers.dev/?text={text}&source_language={source_language}&target_language={target_language}&secret={secret}"
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, requests.get, url, {'verify': False})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"翻译请求出错: {e}")
        return None

async def translate_message_api(text, mode):
    secret = "123456"
    modes = {
        1: ("zh", "en", "中文翻译英文"),
        2: ("en", "zh", "英文翻译中文"),
        3: ("zh", "vi", "中文翻译越南语"),
        4: ("vi", "zh", "越南语翻译中文")
    }
    if mode not in modes:
        return text
    source_lang, target_lang, _ = modes[mode]
    result = await translate(text, source_lang, target_lang, secret)
    return result.get("text", f"[翻译失败] {text}") if result and result.get("code") == 0 else f"[翻译失败] {text}"

async def handle_translation(ferry, sender, content):
    if content == "翻译":
        reply_text = (
            "请选择翻译模式：\n1. 中文翻译英文\n2. 英文翻译中文\n3. 中文翻译越南语\n4. 越南语翻译中文\n"
            "回复数字1-4选择对应模式，回复'退出'取消翻译功能。"
        )
        ferry.send_text(reply_text, sender, sender)
        translation_modes[sender] = None
        is_fanyi['start'] = True
        return

    if content in ["1", "2", "3", "4"] and is_fanyi['start']:
        mode = int(content)
        translation_modes[sender] = mode
        mode_desc = {1: "中文翻译英文", 2: "英文翻译中文", 3: "中文翻译越南语", 4: "越南语翻译中文"}
        ferry.send_text(f"翻译模式已切换为：{mode_desc[mode]}。请发送待翻译的内容。", sender, sender)
        return

    if content == "退出" and is_fanyi['start']:
        if sender in translation_modes:
            del translation_modes[sender]
        is_fanyi['start'] = False
        ferry.send_text("翻译功能已退出。", sender, sender)
        return

    if sender in translation_modes and translation_modes[sender] is not None:
        translated_text = await translate_message_api(content, translation_modes[sender])
        ferry.send_text(translated_text, sender, sender)