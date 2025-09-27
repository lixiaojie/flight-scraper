FROM node:22.20-alpine

# Set working directory
WORKDIR /app

# Configure npm to use Tencent Cloud mirror
RUN npm config set registry https://mirrors.cloud.tencent.com/npm/

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
