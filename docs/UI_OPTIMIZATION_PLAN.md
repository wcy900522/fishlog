# AnglrLog 前端 UI 排版与视觉优化方案

日期：2026-09-10　基线：`dd5490f`

> 注意：`docs/REMEDIATION_STATUS.md` 指出 `/work/fishlog` 正被线上 API 热加载挂载，业务代码修改应在分支或隔离副本进行。本方案只做分析与规划，未改动任何模板。

---

## 一、现状诊断（有据可查的问题）

### 1. 两套配色并存，品牌不聚焦
- `base.html:14-67` 的 token 定义的是 **森林绿 + 湖水青 + 暖米白**（`--brand-deep #0A3C35`、`--brand-teal #1F9E8D`、`--brand-mint #4ECDC4`）。
- 但导航栏（`base.html:115`）、页脚（`:410`）、`.card-header`（`:236`）、`.brand-panel`（`:787`）、首页 hero/mission-band/spot-card（`index.html:62、578、924`）仍用上一版的 **蓝青色系** `rgba(7,52,66)`、`rgba(7,88,106)`、`#07586a`、`#0e8fa3`、`#18a9c0`。
- 全站模板共出现 **74 个不同的十六进制色值**，旧蓝青色在 7 个文件中被引用 25 次。结果是导航栏偏蓝、正文偏绿、按钮偏青，三种"主色"同屏。

### 2. 按钮层级混乱
- `.btn-primary`（`base.html:256`）是浅青→浅绿渐变 + 深色文字，视觉分量像一个 chip，而不是主操作。
- `.btn-success`（`:269`）是绿→柠檬黄渐变，与品牌无关；spots 页把"新增钓点"（primary）和"新增出钓记录"（success）并排，两个 CTA 抢焦点。
- 首页又有第三套 `.btn-hero-primary`（琥珀→薄荷渐变）。同一站点存在三种"主按钮"。

### 3. 字体与排版没有标度
- 全站 `font-size` 出现 **58 个不同值**；`font-weight` 分布为 800×30、900×16、700×23、600×12——几乎所有文字都是加粗，没有层级。
- 首页 h1 `clamp(3.6rem, 7vw, 7rem)` 显示英文 "AnglrLog"，中文品牌名"渔迹录"反而是小字。
- Fraunces 衬线只在 index 用了 4 次，却全站加载；Noto Sans SC 加载 4 个字重。字体来自 `fonts.googleapis.com`，**站点有 ICP 备案面向国内用户，Google Fonts 在国内经常不可达**，会导致 FOIT 或整段字体回退。

### 4. CSS 架构：全部内联在模板里
- `base.html` 1080 行 + `index.html` 1143 行 + 其余页面约 1900 行，**约 4100 行 CSS 内联在 HTML 中**，没有一个静态 CSS 文件，浏览器无法缓存。
- 组件在多处重复定义：`.spot-card`/`.post-card` 在 index 与 spots/forum 各写一份；`.text-link`、`.empty-state` 在 index 里被重新定义；`about.html` 自带 408 行样式。

### 5. 页面骨架不统一
| 页面 | 标题写法 | 操作按钮位置 |
|---|---|---|
| spots | `<div class="page-title">`（非 h1）+ 自带 `.container mt-5` | 副标题下方一行 `btn-lg` |
| logs | `<h1 class="page-title mb-0">` | 标题同一行右侧 |
| forum | `h1.page-title` | 标签栏、搜索框之后，默认隐藏 |
| create_log / edit_log | **没有页面标题**，只有 card-header h4 | 表单底部 |
| spot_detail | `h1.fs-2.text-white` 自写 | — |
| about | 自带 hero | — |

内页容器宽度 1280，首页区块与导航栏是 1480，两者切换时左右留白跳动。

