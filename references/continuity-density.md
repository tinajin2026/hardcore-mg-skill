# 连续性与信息密度

## 全局台账

在生成单段 Prompt 前完成：

```yaml
canvas:
  aspect_ratio: "16:9"
  safe_area: "4%"
  persistent_frame: null
typography:
  chapter: {}
  stamp: {}
  evidence: {}
  data: {}
  ui: {}
colors:
  neutral: ""
  evidence: ""
  risk: ""
  active: ""
objects: {}
timeline:
  current_period: null
  completed_periods: []
causal_state:
  established_nodes: []
  pending_result: null
transition_policy:
  intra_world: "slot_replace"
  chapter_reset: "black_field"
```

## 段间接口

每段必须声明：

```yaml
initial_state:
  inherited_objects: []
  inherited_layout: ""
  inherited_time: ""
end_state:
  visible_objects: []
  layout: ""
  time: ""
  unresolved_motion: "none"
```

下一段的 `initial_state` 必须机械对上上一段 `end_state`。若要清场，清场本身也是一个显式状态。

## 三种连续性

### 世界连续性

锁定画布、边框、网格、纹理、组件槽位和转场政策。内容可换，世界不乱换。

### 对象连续性

锁定位置、尺度、朝向、光源与层状态。属性更新不同时改变所有身份项。

### 论证连续性

记录已经证明的节点、当前比较基线、时间坐标和未回收因果。后段不得把已建立关系重新当新信息，也不得跳过结果回收。

## 密度预算

| 模式 | 视觉元素 | 主动作 | 相机 | 适用 |
|---|---:|---:|---|---|
| 呼吸 | 1 主体 + 1 标签 | 0–1 | 可轻微 | 章节、情绪、产品质感 |
| 解释 | 1 主体 + 1 关系组 | 1 | 稳定 | 默认机制、对比 |
| 证据 | 1 文件/图表 + 辅助标签 | 1 | 固定 | 文件、数据、调查 |
| 高能 | 1 语义印章/单一对象 | 1 强动作 | 短促 | 钩子、发布、转折 |

一段内不要同时使用高能和高密度。先高能命题，再清场进入稳定证据。

## 长片时间层级

- 一级：时代/年份。
- 二级：章节或因果阶段。
- 三级：当前人物、案例、产品或数据。

每 2–4 个章节回到一级或二级锚，显示“我们现在在哪里”。不要把这个常数机械化；当地点、主体和论证都连续时可延长。

## 多主体管理

- 为每个主体分配稳定色、槽位和短标签。
- 中立事实使用白/灰，不偏向任一主体。
- 主体退出时保留低对比锚，或显式完成退场。
- 新主体进入前先说明它与当前结构的关系。

## 章节换风格

允许材质切换，但至少保留一个共同锚：地图、时间、对象、框选/放大动作或语义色。若没有共同锚，先建立桥接段。

## 审核问题

1. 任意暂停一帧，能否判断当前章节和主对象？
2. 去掉旁白，状态变化是否仍可理解？
3. 上段留下的对象是否在下段无理由消失、跳位或变色？
4. 关系图是否保留已建立节点并清楚加入新节点？
5. 高密度段是否稳定，低密度段是否给了呼吸？
