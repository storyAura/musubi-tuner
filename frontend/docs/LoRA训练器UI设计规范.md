# LoRA 训练器 UI 设计规范

**风格定位:黑白极简 · 开发者工具风(Vercel 体系定制版)**

> 本文档基于 design-master 技能库的 Vercel 设计规范(`C:\Users\21699\.claude\skills\design-master\references\vercel.md`)裁剪定制,面向 LoRA 训练器这类「参数表单 + 实时监控 + 日志终端」的工具型界面。开发或让 AI 生成界面时,照本文档执行即可。

---

## 0. 方向结论(TL;DR)

- **主方案:Vercel 式黑白极简。** 近黑墨色 `#171717` + 纯白/98% 白画布,全界面唯一的彩色是蓝 `#0070f3`,等宽字体标注一切技术信息(参数名、路径、数值、日志)。
- **为什么适合训练器:** 训练器 = 大量表单 + 数据监控 + 终端日志,Vercel 这套语言正是为「工程师盯参数」而生;黑白底色还有一个专属好处——**训练样图预览和 loss 曲线会成为画面里唯一的色彩焦点**,界面永远不和图抢眼。
- **暗色模式一并定义**(见 §2)。挂机训练一盯几小时,暗色是刚需;暗色版视觉上即等效于 x.ai 那种黑底方案,一套 token 两种皮肤。

### 备选方案(想换口味时)

| 方案 | 特点 | 适合 | 这次不选的理由 |
|---|---|---|---|
| x.ai | 纯黑底 + 白描边药丸 | 只做暗色的酷炫感 | 单皮肤;高密度表单的对比分层更难做 |
| uber | 最纯血黑白 `#000`/`#fff` | 品牌感强的展示页 | 药丸大字风,表单密集时显笨重 |
| apple | 白 + 浅灰 + 唯一蓝 | 营销展示页 | 是「陈列馆」不是「驾驶舱」,组件密度不够 |

---

## 1. 五条设计原则

1. **黑白为骨,蓝色为脉。** 95% 面积只有黑白灰;蓝 `#0070f3` 只出现在链接、「训练中」状态、loss 曲线主线上。不引入第二个彩色。
2. **mono 即技术。** 凡是「机器读的」——参数名 `unet_lr`、路径、数值、日志、表头——一律等宽字体;凡是「人读的」——标题、说明——一律无衬线。这一条是整套风格的灵魂。
3. **hairline 分层,不靠重阴影。** 1px `#ebebeb` 细线 + 多层微阴影划分区域;禁止单层大黑阴影、禁止玻璃拟态。
4. **留白外松内紧。** 区块之间 32–64px 大间距;卡片内部标题/内容 8–12px 紧凑堆叠。「外面松、里面紧」是这套语言的呼吸感来源。
5. **语义色 = 训练状态,只有三个。** 蓝 = 进行中/完成、红 = 失败、琥珀 = 警告(如显存吃紧)。永远「颜色 + 图标/文字」双编码,不裸靠颜色。注意这套语言的怪癖:**成功也是蓝,没有绿色**。

---

## 2. 色彩 Token

### 亮色(默认)

| Token | 值 | 用途 |
|---|---|---|
| `canvas` | `#fafafa` | 页面底色(98% 白,不是纯白) |
| `surface` | `#ffffff` | 卡片、输入框、弹窗 |
| `surface-2` | `#f5f5f5` | 内嵌区(表头底、代码内底、hover 行) |
| `hairline` | `#ebebeb` | 1px 分隔线、卡片边、输入框边 |
| `hairline-strong` | `#a1a1a1` | 需要更明确的分隔时 |
| `ink` | `#171717` | 标题、主文字 |
| `body` | `#4d4d4d` | 次级文字、说明 |
| `mute` | `#888888` | 占位符、辅助标签、参数名徽章 |
| `primary` | `#171717` | 主按钮底(黑就是行动色) |
| `on-primary` | `#ffffff` | 主按钮文字 |
| `accent` | `#0070f3` | 链接、训练中状态、loss 主线 |
| `accent-deep` | `#0761d1` | 链接 hover/按下 |
| `accent-soft` | `#d3e5ff` | 信息提示底色 |
| `error` | `#ee0000` | 失败、校验错误 |
| `error-soft` | `#f7d4d6` | 错误提示底色 |
| `warning` | `#f5a623` | 警告(显存、学习率异常) |
| `warning-soft` | `#ffefcf` | 警告提示底色 |
| `terminal-bg` | `#171717` | 日志终端底(亮色界面里也保持深底) |
| `terminal-ink` | `#ededed` | 日志文字 |
| `chart-line` | `#0070f3` | loss 平滑线 |
| `chart-raw` | `#c9c9c9` | loss 原始线(细、退后) |

