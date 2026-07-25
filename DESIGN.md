# Design System

## Intent

Midnight kitchen ticket：家人在白天或通勤途中打开手机，像在低光餐厅里快速写下一张今晚菜单。界面冷静、直接，红色只在关键动作和同步反馈中出现。

## Color

Committed dark strategy，全部使用 OKLCH。

- Background: `oklch(0.105 0.018 350)`
- Surface: `oklch(0.155 0.024 350)`
- Ink: `oklch(0.96 0 0)`
- Muted: `oklch(0.70 0 0)`
- Primary: `oklch(0.58 0.20 355)`
- Accent: `oklch(0.86 0.15 110)`

全局画布使用低光漆面餐桌摄影纹理：左侧暖琥珀光、右侧暗色餐巾，中间保持低对比留白；叠加深色遮罩后贯穿首页、菜单和后厨。页面容器保持透明，实体卡片继续使用 Surface 承载内容。

## Typography

中文统一使用随应用打包的 Zen Maru Gothic 圆体，并以幼圆和系统黑体作为回退。标题采用饱满、舒展的圆润字形，正文保持清晰紧凑；菜单编号继续使用等宽数字。角色感来自圆角笔画，不使用夸张泡泡字或描边。

## Layout

手机单列，桌面为标题与菜单错位双栏。菜单本身保持连续列表，不使用商品卡片网格。360px 宽度无横向滚动。

## Components

- Ticket header：日期、应用入口、实时状态。
- Dish line：顺序号、菜名、点菜人、编辑和删除动作。
- Composer：页面底部主要输入，提交后保留操作焦点。
- Toast/status：短暂反馈，不遮挡核心操作。

## Motion

新增使用短距离上移与淡入，删除先划线再收起，实时远端更新使用一次红色脉冲。使用 expo/quint ease-out，不使用弹跳；减少动态效果时仅保留瞬时状态变化。