### 6. 背景与"玻璃"效果过载
- `body` 叠了固定 SVG 湖景 + 三段渐变 + 网格线（`base.html:77-105`）；每张 `.card`、`.data-card`、`.feature-card` 都开 `backdrop-filter: blur(10px)`。视觉上噪点多，性能上每张卡片都是一个合成层。
- 首页 hero 同时有 mesh blob（`blur(60px)` 无限动画）、粒子、水纹三层装饰动画。
- 首页三种区块底色（`#e2efed→#d7e8e5`、`#eef6f4`、深色 mission band）加上 body 渐变，形成明显色带。

### 7. 交互反馈原始
- `alert()` 使用 **54 次**、`confirm()` 9 次，没有 toast、没有确认弹窗组件。
- 表单没有 invalid 状态样式、没有 helper text 规范；加载态只有 spinner，没有骨架屏。
- 所有 `.card:hover` 都会上浮 3px，包括纯展示、不可点击的卡片，误导可点性。
- forum 的 11 个标签筛选用 `btn-primary/outline-primary` 按钮，而 base 里已经有 `.chip` 组件没被使用。

### 8. 其它
- `text-danger`×14、`text-primary`×3、`btn-warning`×2、`bg-info/bg-warning/bg-secondary` 等 Bootstrap 原生色绕过了主题。
- `.reveal` 滚动动画只在 index 使用，其它页面没有入场节奏；`.reveal` 里用了 `filter: blur(6px)` 过渡，成本高。
- 移动端已有较多规则，但登录后导航折叠成 7 项竖排菜单 + 账户下拉，核心动作"记一笔"埋在下拉菜单里。

---

## 二、优化目标与设计原则

1. **一个品牌色系**：森林绿为主、湖水青为强调、琥珀为点缀，删除所有蓝青旧色。
2. **克制的表面**：平面卡片 + 细边框 + 一级阴影；玻璃、模糊、网格线只留在 hero。
3. **清晰的层级**：一套 8 级字号标度、4 个字重（400/500/600/700），标题 700，正文 400，只有数字/强调用 600。
4. **一致的骨架**：所有内页共用"页头 + 工具栏 + 内容区"三段式，容器统一 1200px。
5. **可缓存、可维护**：CSS 抽到静态文件，按 tokens / base / components / pages 分层。
6. **面向国内用户**：字体与第三方库自托管，动画在移动端降级。

---

## 三、设计系统（Token 层）

### 3.1 色彩（替换 `base.html :root`）

```css
:root {
  /* 品牌 */
  --c-primary:        #0F4C45;   /* 森林绿，主按钮/导航/标题 */
  --c-primary-hover:  #0A3C35;
  --c-primary-soft:   #E3F1ED;   /* 主色浅底：选中 chip、信息条 */
  --c-accent:         #1F9E8D;   /* 湖水青，链接/图标/强调 */
  --c-accent-soft:    #D7F0EC;
  --c-amber:          #D9953F;   /* 琥珀，仅用于奖章/提示/hero 点缀 */
  --c-amber-soft:     #FBEFD9;
  --c-danger:         #C94F3D;
  --c-danger-soft:    #FBE9E5;

  /* 表面（三级，不再用 rgba 玻璃） */
  --s-page:    #F6F4EE;   /* 页面底 */
  --s-card:    #FFFFFF;   /* 卡片 */
  --s-muted:   #EEEBE3;   /* 次级底：筛选栏、表头、代码块 */
  --s-inverse: #0A3C35;   /* 深色区块：导航、页脚、hero */

  /* 文字 */
  --t-1: #14231F;   /* 标题、正文 */
  --t-2: #4A5A54;   /* 次要文字 */
  --t-3: #7A8983;   /* 占位、时间戳 */
  --t-inverse: #F2F7F4;

  /* 边框 / 阴影 */
  --b-1: #E2DED3;
  --b-2: #CFCABD;
  --sh-1: 0 1px 2px rgba(20,35,31,.06);
  --sh-2: 0 4px 12px rgba(20,35,31,.08);
  --sh-3: 0 12px 32px rgba(20,35,31,.14);

  /* 圆角 / 间距 / 层级 */
  --r-sm: 8px; --r-md: 12px; --r-lg: 16px; --r-pill: 999px;
  --sp-1: 4px; --sp-2: 8px; --sp-3: 12px; --sp-4: 16px; --sp-5: 24px; --sp-6: 32px; --sp-7: 48px; --sp-8: 64px;
  --z-nav: 100; --z-dropdown: 200; --z-modal: 1050; --z-toast: 1100;
}
```

