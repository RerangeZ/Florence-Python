# 重构前文件状态清单

## 项目文件状态 (重构前)

### 核心代码文件
- [x] FlorenceEngine/ - 主要引擎模块
 - [x] FlorenceScoreDecoder/ScoreDecoder.py - 乐谱解码器
 - [x] FlorenceSpeakGenerateor/TTS.py - 语音合成器
 - [x] Objects/Word.py, Selector.py - 核心数据结构
- [x] main.py - 主入口文件
- [x] mainbak.py - 主程序备份
- [x] test.py - 测试文件

### 配置文件
- [x] requirements.txt - Python依赖
- [x] .gitignore - Git忽略规则
- [x] .github/workflows/ - GitHub工作流配置
- [x] .vscode/ - VS Code编辑器配置
- [x] typings/ - 类型定义文件
- [x] FlorenceEnv/ - Python虚拟环境

### 资源文件
- [x] input/ - 乐谱输入文件目录
- [x] dependence/espeak-ng.msi - eSpeak-NG安装包
- [x] 架构图.jpg - 系统架构图
- [x] output_pinyin.wav - 测试输出音频

### 文档文件
- [x] README.md - 项目说明
- [x] CLAUDE.md - Claude Code使用指南

## 归档状态
所有文件已备份至 archive/ 目录下的相应子目录中

## 归档时间
2025年11月7日 12:55:55

## 归档说明
保留依赖环境不变，仅整理代码和文档结构用于重构