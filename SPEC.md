# SPEC

## §G

家庭成员跨设备实时增删改今晚菜单；单页快开快用。

## §C

- 前后端分离。
- 前端 Vue 3 + TypeScript + Vite，手机优先。
- 后端 Python + FastAPI + SQLite。
- 不做账号、投票、采购、支付、菜品分类。
- 首次输入昵称；家庭通过共享家庭码进入。
- 墨黑舞台、红色焦点、数字点菜单视觉。
- WCAG AA；键盘可用；支持减少动态效果。

## §I

- I1 `GET /api/menus/{family_code}/today`：读取今日菜单。
- I2 `POST /api/menus/{family_code}/dishes`：新增菜品。
- I3 `PATCH /api/menus/{family_code}/dishes/{dish_id}`：修改菜名。
- I4 `DELETE /api/menus/{family_code}/dishes/{dish_id}`：删除菜品。
- I5 `WS /api/menus/{family_code}/live`：广播菜单变更。
- I6 `VITE_API_BASE_URL`：前端 API 地址。
- I7 `docker compose up -d --build`：一键启动 Web 与 API。
- I8 `PUBLIC_ORIGIN`：部署站点公开来源，用于 CORS 白名单。

## §V

- V1 相同家庭码、相同日期的所有设备看到同一菜单。
- V2 菜名去除首尾空白后必须为 1–40 个字符。
- V3 新增、修改、删除成功后所有在线设备收到同步事件。
- V4 页面加载失败、保存失败、断线时给出可恢复提示，不丢失输入。
- V5 核心增删改可用触屏与键盘完成；减少动态效果时禁用位移类动画。
- V6 手机 360px 宽度无横向溢出；桌面端保持单一视觉焦点。
- V7 SQLite 文件与运行时配置不提交仓库。
- V8 后端限制跨域来源，并对家庭码与请求体做校验。
- V9 容器部署仅公开 Web 端口；SQLite 数据通过命名卷持久化。
- V10 同域反代必须支持普通 HTTP API 与 WebSocket 升级。

## §T

id|status|task|cites
T1|x|建立项目骨架、配置与文档|V7,I6
T2|x|实现 FastAPI 菜单 CRUD、SQLite 与校验|V1,V2,V8,I1,I2,I3,I4
T3|x|实现 WebSocket 实时广播|V3,V4,I5
T4|x|实现响应式单页点菜单与交互状态|V2,V4,V5,V6,I1,I2,I3,I4,I6
T5|x|联调、自动化测试与生产构建|V1,V2,V3,V4,V5,V6,V7,V8
T6|x|实现 Docker Compose 一键部署与持久化|V7,V8,V9,V10,I5,I6,I7,I8
T7|~|验证容器健康、API 与 WebSocket 反代|V1,V3,V9,V10,I1,I5,I7

## §B

id|date|cause|fix
