# AnglrLog 域名和部署配置

## 域名信息
- **域名**: anglrlog.com
- **应用名称**: AnglrLog
- **简介**: 专业钓鱼记录工具

## 当前部署配置

### 本地开发 (localhost:8000)
应用已部署在本地，可直接访问：
- **地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 生产部署建议 (anglrlog.com)

#### 1. DNS 配置
```
A 记录: anglrlog.com -> <服务器IP>
CNAME:  www.anglrlog.com -> anglrlog.com
```

#### 2. Nginx 反向代理配置
```nginx
server {
    listen 80;
    server_name anglrlog.com www.anglrlog.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name anglrlog.com www.anglrlog.com;
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/anglrlog.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/anglrlog.com/privkey.pem;
    
    # 代理设置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. Docker部署到生产服务器
```bash
# 构建镜像
docker build -t anglrlog:latest .

# 运行容器
docker run -d \
  --name anglrlog \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/anglrlog" \
  -e JWT_SECRET_KEY="your-production-secret-key" \
  -v /data/anglrlog:/app/data \
  anglrlog:latest
```

#### 4. SSL证书申请 (Let's Encrypt)
```bash
# 使用 certbot
certbot certonly --standalone -d anglrlog.com -d www.anglrlog.com

# 或使用 Docker
docker run -it --rm --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  -p 80:80 \
  certbot/certbot certonly --standalone -d anglrlog.com
```

## 环境配置

### 生产环境 .env
```
DATABASE_URL=postgresql+asyncpg://anglrlog:password@localhost/anglrlog
JWT_SECRET_KEY=your-secure-random-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OPEN_METEO_API_URL=https://api.open-meteo.com/v1
```

### 增强安全性
```python
# 在 app/main.py 中添加安全headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://anglrlog.com", "https://www.anglrlog.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 监控和维护

### 日志管理
```bash
# 查看应用日志
docker logs -f anglrlog

# 查看Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 自动备份
```bash
# 数据库备份脚本
pg_dump anglrlog > /backup/anglrlog_$(date +%Y%m%d).sql

# 配置crontab
0 2 * * * pg_dump anglrlog > /backup/anglrlog_$(date +\%Y\%m\%d).sql
```

### 性能优化
- 配置Redis缓存
- 启用Gzip压缩
- 配置CDN分发静态资源
- 使用数据库连接池

## 迁移检查清单

- [ ] 申请SSL证书
- [ ] 配置DNS记录
- [ ] 部署到生产服务器
- [ ] 配置Nginx反向代理
- [ ] 测试域名访问
- [ ] 配置邮件通知
- [ ] 设置定时备份
- [ ] 配置监控告警
- [ ] 性能测试
- [ ] 安全审计

## 快速参考

### 启动本地开发
```bash
cd /work/my_blog
source venv/bin/activate
uvicorn app.main:app --reload
```

### 测试API
```bash
# 查看所有钓点
curl http://localhost:8000/api/spots

# API文档
open http://localhost:8000/docs
```

---

**AnglrLog** - 为钓鱼爱好者打造的数据管理平台
- 官网: https://anglrlog.com
- API文档: https://anglrlog.com/docs