### 暗色

| Token | 值 | 说明 |
|---|---|---|
| `canvas` | `#000000` | 纯黑页面底 |
| `surface` | `#0a0a0a` | 卡片 |
| `surface-2` | `#141414` | 内嵌区 |
| `hairline` | `#262626` | 暗色下分层几乎全靠它 |
| `hairline-strong` | `#444444` | — |
| `ink` | `#ededed` | 主文字(不用纯白,刺眼) |
| `body` | `#a1a1a1` | 次级文字 |
| `mute` | `#707070` | 辅助 |
| `primary` | `#ededed` | **主按钮极性翻转:白底黑字** |
| `on-primary` | `#0a0a0a` | — |
| `accent` | `#3291ff` | 蓝色提亮一档,黑底上才够清楚 |
| `error` | `#ff6166` | 同理提亮 |
| `warning` | `#ffb224` | 同理提亮 |
| `terminal-bg` | `#0a0a0a` | 加 1px hairline 边和卡片区分 |
| `chart-raw` | `#3a3a3a` | 暗色下的原始线 |

### 使用规则

- 主按钮:亮色黑底白字、暗色白底黑字。**极性翻转是这套语言的招牌深度手法**,亮色界面里的黑色终端块本身就是「深度装饰」。
- 训练状态映射:`空闲` 灰 → `排队中` 灰 → `训练中` 蓝(呼吸点)→ `已完成` 蓝 → `失败` 红;`显存警告` 琥珀,可与任意状态叠加。

---

## 3. 字体与排版

### 字族

```
无衬线(界面):Inter, -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif
等宽(技术):"JetBrains Mono", ui-monospace, Consolas, monospace
```

- Geist 是 Vercel 私有字体,**Inter 是官方推荐替身**(mono 替身是 JetBrains Mono)。
- 所有数值列 / 步数 / loss 值加 `font-variant-numeric: tabular-nums`,数字才会上下对齐。

### 层级(工具界面,比营销页整体小一档)

| 用途 | 字号/行高 | 字重 | 字距 | 字体 |
|---|---|---|---|---|
| 页面标题 | 20/28 | 600 | -0.4px | sans |
| 区块标题 | 16/24 | 600 | -0.2px | sans |
| 分组 eyebrow | 12/16 大写 | 400 | +0.5px | **mono** |
| 表单 label | 14/20 | 500 | 0 | sans |
| 正文 | 14/20 | 400 | 0 | sans |
| 辅助说明 | 12/16 | 400 | 0 | sans, mute 色 |
| 参数名徽章 | 12/16 | 400 | 0 | **mono**, mute 色 |
| 日志 | 13/20 | 400 | 0 | **mono** |
| 大数字(loss/步数) | 24–32 | 600 | 0 | **mono** |

### 规则

- **600 是字重天花板**,永不用 700/800。
- 英文和数字可以用负字距;**中文标题字距归零或最多 -0.25px**,中文吃不了英文那种 -2.4px 的狠字距。
- mono 永不用于成段正文,只标技术信息。
- 大写 + 正字距只允许出现在 mono eyebrow 上(如 `NETWORK`、`OPTIMIZER`),无衬线标题永远句式大小写。

---

## 4. 间距 · 圆角 · 阴影

- **间距 4px 基数:** 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64。
- **圆角:** 工具界面统一 **6px**(按钮、输入框、下拉、徽章),卡片 8px,弹窗 12px。**不要用 100px 药丸**——那是 Vercel 营销页的尺度,和 6px 同屏会打架。
- **阴影(叠加式,永远带 1px 内圈线):**

