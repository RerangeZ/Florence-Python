"""
基于Windows SAPI和pyttsx3的语音合成器
使用微软Windows内置的语音引擎（包括慧慧）
"""

import numpy as np
import wave
import io
import pyttsx3
from typing import List
import tempfile
import os
import sys

# 临时导入路径处理，用于独立测试
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from FlorenceEngine.Objects.data_models import Song, Word
except ImportError:
    # 测试时不导入这些模型
    Song = None
    Word = None


class WindowsFlorenceSpeakGenerateor:
    """基于Windows SAPI的语音合成器，使用pyttsx3库"""

    # 写死的采样率 - 统一为44100Hz
    OUTPUT_SAMPLE_RATE = 44100  # Hz

    def __init__(self):
        """
        初始化Windows语音合成引擎
        """
        try:
            self.engine = pyttsx3.init('sapi5')

            # 设置语音参数
            self.engine.setProperty('rate', 140)   # 语速，中文建议140左右
            self.engine.setProperty('volume', 0.9) # 音量0.0-1.0

            # 获取并设置中文语音
            voices = self.engine.getProperty('voices')
            chinese_voice = None

            for i, voice in enumerate(voices):
                print(f"语音{i}: {voice.id}")
                # 查找中文语音（包含zh-CN或Language标识为中文的）
                if 'zh-CN' in voice.id or 'zh-CN' in str(voice.languages) if hasattr(voice, 'languages') else False:
                    chinese_voice = voice
                    print(f"找到中文语音: {voice.id}")
                    break
                elif 'Hui' in voice.id or 'Xiaoxiao' in voice.id:  # 慧慧或晓晓
                    chinese_voice = voice
                    print(f"找到慧慧/晓晓语音: {voice.id}")
                    break

            if chinese_voice:
                self.engine.setProperty('voice', chinese_voice.id)
                self.chinese_voice_id = chinese_voice.id
            else:
                # 如果没有中文语音，使用第一个可用的语音
                if voices:
                    self.engine.setProperty('voice', voices[0].id)
                    self.chinese_voice_id = voices[0].id
                    print(f"使用默认语音: {voices[0].id}")
                else:
                    raise Exception("没有找到可用的语音")

            print(f"初始化Windows语音合成器成功，使用语音: {self.chinese_voice_id}")

        except Exception as e:
            print(f"初始化Windows语音合成器失败: {e}")
            print("请确保系统已安装中文语音包")
            raise

    @staticmethod
    def judgeChinese(string: str) -> bool:
        """
        检测是否包含中文
        """
        for char in string:
            if '\u4e00' <= char <= '\u9fa5':
                return True
        return False

    def generate_song_speech(self, song):
        """
        为整个song中的所有word合成原始语音数据
        """
        if Song is None:
            print("警告：Song模型未加载，无法处理完整歌曲")
            return song

        print(f"开始处理歌曲，共{len(song.trackList)}个track")

        for i, track in enumerate(song.trackList):
            print(f"处理第{i+1}个track...")
            for section in track.sectionList:
                self._process_section(section)

        print("所有语音合成完成")
        return song

    def _process_section(self, section):
        """处理整个section中的所有words"""
        for i, word in enumerate(section.wordList):
            # 只为还没有oriWave的word生成语音
            if word.oriWave is None:
                print(f"  合成语音: {word.lrc}")
                word.oriWave = self._generate_single_word_speech(word.lrc)
                if i % 10 == 0:  # 每10个词报告一次进度
                    print(f"  进度: {i+1}/{len(section.wordList)}")
            else:
                print(f"  跳过已合成: {word.lrc}")

    def _generate_single_word_speech(self, text: str) -> np.ndarray:
        """
        使用Windows TTS合成单个词语的语音
        """
        if not text or not text.strip():
            # 空文本返回静音
            return self._generate_silence(0.2, self.OUTPUT_SAMPLE_RATE)

        try:
            # 创建一个临时WAV文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as f:
                temp_wav_path = f.name

            # 配置TTS引擎
            self.engine.setProperty('rate', 140)  # 语速适中
            self.engine.setProperty('volume', 0.9)  # 音量

            # 保存语音到文件
            self.engine.save_to_file(text, temp_wav_path)
            self.engine.runAndWait()

            # 等待文件写入完成
            attempts = 0
            while not os.path.exists(temp_wav_path) and attempts < 50:
                import time
                time.sleep(0.1)
                attempts += 1

            if not os.path.exists(temp_wav_path):
                raise Exception("语音文件生成失败")

            # 读取生成的WAV文件
            with open(temp_wav_path, 'rb') as f:
                wav_data = f.read()

            # 将WAV数据转换为numpy数组
            audio_data = self._wav_bytes_to_numpy(wav_data)

            # 清理临时文件
            try:
                os.remove(temp_wav_path)
            except:
                pass

            return audio_data

        except Exception as e:
            print(f"TTS合成出错：{e}")
            # 返回静音
            return self._generate_silence(0.2, self.OUTPUT_SAMPLE_RATE)

    def _wav_bytes_to_numpy(self, wav_bytes: bytes) -> np.ndarray:
        """
        将WAV字节数据转换为numpy数组
        """
        try:
            # 使用wave模块解析WAV数据
            wav_file = wave.open(io.BytesIO(wav_bytes), 'rb')

            # 获取音频参数
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()

            print(f"WAV参数: {n_channels}声道, {sample_width}字节, {sample_rate}Hz, {n_frames}帧")

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

            # 如果采样率不是目标采样率，进行重采样
            if sample_rate != self.OUTPUT_SAMPLE_RATE:
                audio_data = self._resample_audio(audio_data, sample_rate, self.OUTPUT_SAMPLE_RATE)

            return audio_data

        except Exception as e:
            print(f"WAV转换出错：{e}")
            return self._generate_silence(0.5, self.OUTPUT_SAMPLE_RATE)

    def _resample_audio(self, audio_data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        """
        简单的音频重采样
        """
        if original_rate == target_rate:
            return audio_data

        # 计算新的长度
        new_length = int(len(audio_data) * target_rate / original_rate)

        # 使用线性插值进行重采样
        old_indices = np.arange(len(audio_data))
        new_indices = np.linspace(0, len(audio_data) - 1, new_length)

        # 线性插值
        resampled_audio = np.interp(new_indices, old_indices, audio_data)

        return resampled_audio.astype(np.float32)

    def _generate_silence(self, duration: float, sample_rate: int = 22050) -> np.ndarray:
        """生成静音"""
        if sample_rate is None:
            sample_rate = self.OUTPUT_SAMPLE_RATE
        samples = int(sample_rate * duration)
        return np.zeros(samples, dtype=np.float32)

    # 兼容性方法，保持与原FlorenceSpeakGenerateor相同的接口
    @staticmethod
    def judgeChinese(string: str) -> bool:
        """
        如果全是中文，则返回True
        """
        for char in string:
            if '\u4e00' <= char <= '\u9fa5':
                return True
        return False


# 测试函数
def test_windows_tts():
    """测试Windows TTS功能"""
    print("开始测试Windows TTS语音合成器...")

    try:
        # 创建TTS引擎
        tts = WindowsFlorenceSpeakGenerateor()

        # 测试文本
        test_texts = [
            "你好",
            "这是一段测试语音",
            "微软慧慧语音合成测试"
        ]

        for text in test_texts:
            print(f"\n正在合成: {text}")
            audio_data = tts._generate_single_word_speech(text)

            print(f"音频长度: {len(audio_data)} 样本")
            print(f"预计时长: {len(audio_data)/tts.OUTPUT_SAMPLE_RATE:.3f} 秒")

            # 播放测试
            try:
                from debugger import play
                print("正在播放...")
                play(audio_data, volume=0.7)
                print("播放完成")
            except Exception as e:
                print(f"播放失败: {e}")

        print("\nWindows TTS测试完成")

    except Exception as e:
        print(f"Windows TTS测试失败: {e}")


if __name__ == "__main__":
    test_windows_tts()