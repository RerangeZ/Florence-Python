#!/usr/bin/env python3
"""
Florence歌声合成引擎 - 主程序
"""

import sys
import os
from FlorenceEngine.FlorenceEngine0 import FlorenceEngine0

def main():
    """主函数：Florence歌声合成引擎入口"""
    try:
        print("🎼 Florence歌声合成引擎启动...")

        # 初始化引擎
        engine = FlorenceEngine0()

        # 执行引擎自检
        if not engine.test_engine():
            print("⚠️  引擎自检未通过，但是继续进行")

        # 获取引擎信息
        info = engine.get_engine_info()
        print(f"引擎信息: {info['version']}")
        print(f"输出目录: {info['output_directory']}")
        print(f"输入目录: {info['input_directory']}")

        # 提供文件选择和处理
        print("\n正在等待用户选择乐谱文件...")
        result = engine.select_and_process()

        if result:
            print(f"\n🎉 歌声合成完成！")
            print(f"📁 输出文件: {result}")
        else:
            print("\n❌ 处理失败或用户取消")
            return 1

    except KeyboardInterrupt:
        print("\n🚪 用户中断操作")
        return 1
    except Exception as e:
        print(f"\n💥 程序发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())