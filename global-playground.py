from music21 import converter, note

# 1. 加载乐谱
score = converter.parse('input/心印-测试.musicxml') 
part = score.parts[0] if score.parts else score

# 2. 展平流 (Flatten) 以获取所有元素的时间线
# 注意：使用 .flatten() 替代 .flat 以消除警告
part_flat = part.flatten()

# 3. 使用 secondsMap 获取绝对时间信息
# secondsMap 返回一个列表，包含每个元素的绝对时间数据
s_map = part_flat.secondsMap

# 4. 遍历并提取 Note 类型的数据
print(f"{'Pitch':<10} | {'Offset(Beats)':<15} | {'Start Time(s)':<15} | {'Duration(s)':<15}")
print("-" * 60)

count = 0
for event in s_map:
    element = event['element']
    
    # 只处理前3个音符作为演示
    if isinstance(element, note.Note):
        start_seconds = event['offsetSeconds']   # <--- 这就是你要的绝对开始时间
        duration_seconds = event['durationSeconds'] # 这等于 note.seconds
        
        print(f"{str(element.pitch):<10} | {element.offset:<15} | {start_seconds:<15.4f} | {duration_seconds:<15.4f}")
        
        count += 1
        if count >= 3:
            break