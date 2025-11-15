import numpy as np
import scipy.interpolate as interpolate
from typing import List
from FlorenceEngine.Objects.data_models import Song, Word, Section, Track
import librosa


class FlorenceCoder:
    """输入一个song对象，负责调用world声码器，使得word中oriWave的基频与pitch符合"""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def process_song(self, song: Song) -> Song:
        """
        处理整个song的音高校正

        Args:
            song: Song对象

        Returns:
            处理后的Song对象，包含音高校正后的音频数据
        """
        for track in song.trackList:
            for section in track.sectionList:
                self._process_section(section)

        return song

    def _process_section(self, section: Section) -> None:
        """处理整个section的音高校正"""
        for word in section.wordList:
            if word.oriWave is not None and len(word.oriWave) > 0:
                # 计算目标基频
                target_f0 = word.pitch

                # 对原始语音进行基频调整
                adjusted_wave = self._adjust_fundamental_frequency(
                    word.oriWave,
                    target_f0
                )

                # 存储处理后的音频到sectionSrc
                if section.sectionSrc is None:
                    section.sectionSrc = adjusted_wave
                else:
                    # 将多个单词的音频拼接
                    section.sectionSrc = np.concatenate([section.sectionSrc, adjusted_wave])

    def _adjust_fundamental_frequency(self, audio: np.ndarray, target_f0: float) -> np.ndarray:
        """
        使用PSOLA算法调整语音的基频

        Args:
            audio: 输入音频信号
            target_f0: 目标基频（Hz）

        Returns:
            基频调整后的音频信号
        """
        try:
            # 计算原始音频的基频
            f0_original, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=self.sample_rate
            )

            # 计算平均原始基频（仅考虑有声部分）
            original_f0 = np.nanmean(f0_original[voiced_flag])

            if np.isnan(original_f0) or original_f0 <= 0 or np.isnan(target_f0) or target_f0 <= 0:
                print(f"警告：无法正确估计基频或目标基频无效，返回原始音频")
                return audio

            # 计算音高调整比例
            pitch_ratio = target_f0 / original_f0

            # 使用librosa的音高变换功能
            adjusted_audio = librosa.effects.pitch_shift(
                audio,
                sr=self.sample_rate,
                n_steps=12 * np.log2(pitch_ratio)
            )

            return adjusted_audio

        except Exception as e:
            print(f"基频调整出错：{e}")
            return audio

    def _simple_pitch_shift(self, audio: np.ndarray, pitch_ratio: float) -> np.ndarray:
        """
        简化的音高调整算法（male-to-female风格转换）

        Args:
            audio: 输入音频
            pitch_ratio: 音高比率

        Returns:
            调整后的音频
        """
        try:
            # 使用librosa的phase vocoder进行时域伸缩和音高变换
            stretched = librosa.effects.time_stretch(audio, rate=1.0)
            pitch_shifted = librosa.effects.pitch_shift(
                stretched,
                sr=self.sample_rate,
                n_steps=12 * np.log2(pitch_ratio)
            )

            return pitch_shifted

        except Exception as e:
            print(f"简化音高调整出错：{e}")
            return audio

    def _extract_f0_from_note(self, frequency: float) -> float:
        """从音符频率提取基频"""
        # 对于歌声，基频就是音符频率
        # 但对于真实语音，可能需要倍频检测
        return frequency

    def _smooth_pitch_transitions(self, audio_segments: List[np.ndarray], pitches: List[float]) -> np.ndarray:
        """
        平滑音高过渡（备用方法）

        Args:
            audio_segments: 音频片段列表
            pitches: 对应音高列表

        Returns:
            平滑拼接的音频
        """
        if len(audio_segments) == 0:
            return np.array([])

        if len(audio_segments) == 1:
            return audio_segments[0]

        # 简单的交叉淡入淡出
        result = audio_segments[0]
        fade_length = int(0.01 * self.sample_rate)  # 10ms渐变

        for i in range(1, len(audio_segments)):
            current = audio_segments[i]

            # 添加交叉淡化
            if len(result) >= fade_length and len(current) >= fade_length:
                # 淡出
                fade_out = np.linspace(1, 0, fade_length)
                result[-fade_length:] = result[-fade_length:] * fade_out

                # 淡入
                fade_in = np.linspace(0, 1, fade_length)
                current[:fade_length] = current[:fade_length] * fade_in

                # 重叠相加
                result[-fade_length:] += current[:fade_length]

                # 附加剩余部分
                result = np.concatenate([result, current[fade_length:]])
            else:
                result = np.concatenate([result, current])

        return result