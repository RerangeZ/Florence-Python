#!/usr/bin/env python3
"""
Florence歌声合成引擎 - 主程序
"""

import sys
import os
from FlorenceEngine.FlorenceEngine0 import FlorenceEngine0

def main():
    """主函数：Florence歌声合成引擎入口"""
    print("Florence歌声合成引擎启动...")

    # 初始化引擎
    engine = FlorenceEngine0()

    # 获取引擎信息
    info = engine.get_engine_info()
    print(f"引擎信息: {info['version']}")
    print(f"输出目录: {info['output_directory']}")
    print(f"输入目录: {info['input_directory']}")

    # 提供文件选择和处理
    print("\n正在等待用户选择乐谱文件...")
    result = engine.select_and_process()

    print(f"\n🎉 歌声合成完成！")
    print(f"📁 输出文件: {result}")


if __name__ == "__main__":
    main()