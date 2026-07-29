# 1. 使用官方轻量级 Python 3.11 镜像
FROM python:3.11-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 先把依赖清单拷进去，并安装依赖 (这样可以利用 Docker 缓存加速构建)
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary pydantic

# 4. 把当前目录下所有文件（包括 main.py 和打包好的 dist 文件夹）拷到容器里
COPY . .

# 5. 声明容器要使用的端口
EXPOSE 8001

# 6. 容器启动时执行的命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]