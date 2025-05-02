# modules/message/handler.py
import asyncio
import traceback
from queue import Empty
from config import LOG_FILE, translation_modes, gongyidan_modes, is_fanyi, is_gongyi_chazhao, zhizaozhiling_modes, is_zhizaozhiling_chazhao
from modules.features.translation import handle_translation
from modules.features.gongyidan import handle_gongyidan
from modules.features.zhizaozhiling import handle_zhizaozhiling
from modules.features.tasks import handle_daily_task, handle_gongyidan_task
from modules.message.types import WxMsg
async def handle_message(ferry, msg):
    if not isinstance(msg, WxMsg):
        print(f"未知消息类型: {type(msg)} - {msg}")
        return

    sender = msg.sender
    content = msg.content.strip()
    is_group = msg._is_group
    roomid = msg.roomid

    if is_group and roomid == "48061452070@chatroom":
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as file:
                file.write(content + "\n\n\n")
            print(f"群聊消息已记录: {roomid} - {sender}: {content}")
        except Exception as e:
            print(f"写入日志文件出错: {e}")
        return

    print(f"私人消息 - {sender}: {content}")

    if content == "翻译" or (sender in translation_modes and translation_modes[sender] is not None) or is_fanyi['start']:
        await handle_translation(ferry, sender, content)
        return

    if content == "工艺单" or (sender in gongyidan_modes and gongyidan_modes[sender] is not None) or is_gongyi_chazhao['start']:
        await handle_gongyidan(ferry, sender, content)
        return

    if content == "每日任务":
        await handle_daily_task(ferry, sender)

        
    if content == "织造指令" or (sender in zhizaozhiling_modes and zhizaozhiling_modes[sender] is not None) or is_zhizaozhiling_chazhao['start']:
        await handle_zhizaozhiling(ferry, sender, content)
        return

async def start_receiving_messages(ferry):

    print("开始接收消息...")

    while True:
        try:
            msg_list = ferry.get_msg()
            if msg_list is None:
                #print("未收到消息，继续等待...")
                await asyncio.sleep(1)
                continue

            if isinstance(msg_list, WxMsg):
                print("收到单条消息，正在处理...")
                await handle_message(ferry, msg_list)
            elif isinstance(msg_list, list):
                print(f"收到消息列表，长度: {len(msg_list)}")
                for msg in msg_list:
                    await handle_message(ferry, msg)
            else:
                print(f"未知消息格式: {type(msg_list)} - {msg_list}")

        except Empty:
            # 队列为空是正常情况，不打印错误
            await asyncio.sleep(1)  # 静静地等待1秒再重试
            continue
        except Exception as e:
            print(f"接收消息时发生异常: {e}")
            traceback.print_exc()  # 仅对真正的异常打印堆栈
            await asyncio.sleep(1)

        await asyncio.sleep(0.1)  # 正常循环间隔