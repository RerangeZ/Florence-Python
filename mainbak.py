import pyworld as pw
import numpy as np

# 示例音频数据和采样率
x: np.ndarray = np.random.randn(16000)  # 1秒的随机音频数据
fs: int = 16000  # 采样率

# Convert speech into features (using default arguments)
f0: np.ndarray
sp: np.ndarray
ap: np.ndarray
f0, sp, ap = pw.wav2world(x, fs)

y: np.ndarray = pw.synthesize(f0, sp, ap, fs)  
