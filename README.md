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

首次进入时填写家庭码和昵称。家人在不同设备上填写相同家庭码，即可共享并实时同步同一份今晚菜单。

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
docker compose up -d --build
```

浏览器访问 `http://localhost`。停止服务：

```powershell
docker compose down
```

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
