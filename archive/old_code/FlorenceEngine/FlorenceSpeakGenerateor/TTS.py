import subprocess
import shutil

from xpinyin import Pinyin

class FlorenceSpeakGenerateor:
    outputWav:bytes
    word:str

    @staticmethod
    def judgeChinese(string:str)->bool:
        """
        如果全是中文，则返回True
        """
        for char in string:
            if '\u4e00' <= char <= '\u9fa5':
                return True
        return False


    def init(self,word:str):
        """
        输入中文字符或拼音，若是汉字则转拼音。
        包含合法性检测。
        """
        #此为拼音转换器
        p = Pinyin() 

        if len(word)>1:
            raise ValueError("每个音符只支持一个字")

        if self.judgeChinese(word):
            p.get_pinyin(word, ' ')

        self.word = word


    def synthesize_pinyin_speech(self) -> bytes | None:
        """
        使用 eSpeak-NG 将带音调的拼音字符串合成为语音。

        Args:
            pinyin_text: 拼音字符串.

        Returns:
            如果成功，返回包含 WAV 音频数据的 bytes 对象。
            如果失败 (例如 espeak-ng 未安装或出错), 则退出。
        """
        if not shutil.which("espeak-ng"):
            print("错误: 'espeak-ng' 命令未找到。")
            print("请确保已经安装 eSpeak-NG 并将其添加到了系统的 PATH 环境变量中。")
            return None

        formatted_text = f"[[{pinyin_text}]]"



        command = [
            "espeak-ng",
            "-v", "cmn-latn-pinyin",
            "--stdout",
            formatted_text
        ]

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True
            )
            print("语音合成成功，已在内存中生成 WAV 音频数据。")
            self.outputWav = result.stdout
        
        except subprocess.CalledProcessError as e:
            print(f"eSpeak-NG 执行出错 (返回码: {e.returncode}):")
            print(e.stderr.decode('utf-8', errors='ignore'))
            exit()