# AnglrLog - 钓鱼记录数据工具

AnglrLog 是一个专注于钓鱼记录的数据工具，帮助钓鱼人记录每一次出钓，并积累属于自己的钓鱼数据库。

**官网**: https://anglrlog.com

## 项目结构

```
app/
├── api/              # API 路由
├── core/             # 核心配置和工具
├── models/           # 数据库模型
├── repositories/     # 数据层
├── schemas/          # Pydantic 模型
├── services/         # 业务逻辑
├── templates/        # HTML 模板
├── static/           # 静态资源
└── main.py          # 应用入口
scripts/
├── init_data.py     # 初始化数据
```

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- 或 Python 3.12 + PostgreSQL

### 使用 Docker 启动

```bash
docker-compose up
```

系统会自动：
1. 启动 PostgreSQL 数据库
2. 运行 FastAPI 应用
3. 创建数据库表

### API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 认证

- `POST /api/auth/register` - 注册账户
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 获取当前用户信息

### 钓点

- `GET /api/spots` - 获取所有钓点
- `GET /api/spots/{id}` - 获取钓点详情
- `GET /api/spots/{id}/weather` - 获取钓点实时天气

### 出钓记录

- `GET /api/logs` - 获取我的记录
- `POST /api/logs` - 新建记录
- `GET /api/logs/{id}` - 获取记录详情
- `PUT /api/logs/{id}` - 更新记录
- `DELETE /api/logs/{id}` - 删除记录

## 技术栈

**后端：**
- FastAPI 0.104
- SQLAlchemy 2.0 Async
- PostgreSQL 16
- Pydantic V2

**部署：**
- Docker & Docker Compose
- Nginx (待实现)

## V1.0 验收标准

- [x] 项目初始化和数据库设计
- [ ] 前端页面开发（Jinja2 + HTMX）
- [ ] 完整的 CRUD 功能
- [ ] 天气数据集成
- [ ] 认证和权限管理
- [ ] Docker 一键启动
- [ ] 移动端适配
- [ ] Chrome 兼容性测试
