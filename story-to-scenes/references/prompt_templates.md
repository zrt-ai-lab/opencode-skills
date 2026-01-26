# 提示词模板库

本文档包含 story-to-scenes 技能使用的标准提示词模板。

## 角色胚子图模板

### 人物角色
```
[风格关键词], single character portrait of [角色名], 
[性别] [年龄段] [种族/民族], 
[发型发色], [眼睛描述], [服装描述], [配饰描述],
[表情/姿态], standing pose,
clean solid [背景色] background, 
full body shot, character design reference,
high quality, detailed,
--no multiple views, turnaround, collage, grid, panels, border, frame, split image
```

### 动物角色
```
[风格关键词], single character portrait of [动物名],
[动物种类], [体型大小], [毛色/皮肤颜色],
[特殊特征如斑纹、角、翅膀等],
[拟人化服装/配饰（如有）],
[表情/姿态], 
clean solid [背景色] background,
full body shot, character design reference,
high quality, detailed,
--no multiple views, turnaround, collage, grid, panels, border, frame, split image
```

### 幻想生物
```
[风格关键词], single character portrait of [生物名],
[生物类型], [体型], [颜色],
[独特特征描述],
[魔法元素/光效（如有）],
[表情/姿态],
clean solid [背景色] background,
full body shot, creature design reference,
high quality, detailed,
--no multiple views, turnaround, collage, grid, panels, border, frame, split image
```

## 场景胚子图模板

### 室内场景
```
[风格关键词], interior scene of [场景名],
[房间类型], [建筑风格],
[主要家具/物品], [装饰细节],
[光线条件], [时间氛围],
[情绪氛围], empty scene without characters,
wide shot, establishing shot,
high quality, detailed environment,
--no people, characters, figures, panels, border, frame, collage
```

### 室外场景
```
[风格关键词], exterior scene of [场景名],
[地点类型], [自然/城市环境],
[主要地标/元素], [植被/建筑],
[天气条件], [时间（日/夜）],
[情绪氛围], empty scene without characters,
wide shot, establishing shot,
high quality, detailed environment,
--no people, characters, figures, panels, border, frame, collage
```

## 故事场景图模板

### 远景
```
[风格关键词], wide establishing shot,
[场景环境描述],
[角色A描述] and [角色B描述] in the distance,
[角色动作/位置关系],
[光线条件], [天气/时间],
[情绪氛围],
cinematic composition, environmental storytelling,
--no multiple panels, comic layout, grid, collage, split frame, border, manga panels
```

### 中景
```
[风格关键词], medium shot,
[场景环境简述],
[角色A描述] [动作/表情], 
[角色B描述] [动作/表情],
[角色互动/位置关系],
[光线条件], [情绪氛围],
balanced composition, narrative scene,
--no multiple panels, comic layout, grid, collage, split frame, border, manga panels
```

### 特写
```
[风格关键词], close-up shot,
[角色描述] [表情细节],
[关键物品/细节（如有）],
[背景虚化/简化处理],
[光线条件], [情绪氛围],
emotional focus, intimate framing,
--no multiple panels, comic layout, grid, collage, split frame, border, manga panels
```

## 排除词标准集

### 反多格拼接
```
--no multiple panels, comic layout, grid, collage, split frame, border, manga panels, 
comic book style, sequential art, storyboard, multi-panel, divided image, frames
```

### 反多视角
```
--no multiple views, turnaround, front and back, side view combination, 
character sheet with poses, reference sheet, model sheet
```

### 反人物（用于纯场景）
```
--no people, characters, figures, humans, animals, creatures, silhouettes
```

## 风格关键词组合

### 温馨治愈系
```
soft lighting, warm color palette, gentle atmosphere, 
cozy feeling, heartwarming scene, peaceful mood
```

### 紧张悬疑系
```
dramatic lighting, high contrast, tense atmosphere,
mysterious shadows, suspenseful mood, cinematic tension
```

### 欢快活泼系
```
bright colors, dynamic composition, joyful atmosphere,
energetic mood, playful scene, vibrant lighting
```

### 忧伤抒情系
```
muted colors, soft focus, melancholic atmosphere,
gentle rain or mist, contemplative mood, emotional depth
```

### 史诗宏大系
```
epic scale, dramatic sky, grand composition,
majestic atmosphere, awe-inspiring, cinematic scope
```