对比度校验：`--t-2` 在 `--s-card` 上 ≈ 7.4:1，`--t-3` ≈ 4.6:1（仅用于 ≥14px 辅助文字），`--c-primary` 上白字 ≈ 9.8:1，`--c-accent` 上白字 ≈ 3.6:1（**因此 accent 只用于文字/图标，不用于白字按钮底**）。

### 3.2 字体

- 中文：`"Noto Sans SC"` 自托管（`app/static/fonts/`，woff2 子集，仅 400/500/700），`font-display: swap`，回退 `"PingFang SC","Microsoft YaHei"`。
- 数字/英文品牌名：保留 Fraunces 仅用于 `.font-display`（hero h1、排行榜名次、等级数字），仅加载 600 一档；其它地方去掉。
- 停用 Google Fonts 与 cdnjs 字体请求，`fonts.googleapis.com` preconnect 删除。

### 3.3 字号标度（8 级，rem）

| Token | 尺寸 | 用途 |
|---|---|---|
| `--fs-xs` | 0.75 | 徽章、表头、时间戳 |
| `--fs-sm` | 0.875 | 辅助说明、meta |
| `--fs-md` | 1 | 正文、表单 |
| `--fs-lg` | 1.125 | 卡片标题 |
| `--fs-xl` | 1.375 | 区块标题 h3 |
| `--fs-2xl` | 1.75 | 页面标题 h1（内页） |
| `--fs-3xl` | 2.5 | 首页区块标题 |
| `--fs-4xl` | clamp(2.75rem, 5vw, 4.25rem) | hero h1 |

行高：标题 1.2，正文 1.7，中文段落 `letter-spacing: 0.01em`。

### 3.4 图标

沿用 Font Awesome 6，但**统一图标出现位置**：页面标题前一个图标、按钮内一个图标、卡片 meta 项前一个图标；不再在标题、副标题、徽章里叠加多个图标。

---

## 四、全局骨架

### 4.1 CSS 文件拆分

