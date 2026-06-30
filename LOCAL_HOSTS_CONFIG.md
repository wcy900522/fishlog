# AnglrLog 本地测试配置

## 使用本地 /etc/hosts 配置测试 anglrlog.com 域名

将以下一行添加到 `/etc/hosts` 文件中：

```
127.0.0.1  anglrlog.com www.anglrlog.com
```

### Linux/Mac
```bash
sudo nano /etc/hosts
# 添加上面的一行，然后 Ctrl+X, Y, Enter 保存退出
```

### Windows
编辑 `C:\Windows\System32\drivers\etc\hosts`（需要管理员权限）

## 本地测试

配置完成后，可以直接访问：
- http://anglrlog.com:8000
- http://www.anglrlog.com:8000

## 使用 Nginx 本地反向代理（可选）

如果需要去掉端口号，可以配置本地 Nginx：

```nginx
# /etc/nginx/sites-available/anglrlog-local

server {
    listen 80;
    server_name anglrlog.com www.anglrlog.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/anglrlog-local /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

之后就可以直接访问 http://anglrlog.com

## 回滚

如果不再需要本地测试，删除 /etc/hosts 中的这一行即可。