| 层级 | 值 | 用途 |
|---|---|---|
| 卡片默认 | `0 0 0 1px rgba(0,0,0,.08)` | 细线即边界 |
| 悬浮卡 | `0 1px 1px rgba(0,0,0,.02), 0 2px 2px rgba(0,0,0,.04), 0 0 0 1px rgba(0,0,0,.08)` | hover 的卡片、tooltip |
| 弹窗 | `0 8px 16px -4px rgba(0,0,0,.04), 0 24px 32px -8px rgba(0,0,0,.06), 0 0 0 1px rgba(0,0,0,.08)` | modal、下拉菜单 |

- 暗色下阴影基本不可见,分层改为完全依赖 `hairline #262626` + surface 阶梯(#000 → #0a0a0a → #141414)。

---

## 5. 布局蓝图

```
┌────────────────────────────────────────────────────────┐
│ 顶栏 56–64px: wordmark · 页签     GPU/显存徽章 · 主按钮 │
├─────────┬──────────────────────────┬───────────────────┤
│ 侧栏     │ 参数表单区                │ 监控栏(sticky)   │
│ 220–    │ max-width 680–760px      │ 320–380px         │
│ 240px   │ 分组卡片纵向流             │ 进度 / loss / 日志 │
│         │                          │ / 样图预览         │
└─────────┴──────────────────────────┴───────────────────┘
```

- **侧栏项:** 训练 / 数据集 / 监控 / 预设 / 设置。激活态 = 左缘 2px `ink` 指示条 + `surface-2` 底 + 文字变 `ink`;非激活文字用 `body` 色。
- **响应式:** <1200px 时监控栏折叠为表单区上方的标签页;<768px 侧栏收成图标条。
- **节奏:** 表单区块之间 32px;卡片内 padding 16–24px;表单行间 16px。
- GPU 徽章示例:`RTX 4090 · 23.2/24 GB`,mono 12px,显存超过 90% 时染琥珀色。

---

## 6. 组件配方

### 6.1 参数表单(训练器的主体)

- 每个字段一行:左侧中文 label(14/500),label 右侧跟一个 **mono 参数名徽章**(12px,mute 色,如 `unet_lr`、`network_dim`)——既照顾新手认中文,又让老手一眼对上 kohya 参数。
- 输入框:高 36–40px,`surface` 底,1px `hairline` 边,6px 圆角;聚焦时边框变 `ink` + 外圈 `0 0 0 4px rgba(0,0,0,.06)`(暗色外圈 `rgba(255,255,255,.08)`)。
- 数字输入右对齐 + mono;路径输入整体 mono。
- **分组:一张卡片一组**——基础(底模/数据集/输出)、网络(dim/alpha/类型)、优化器与学习率、训练参数(epoch/batch/精度)、保存与采样。组名 16/600,上方配 mono eyebrow(`NETWORK`)。
- 高级参数用 `<details>` 原生折叠收进「高级」区,**不要做成第二个页面**。
- 开关:36×20 胶囊,开 = `ink`(暗色 = 白),不用彩色开关。
- 校验错误:边框变 `error` + 下方 12px 红字,直说怎么改(「学习率需为正数,常用 1e-4」),不说「输入无效」。

### 6.2 按钮

| 类型 | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| 主按钮 | 黑底白字 | 白底黑字 | 开始训练 |
| 次按钮 | 白底 + hairline 边 | 透明 + hairline 边 | 保存预设、导出 toml |
| 危险 | 白底红字红边;hover 红底白字 | 同理 | 停止训练 |

高度 36–40px,6px 圆角,字 14/500。禁用态 40% 透明度 + `cursor: not-allowed`。「开始训练」在训练中变为「停止训练」(危险态),不要并排放两个按钮。

### 6.3 状态徽章

格式统一:状态点(6px 圆)+ 12px mono 文字,`soft` 底色,6px 圆角,padding 2px 8px。

`● 空闲`(灰)/ `● 排队中`(灰)/ `● 训练中`(蓝,点带 2s 呼吸动画)/ `● 已完成`(蓝)/ `● 失败`(红)/ `▲ 显存警告`(琥珀)

### 6.4 进度模块

- 信息行:`Epoch 3/10 · Step 1480/4000 · ETA 21:10` —— 全 mono + tabular-nums。
- 进度条:高 6px,底 `hairline` 色,填充 `ink`(暗色 = 白);训练中条尾加一个蓝色小点。
- 当前 loss 大数字:24–32px mono 600,旁边配 12px mute 的 `avr_loss` 标签。

### 6.5 Loss 曲线卡(图表规范)

- 两个系列:**平滑线 2px `accent` 蓝** + **原始线 1.5px `chart-raw` 浅灰**(退后当背景)。卡片头放两枚图例胶囊(色点 + mono 文字)。
- **单 y 轴,永不双轴**;网格只留 3–4 条水平线,1px `hairline`。
- 轴标签 11–12px mono mute;**不给每个数据点标数值**。
- 悬浮 crosshair(1px 竖线)+ tooltip(`surface` 卡 + hairline + 悬浮阴影,step 与 loss 值用 mono)。
- 空态:居中 mute 文字「等待第一个 step…」。
- 文字永远用文字色,不用系列色写数值。

### 6.6 终端日志面板

- **亮色界面里也保持深底**:`#171717` 底 + `#ededed` 字(这块黑就是界面的深度装饰);暗色:`#0a0a0a` + 1px hairline 边。
- 13px mono,行高 20px;自动吸底滚动,手动上翻后出现「回到底部」浮钮。
- kohya/sd-scripts 的进度行原样展示(`steps: 37%|███▋ | 1480/4000 [12:34<21:10, 1.98it/s, avr_loss=0.0912]`)。
- `WARN` 行文字染琥珀、`ERROR` 行染红——**染文字不染背景**。
- 面板顶部小工具条:复制 / 清空 / 自动滚动开关,28px 高小按钮。

### 6.7 样图预览(采样图)

- 2 列网格,格子按训练分辨率比例(如 1:1 或 832:1216),8px 圆角 + 1px hairline。
- 左上角 mono 角标标注 `epoch 3`,点击放大查看。
- 黑白界面在此兑现价值:样图是页面上唯一的彩色,焦点天然聚过去。

### 6.8 数据表(数据集 / 预设列表)

- 表头:12px mono 大写,mute 色,`surface-2` 底。
- 行:14px,行高 44px,`hairline` 分线,hover 整行 `surface-2` 底。
- 数值列(图片数、repeat 数)右对齐 + mono。

### 6.9 Toast / 弹窗

- Toast:右下角,`surface` 卡 + hairline + 悬浮阴影,状态点 + 14px 文案:「训练完成 · character-v1.safetensors 已保存」。
- 弹窗:12px 圆角,遮罩 `rgba(0,0,0,.4)`(暗色 `.6`),标题 16/600,按钮右对齐(次按钮在左、主按钮在右)。

---

## 7. Do / Don't(训练器版)

**Do**

- 参数名、路径、数值、日志、表头——所有技术信息一律 mono。
- 用 surface 阶梯 + hairline 分层;区块间距宁大勿小。
- 用极性翻转制造深度(亮色界面里的黑终端块、黑主按钮)。
- 状态永远「颜色 + 文字/图标」双编码。
- 交互元素看起来就要能点:输入框有边、按钮有底、hover 有反馈。

**Don't**

- 别引入蓝以外的第二个彩色(**绿色成功也不要**,这套语言里成功 = 蓝)。
- 别用渐变、玻璃拟态、大圆角药丸、单层重阴影。
- 别把 Vercel 营销页的彩色 mesh 渐变搬进来——那是 hero 装饰,工具界面用不上。
- 别给中文标题上狠负字距;别用 700 字重。
- 别做双 y 轴图表;loss 图别加彩色渐变填充。
- 别让 mono 写成段正文。

---

## 8. 可直接复制的 CSS 变量

```css
:root {
  /* 画布与分层 */
  --canvas: #fafafa;
  --surface: #ffffff;
  --surface-2: #f5f5f5;
  --hairline: #ebebeb;
  --hairline-strong: #a1a1a1;
  /* 文字 */
  --ink: #171717;
  --body: #4d4d4d;
  --mute: #888888;
  /* 动作 */
  --primary: #171717;
  --on-primary: #ffffff;
  --accent: #0070f3;
  --accent-deep: #0761d1;
  --accent-soft: #d3e5ff;
  /* 语义 */
  --error: #ee0000;
  --error-soft: #f7d4d6;
  --warning: #f5a623;
  --warning-soft: #ffefcf;
  /* 终端与图表 */
  --terminal-bg: #171717;
  --terminal-ink: #ededed;
  --chart-line: var(--accent);
  --chart-raw: #c9c9c9;
  /* 字体 */
  --font-sans: Inter, -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
  /* 形状与深度 */
  --radius-ui: 6px;
  --radius-card: 8px;
  --radius-modal: 12px;
  --shadow-card: 0 0 0 1px rgba(0, 0, 0, .08);
  --shadow-float: 0 1px 1px rgba(0, 0, 0, .02), 0 2px 2px rgba(0, 0, 0, .04), 0 0 0 1px rgba(0, 0, 0, .08);
  --shadow-modal: 0 8px 16px -4px rgba(0, 0, 0, .04), 0 24px 32px -8px rgba(0, 0, 0, .06), 0 0 0 1px rgba(0, 0, 0, .08);
}

/* 暗色:两个钩子都挂上——系统偏好 + 应用内手动切换(data-theme 优先) */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --canvas: #000000;
    --surface: #0a0a0a;
    --surface-2: #141414;
    --hairline: #262626;
    --hairline-strong: #444444;
    --ink: #ededed;
    --body: #a1a1a1;
    --mute: #707070;
    --primary: #ededed;
    --on-primary: #0a0a0a;
    --accent: #3291ff;
    --error: #ff6166;
    --warning: #ffb224;
    --terminal-bg: #0a0a0a;
    --chart-raw: #3a3a3a;
    --shadow-card: 0 0 0 1px #262626;
    --shadow-float: 0 0 0 1px #262626;
    --shadow-modal: 0 0 0 1px #262626, 0 16px 32px rgba(0, 0, 0, .5);
  }
}
:root[data-theme="dark"] {
  --canvas: #000000;
  --surface: #0a0a0a;
  --surface-2: #141414;
  --hairline: #262626;
  --hairline-strong: #444444;
  --ink: #ededed;
  --body: #a1a1a1;
  --mute: #707070;
  --primary: #ededed;
  --on-primary: #0a0a0a;
  --accent: #3291ff;
  --error: #ff6166;
  --warning: #ffb224;
  --terminal-bg: #0a0a0a;
  --chart-raw: #3a3a3a;
  --shadow-card: 0 0 0 1px #262626;
  --shadow-float: 0 0 0 1px #262626;
  --shadow-modal: 0 0 0 1px #262626, 0 16px 32px rgba(0, 0, 0, .5);
}
```

组件一律通过变量取色(`background: var(--surface)`),不要在暗色媒体查询里直接写组件样式——这样切主题只动 token,组件零改动。

---

## 9. 给 AI 的风格提示词(可直接粘贴)

> 使用黑白极简开发者工具风格(Vercel 风):`#fafafa` 画布、`#ffffff` 卡片、`#171717` 墨色文字与主按钮、1px `#ebebeb` 细线分隔;全界面唯一彩色 `#0070f3` 蓝,只用于链接/训练中状态/loss 曲线主线;Inter + 中文黑体做界面字体,JetBrains Mono 标注所有参数名、路径、数值、日志;6px 圆角、多层微阴影(禁单层重阴影)、无渐变、字重上限 600;中文标题不用负字距。暗色模式:`#000` 画布、`#0a0a0a` 卡片、`#ededed` 文字、主按钮翻转为白底黑字、蓝色换 `#3291ff`。

---

## 10. 参考

- 完整原始规范:`C:\Users\21699\.claude\skills\design-master\references\vercel.md`(让 AI 搭页面时可连同本文档一起投喂)
- 图表方法论:dataviz 技能(loss 曲线遵循:单轴、固定系列色、悬浮 tooltip、图例 + 克制的直接标注)
- 备选风格:黑底方案看 `references/x.ai.md`,最纯黑白看 `references/uber.md`
