from music21 import converter
from music21.stream import Score, Part, Opus
from music21.note import Note
from Objects.Word import Word, TimeSpan


class ScoreDecoder:
    oriScoreObj: Score
    worldList: list[Word]

    def __init__(self, scorePath: str) -> None:
        self.worldList = []  # 初始化空列表
        parsed = converter.parse(scorePath)
        if isinstance(parsed, Score):
            self.oriScoreObj = parsed
        elif isinstance(parsed, Part):
            # 如果是单个声部，将其包装成 Score
            self.oriScoreObj = Score()
            self.oriScoreObj.append(parsed)
        elif isinstance(parsed, Opus):
            # 如果是 作品集，获取第一个乐谱
            self.oriScoreObj = parsed.scores[0] if parsed.scores else Score()
        else:
            raise ValueError(f"解析musicXml失败，非法类型: {type(parsed)}")
    
    def decode(self) -> None:
        for note in self.oriScoreObj.flatten().notes:
            if not isinstance(note, Note):  # 跳过非音符对象
                continue
                
            # 从音符中提取需要的信息
            start_time = float(note.offset)  # 转换为浮点数
            duration = float(note.duration.quarterLength)  # 转换为浮点数
            freq = note.pitch.frequency  # 获取频率
            
            # 检查歌词是否存在
            if not note.lyric:
                raise ValueError(f"音符缺少歌词：位置 {start_time}, 音高 {note.pitch}")
            text = note.lyric
            
            # 创建新的 Word 实例
            word = Word(
                time=TimeSpan(start=start_time, duration=duration),
                baseFreq=freq,
                wordStr=text
            )
            self.worldList.append(word)