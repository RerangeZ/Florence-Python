import subprocess
import shutil
import numpy as np
from typing import List
from FlorenceEngine.Objects.data_models import Song, Word
import wave
import io


class FlorenceSpeakGenerateor:
    """输入一个song对象，对里面的word对象处理，根据lrc合成oriWave"""

    def __init__(self):
        if not shutil.which("espeak-ng"):
            print("错误: 'espeak-ng' 命令未找到。请确保已经安装eSpeak-NG并添加到PATH环境变量中。")

    def generate_song_speech(self, song: Song) -> Song:
        """
        为整个song中的所有word合成原始语音数据

        Args:
            song: Song对象

        Returns:
            处理后包含oriWave数据的Song对象
        """
        for track in song.trackList:
            for section in track.sectionList:
                self._process_section(section)

        return song

    def _process_section(self, section):
        """处理整个section中的所有words"""
        for word in section.wordList:
            # 只为还没有oriWave的word生成语音
            if word.oriWave is None:
                word.oriWave = self._generate_single_word_speech(word.lrc)

    def _generate_single_word_speech(self, lyric: str) -> np.ndarray:
        """
        使用eSpeak-NG合成单个词语的语音

        Args:
            lyric: 需要合成的歌词（拼音或英文）

        Returns:
            音频数据numpy数组
        """
        if not shutil.which("espeak-ng"):
            # 创建静默音频作为替代
            sample_rate = 22050
            duration = 0.5  # 假设每个字0.5秒
            samples = int(sample_rate * duration)
            silence = np.zeros(samples, dtype=np.float32)
            return silence

        try:
            # 根据文本类型选择不同的eSpeak语音
            if self._is_chinese_pinyin(lyric):
                # 使用拼音音调格式
                formatted_text = f"[{lyric}]"
                voice = "cmn-latn-pinyin"
            else:
                # 普通英文
                formatted_text = lyric
                voice = "en"

            command = [
                "espeak-ng",
                "-v", voice,
                "-s", "150",  # 语速
                "-p", "50",   # 音调
                "--stdout",
                formatted_text
            ]

            result = subprocess.run(
                command,
                check=True,
                capture_output=True
            )

            # 将WAV数据转换为numpy数组
            audio_data = self._wav_bytes_to_numpy(result.stdout)
            return audio_data

        except subprocess.CalledProcessError as e:
            print(f"eSpeak-NG执行出错：{e}")
            return self._generate_silence(0.5)
        except Exception as e:
            print(f"语音合成出错：{e}")
            return self._generate_silence(0.5)

    def _is_chinese_pinyin(self, text: str) -> bool:
        """判断是否为拼音（包含数字）"""
        import re
        return bool(re.search(r'[a-zA-Z]+\d', text))

    def _wav_bytes_to_numpy(self, wav_bytes: bytes) -> np.ndarray:
        """将WAV字节数据转换为numpy数组"""
        try:
            # 使用wave模块解析WAV数据
            wav_file = wave.open(io.BytesIO(wav_bytes), 'rb')

            # 获取音频参数
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            n_frames = wav_file.getnframes()

            # 读取所有帧
            frames = wav_file.readframes(n_frames)
            wav_file.close()

            # 转换为numpy数组
            if sample_width == 2:  # 16-bit PCM
                audio_data = np.frombuffer(frames, dtype=np.int16)
                # 归一化到[-1, 1]
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif sample_width == 1:  # 8-bit PCM
                audio_data = np.frombuffer(frames, dtype=np.uint8)
                # 归一化到[-1, 1]
                audio_data = (audio_data.astype(np.float32) - 128) / 128.0
            else:
                raise ValueError(f"不支持的采样宽度: {sample_width}")

            # 如果是立体声，转换为单声道
            if n_channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)

            return audio_data

        except Exception as e:
            print(f"WAV转换出错：{e}")
            return self._generate_silence(0.5)

    def _generate_silence(self, duration: float, sample_rate: int = 22050) -> np.ndarray:
        """生成静音"""
        samples = int(sample_rate * duration)
        return np.zeros(samples, dtype=np.float32)