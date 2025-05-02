# modules/features/tasks.py
import asyncio
import os
import shutil
import subprocess
import win32com.client
from config import SCREENSHOT_PATH, DAILY_TASK_SOURCE_FILE, DAILY_TASK_TARGET_DIR, FIND_REPORT_BAT,ZHILING_SCREENSHOT_PATH,HU_TONG
from modules.websocket.send import send_message_to_all_clients
import json
from PIL import Image
async def merge_images_vertically(image_folder, output_file, compressed_output_file, quality=85):
    image_files = ["zhi_ling{}.JPEG".format(i) for i in range(1, 8)]
    images = []
    
    for file in image_files:
        file_path = os.path.join(image_folder, file)
        if os.path.exists(file_path):
            img = Image.open(file_path)
            images.append(img)
        else:
            print(f"警告：文件 {file} 不存在，跳过。")
    
    if not images:
        print("没有可用的图片进行合并！")
        return
    
    width = images[0].width
    total_height = sum(img.height for img in images)
    merged_image = Image.new("RGB", (width, total_height))
    
    y_offset = 0
    for img in images:
        merged_image.paste(img, (0, y_offset))
        y_offset += img.height
    
    output_path = os.path.join(image_folder, output_file)
    merged_image.save(output_path)
    print("拼接完成，保存为:", output_path)
    
    await compress_image(output_path, os.path.join(image_folder, compressed_output_file), quality)

async def compress_image(input_path, output_path, quality=85):
    loop = asyncio.get_running_loop()
    
    def sync_compress():
        img = Image.open(input_path)
        if output_path.lower().endswith(".png"):
            img.save(output_path, "PNG", optimize=True)
        else:
            img.save(output_path, "JPEG", quality=quality, optimize=True)
    
    await loop.run_in_executor(None, sync_compress)
    print("图片压缩完成，保存为:", output_path)
async def handle_zhizaozhiling_jie_tu(ferry, sender, message):

    await merge_images_vertically(HU_TONG, "merged.bmp", "zhizaozhiling.jpg", quality=85)
    send_result = ferry.send_image(ZHILING_SCREENSHOT_PATH, sender)
    if send_result == 0:
        print("截图已发送给", sender)
        await send_message_to_all_clients(message, sender, ferry)
    else:
        ferry.send_text("截图发送失败!", sender, sender)
async def handle_daily_jie_tu(ferry, sender, message):

    send_result = ferry.send_image(SCREENSHOT_PATH, sender)
    if send_result == 0:
        print("截图已发送给", sender)
        await send_message_to_all_clients(message, sender, ferry)
    else:
        ferry.send_text("截图发送失败!", sender, sender)

async def handle_daily_task_complete(ferry, sender):

    
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False  # 不显示 Excel 窗口
        excel.DisplayAlerts = False  # 关闭弹窗警告
        
        excel.Quit()  # 退出 Excel
        print("Excel 文件已保存并成功关闭。")
    
    except Exception as e:
        print("未找到 Excel 或出错:", e)

    await asyncio.sleep(10)

    target_file = os.path.join(DAILY_TASK_TARGET_DIR, "测试结果.xls")

    if not os.path.exists(DAILY_TASK_TARGET_DIR):
        os.makedirs(DAILY_TASK_TARGET_DIR)
    
    if os.path.exists(target_file):
        os.remove(target_file)
    try:
        shutil.copy2(DAILY_TASK_SOURCE_FILE, target_file)
        print("文件复制成功:", target_file)
        if os.path.exists(FIND_REPORT_BAT):
            subprocess.call([FIND_REPORT_BAT], shell=True)
            ferry.send_text("查找报告.bat 每日任务完成", sender, sender)
        else:
            ferry.send_text("找不到 查找报告.bat", sender, sender)
    except:
        print("文件复制失败:")
        ferry.send_text("复制测试结果.xls 失败，未找到!", sender, sender)
        



async def handle_daily_task(ferry, sender):

    try:
        data = {"text": "每日任务", "sender": sender}
        await send_message_to_all_clients(json.dumps(data, ensure_ascii=False), sender, ferry)
    except Exception as e:
        print(f"执行每日任务出错: {e}")
        ferry.send_text("每日任务执行失败！", sender, sender)

async def handle_gongyidan_task(ferry, sender):

    data = {"text": "执行工艺单截图任务完成！", "sender": sender}
    await handle_daily_jie_tu(ferry, sender, json.dumps(data, ensure_ascii=False))