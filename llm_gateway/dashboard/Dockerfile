FROM oven/bun:1.1.21

WORKDIR /app/dashboard

COPY package.json ./
RUN bun install

COPY . .

RUN mkdir -p /data /app && ln -s /data/llm_gateway.db /app/llm_gateway.db

EXPOSE 8010

CMD ["bun", "src/server.ts"]
