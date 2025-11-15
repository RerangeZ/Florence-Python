from music21 import converter
from music21.stream import Score, Part, Opus
from music21.note import Note
from xpinyin import Pinyin
from typing import List
import os
from FlorenceEngine.Objects.data_models import Song, Track, Section, Word, Time


class FlorenceScoreDecoder:
    """负责处理musicXML输入并解析为song对象"""

    def __init__(self):
        self.pinyin_converter = Pinyin()

    def decode_score(self, score_path: str) -> Song:
        """
        解析MusicXML文件并创建Song对象

        Args:
            score_path: MusicXML文件路径

        Returns:
            Song对象
        """
        # 解析MusicXML文件
        parsed = converter.parse(score_path)

        if isinstance(parsed, Score):
            score = parsed
        elif isinstance(parsed, Part):
            # 如果是单个声部，将其包装成 Score
            score = Score()
            score.append(parsed)
        elif isinstance(parsed, Opus):
            # 如果是作品集，获取第一个乐谱
            score = parsed.scores[0] if parsed.scores else Score()
        else:
            raise ValueError(f"解析musicXml失败，非法类型: {type(parsed)}")

        # 获取文件名（不含扩展名）
        song_name = os.path.splitext(os.path.basename(score_path))[0]

        # 创建歌曲对象
        song = Song(
            trackList=[],
            name=song_name
        )

        # 处理每个声部
        for part in score.parts:
            track = self._process_part(part)
            song.trackList.append(track)

        return song

    def _process_part(self, part) -> Track:
        """处理单个声部，创建Track对象"""
        sections = []
        current_section_words = []

        # 获取四分音符时长（毫秒）
        quarter_duration_ms = 500  # 假设120 BPM，可根据实际需要调整

        for note in part.flatten().notes:
            if not isinstance(note, Note):
                continue

            # 检查音域限制
            freq = note.pitch.frequency
            if freq < 130:  # C3
                print(f"警告：音符音域低于130Hz，将被跳过：{note.pitch}")
                continue

            # 检查歌词
            if not note.lyric:
                raise ValueError(f"音符缺少歌词：位置 {note.offset}, 音高 {note.pitch}")

            # 转换中文为拼音并去除声调
            lyric = self._convert_to_pinyin(note.lyric)

            # 计算时间（转换为毫秒）
            start_time = int(float(note.offset) * quarter_duration_ms)
            duration = int(float(note.duration.quarterLength) * quarter_duration_ms)
            end_time = start_time + duration

            # 创建Word对象
            word = Word(
                pitch=freq,
                time=Time(start=start_time, end=end_time),
                lrc=lyric
            )

            current_section_words.append(word)

        # 创建第一个section（整个part作为一个section）
        if current_section_words:
            # 检查音符重叠
            self._check_overlap(current_section_words)

            section = Section(
                wordList=current_section_words,
                sectionStart=0  # 相对track开始
            )
            sections.append(section)

        return Track(sectionList=sections)

    def _convert_to_pinyin(self, text: str) -> str:
        """转换中文为拼音并去除声调"""
        # 如果是纯英文字符，直接返回
        if text.isascii():
            return text.lower()

        # 转换为拼音
        pinyin = self.pinyin_converter.get_pinyin(text, tone_marks='numbers')

        # 去除声调数字
        import re
        pinyin_no_tone = re.sub(r'\d', '', pinyin)

        return pinyin_no_tone.lower()

    def _check_overlap(self, words: List[Word]) -> None:
        """检查音符是否重叠"""
        for i in range(len(words) - 1):
            current_word = words[i]
            next_word = words[i + 1]

            if current_word.time.end > next_word.time.start:
                raise ValueError(f"音符时间重叠：第{i}个音符结束时间{current_word.time.end} > 第{i+1}个音符开始时间{next_word.time.start}")