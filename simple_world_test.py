#!/usr/bin/env python3
"""
简单直接的World声码器测试
"""

import numpy as np
import pyworld as pw
import wave
import os

def save_audio(audio_data, filename, sample_rate=22050):
    """保存音频数据为WAV文件"""
    # 确保是float64格式
    if audio_data.dtype != np.float64:
        audio_data = audio_data.astype(np.float64)

    # 转换为16位整数
    audio_16bit = (audio_data * 32767).astype(np.int16)

    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_16bit.tobytes())

def generate_test_sine_wave(frequency=150, duration=2.0, sample_rate=22050):
    """生成测试用的正弦波"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # 添加谐波模拟语音结构
    signal = np.sin(2 * np.pi * frequency * t)
    signal += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)
    signal += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)

    # 添加衰减包络
    envelope = np.exp(-t * 1.5)
    signal = signal * envelope

    # 归一化
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal = signal / max_val * 0.9

    return signal.astype(np.float64)

def test_world_basic():
    """测试基本的World声码器功能"""
    print("Testing basic World vocoder functionality...")

    try:
        # 生成测试音频
        original_freq = 150.0
        target_freq = 200.0
        sample_rate = 22050

        original_audio = generate_test_sine_wave(frequency=original_freq, duration=1.5)

        # 使用World声码器分析
        print("Step 1: Extracting F0 using DIO...")
        f0, time_axis = pw.dio(original_audio, sample_rate, frame_period=5.0)
        f0 = pw.stonemask(original_audio, f0, time_axis, sample_rate)

        print("Step 2: Extracting spectral envelope...")
        sp = pw.cheaptrick(original_audio, f0, time_axis, sample_rate)

        print("Step 3: Extracting aperiodicity...")
        ap = pw.d4c(original_audio, f0, time_axis, sample_rate)

        print("Step 4: Calculating pitch adjustment...")
        # 计算平均基频
        valid_f0 = f0[f0 > 0]
        if len(valid_f0) == 0:
            print("Error: No valid F0 detected")
            return False

        original_mean = np.mean(valid_f0)
        f0_ratio = target_freq / original_mean
        modified_f0 = f0 * f0_ratio

        print(f"Original mean F0: {original_mean:.2f} Hz")
        print(f"Target F0: {target_freq} Hz")
        print(f"Adjustment ratio: {f0_ratio:.3f}")

        # 合成新音频
        print("Step 5: Synthesizing with World...")
        synthesized = pw.synthesize(modified_f0, sp, ap, sample_rate)

        # 保存文件
        os.makedirs("world_test", exist_ok=True)
        save_audio(original_audio, "world_test/original_150hz.wav", sample_rate)
        save_audio(synthesized, "world_test/synthesized_200hz.wav", sample_rate)

        print(f"Results saved to: world_test/")
        print(f"Original length: {len(original_audio)} samples")
        print(f"Synthesized length: {len(synthesized)} samples")

        return True

    except Exception as e:
        print(f"World vocoder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_world_pitch_ranges():
    """测试不同音高范围的World处理"""
    print("\nTesting different pitch ranges...")

    try:
        sample_rate = 22050
        base_audio = generate_test_sine_wave(frequency=130, duration=1.0)

        test_pitches = [100, 130, 160, 200, 250, 300]

        os.makedirs("world_pitch_test", exist_ok=True)

        # 分析原始音频的基频
        f0_orig, _ = pw.dio(base_audio, sample_rate, frame_period=5.0)
        original_mean = np.mean(f0_orig[f0_orig > 0])
        print(f"Original mean F0: {original_mean:.2f} Hz")

        for i, pitch in enumerate(test_pitches):
            try:
                # 获取频谱参数
                f0, t = pw.dio(base_audio, sample_rate, frame_period=5.0)
                f0 = pw.stonemask(base_audio, f0, t, sample_rate)
                sp = pw.cheaptrick(base_audio, f0, t, sample_rate)
                ap = pw.d4c(base_audio, f0, t, sample_rate)

                # 调整基频
                pitch_adjust = pitch / original_mean
                modified_f0 = f0 * pitch_adjust
                modified_f0 = np.clip(modified_f0, 40, 800)

                # 合成
                synthesized = pw.synthesize(modified_f0, sp, ap, sample_rate)

                # 保存
                filename = f"world_pitch_test/{pitch}hz_target_{i+1}.wav"
                save_audio(synthesized, filename, sample_rate)
                print(f"Created {filename}")

            except Exception as e:
                print(f"Error at pitch {pitch}: {e}")

        print("Pitch range test completed!")
        return True

    except Exception as e:
        print(f"Pitch range test failed: {e}")
        return False

def main():
    """主函数"""
    print("World Vocoder Test")
    print("="*40)

    # 基础测试
    basic_success = test_world_basic()

    # 音高范围测试
    pitch_success = test_world_pitch_ranges()

    print("\n" + "="*40)

    if basic_success and pitch_success:
        print("SUCCESS: World vocoder tests passed!")
        print("Test files created in world_test/ and world_pitch_test/")
        return 0
    else:
        print("ERROR: Some tests failed")
        return 1

if __name__ == "__main__":
    # 快速验证
    try:
        import pyworld
        print(f"PyWorld version: {pyworld.__version__}")

        # 测试简单功能
        test_signal = np.sin(2 * np.pi * 200 * np.linspace(0, 1, 22050)).astype(np.float64)
        f0, _ = pyworld.dio(test_signal, 22050)
        print(f"F0 detection successful - mean F0: {np.mean(f0[f0 > 0]):.1f} Hz")

        print("PyWorld is working correctly")
        exit(main())

    except ImportError:
        print("PyWorld not available")
        exit(1)
    except Exception as e:
        print(f"PyWorld verification failed: {e}")
        exit(1)