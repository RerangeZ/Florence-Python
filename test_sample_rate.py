#!/usr/bin/env python3
"""
测试FlorenceSpeakGenerateor采样率配置
"""

import sys
import numpy as np
sys.path.append('.')

from FlorenceEngine.FlorenceSpeakGenerateor.FlorenceSpeakGenerateor import FlorenceSpeakGenerateor

def test_sample_rate():
    """测试采样率设置"""
    print("开始测试FlorenceSpeakGenerateor采样率设置...")

    # 创建FlorenceSpeakGenerateor实例
    generator = FlorenceSpeakGenerateor()

    # 检查采样率常量
    print(f"ESPEAK_SAMPLE_RATE 常量: {generator.ESPEAK_SAMPLE_RATE} Hz")

    # 创建一个简单的测试文本
    test_text = "你好"
    print(f"测试文本: '{test_text}'")

    try:
        # 生成语音
        audio_data = generator._generate_single_word_speech(test_text)
        print(f"生成的音频数据类型: {type(audio_data)}")
        print(f"音频数据形状: {audio_data.shape}")
        print(f"音频数据长度: {len(audio_data)} 样本")
        print(f"预计时长: {len(audio_data) / generator.ESPEAK_SAMPLE_RATE:.3f} 秒")
        print(f"音频数据范围: [{audio_data.min():.4f}, {audio_data.max():.4f}]")

        # 验证数据类型
        if isinstance(audio_data, np.ndarray):
            print("✅ 音频数据是numpy数组")
        else:
            print("❌ 音频数据不是numpy数组")

        # 验证数据完整性
        if len(audio_data) > 0:
            print("✅ 音频数据不为空")
        else:
            print("❌ 音频数据为空")

        if not np.allclose(audio_data, 0):
            print("✅ 音频数据包含有效音频")
        else:
            print("❌ 音频数据全是静音")

        # 播放测试音频（如果需要）
        try:
            from debugger import play
            print("\n正在播放测试音频...")
            play(audio_data)
            print("✅ 音频播放成功")
        except Exception as e:
            print(f"⚠️  音频播放失败: {e}")

    except Exception as e:
        print(f"生成语音时出错: {e}")
        return False

    print("\n✅ 采样率设置测试完成")
    return True

if __name__ == "__main__":
    test_sample_rate()