```
app/static/css/
├── tokens.css        # 上面的 :root
├── base.css          # reset、body、排版、链接、focus
├── components.css    # 按钮、卡片、chip、badge、表单、表格、状态、toast、modal
├── layout.css        # navbar、page-head、toolbar、footer、grid、container
└── pages/
    ├── home.css
    ├── spots.css
    ├── logs.css
    ├── forum.css
    ├── detail.css    # spot_detail + post_detail 共用
    ├── profile.css   # profile + level 共用
    └── about.css
```
`base.html` 只保留 `<link>`；页面模板的 `extra_css` 只引一份对应的 pages/*.css。目标：模板中的 `<style>` 从 ~4100 行归零，`style=""` 属性归零。

### 4.2 导航栏
- 底色改为纯色 `--s-inverse`（去掉渐变和 backdrop-filter），高度 64px，底部 1px `rgba(255,255,255,.08)`。
- 菜单按任务分组并加当前页高亮（`aria-current="page"` + 底部 2px accent 线）：
  `首页 · 钓点 · 记录 · 讨论 · 排行榜`，其余（装备/鱼种/饵料/等级/关于/管理）进"账户"下拉。
- 登录用户右侧增加一个实心主按钮 **"+ 记一笔"**（`/logs/create`），全站可达。
- 移动端（<992px）：折叠菜单改为白底面板；登录用户增加**底部 Tab 栏**（首页 / 钓点 / ＋记录 / 讨论 / 我的），用 `env(safe-area-inset-bottom)` 留边。

### 4.3 页头组件（所有内页统一）

```html
<header class="page-head">
  <div class="page-head__text">
    <p class="page-head__eyebrow">我的数据</p>          <!-- 可选 -->
    <h1 class="page-head__title"><i class="fas fa-list"></i> 出钓记录</h1>
    <p class="page-head__sub">共 128 条 · 最近一次 9 月 6 日</p>
  </div>
  <div class="page-head__actions">
    <a class="btn btn-secondary">导出</a>
    <a class="btn btn-primary">+ 记一笔</a>
  </div>
</header>
```
- 桌面：左右两栏，标题 `--fs-2xl / 700`，副标题 `--t-2`；移动端纵向堆叠，按钮撑满。
- 做成 Jinja macro（`templates/_macros/page_head.html`），spots/logs/forum/leaderboards/equipment/species/baits/profile/level/admin/create_log/edit_log/create_post 全部改用。

### 4.4 容器与页面底
- 统一 `.container-app { max-width: 1200px; padding-inline: clamp(16px, 3vw, 32px) }`，首页区块也用它（1480 太宽，卡片被拉扁）。
- `body` 背景改为纯色 `--s-page`，删除固定 SVG 湖景与网格线；湖景 SVG 只在首页 hero 与 about hero 使用。
- 内页首个区块上边距统一 `--sp-6`，区块之间 `--sp-6`，页脚上方 `--sp-8`。

### 4.5 页脚
两栏：左侧品牌 + 一句话；右侧链接（关于 / 讨论 / 安全合规）。ICP 备案信息单独一行、`--fs-xs`、`--t-3` 反白。

---

## 五、组件层

### 5.1 按钮（只保留 4 种语义 + 3 个尺寸）
| 类 | 外观 | 用途 |
|---|---|---|
| `.btn-primary` | 实心 `--c-primary`，白字，`--sh-1` | 每屏最多一个主操作 |
| `.btn-secondary` | 白底 + `--b-2` 边框，`--t-1` | 次操作 |
| `.btn-ghost` | 透明，`--c-accent` 文字 | 行内/卡片内轻操作 |
| `.btn-danger` | 白底 + danger 边框，hover 实心 | 删除类 |

- 删除 `.btn-success`、`.btn-hero-primary/ghost`、`.spot-card__action`，全部映射到上表；深色区块（hero/mission）上的主按钮用 `.btn-primary.btn-on-dark`（白底深绿字）。
- 尺寸：sm 32px / md 40px / lg 48px；圆角 `--r-md`；去掉 hover 上浮 `translateY`，改为背景加深 + 阴影升一级。
- 图标与文字间距固定 `--sp-2`。

### 5.2 卡片（一个基类 + 修饰符）
```
.card                 白底、1px --b-1、--r-lg、--sh-1、padding --sp-5
.card--interactive    整卡可点时才加：hover 边框变 --c-accent、--sh-2；不再位移
.card--inverse        深色卡（hero 天气卡、mission stat）
.card__head / __body / __foot
```
- 删除 `.card-header` 的蓝色渐变头，改为白底 + 底边线；标题 `--fs-lg / 700`。
- `.data-card`、`.shell-card`、`.feature-card`、`.spot-card`、`.post-card` 收敛为 `.card` 的修饰符：`.card--spot`（顶部地图缩略）、`.card--post`（标签 + 摘要 + meta）、`.card--feature`（顶部 4px 色条保留，仅首页/about）。
- 去掉所有 `backdrop-filter`。

### 5.3 Chip / Badge
- `.chip`（已存在）成为唯一的筛选/多选组件：forum 标签栏、鱼种选择、logs 筛选全部改用；选中态 `--c-primary-soft` 底 + `--c-primary` 字 + 1px primary 边。
- `.badge` 语义化：`--info`（accent-soft）、`--warn`（amber-soft）、`--danger`、`--muted`；删除对 Bootstrap `bg-*` 的直接使用。

### 5.4 表单
- 标签 `--fs-sm / 600 / --t-1`，必填用 `.req::after { content:"*" }` 而不是 `text-danger` span。
- 输入框高度 44px，边框 `--b-2`，focus 2px accent 外环；`.is-invalid` + `.form-msg` 红字提示；`.form-hint` 灰字说明。
- **分组**：长表单用 `<fieldset class="form-section">` + `<legend>`，如出钓记录分为「基本信息 / 环境水情 / 渔获 / 装备 / 备注」。
- 桌面端布局：表单 8 列 + 右侧 4 列 sticky 说明卡（钓点信息预览、天气自动填充状态、必填提示）；移动端说明卡移到表单上方折叠。
- 提交栏：桌面在表单末尾右对齐；移动端 `position: sticky; bottom: 0` 白底栏，主按钮撑满。

### 5.5 表格 / 列表
- `.table-app`：表头 `--s-muted` 底 + `--fs-xs` 大写间距，行高 48px，斑马纹去掉、改 hover 底色，首列固定。
- 移动端 <768px：`admin_users`、`leaderboards` 改为卡片列表（用 `data-label` 方式渲染 `<td>`），不再横向滚动 680px。

### 5.6 状态组件
- `.state`（empty / error / loading）统一：图标 40px `--t-3`、标题 `--fs-lg`、一句说明、一个 `.btn-secondary`。
- **骨架屏**：`.skeleton` 工具类（灰底 + shimmer），spot-card、post-card、log row 各给一个骨架模板，替换 spinner。
- **Toast**：`window.AnglrToast.success/error/info(msg)`，右上角（移动端底部居中），3s 自动消失，替换全部 `alert()`。
- **确认弹窗**：`AnglrConfirm({title, body, danger:true})` 基于 Bootstrap modal，替换全部 `confirm()`。

---

## 六、页面级排版

### 6.1 首页（index.html）
1. **公告条**：跑马灯改为静态单行提示（图标 + 一句话 + "查看全文"），高 40px，amber-soft 底，可关闭并记 localStorage。跑马灯在移动端不可读且分散注意。
2. **Hero**：
   - 单层背景：湖景 SVG + 一层深绿渐变遮罩，删除 mesh/粒子/水纹三套动画，只保留一个缓慢的 `background-position` 漂移（或不动）。
   - 左栏：eyebrow "钓鱼人的个人数据中心" → h1 **「渔迹录」**（中文为主，`--fs-4xl`），"AnglrLog" 作为 Fraunces 小字副标 → 一句 lead（限 2 行）→ 两个按钮（`.btn-primary.btn-on-dark` "开始记录" + `.btn-ghost` "浏览钓点"）。
   - 右栏：只放**天气卡**一个组件（`.card--inverse`），三条"位置/时间/复盘"文案移到下方三栏 feature 带。
   - 高度 `min-height: 560px`，`align-items: center`。
3. **价值带**：紧跟 hero 的三栏 `.card--feature`（位置维度 / 出钓维度 / 复盘维度），替代原 hero 右栏和 mission-band 的重复内容。
4. **区块**：「全国钓点」「热门讨论」共用 `section-bar`（标题 `--fs-3xl` + 右侧操作），区块底色只用 `--s-page` / `--s-card` 交替，去掉两种自定义绿灰渐变。附近钓点面板改为地图 7 列 + 列表 5 列。
5. **卡片网格**：`row-cols-1 row-cols-md-2 row-cols-xl-3`，spot/post 卡片与 spots/forum 页共用同一组件。
6. **Mission band**：保留但简化为深绿单色块 + 标题 + 一句话 + 一个主按钮；删掉右侧三张 stat 卡（已上移到价值带）。
7. 登录后的「我的出钓数据」区块放在 hero 之下第一屏，4 个 `.stat-tile`（本月出钓、总渔获、常去钓点、等级）。

### 6.2 列表页（spots / logs / forum / leaderboards / equipment / species / baits）
统一三段式：**page-head → toolbar → 内容**。
- **toolbar**：白底 `.card`，左侧搜索框（带放大镜、清除键），中间 chip 筛选行，右侧排序下拉；结果数 "共 N 条" 显示在 toolbar 下方 `--fs-sm --t-2`。
- **spots**：桌面端地图 5 列 sticky（`top: 80px`）+ 钓点卡片 7 列可滚动，地图与列表联动高亮；移动端地图折叠为"展开地图"按钮。两个 CTA 合并：主按钮"新增钓点"，"记一笔"走导航栏。
- **logs**：由大卡片改为紧凑行（时间 | 钓点 | 鱼种/数量/重量 | 天气 | 操作），桌面用 `.table-app`，移动端用 `.log-row` 卡片；顶部加月份分组标题。
- **forum**：标签栏改 `.chip` 横向可滚动；帖子列表改为左侧内容（标题 `--fs-lg`、摘要 2 行截断、标签）+ 右侧 meta 列（作者、时间、评论数）的行式布局；"发布新帖"进 page-head actions。
- **leaderboards**：三个榜单用 tab 切换而非并排；前三名用 `--medal-*` 色的序号徽章，其余用数字；名次列用 Fraunces。
- **equipment / species / baits**：同一模板结构（`_macros/catalog_page.html`），卡片网格 + 右上角"新增"。

### 6.3 表单页（create_log / edit_log / create_post / spots 模态）
- 使用 page-head（标题"记录一次出钓"，副标题一句说明），删除 card-header 内的标题。
- 分组 fieldset + 8/4 两栏（见 5.4）；出钓记录的鱼种 chip 选择器放在输入框下方并限高可滚动。
- create_post：标题输入放大（`--fs-xl`），正文 textarea 最小 320px，图片上传区改为虚线拖放区 + 缩略图预览。
- 钓点模态：改为右侧抽屉（`offcanvas-end`，宽 520px），地图选点在抽屉内 300px 高，移动端全屏。

### 6.4 详情页（spot_detail / post_detail）
- 顶部：面包屑（`--fs-sm`）→ 标题 `--fs-2xl` → meta 行（chip 化的水体类型、城市、作者、时间）→ 操作按钮。
- 主体 8/4：左侧内容（地图 360px / 正文），右侧 sticky 侧栏（天气 stat-tile 组、相关记录、作者卡）。
- spot_detail 去掉白字覆盖在渐变上的标题写法，改用与其它页一致的浅色页头。
- post_detail 评论区：头像 36px + 姓名/时间一行 + 内容，回复缩进 44px；输入框固定在评论列表底部。

### 6.5 个人中心 / 等级（profile / level）
- 合并 `profile-hero` 与 `level-hero` 为同一个 `.identity-card`：头像 72px、昵称、等级徽章、经验进度条（`--c-accent` 单色，去掉三色渐变）、4 个 stat-tile。
- 下方两栏：左"常用作钓模式"/"勋章墙"（勋章统一 64px 圆形，未获得用灰阶），右"最近记录"列表。

### 6.6 认证页（login / register）
- 桌面端左右分栏：左 5 列深绿品牌面板（湖景 SVG + 一句话），右 7 列表单；移动端只显示表单。
- 表单卡片去掉大图标头部，改为小 logo + 标题 + 副标题；输入框 48px；主按钮撑满；注册页密码强度条。

---

## 七、动效与性能

- **入场**：`.reveal` 保留但去掉 `filter: blur`，只做 `opacity + translateY(16px)`，时长 0.5s；在所有页面的 page-head、toolbar、首屏卡片上应用，卡片用 `--i` 自定义属性做 60ms 级联。
- **hover**：卡片只变边框与阴影；按钮只变底色；禁用一切 `translateY` 位移（避免布局抖动与移动端"卡住"）。
- **hero**：最多一个环境动画；`prefers-reduced-motion` 时全部关闭。
- **加载**：Leaflet CSS/JS 只在有地图的页面引入（spots、spot_detail、index、create/edit_log），其它页面不加载；Bootstrap/HTMX/Leaflet/Font Awesome 自托管到 `app/static/vendor/`，避免 jsdelivr/cdnjs 在国内的不稳定。
- **图片**：上传头像与帖子图片输出 `loading="lazy"` + 固定宽高比容器（`aspect-ratio: 4/3`），避免 CLS。
- **CSS 体积目标**：tokens+base+layout+components ≈ 25KB 未压缩，页面 CSS 各 ≤ 6KB。

---

## 八、移动端专项

- 底部 Tab 栏（登录态）+ 顶部精简导航（logo + 账户头像）。
- 所有 toolbar 在 <768px 变为：搜索框一行、chip 行横向滚动、排序收进"筛选"按钮打开的 offcanvas。
- 表单 sticky 提交栏；输入框 `font-size: 16px` 防 iOS 缩放（已有，保留）。
- 卡片网格单列，卡片 padding `--sp-4`；地图高度 260px（已有，保留）。
- 表格转卡片（见 5.5）。
- 触摸目标最小 44×44px；chip 高度 36px 但外扩 4px 点击区。

---

## 九、实施路线

| 阶段 | 内容 | 涉及文件 | 预估 |
|---|---|---|---|
| **P0 基础** | 抽出 CSS 到 `app/static/css/`；自托管字体与 vendor 库；建立 tokens.css | base.html、所有模板的 `extra_css`、新增 static/css、static/fonts、static/vendor | 1 天 |
| **P1 Token 收敛** | 用新 token 替换 74 个硬编码色；删除蓝青旧色；按钮/卡片/表单/badge 重写 | components.css、layout.css；全模板 grep 替换 | 1.5 天 |
| **P2 骨架** | navbar 重做 + 底部 Tab；page-head macro 并应用到 14 个页面；容器统一；页脚 | base.html、`_macros/page_head.html`、各页面顶部 | 1 天 |
| **P3 反馈组件** | Toast、Confirm、骨架屏、表单校验态；替换 54 处 alert 与 9 处 confirm | base.html JS、各页面 JS | 1 天 |
| **P4 首页** | Hero 简化、价值带、区块重排、卡片共用 | index.html、pages/home.css | 1 天 |
| **P5 列表页** | toolbar 组件；spots 地图侧栏布局；logs 行式；forum 行式；leaderboards tab；catalog macro | spots/logs/forum/leaderboards/equipment/species/baits | 2 天 |
| **P6 表单与详情** | fieldset 分组 + 8/4 布局 + sticky 提交；钓点抽屉；详情页 8/4 | create_log/edit_log/create_post/spots 模态/spot_detail/post_detail | 1.5 天 |
| **P7 个人/认证/关于** | identity-card；auth 分栏；about 复用组件去掉 408 行私有 CSS | profile/level/login/register/about | 1 天 |
| **P8 收尾** | 动效降级、Leaflet 按需加载、a11y 检查（对比度、焦点、aria-current、h1 唯一）、真机回归 | 全站 | 1 天 |

建议顺序严格按 P0→P1→P2 先做，这三步完成后每个后续页面改造都只是"换骨架 + 删私有 CSS"，可以并行。

---

## 十、验收清单

- [ ] 模板内 `<style>` 与 `style=""` 归零；`grep -c '#[0-9a-f]\{6\}' templates/*.html` 为 0
- [ ] 全站只有 `.btn-primary / secondary / ghost / danger` 四种按钮
- [ ] 每个内页有且仅有一个 `h1.page-head__title`
- [ ] 不再出现 `alert(` / `confirm(`
- [ ] Lighthouse 移动端 Performance ≥ 85、Accessibility ≥ 95
- [ ] 断网 Google Fonts / jsdelivr 情况下页面正常渲染
- [ ] iPhone SE（375px）与 iPad（768px）无横向滚动
- [ ] `prefers-reduced-motion` 下无任何持续动画
