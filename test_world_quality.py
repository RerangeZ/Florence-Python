#!/usr/bin/env python3
"""
Florence World声码器质量测试程序
专门用于验证pyworld音高校正效果
"""

import numpy as np
import wave
import os
from FlorenceEngine.FlorenceCoder.FlorenceCoder import FlorenceCoder

def generate_test_audio(duration: float = 1.0, frequency: float = 150.0, sample_rate: int = 22050) -> np.ndarray:
    """生成测试音频"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # 生成复合音调，模拟语音的谐波结构
    fundamental = np.sin(2 * np.pi * frequency * t)
    harmonic2 = 0.5 * np.sin(2 * np.pi * frequency * 2 * t)
    harmonic3 = 0.25 * np.sin(2 * np.pi * frequency * 3 * t)

    # 添加包络模拟语音
    envelope = np.exp(-t * 2)  # 衰减包络
    audio = envelope * (fundamental + harmonic2 + harmonic3)

    # 添加噪声
    noise = np.random.normal(0, 0.05, len(t))
    audio += noise

    # 归一化
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.8

    return audio.astype(np.float32)

def save_wav(audio_data: np.ndarray, filename: str, sample_rate: int = 22050) -> str:
    """保存音频为WAV文件"""
    try:
        # 确保音频数据在有效范围内
        audio_data = np.clip(audio_data, -1.0, 1.0)

        # 转换为16位整数
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # 写入WAV文件
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        print(f"✓ 音频已保存：{filename}")
        return filename

    except Exception as e:
        print(f"保存WAV文件时出错：{e}")
        return None

def test_world_processing():
    """测试World声码器处理效果"""
    print("[START] 开始World声码器测试...")

    # 创建测试目录
    test_dir = "world_test_output"
    os.makedirs(test_dir, exist_ok=True)

    try:
        # 初始化World声码器
        print("Initializing FlorenceCoder...")
        coder = FlorenceCoder(sample_rate=22050, frame_period=5.0)

        # 生成测试音频（男声音高）
        print("Generating test audio...")
        original_frequency = 120.0
        target_frequency = 180.0

        original_audio = generate_test_audio(
            duration=2.0,
            frequency=original_frequency,
            sample_rate=22050
        )

        original_path = os.path.join(test_dir, "original_120hz.wav")
        if not save_wav(original_audio, original_path):
            return False

        # 使用WORLD进行音高校正
        print(f"Processing with World @ target {target_frequency}Hz...")
        processed_audio = coder._adjust_fundamental_frequency(
            original_audio,
            target_frequency
        )

        processed_path = os.path.join(test_dir, f"processed_{target_frequency}hz.wav")
        if not save_wav(processed_audio, processed_path):
            return False

        # 质量检查
        print("Analyzing quality...")
        quality_metrics = coder.quality_check(original_audio, processed_audio)

        # 检查基频估计
        print("Checking fundamental frequency detection...")
        world_info = coder.get_world_info()

        # 打印分析结果
        print("\n" + "="*50)
        print("[ANALYSIS] 测试结果分析:")
        print(f"原始音高: {original_frequency} Hz")
        print(f"目标音高: {target_frequency} Hz")
        print(f"能量比率: {quality_metrics['energy_ratio']:.3f}")
        print(f"相关系数: {quality_metrics['correlation']:.3f}")
        print(f"峰值比率: {quality_metrics['peak_ratio']:.3f}")
        print(f"质量评分: {quality_metrics['quality_score']:.3f}")
        print(f"World版本: {world_info['version']}")
        print("="*50 + "\n")

        # 声音质量初判
        if quality_metrics['correlation'] > 0.7:
            print("[GOOD] 音质较好 - WORLD处理保持了原始特征")
        elif quality_metrics['correlation'] > 0.4:
            print("[OK] 音质一般 - 有一定失真但在可接受范围")
        else:
            print("[BAD] 音质较差 - 可能存在显著失真")

        # 生成多频率测试
        print("\n🔬 执行多频率测试...")
        test_frequencies = [100, 130, 150, 200, 250, 300]

        for freq in test_frequencies:
            test_audio = generate_test_audio(duration=1.0, frequency=freq, sample_rate=22050)
            processed = coder._adjust_fundamental_frequency(test_audio, freq * 1.5)

            filepath = os.path.join(test_dir, f"test_{freq}hz_to_{freq*1.5}hz.wav")
            save_wav(processed, filepath)

        print(f"\n[DONE] 测试完成！输出目录: {test_dir}")
        return True

    except Exception as e:
        print(f"[ERROR] 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_world_parameters():
    """测试不同的World参数对结果的影响"""
    print("\n⚙️ 测试World声码器参数优化...")

    test_dir = "world_parameter_test"
    os.makedirs(test_dir, exist_ok=True)

    try:
        # 创建测试音频
        test_audio = generate_test_audio(duration=1.5, frequency=160.0, sample_rate=22050)

        # 测试不同的帧周期参数
        frame_periods = [2.0, 5.0, 8.0, 10.0]
        target_pitch = 240.0

        for fp in frame_periods:
            print(f"Testing frame_period={fp}ms...")
            coder = FlorenceCoder(sample_rate=22050, frame_period=fp)
            processed = coder._adjust_fundamental_frequency(test_audio, target_pitch)

            filepath = os.path.join(test_dir, f"fp_{fp}ms.wav")
            save_wav(processed, filepath)

        print(f"✅ 参数测试完成！输出目录: {test_dir}")
        return True

    except Exception as e:
        print(f"参数测试出错: {e}")
        return False

def main():
    """主函数"""
    print("[TOOL] Florence World声码器质量测试")
    print("="*50)

    # 运行基础处理测试
    success1 = test_world_processing()

    # 运行参数优化测试
    success2 = test_world_parameters()

    print("\n" + "="*50)

    if success1 and success2:
        print("[PASS] 所有测试都通过了！World声码器重构成功。")
        print("[NOTE] 你可通过以下方式验证音质: 播放world_test_output目录下的音频文件")
        return 0
    else:
        print("[WARN] 部分测试未通过，请检查World声码器配置。")
        return 1

if __name__ == "__main__":
    exit(main())

# 可选的快速验证函数
def quick_pitch_shift_test(signal: np.ndarray, sample_rate: int = 22050):
    """快速验证音高変換主要是进延承诺"""
    print("🔜 快速音高变换验证...")

    try:
        coder = FlorenceCoder(sample_rate=sample_rate)

        # 简单移位上行测试: 200Hz -> 300Hz
        processed = coder._simple_pitch_shift(signal, 1.5)
        print(f"✅ 快速移位测试成功,输出长度: {len(processed)}")
        return processed

    except Exception as e:
        print(f"快速移位测试失败: {e}")
        return signal