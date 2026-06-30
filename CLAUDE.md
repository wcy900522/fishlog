# AnglrLog 项目指南

## 项目概述

AnglrLog 是一个专注于钓鱼记录的数据工具，帮助钓鱼人记录每一次出钓，并积累属于自己的钓鱼数据库。

**官网**: https://anglrlog.com

## 技术栈

- **后端**：FastAPI + SQLAlchemy 2.0 Async + PostgreSQL
- **前端**：Jinja2 + HTMX + Bootstrap 5 + Leaflet 地图
- **部署**：Docker + Docker Compose

## 项目结构

```
app/
├── api/           # API 路由
│   ├── auth.py   # 认证相关
│   ├── spots.py  # 钓点相关
│   └── logs.py   # 记录相关
├── core/
│   ├── config.py    # 数据库配置
│   └── security.py  # 认证和加密
├── models/        # SQLAlchemy 模型
├── repositories/  # 数据访问层
├── schemas/       # Pydantic 模型
├── services/      # 业务逻辑
├── templates/     # HTML 模板
├── static/        # 静态资源
└── main.py       # 应用入口
```

## 开发进度

### 已完成
- [x] 项目初始化和基础架构
- [x] 数据库模型设计
- [x] API 层开发
- [x] 认证模块（JWT）
- [x] 天气服务集成（Open-Meteo API）
- [x] Docker 配置
- [x] 示例数据初始化（20个钓点）
- [x] 基础模板

### 待完成
- [ ] 前端页面完善（登录、注册、记录表单）
- [ ] HTML 模板开发
- [ ] HTMX 交互实现
- [ ] 移动端适配
- [ ] API 与前端集成
- [ ] 身份验证在模板中的应用
- [ ] 测试用例
- [ ] 性能优化

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
docker-compose up
```

应用会在 http://localhost:8000 启动。

### 方式二：本地开发

1. 创建虚拟环境并安装依赖：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. 启动 PostgreSQL（需自行安装）：
```bash
# 假设已安装 PostgreSQL
psql -U postgres -c "CREATE DATABASE fishlog;"
psql -U postgres fishlog < schema.sql
```

3. 运行应用：
```bash
uvicorn app.main:app --reload
```

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量

在 `.env` 中配置：
- `DATABASE_URL`: PostgreSQL 连接字符串
- `JWT_SECRET_KEY`: JWT 签名密钥
- `ALGORITHM`: JWT 算法（默认 HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（默认 30 分钟）
- `OPEN_METEO_API_URL`: 天气 API 地址

## 下一步

1. **前端开发**：完善首页、登录、注册页面
2. **API 完善**：添加分页、筛选、搜索功能
3. **测试**：编写单元测试和集成测试
4. **部署**：配置 Nginx，完成生产部署
5. **功能优化**：添加数据缓存、性能优化

## 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [Open-Meteo API](https://open-meteo.com/)
- [Bootstrap 5](https://getbootstrap.com/)
- [HTMX](https://htmx.org/)
- [Leaflet 地图](https://leafletjs.com/)
