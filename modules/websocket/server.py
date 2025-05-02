# modules/websocket/server.py
import asyncio
import websockets
from config import WEBSOCKET_HOST, WEBSOCKET_PORT, PING_INTERVAL, PING_TIMEOUT, connected_clients
import json
from modules.features.tasks import handle_daily_task_complete ,handle_daily_jie_tu,handle_zhizaozhiling_jie_tu
from modules.websocket.send import send_message_to_all_clients

async def handle_client(websocket, path):
    print("客户端已连接")
    connected_clients.add(websocket)
    try:
        while True:
            message = await websocket.recv()
            print(f"收到消息: {message}")
            data = json.loads(message)
            text = data.get("text", "")  # 获取 "text" 字段
            sender = data.get("sender", "")  # 获取 "sender" 字段
            '''
            if text == '每日任务':
                print('执行每日任务')
                # 发送响应给客户端
                await send_message_to_all_clients(message,sender)
            if text == '工艺单':
                print('执行截图工艺单任务')
                # 发送响应给客户端
                await send_message_to_all_clients(message,sender)
            '''
            if text == '每日任务完成！':
                await handle_daily_task_complete(websocket.ferry,sender)

            if text == '执行工艺单截图任务完成！':
                print('执行截图工艺单任务')
                # 发送响应给客户端
                await handle_daily_jie_tu(websocket.ferry, sender,message)
            if text == '执行指令信息查找截图任务完成！':
                print('执行指令信息查找截图任务完成！')
                # 发送响应给客户端
                await handle_zhizaozhiling_jie_tu(websocket.ferry, sender,message)
            if text == '执行织造指令织造工艺对比信息截图任务任务完成！':
                print('执行织造指令织造工艺对比信息截图任务任务完成！')
                # 发送响应给客户端
                await handle_zhizaozhiling_jie_tu(websocket.ferry, sender,message)
            #await send_message_to_all_clients(message, data.get("sender", ""), websocket.ferry)
    except json.JSONDecodeError:
        print("收到的消息不是有效的 JSON 格式:", message)
    except websockets.exceptions.ConnectionClosed:
        print("连接已关闭")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
            print("已移除断开的客户端")

async def keep_alive():
    while True:
        for ws in connected_clients.copy():
            try:
                await ws.ping()
                print("发送 Ping 以保持 WebSocket 连接")
            except websockets.exceptions.ConnectionClosed:
                connected_clients.remove(ws)
                print("客户端已断开连接")
        await asyncio.sleep(30)
'''
async def send_message_to_all_clients(message, sender, ferry):
    if not ferry.is_login():
        print("微信未登录，无法发送消息")
        return
    if len(connected_clients) == 0 :
        ferry.send_text("虚拟机未连接，稍后再发送消息！", sender, sender)
    for websocket in connected_clients:
        try:
            await websocket.send(message)
            print(f"消息发送到客户端: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("无法发送消息，客户端已断开连接")
'''
async def start_websocket_server(ferry):
    # 将 ferry 附加到每个 websocket 对象上
    async def wrapper(websocket, path):
        websocket.ferry = ferry
        await handle_client(websocket, path)

    server = await websockets.serve(
        wrapper, WEBSOCKET_HOST, WEBSOCKET_PORT,
        ping_interval=PING_INTERVAL, ping_timeout=PING_TIMEOUT
    )
    print(f"WebSocket 服务器已启动，监听端口 {WEBSOCKET_PORT}...")
    asyncio.create_task(keep_alive())
    await server.wait_closed()