# 今晚吃什么

家庭内部使用的实时共享晚餐菜单。家庭成员可以从不同设备添加、修改或删除今晚想吃的菜。

## 技术栈

- 前端：Vue 3、TypeScript、Vite
- 后端：FastAPI、SQLAlchemy、SQLite、WebSocket

## 本地开发

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

默认前端地址为 `http://localhost:5173`，后端地址为 `http://localhost:8000`。

打开就是“小袁的专属食堂”，用两列卡片集中查看已点菜品、修改特殊要求或取消菜品。点击底部按钮进入菜单，可按分类筛选或搜索菜名；点击图片会立即加入或取消，返回后所有设备实时同步。

菜品维护入口默认隐藏：在 1.8 秒内连续点击左上角图标 5 次，即可进入后厨工作台，维护分类，并上传图片、增删改菜品及调整所属分类。支持不超过 20MB 的 JPG、PNG、WebP、HEIC、HEIF 图片，手机原片会自动校正方向并转为 WebP。初始分类为荤菜、素菜、汤品。这个入口只用于隐藏界面，不是安全鉴权。

部署时复制两端的 `.env.example` 并按域名修改：后端 `ALLOWED_ORIGINS` 只填写实际前端来源，前端 `VITE_API_BASE_URL` 指向公网 API 地址。

## 验证

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run test
npm run check
npm run build
```

## Docker 一键部署

确保 Docker Desktop 或 Docker Engine 已启动，然后在项目根目录执行：

```powershell
cd E:\yehan\FoodOrder
Copy-Item .env.example .env
docker compose build --no-cache web api
docker compose up -d --force-recreate
```

浏览器访问 `http://localhost`。停止服务：

```powershell
docker compose down
```

更新发布时也使用上面的 `build --no-cache` 和 `up --force-recreate`，确保服务器不会继续运行旧前端镜像。发布后可用无痕窗口打开，或强制刷新一次页面。

菜单数据保存在 Docker 命名卷 `foodorder_dinner_data` 中，执行 `docker compose down` 或重新构建镜像不会删除数据。

如需改端口或绑定正式域名，编辑根目录 `.env`：

```dotenv
WEB_PORT=8080
PUBLIC_ORIGIN=https://dinner.example.com
```

修改端口后访问 `http://localhost:8080`。使用正式域名时应在服务器或上层反向代理配置 HTTPS，并将 `PUBLIC_ORIGIN` 写成浏览器实际访问的完整来源。

查看状态和日志：

```powershell
docker compose ps
docker compose logs -f
```
