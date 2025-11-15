import numpy as np
import pyworld as pw
from typing import List
from FlorenceEngine.Objects.data_models import Song, Word, Section, Track


class FlorenceCoder:
    """输入一个song对象，负责调用world声码器，使得word中oriWave的基频与pitch符合"""

    def __init__(self, sample_rate: int = 22050, frame_period: float = 5.0):
        """
        初始化World声码器参数

        Args:
            sample_rate: 音频采样率
            frame_period: World分析的帧周期（毫秒）
        """
        self.sample_rate = sample_rate
        self.frame_period = frame_period

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
        processed_segments = []

        for word in section.wordList:
            if word.oriWave is not None and len(word.oriWave) > 0:
                # 校正这个word的音高
                adjusted_wave = self._adjust_fundamental_frequency(
                    word.oriWave,
                    word.pitch
                )
                processed_segments.append(adjusted_wave)

        # 将所有处理后的音频片段连接成section
        if processed_segments:
            section.sectionSrc = self._connect_segments(processed_segments)

    def _adjust_fundamental_frequency(self, audio: np.ndarray, target_f0: float) -> np.ndarray:
        """
        使用World声码器校正音频的基频

        Args:
            audio: 输入音频信号
            target_f0: 目标基频（Hz）

        Returns:
            基于World声码器校正后的音频信号
        """
        try:
            # 确保音频数据类型正确（转换为float64）
            if audio.dtype != np.float64:
                audio = audio.astype(np.float64)

            # 步骤1: 使用dio算法进行基频提取
            f0, time_axis = pw.dio(audio, self.sample_rate, frame_period=self.frame_period)

            # 步骤2: 使用stomask进行基频精确化
            f0 = pw.stonemask(audio, f0, time_axis, self.sample_rate)

            # 步骤3: 提取频谱包络（每个帧的频谱特征）
            sp = pw.cheaptrick(audio, f0, time_axis, self.sample_rate)

            # 步骤4: 提取非周期成分（aperiodicity）
            ap = pw.d4c(audio, f0, time_axis, self.sample_rate)

            # 步骤5: 分析原始基频，计算比例因子
            valid_f0 = f0[f0 > 0]  # 只考虑有声部分的基频

            if len(valid_f0) == 0:
                print("警告：无法从音频中提取有效基频，返回静音")
                return np.zeros_like(audio, dtype=np.float32)

            original_f0_mean = np.mean(valid_f0)

            # 步骤6: 构建目标基频轮廓
            # 保持原始基频变化模式，但整体移动到目标音高
            f0_ratio = target_f0 / original_f0_mean
            modified_f0 = f0 * f0_ratio

            # 步骤7: 确保目标基频在合理范围内
            # WORLD对f0范围有限制，需要检查和钳制
            modified_f0 = np.clip(modified_f0, 40, 800)  # 限制在40-800Hz之间

            # 步骤8: 使用WORLD声码器重新合成音频
            synthesized = pw.synthesize(
                modified_f0,
                sp,
                ap,
                self.sample_rate,
                frame_period=self.frame_period
            )

            # 步骤9: 返回与输入相同长度的音频，并转换回float32
            if len(synthesized) > len(audio):
                synthesized = synthesized[:len(audio)]
            elif len(synthesized) < len(audio):
                synthesized = np.pad(synthesized, (0, len(audio) - len(synthesized)))

            return synthesized.astype(np.float32)

        except Exception as e:
            print(f"World声码器处理出错: {e}")
            return self._fallback_processing(audio, target_f0)

    def _fallback_processing(self, audio: np.ndarray, target_f0: float) -> np.ndarray:
        """备用处理方法：简单的音高变换作为降级方案"""
        print("使用降级方案进行音高处理")

        # 计算音频能量平均值作为target_f0的参考
        # 这里使用简化的近似方法
        energy = np.sqrt(np.mean(audio ** 2))

        if energy > 0:
            # 简单的时域伸缩（这是非常简化的方法）
            pitch_ratio = target_f0 / 150.0  # 假设平均语音基频为150Hz

            # 使用重采样模拟音高变化（注：这不是真正的基频变换）
            new_length = int(len(audio) / pitch_ratio)
            indices = np.round(np.linspace(0, len(audio) - 1, new_length)).astype(int)

            # 防越界
            indices = np.clip(indices, 0, len(audio) - 1)
            stretched = audio[indices]

            # 调整长度匹配
            if len(stretched) > len(audio):
                return stretched[:len(audio)].astype(np.float32)
            else:
                # 重复音频补齐长度
                repeats = len(audio) // len(stretched) + 1
                extended = np.tile(stretched, repeats)[:len(audio)]
                return extended.astype(np.float32)

        return np.zeros_like(audio, dtype=np.float32)

    def _connect_segments(self, segments: List[np.ndarray]) -> np.ndarray:
        """连接音频片段，添加适当的静默"""
        if not segments:
            return np.array([], dtype=np.float32)

        if len(segments) == 1:
            return segments[0]

        connected = segments[0]

        for i in range(1, len(segments)):
            # 在每个片段之间添加短静默（可选）
            silence_duration = int(0.01 * self.sample_rate)  # 10ms静默
            silence = np.zeros(silence_duration, dtype=np.float32)

            current = np.concatenate([silence, segments[i]])
            connected = np.concatenate([connected, current])

        return connected

    def optimize_world_parameters(self,
                                audio: np.ndarray,
                                enable_harvest: bool = False) -> dict:
        """
        优化WORLD参数以提高处理质量

        Args:
            audio: 输入音频
            enable_harvest: 是否使用HARVEST算法替代DIO

        Returns:
            优化参数字典
        """
        try:
            # 使用HARVEST算法（通常比DIO更精确但更慢）
            if enable_harvest:
                f0, time_axis = pw.harvest(audio, self.sample_rate, frame_period=self.frame_period)
            else:
                # 默认使用DIO+StoneMask组合
                f0, time_axis = pw.dio(audio, self.sample_rate, frame_period=self.frame_period)
                f0 = pw.stonemask(audio, f0, time_axis, self.sample_rate)

            # 调整StoneMask的搜索范围和平滑参数
            sp = pw.cheaptrick(audio, f0, time_axis, self.sample_rate)
            ap = pw.d4c(audio, f0, time_axis, self.sample_rate)

            return {
                'f0': f0,
                'sp': sp,
                'ap': ap,
                'f0_method': 'harvest' if enable_harvest else 'dio_stonemask'
            }

        except Exception as e:
            print(f"WORLD参数优化出错：{e}")
            return {}

    def quality_check(self, original: np.ndarray, processed: np.ndarray) -> dict:
        """
        质量检查，对比处理前后的音频质量

        Args:
            original: 原始音频
            processed: 处理后的音频

        Returns:
            质量指标字典
        """
        try:
            # 计算信噪比（简单的对比）
            if len(original) != len(processed):
                min_len = min(len(original), len(processed))
                original = original[:min_len]
                processed = processed[:min_len]

            # 计算能量比
            orig_energy = np.sqrt(np.mean(original**2))
            proc_energy = np.sqrt(np.mean(processed**2))
            energy_ratio = proc_energy / (orig_energy + 1e-10)

            # 计算相关系数
            correlation = np.corrcoef(original, processed)[0, 1]

            # 峰值检测
            orig_peak = np.max(np.abs(original))
            proc_peak = np.max(np.abs(processed))
            peak_ratio = proc_peak / (orig_peak + 1e-10)

            return {
                'energy_ratio': energy_ratio,
                'correlation': correlation,
                'peak_ratio': peak_ratio,
                'length_ratio': len(processed) / len(original),
                'quality_score': min(1.0, correlation * energy_ratio)
            }

        except Exception as e:
            print(f"质量检查出错：{e}")
            return {'error': str(e)}

    def get_world_info(self) -> dict:
        """获取World声码器信息"""
        try:
            import pyworld
            return {
                'version': pyworld.__version__,
                'sample_rate': self.sample_rate,
                'frame_period': self.frame_period,
                'features': ['dio', 'harvest', 'stonemask', 'cheaptrick', 'd4c', 'synthesize'],
                'status': 'active'
            }
        except ImportError:
            return {'error': 'pyworld not available'}