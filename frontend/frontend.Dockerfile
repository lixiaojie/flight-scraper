FROM node:20-alpine

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 配置npm国内源并安装依赖
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

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

# 复制nginx配置文件
COPY nginx.conf /etc/nginx/nginx.conf

# 删除默认配置文件避免冲突
RUN rm -f /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 3000

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
