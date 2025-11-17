# Docker Quick Start Guide

快速开始使用 PostgreSQL 16 Docker 环境。

## 前置要求

✅ 已安装 Docker Desktop
- Windows: https://www.docker.com/products/docker-desktop
- 确保 Docker Desktop 正在运行

## 快速开始（3步）

### 1️⃣ 启动数据库

```bash
# 进入 docker 目录
cd docker

# 启动 PostgreSQL 16
docker-compose up -d postgres
```

预期输出：
```
✅ Network hyper-demo_trading_bot_network  Created
✅ Volume hyper-demo_postgres_data  Created
✅ Container trading_bot_postgres  Started
```

### 2️⃣ 验证数据库

```bash
# 查看容器状态
docker-compose ps

# 应该显示:
# NAME                    STATUS
# trading_bot_postgres    Up (healthy)

# 查看初始化日志
docker-compose logs postgres | findstr "initialization"
```

应该看到：
```
✅ Database initialization completed!
```

### 3️⃣ 连接到数据库

```bash
# 方式1: 使用 psql (在容器内)
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev

# 在 psql 提示符中:
\dt                    # 列出所有表
SELECT * FROM trading_agents;  # 查看示例数据
\q                     # 退出

# 方式2: 使用 pgAdmin (可选)
docker-compose --profile tools up -d
# 访问 http://localhost:5050
# 邮箱: admin@tradingbot.local
# 密码: admin123
```

## 验证 Python 连接

### 更新 .env 文件

确保项目根目录的 `.env` 包含：

```bash
# Database Configuration (Docker)
DB_USER=trading_bot
DB_PASSWORD=trading_bot_2025
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_bot_dev
```

### 运行集成测试

```bash
# 回到项目根目录
cd ..

# 测试数据库连接
python run_db_tests.py
```

预期输出：
```
============================= 22 passed in 0.84s ==============================
```

## 常用命令

所有命令都在 `docker/` 目录下执行：

```bash
cd docker

# 查看日志
docker-compose logs -f postgres

# 重启数据库
docker-compose restart postgres

# 停止数据库
docker-compose stop postgres

# 停止并删除容器（数据保留）
docker-compose down

# 停止并删除所有数据（⚠️ 谨慎使用）
docker-compose down -v
```

## 数据库管理

### 备份

```bash
cd docker

# 创建备份
docker-compose exec -T postgres pg_dump -U trading_bot trading_bot_dev > ../backups/backup.sql
```

### 恢复

```bash
cd docker

# 从备份恢复
docker-compose exec -T postgres psql -U trading_bot -d trading_bot_dev < ../backups/backup.sql
```

### 查看数据库大小

```bash
cd docker

docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c "SELECT pg_size_pretty(pg_database_size('trading_bot_dev'));"
```

## 故障排除

### 端口已被占用

如果 5432 端口已被占用：

1. 编辑 `docker/docker-compose.yml`
2. 修改端口映射：
   ```yaml
   ports:
     - "5433:5432"  # 使用 5433 代替
   ```
3. 更新项目根目录的 `.env` 中的 `DB_PORT=5433`

### 容器无法启动

```bash
cd docker

# 查看详细日志
docker-compose logs postgres

# 重新创建容器
docker-compose down
docker-compose up -d postgres
```

### 重置数据库

**方式1: 使用重置脚本（推荐）**

```bash
cd docker

# Windows PowerShell
.\reset-db.ps1

# Linux/Mac
chmod +x reset-db.sh
./reset-db.sh
```

**方式2: 手动重置**

```bash
cd docker

# ⚠️ 这会删除所有数据
docker-compose down -v
docker-compose up -d postgres

# 查看初始化日志
docker-compose logs postgres | findstr "initialization"
```

## 生产环境配置

### 更改密码

1. 编辑 `docker/docker-compose.yml`:
   ```yaml
   environment:
     POSTGRES_PASSWORD: YOUR_STRONG_PASSWORD
   ```

2. 更新项目根目录的 `.env`:
   ```bash
   DB_PASSWORD=YOUR_STRONG_PASSWORD
   ```

3. 重启容器:
   ```bash
   cd docker
   docker-compose down
   docker-compose up -d postgres
   ```

## 下一步

- 📖 完整文档: [../docs/06_deployment/database_setup.md](../docs/06_deployment/database_setup.md)
- 📊 数据库架构: [../docs/02_architecture/database_schema.md](../docs/02_architecture/database_schema.md)
- 🧪 测试指南: [../docs/04_testing/integration_testing.md](../docs/04_testing/integration_testing.md)

## 技术栈

- PostgreSQL 16 Alpine (轻量级官方镜像)
- Docker Compose 3.8
- 自动健康检查
- 持久化数据卷
- 自动初始化脚本

---

**享受使用 Docker PostgreSQL 16！** 🐘🐳
