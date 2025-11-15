import numpy as np
import wave
import os
from typing import List
from FlorenceEngine.Objects.data_models import Song, Track, Section


class FlorenceOutputGenerater:
    """负责拼接section到track进而到song，并输出{name}.wav文件"""

    def __init__(self, output_dir: str = "output", sample_rate: int = 22050):
        """
        初始化输出生成器

        Args:
            output_dir: 输出目录路径
            sample_rate: 音频采样率
        """
        self.output_dir = output_dir
        self.sample_rate = sample_rate

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

    def generate_output(self, song: Song) -> str:
        """
        生成最终的WAV输出文件

        Args:
            song: 处理完成的Song对象

        Returns:
            输出文件路径
        """
        try:
            # 合并所有轨道的音频
            final_audio = self._merge_tracks(song)

            # 应用音频处理和标准化
            processed_audio = self._process_audio(final_audio)

            # 生成输出文件名
            output_filename = f"{song.name}.wav"
            output_path = os.path.join(self.output_dir, output_filename)

            # 保存WAV文件
            self._save_wav_file(processed_audio, output_path)

            print(f"音频文件生成成功：{output_path}")
            return output_path

        except Exception as e:
            print(f"生成音频文件时出错：{e}")
            raise

    def _merge_tracks(self, song: Song) -> np.ndarray:
        """
        合并所有轨道的音频
        简单的按时间叠加，不需要平滑连接
        """
        if not song.trackList:
            return np.array([])

        # 先找到最长的轨道
        max_length = 0
        for track in song.trackList:
            if track.trackWaveData is not None and len(track.trackWaveData) > max_length:
                max_length = len(track.trackWaveData)

        if max_length == 0:
            return np.array([])

        # 创建最终的音频数组
        final_audio = np.zeros(max_length, dtype=np.float32)

        # 叠加所有轨道
        for track in song.trackList:
            if track.trackWaveData is not None and len(track.trackWaveData) > 0:
                # 将轨道音频叠加到最终音频中
                track_length = len(track.trackWaveData)
                final_audio[:track_length] += track.trackWaveData

        return final_audio

    def _process_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        处理最终音频
        - 防止削波
        - 标准化音量
        - 可选的后期处理
        """
        if len(audio) == 0:
            return audio

        # 防止削波和过载
        processed = self._prevent_clipping(audio)

        # 标准化音量
        processed = self._normalize_audio(processed)

        return processed

    def _prevent_clipping(self, audio: np.ndarray) -> np.ndarray:
        """防止音频削波"""
        # 使用软限制器防止削波
        threshold = 0.95
        ratio = 20.0

        # 软限制
        above_threshold = np.abs(audio) > threshold
        audio_clipped = np.copy(audio)

        audio_clipped[above_threshold] = np.sign(audio[above_threshold]) * (
            threshold + (np.abs(audio[above_threshold]) - threshold) / ratio
        )

        return audio_clipped

    def _normalize_audio(self, audio: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
        """
        标准化音频音量

        Args:
            audio: 输入音频
            target_rms: 目标RMS电平

        Returns:
            标准化后的音频
        """
        if len(audio) == 0:
            return audio

        # 计算当前RMS
        current_rms = np.sqrt(np.mean(audio ** 2))

        if current_rms > 0:
            # 计算增益
            gain = target_rms / current_rms

            # 缓释增益，确保不会过度放大噪声
            max_gain = 4.0
            gain = min(gain, max_gain)

            normalized = audio * gain
        else:
            normalized = audio

        return normalized

    def _save_wav_file(self, audio_data: np.ndarray, output_path: str) -> None:
        """
        保存音频为WAV文件

        Args:
            audio_data: numpy音频数据（浮点格式，范围[-1, 1]）
            output_path: 输出文件路径
        """
        try:
            # 确保音频数据在有效范围内
            audio_data = np.clip(audio_data, -1.0, 1.0)

            # 转换为16位整数
            audio_int16 = (audio_data * 32767).astype(np.int16)

            # 写入WAV文件
            with wave.open(output_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

        except Exception as e:
            print(f"保存WAV文件时出错：{e}")
            raise

    def set_output_directory(self, output_dir: str) -> None:
        """设置输出目录"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_supported_formats(self) -> List[str]:
        """获取支持的音频格式"""
        return ["wav"]