FROM node:20-alpine

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 设置环境变量
ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE

# 构建应用
RUN npm run build

# 使用nginx服务静态文件
FROM nginx:alpine

# 复制构建好的文件
COPY --from=0 /app/dist /usr/share/nginx/html

# 创建nginx配置
RUN echo 'events { worker_connections 1024; } http { include /etc/nginx/mime.types; default_type application/octet-stream; sendfile on; keepalive_timeout 65; server { listen 3000; server_name localhost; location / { root /usr/share/nginx/html; index index.html index.htm; try_files $uri $uri/ /index.html; } } }' > /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 3000

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
