FROM node:20-alpine AS builder

WORKDIR /app

# 複製依賴檔案
COPY package*.json ./

# 安裝依賴
RUN npm ci

# 複製原始碼
COPY . .

# 建置
RUN npm run build

# 生產階段
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 複製建置結果
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# 暴露端口
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
