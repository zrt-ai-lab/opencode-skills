# {{PROJECT_NAME}} 场景图集

## 项目信息

| 属性 | 值 |
|------|------|
| **项目名称** | {{PROJECT_NAME}} |
| **风格** | {{STYLE_PRESET}} |
| **尺寸** | {{ASPECT_RATIO}} |
| **场景数** | {{SCENE_COUNT}} |
| **生成日期** | {{DATE}} |

---

## 角色一览

| 角色 | 胚子图 | 描述 |
|------|--------|------|
{{#CHARACTERS}}
| {{NAME}} | ![[characters/{{NAME}}.png\|200]] | {{DESCRIPTION}} |
{{/CHARACTERS}}

---

## 场景图集

{{#SCENES}}
### Scene {{INDEX}}：{{SCENE_NAME}}

![[scenes/scene_{{INDEX}}_{{SCENE_NAME}}.png]]

> {{SCENE_DESCRIPTION}}

**出场角色**：{{CHARACTERS}}
**镜头类型**：{{SHOT_TYPE}}
**情绪氛围**：{{MOOD}}

<details>
<summary>生成提示词</summary>

```
{{PROMPT}}
```

</details>

---

{{/SCENES}}

## 生成记录

- **开始时间**：{{START_TIME}}
- **完成时间**：{{END_TIME}}
- **总耗时**：{{DURATION}}
- **重试次数**：{{RETRY_COUNT}}

---

*由 story-to-scenes 技能自动生成*
