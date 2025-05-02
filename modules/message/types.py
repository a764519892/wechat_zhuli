# modules/message/types.py

class WxMsg:
    def __init__(self, content: str, sender: str, is_group: bool, roomid: str):
        self.content = content
        self.sender = sender
        self._is_group = is_group
        self.roomid = roomid