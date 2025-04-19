import os
import shutil
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 设置日志
logging.basicConfig(filename='file_organizer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 文件类型分类字典
FILE_TYPES = {
    '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
    '文档': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'],
    '音频': ['.mp3', '.wav', '.aac', '.flac', '.ogg'],
    '视频': ['.mp4', '.avi', '.mov', '.mkv', '.flv'],
    '压缩包': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    '程序': ['.exe', '.msi', '.bat', '.sh', '.py', '.js', '.html', '.css']
}

def organize_files(source_dir):
    """
    整理指定目录中的文件
    :param source_dir: 要整理的目录路径
    """
    try:
        # 确保源目录存在
        if not os.path.exists(source_dir):
            logging.error(f"源目录不存在: {source_dir}")
            return

        # 为每种文件类型创建目标目录
        for folder_name in FILE_TYPES.keys():
            target_dir = os.path.join(source_dir, folder_name)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                logging.info(f"创建目录: {target_dir}")

        # 遍历源目录中的文件
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            
            # 跳过目录
            if os.path.isdir(file_path):
                continue
                
            # 获取文件扩展名
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # 查找匹配的文件类型
            moved = False
            for folder_name, extensions in FILE_TYPES.items():
                if ext in extensions:
                    target_path = os.path.join(source_dir, folder_name, filename)
                    
                    # 处理文件名冲突
                    while os.path.exists(target_path):
                        logging.warning(f"文件冲突: {filename} 已存在于 {folder_name} 目录中")
                        base, ext = os.path.splitext(filename)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_filename = f"{base}_{timestamp}{ext}"
                        target_path = os.path.join(source_dir, folder_name, new_filename)
                        logging.info(f"生成新文件名: {new_filename}")
                    
                    # 移动文件
                    shutil.move(file_path, target_path)
                    logging.info(f"移动文件: {filename} -> {target_path}")
                    moved = True
                    break
            
            if not moved:
                logging.info(f"未分类文件: {filename}")
                
    except Exception as e:
        logging.error(f"整理文件时出错: {str(e)}")

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, directory):
        self.directory = directory
    
    def on_created(self, event):
        if not event.is_directory:
            # 检查新创建的文件是否为常规文件
            if os.path.isfile(event.src_path):
                organize_files(self.directory)
            else:
                logging.warning(f"忽略非文件创建事件: {event.src_path}")

def watch_directory(directory):
    """
    监视指定目录的文件变动并自动整理
    :param directory: 要监视的目录路径
    """
    event_handler = FileChangeHandler(directory)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    print("文件整理工具")
    print("请确保备份重要文件后再运行此程序")
    
    source_dir = input("请输入要整理的目录路径: ")
    
    if os.path.exists(source_dir):
        print(f"即将整理目录: {source_dir}")
        confirm = input("确认开始整理? (y/n): ").lower()
        
        if confirm == 'y':
            organize_files(source_dir)
            print("文件整理完成!")
            
            watch_confirm = input("是否要监视此目录的文件变动? (y/n): ").lower()
            if watch_confirm == 'y':
                print("开始监视目录... (按Ctrl+C停止)")
                watch_directory(source_dir)
        else:
            print("操作已取消")
    else:
        print("错误: 指定的目录不存在")