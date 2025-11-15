"""
TTS引擎工厂类
提供统一的接口来创建和使用不同的语音合成引擎
支持 espeak-ng 和 Windows SAPI (pyttsx3)
"""

import shutil
import platform
from typing import Optional

# 动态导入模块，避免导入错误
def import_espeak_engine():
    """导入espeak引擎"""
    try:
        from FlorenceEngine.FlorenceSpeakGenerateor.FlorenceSpeakGenerateor import FlorenceSpeakGenerateor
        return FlorenceSpeakGenerateor
    except ImportError:
        return None

def import_windows_engine():
    """导入Windows TTS引擎"""
    try:
        from FlorenceEngine.FlorenceSpeakGenerateor.WindowsFlorenceSpeakGenerateor import WindowsFlorenceSpeakGenerateor
        return WindowsFlorenceSpeakGenerateor
    except ImportError:
        return None


class TTSFactory:
    """TTS引擎工厂类"""

    # 可用引擎类型
    ENGINES = {
        'espeak': {
            'name': 'eSpeak-NG',
            'description': '开源语音合成引擎（质量一般但跨平台）',
            'engine': 'espeak_ng',
            'priority': 1
        },
        'windows': {
            'name': 'Windows SAPI',
            'description': '微软Windows语音合成（质量较好，原生支持慧慧）',
            'engine': 'windows_sapi',
            'priority': 2 if platform.system() == 'Windows' else 0
        }
    }

    def __init__(self):
        """
        初始化TTS工厂
        """
        self.available_engines = []
        self.detect_available_engines()
        self.current_engine = None

    def detect_available_engines(self):
        """
        检测系统中可用的TTS引擎
        """
        print("正在检测可用TTS引擎...")

        # 检测Windows TTS
        if platform.system() == 'Windows':
            try:
                print("正在测试Windows SAPI...")
                temp_engine = import_windows_engine()
                if temp_engine:
                    # 快速测试
                    test_engine = temp_engine()
                    print("  Windows SAPI 可用")
                    self.available_engines.append('windows')
                else:
                    print("  Windows SAPI 加载失败")
            except Exception as e:
                print(f"  Windows SAPI 不可用: {e}")

        # 检测eSpeak-NG
        if shutil.which("espeak-ng"):
            try:
                print("正在测试eSpeak-NG...")
                espeak_engine = import_espeak_engine()
                if espeak_engine:
                    print("　　eSpeak-NG 可用")
                    self.available_engines.append('espeak')
                else:
                    print("　　eSpeak-NG 模块加载失败")
            except Exception as e:
                print(f"　　eSpeak-NG 不可用: {e}")
        else:
            print("　　eSpeak-NG 未安装")

        # 排序优先级
        self.available_engines.sort(key=lambda x: self.ENGINES[x]['priority'], reverse=True)
        print(f"可用引擎排序完成: {self.available_engines}")

    def get_available_engines(self) -> list:
        """
        获取可用的TTS引擎列表
        """
        return self.available_engines.copy()

    def get_engine_info(self, engine_name: str) -> dict:
        """
        获取引擎信息
        """
        return self.ENGINES.get(engine_name, {})

    def create_engine(self, engine_name: str = None):
        """
        创建TTS引擎实例

        Args:
            engine_name: 引擎名称，如果为空则使用最佳可用引擎

        Returns:
            TTS引擎实例
        """
        if engine_name is None:
            if not self.available_engines:
                raise Exception("没有可用的TTS引擎")
            engine_name = self.available_engines[0]

        if engine_name not in self.available_engines:
            raise Exception(f"TTS引擎 '{engine_name}' 不可用")

        print(f"正在创建TTS引擎: {self.ENGINES[engine_name]['name']}")

        if engine_name == 'espeak':
            espeak_class = import_espeak_engine()
            if espeak_class:
                self.current_engine = espeak_class()
                return self.current_engine
            else:
                raise Exception("eSpeak-NG模块加载失败")

        elif engine_name == 'windows':
            windows_class = import_windows_engine()
            if windows_class:
                self.current_engine = windows_class()
                return self.current_engine
            else:
                raise Exception("Windows SAPI模块加载失败")

        else:
            raise Exception(f"未知的TTS引擎: {engine_name}")

    def create_best_engine(self):
        """
        创建最佳的TTS引擎
        """
        return self.create_engine()

    def get_current_engine(self):
        """
        获取当前使用的引擎
        """
        return self.current_engine

    def auto_select_engine(self) -> str:
        """
        自动选择最合适的引擎
        """
        if 'windows' in self.available_engines:
            print("自动选择Windows SAPI（微软慧慧）- 推荐")
            return 'windows'
        elif 'espeak' in self.available_engines:
            print("自动选择eSpeak-NG - 备选方案")
            return 'espeak'
        else:
            raise Exception("没有可用的TTS引擎")


# 测试函数
def test_tts_factory():
    """测试TTS工厂功能"""
    print("=== TTS工厂测试 ===")

    factory = TTSFactory()

    print("\n可用引擎:")
    for engine_name in factory.get_available_engines():
        info = factory.get_engine_info(engine_name)
        print(f"  {engine_name}: {info['name']} - {info['description']}")

    try:
        # 自动选择最佳引擎
        best_engine_name = factory.auto_select_engine()
        print(f"\n选择引擎: {best_engine_name}")

        # 创建引擎
        engine = factory.create_best_engine()
        print("引擎创建成功")

        # 测试文本
        test_text = "你好，这是Windows TTS测试"
        print(f"\n测试语音: {test_text}")

        if hasattr(engine, '_generate_single_word_speech'):
            audio_data = engine._generate_single_word_speech(test_text)
        else:
            audio_data = None

        if audio_data is not None:
            print(f"语音合成成功，数据长度: {len(audio_data)}")

            # 播放测试
            try:
                from debugger import play
                print("正在播放...")
                play(audio_data)
            except ImportError:
                print("无法播放，debugger模块不可用")
            except Exception as e:
                print(f"播放失败: {e}")

    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_tts_factory()