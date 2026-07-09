# FishLog / AnglrLog - 钓鱼记录数据工具

FishLog 是一个面向钓鱼爱好者的数字化钓鱼记录平台。核心目标是记录每一次出钓，把钓点、天气、装备、饵料、鱼获、经验分享和用户成长沉淀成个人钓鱼数据库。

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
docker compose up
```

系统会自动：
1. 启动 PostgreSQL 数据库
2. 执行 `alembic upgrade head`
3. 运行 FastAPI 应用

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
- `GET /api/spots/mine` - 获取我的钓点
- `POST /api/spots` - 新建钓点
- `GET /api/spots/{id}` - 获取钓点详情
- `PUT /api/spots/{id}` - 更新钓点
- `DELETE /api/spots/{id}` - 删除钓点
- `GET /api/spots/{id}/weather` - 获取钓点实时天气
- `GET /api/spots/{id}/catch-logs` - 获取钓点社区记录

### 出钓记录

- `GET /api/logs` - 获取我的记录
- `GET /api/logs/public` - 获取公开记录
- `POST /api/logs` - 新建记录
- `GET /api/logs/{id}` - 获取记录详情
- `PUT /api/logs/{id}` - 更新记录
- `DELETE /api/logs/{id}` - 删除记录
- `GET /api/records` - V1.2 兼容命名，等价记录接口

### 基础资料库

- `GET /api/species` - 鱼种列表，支持 `keyword`、`category`
- `POST /api/species` - 新建鱼种，管理员
- `GET /api/species/{id}` - 鱼种详情
- `PUT /api/species/{id}` - 更新鱼种，管理员
- `DELETE /api/species/{id}` - 删除鱼种，管理员
- `GET /api/baits` - 饵料列表，支持 `keyword`、`bait_type`
- `POST /api/baits` - 新建饵料，管理员
- `GET /api/baits/{id}` - 饵料详情
- `PUT /api/baits/{id}` - 更新饵料，管理员
- `DELETE /api/baits/{id}` - 删除饵料，管理员
- `GET /api/equipment` - 我的装备，支持 `keyword`、`equipment_type`
- `POST /api/equipment` - 新建装备
- `GET /api/equipment/{id}` - 装备详情
- `PUT /api/equipment/{id}` - 更新装备
- `DELETE /api/equipment/{id}` - 删除装备

### 社区与成长

- `GET /api/forum/posts` - 帖子列表
- `POST /api/forum/posts` - 发布帖子
- `GET /api/forum/posts/{id}` - 帖子详情并累计浏览量
- `PUT /api/forum/posts/{id}` - 更新帖子
- `DELETE /api/forum/posts/{id}` - 删除帖子
- `POST /api/forum/posts/{id}/comments` - 发表评论
- `POST /api/forum/posts/{id}/likes` - 点赞帖子
- `POST /api/forum/comments/{id}/likes` - 点赞评论
- `POST /api/forum/posts/{id}/feature` - 设为精华，管理员
- `GET /api/users/me/level` - 我的等级、称号、升级进度和勋章
- `GET /api/users/me/xp-logs` - 我的经验记录
- `GET /api/users/leaderboards` - 排行榜数据
- `GET /api/dashboard/me` - 首页个人 Dashboard 数据

## 页面入口

- `/` - 首页 Dashboard
- `/spots` - 钓点地图、列表、搜索、标签过滤
- `/records` 或 `/logs` - 出钓记录
- `/species` - 鱼种库
- `/baits` - 饵料库
- `/equipment` - 我的装备
- `/forum` - 讨论专区
- `/level` - 我的等级
- `/leaderboards` - 排行榜
- `/profile` - 个人中心
- `/admin/users` - 用户管理，仅管理员

## 技术栈

**后端：**
- FastAPI 0.104
- SQLAlchemy 2.0 Async
- PostgreSQL 16
- Pydantic V2

**部署：**
- Docker & Docker Compose
- Alembic 数据迁移
- Nginx

## V1.2 当前能力

- [x] 项目初始化和数据库设计
- [x] 前端页面开发（Jinja2 + Bootstrap 5 + Leaflet）
- [x] 钓点、出钓记录、鱼种、饵料、装备 CRUD
- [x] 天气数据集成
- [x] 社区论坛、评论、点赞、精华帖
- [x] 用户等级、经验记录、勋章、排行榜
- [x] 认证和权限管理
- [x] 管理员用户管理、禁用、禁言、重置密码
- [x] 昵称敏感词校验
- [x] Docker 一键启动
- [x] 移动端适配基础支持

## 测试

```bash
python -m unittest tests/test_catalog_and_record_services.py tests/test_nickname_validator.py tests/test_level_and_experience_services.py
```

本机未安装完整后端依赖时，部分服务测试会跳过；在 Docker API 容器内会完整执行。
