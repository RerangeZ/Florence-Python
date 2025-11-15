import os
from FlorenceScoreDecoder import ScoreDecoder
from Objects import selectScoreFile

# 获取项目根目录（程序入口所在目录）
root_dir = os.path.dirname(os.path.abspath(__file__))

# 选择文件
path = selectScoreFile(root_dir)
if not path:
    print("未选择文件，程序退出")
    exit()

# 创建解码器并处理文件
try:
    decoder = ScoreDecoder(path)
    decoder.decode()
    print(f"成功解码文件：{path}")
except Exception as e:
    print(f"处理文件时出错：{e}")
    exit()

