import asyncio
import websockets
from config import WEBSOCKET_HOST, WEBSOCKET_PORT, PING_INTERVAL, PING_TIMEOUT, connected_clients

async def send_message_to_all_clients(message, sender, ferry):

    if len(connected_clients) == 0 :
        ferry.send_text("虚拟机未连接，稍后再发送消息！", sender, sender)
    for websocket in connected_clients:
        try:
            await websocket.send(message)
            print(f"消息发送到客户端: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("无法发送消息，客户端已断开连接")
