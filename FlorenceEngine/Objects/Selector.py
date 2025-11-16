from tkinter import filedialog
import tkinter as tk
import os

def selectScoreFile(relative_path: str ) -> str | None:
    """
    打开文件选择对话框选择乐谱文件
    
    Args:
        root_dir: 项目根目录路径，如果为 None 则使用当前目录
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 获取 input 目录的绝对路径
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, relative_path)
    
    # 确保 input 目录存在
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    
    # 打开文件选择对话框
    file_path = filedialog.askopenfilename(
        title="选择乐谱文件",
        initialdir=input_dir,
        filetypes=[
            ("乐谱文件", "*.musicxml;*.mxl"),
            ("MusicXML", "*.musicxml"),
            ("压缩的 MusicXML", "*.mxl"),
            ("所有文件", "*.*")
        ]
    )
    
    return file_path if file_path else None