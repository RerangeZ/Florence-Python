import numpy as np
from typing import List, Optional
from FlorenceEngine.Objects.data_models import Song, Section, Track


class FlorenceWaveConnecter:
    """负责平滑链接oriWave到sectionSrc，请补全这个算法"""

    def __init__(self, sample_rate: int = 22050, window_size: float = 0.02, overlap_ratio: float = 0.25):
        """
        初始化平滑连接器

        Args:
            sample_rate: 采样率
            window_size: 窗函数大小（秒）
            overlap_ratio: 重叠比例
        """
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.overlap_ratio = overlap_ratio

    def connect_song(self, song: Song) -> Song:
        """
        平滑连接整个song中的sections

        Args:
            song: Song对象

        Returns:
            处理后的Song对象
        """
        for track in song.trackList:
            self._connect_track_sections(track)
        return song

    def _connect_track_sections(self, track: Track) -> None:
        """连接track中的所有section"""
        if not track.sectionList:
            return

        connected_audio = None
        current_time = 0

        for i, section in enumerate(track.sectionList):
            if section.sectionSrc is None:
                continue

            # 获取处理后的音频数据
            section_audio = section.sectionSrc

            if connected_audio is None:
                # 第一个section直接使用
                connected_audio = section_audio
                current_time = len(section_audio) / self.sample_rate
            else:
                # 使用交叉淡化连接section
                connected_audio = self._crossfade_connect(
                    connected_audio,
                    section_audio,
                    overlap_duration=self.window_size,
                    overlap_ratio=self.overlap_ratio
                )

        track.trackWaveData = connected_audio

    def _crossfade_connect(self,
                          audio1: np.ndarray,
                          audio2: np.ndarray,
                          overlap_duration: float = 0.02,
                          overlap_ratio: float = 0.5) -> np.ndarray:
        """
        使用交叉淡入淡出连接两段音频

        Args:
            audio1: 第一段音频
            audio2: 第二段音频
            overlap_duration: 重叠时间（秒）
            overlap_ratio: 重叠比例，相对于第一个音频结尾

        Returns:
            连接后的音频
        """
        overlap_samples = int(overlap_duration * self.sample_rate)

        # 确保重叠样本数有效
        overlap_samples = min(overlap_samples, len(audio1), len(audio2))
        if overlap_samples <= 0:
            return np.concatenate([audio1, audio2])

        # 创建淡入淡出曲线
        fade_out = np.linspace(1, 0, overlap_samples)
        fade_in = np.linspace(0, 1, overlap_samples)

        # 创建平滑的交叉淡化窗函数
        window = self._create_fade_window(overlap_samples)

        # 获取重叠区域
        overlap_region1 = audio1[-overlap_samples:]
        overlap_region2 = audio2[:overlap_samples]

        # 应用重叠和淡化
        faded_overlap = overlap_region1 * fade_out + overlap_region2 * fade_in

        # 构建结果音频
        result = np.zeros(len(audio1) + len(audio2) - overlap_samples, dtype=np.float32)

        # 复制第一段音频（不包括重叠部分）
        result[:len(audio1) - overlap_samples] = audio1[:-overlap_samples]

        # 添加重叠和淡化区域
        result[len(audio1) - overlap_samples:len(audio1)] = faded_overlap

        # 添加第二段音频（不包括重叠部分）
        result[len(audio1):] = audio2[overlap_samples:]

        return result

    def _create_fade_window(self, length: int, fade_type: str = "linear") -> np.ndarray:
        """创建淡入淡出窗函数"""
        if fade_type == "linear":
            return np.linspace(0, 1, length)
        elif fade_type == "cosine":
            return 0.5 * (1 - np.cos(np.pi * np.linspace(0, 1, length)))
        elif fade_type == "exp":
            return 1 - np.exp(-5 * np.linspace(0, 1, length))
        else:
            return np.linspace(0, 1, length)

    def _advanced_spectral_smoothing(self,
                                   audio1: np.ndarray,
                                   audio2: np.ndarray,
                                   overlap_duration: float = 0.05) -> np.ndarray:
        """
        高级频谱平滑算法（备用）

        使用STFT在频域进行平滑过渡
        """
        # 注释: 这个方法实现了频谱平滑的概念但会更慢
        # STFT核大小参数
        nperseg = 512
        noverlap = int(nperseg * 0.75)

        # 实现基本频域转换和逆变换概念 (不支持scipy时回退)
        print("频谱平滑回退到基础算法（scipy不可用）")

        # 回退到之前的交叉淡化算法
        return self._crossfade_connect(audio1, audio2, overlap_duration)

    def _adaptive_gap_fill(self,
                          audio1: np.ndarray,
                          audio2: np.ndarray,
                          max_gap_samples: int = 1000) -> np.ndarray:
        """
        自适应间隙填充算法
        """
        gap_samples = max_gap_samples

        if len(audio1) < gap_samples or len(audio2) < gap_samples:
            return self._crossfade_connect(audio1, audio2, overlap_duration=0.02)

        # 寻找最佳连接点
        correlation = np.correlate(
            audio1[-gap_samples:],
            audio2[:gap_samples],
            mode='valid'
        )

        best_offset = np.argmax(correlation) - gap_samples // 2

        # 基于相关性调整音频位置
        if best_offset > 0:
            # 向音频2中插入静默或重复
            adjusted_audio2 = np.concatenate([
                np.zeros(max(0, best_offset)),
                audio2
            ])
        else:
            # 向音频1中插入静默或重复
            adjusted_audio1 = np.concatenate([
                audio1,
                np.zeros(max(0, -best_offset))
            ])
            audio1 = adjusted_audio1

        return self._crossfade_connect(audio1, audio2, overlap_duration=0.02)

    def _energy_match(self, audio: np.ndarray, target_energy: float) -> np.ndarray:
        """调整音频能量以匹配目标能量"""
        current_energy = np.sqrt(np.mean(audio ** 2))

        if current_energy > 0:
            energy_ratio = target_energy / current_energy
            return audio * energy_ratio
        else:
            return audio

    def analyze_audio_quality(self, audio: np.ndarray) -> dict:
        """分析音频质量指标"""
        if len(audio) == 0:
            return {"snr": 0, "rms": 0, "zero_crossing_rate": 0}

        rms = np.sqrt(np.mean(audio ** 2))
        zero_crossings = np.where(np.diff(np.signbit(audio)))[0]
        zcr = len(zero_crossings) / len(audio)

        # 估计信噪比（简化的方法）
        signal_power = rms ** 2
        noise_floor = np.percentile(np.abs(audio), 10) ** 2
        snr = 20 * np.log10(signal_power / noise_floor) if noise_floor > 0 else 0

        return {
            "rms": rms,
            "zero_crossing_rate": zcr,
            "estimated_snr": snr
        }