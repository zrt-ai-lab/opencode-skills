# Edge-TTS 中文音色参考

## 常用音色推荐

| 音色 ID | 性别 | 风格 | 适用场景 |
|---------|------|------|----------|
| zh-CN-YunxiNeural | 男 | 新闻播报风 | 资讯类、技术分享 |
| zh-CN-YunyangNeural | 男 | 温和亲切 | 教程、讲解 |
| zh-CN-XiaoxiaoNeural | 女 | 活泼自然 | 日常分享、生活类 |
| zh-CN-XiaoyiNeural | 女 | 温柔知性 | 文艺、情感类 |
| zh-CN-YunjianNeural | 男 | 浑厚大气 | 宣传片、正式场合 |
| zh-CN-XiaochenNeural | 女 | 甜美可爱 | 儿童内容、轻松话题 |

## 全部中文音色列表

### 普通话（大陆）
- zh-CN-XiaoxiaoNeural (女)
- zh-CN-XiaoyiNeural (女)
- zh-CN-YunjianNeural (男)
- zh-CN-YunxiNeural (男)
- zh-CN-YunyangNeural (男)
- zh-CN-XiaochenNeural (女)
- zh-CN-XiaohanNeural (女)
- zh-CN-XiaomengNeural (女)
- zh-CN-XiaomoNeural (女)
- zh-CN-XiaoqiuNeural (女)
- zh-CN-XiaoruiNeural (女)
- zh-CN-XiaoshuangNeural (女)
- zh-CN-XiaoxuanNeural (女)
- zh-CN-XiaoyanNeural (女)
- zh-CN-XiaoyouNeural (女)
- zh-CN-XiaozhenNeural (女)
- zh-CN-YunfengNeural (男)
- zh-CN-YunhaoNeural (男)
- zh-CN-YunzeNeural (男)

### 粤语（香港）
- zh-HK-HiuGaaiNeural (女)
- zh-HK-HiuMaanNeural (女)
- zh-HK-WanLungNeural (男)

### 台湾
- zh-TW-HsiaoChenNeural (女)
- zh-TW-HsiaoYuNeural (女)
- zh-TW-YunJheNeural (男)

## 语速和音调调整

### 语速 (rate)
- 加快: `+10%`, `+20%`, `+50%`
- 减慢: `-10%`, `-20%`, `-30%`
- 默认: `+0%`

### 音调 (pitch)
- 升高: `+5Hz`, `+10Hz`, `+20Hz`
- 降低: `-5Hz`, `-10Hz`, `-20Hz`
- 默认: `+0Hz`

### 配置示例

```yaml
voice:
  name: "zh-CN-YunxiNeural"
  rate: "+10%"   # 稍快一点
  pitch: "-5Hz"  # 稍低沉一点
```

## 查看所有可用音色

```bash
python scripts/tts_generator.py --list-voices
```
