# Design System

## Intent

Midnight kitchen ticket：家人在白天或通勤途中打开手机，像在低光餐厅里快速写下一张今晚菜单。界面冷静、直接，红色只在关键动作和同步反馈中出现。

## Color

Committed dark strategy，全部使用 OKLCH。

- Background: `oklch(0.075 0 0)`
- Surface: `oklch(0.12 0 0)`
- Ink: `oklch(0.96 0 0)`
- Muted: `oklch(0.70 0 0)`
- Primary: `oklch(0.58 0.20 355)`
- Accent: `oklch(0.86 0.15 110)`

## Typography

中文使用系统黑体栈。标题采用紧凑粗体，正文采用正常字重；菜单编号使用等宽数字。大标题最大 88px，字距不低于 `-0.04em`。

## Layout

手机单列，桌面为标题与菜单错位双栏。菜单本身保持连续列表，不使用商品卡片网格。360px 宽度无横向滚动。

## Components

- Ticket header：日期、家庭码入口、实时状态。
- Dish line：顺序号、菜名、点菜人、编辑和删除动作。
- Composer：页面底部主要输入，提交后保留操作焦点。
- Toast/status：短暂反馈，不遮挡核心操作。

## Motion

新增使用短距离上移与淡入，删除先划线再收起，实时远端更新使用一次红色脉冲。使用 expo/quint ease-out，不使用弹跳；减少动态效果时仅保留瞬时状态变化。

