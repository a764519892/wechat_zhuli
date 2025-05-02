import sys
import time
import asyncio
from queue import Queue, Empty
from modules.websocket.server import start_websocket_server
from modules.message.handler import start_receiving_messages
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError
from modules.message.types import WxMsg
import socket
# 一个简单的消息封装


class WxFerry:
    def __init__(self):
        # 消息队列
        self._msg_queue = Queue()
        # 以下几个属性会在 async init 时创建
        self.browser = None
        self.page = None
        self.msg_locator = None

    async def init(self):
        """异步启动浏览器并登录，必须在 asyncio 里调用。"""
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
                # 监听浏览器断开事件，触发程序退出
        self.browser.on("disconnected", lambda: asyncio.get_event_loop().create_task(self._on_disconnect()))
        self.page = await self.browser.new_page()
        await self.page.goto("https://filehelper.weixin.qq.com", timeout=0)
        print("请扫码登录微信网页版…")
        await self.page.wait_for_selector("span.chat-panel__header__main__extend", timeout=120000)
        print("✅ 登录成功，已切换到 文件传输助手 窗口")
        # 点击切换到“文件传输助手”并聚焦输入框
        await self.page.click("span.chat-panel__header__main__extend")
        await self.page.click("textarea.chat-panel__input-container")
        # 1. 注入 CSS: 对 .msg-item.mine.pc-sent 增加背景样式
        # 1. 注入全局 CSS 样式
        await self.page.add_style_tag(content="""
        .msg-item.mine {
          display: flex !important;
          align-items: center !important;
        }
        .msg-item.mine .msg-avatar {
          width: 40px !important;
          height: 40px !important;
          margin-right: 10px !important;
          border-radius: 50% !important;
        }
        .msg-item.mine .msg-item__content {
          display: flex !important;
          flex-direction: column !important;
        }
        .msg-item.mine .msg-text {
          max-width: 300px !important;
          word-wrap: break-word !important;
        }
        .msg-item.mine.pc-sent {
          flex-direction: row-reverse !important;
          background-color: #d0f0ff !important;
          border-left: 4px solid #007bff !important;
        }
        """ )

        # 2. 注入“键盘/按钮触发标记”脚本
        await self.page.evaluate("""
        (() => {
          let lastCount = document.querySelectorAll('.msg-item.mine').length;
          function markLatest() {
            const all = document.querySelectorAll('.msg-item.mine');
            if (all.length > lastCount) {
              all[all.length - 1].classList.add('pc-sent');
              lastCount = all.length;
              console.log('✅ 新消息标记 pc-sent');
            }
          }
          function bindTriggers() {
            const ta = document.querySelector('textarea.chat-panel__input-container');
            if (ta && !ta.hasAttribute('data-triggered')) {
              ta.setAttribute('data-triggered', '1');
              ta.addEventListener('keydown', e => {
                if (e.key === 'Enter' && !e.shiftKey) setTimeout(markLatest, 300);
              });
            }
            const btn = document.querySelector('.chat-send__button');
            if (btn && !btn.hasAttribute('data-triggered')) {
              btn.setAttribute('data-triggered', '1');
              btn.addEventListener('click', () => setTimeout(markLatest, 300));
            }
          }
          window.setupTrigger = bindTriggers;
          setTimeout(bindTriggers, 2000);
        })();
        """
        )

        # 3. 注入增强版 MutationObserver，针对每条 mine 消息动态微调布局和样式
        await self.page.evaluate("""
        () => {
           function attachObserver(list) {

          const obs = new MutationObserver(() => {
            const msgItems = document.querySelectorAll('.msg-item.mine');
            msgItems.forEach(msgItem => {
              // 设置基础布局
              msgItem.style.display = 'flex';
              msgItem.style.alignItems = 'center';
              msgItem.style.flexDirection = 'row';

              // 如果标记为 pc-sent，则反转方向
              if (msgItem.classList.contains('pc-sent')) {
                msgItem.style.flexDirection = 'row-reverse';
              }

              // 调整头像样式
              const avatar = msgItem.querySelector('.msg-avatar');
              if (avatar) {
                avatar.style.width = '40px';
                avatar.style.height = '40px';
                avatar.style.marginRight = '10px';
                avatar.style.borderRadius = '50%';
              }

              // 调整内容容器为列布局
              const content = msgItem.querySelector('.msg-item__content');
              if (content) {
                content.style.display = 'flex';
                content.style.flexDirection = 'column';
              }

              // 限制文字宽度并自动换行
              const msgText = msgItem.querySelector('.msg-text');
              if (msgText) {
                msgText.style.maxWidth = '300px';
                msgText.style.wordWrap = 'break-word';
              }
            });
          });

          obs.observe(list, { childList: true, subtree: true });
          console.log('✅ 监听消息列表的变化成功');
        }
        function tryInit() {
            const msgList = document.querySelector('.msg-list');
            if (msgList) {
              attachObserver(msgList);
            } else {
              // 500ms 后重试一次
              setTimeout(tryInit, 500);
            }
  }

  tryInit();
}
""")

        # 初始化 Locator
        self.msg_locator = self.page.locator(".msg-text")
        # 启动后台任务：轮询 Web 界面，把新消息放队列
        asyncio.create_task(self._listen_and_enqueue())
    async def _on_disconnect(self):
        print("⚠️ 浏览器已关闭，正在退出…")
        # 这里可根据需求优雅关闭 WebSocket 服务
        await self.close()
        sys.exit(0)

    async def _listen_and_enqueue(self):
        """后台不断从页面拉消息并放入队列。"""
        last_count = 0
        while True:
            # 保证输入/发送监听始终有效
            await self.page.evaluate("window.setupTrigger && window.setupTrigger()")
            try:
                count = await self.msg_locator.count()
            except PlaywrightError:
                # 如果上下文丢失，重新选
                await self.page.click("span.chat-panel__header__main__extend")
                await asyncio.sleep(1)
                self.msg_locator = self.page.locator(".msg-text")
                continue

            if count > last_count:
                node = self.msg_locator.nth(count - 1)
                content = (await node.inner_text()).strip()
                # 判断父元素 .msg-item.mine 是否包含 pc-sent
                is_pc = await node.evaluate(
                    "el => !!el.closest('.msg-item.mine') && el.closest('.msg-item.mine').classList.contains('pc-sent')"
                )
                sender = "PC" if is_pc else "iPhone" 
                is_group = False     
                roomid = "filehelper" 

                # 如果你要从 group 窗口获取 roomid，可以用：
                # roomid = await self.page.locator("css=selector-for-roomid").inner_text()

                msg = WxMsg(content, sender, is_group, roomid)
                print(f"📥 收到新消息：{msg.__dict__}")
                self._msg_queue.put(msg)
                last_count = count

            await asyncio.sleep(1)

    def get_msg(self):
        lst = []
        while True:
            try:
                lst.append(self._msg_queue.get_nowait())
            except Empty:
                break
        if not lst:
            return None
        return lst[0] if len(lst) == 1 else lst
    async def _send_text(self, msg, to_wxid=None, at_wxid=None):
        """异步发送消息到文件传输助手"""
        await self.page.fill('textarea.chat-panel__input-container', msg)
        await self.page.keyboard.press("Enter")
        print(f"📤 已发送：{msg}")
        # 新增一个同步方法
    def send_text(self, msg, to_wxid=None, at_wxid=None):
        asyncio.get_event_loop().create_task(self._send_text(msg, to_wxid, at_wxid))
    async def close(self):
        await self.browser.close()

# 监测登录状态（可以留空或扩展检查页面元素）
async def monitor_login(ferry: WxFerry):
    while True:

        # 如需检测掉线，可在此加逻辑
        await asyncio.sleep(10)
def get_local_ip():
    try:
        # 创建 UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 使用一个不需要真的连接的外部地址（比如 Google 的 DNS）
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"获取失败: {e}"
async def main():
    
    ferry = WxFerry()
    await ferry.init()

    print("程序启动中…")
    
    print("当前本地局域网 IP 地址是：", get_local_ip())

    # 启动各项任务
    recv_task = asyncio.create_task(start_receiving_messages(ferry))
    ws_task = asyncio.create_task(start_websocket_server(ferry))
    login_task = asyncio.create_task(monitor_login(ferry))
 

    # 等待任意任务完成（如浏览器关闭）
    done, pending = await asyncio.wait(
        [recv_task, ws_task, login_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    if browser_task in done:
        print("⚠️ 浏览器断开，开始清理…")
    else:
        print("⚠️ 任务结束，开始清理…")

    # 取消其他未完成任务
    for t in pending:
        t.cancel()

    # 关闭浏览器并退出
    await ferry.close()
    sys.exit(0)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("退出中…")
        sys.exit(0)
