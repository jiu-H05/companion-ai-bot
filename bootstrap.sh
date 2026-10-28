#!/usr/bin/env bash
# 在云服务器上执行：sudo bash bootstrap.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

if [[ ${EUID} -ne 0 ]]; then
  echo "请用 root 运行：sudo bash bootstrap.sh"
  exit 1
fi

log() { echo -e "\n\033[1;36m[$(date +%H:%M:%S)] $*\033[0m"; }

# ---------- 1. Swap：2G 内存的机器必须加，防止 QQ/AstrBot 被 OOM 杀掉 ----------
if ! swapon --show 2>/dev/null | grep -q .; then
  if [[ ! -f /swapfile ]]; then
    log "创建 4G swap"
    fallocate -l 4G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
  fi
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl -w vm.swappiness=20 >/dev/null
  grep -q '^vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=20' >> /etc/sysctl.conf
  log "swap 已启用"
else
  log "已存在 swap，跳过"
fi

# ---------- 2. Docker ----------
if ! command -v docker >/dev/null 2>&1; then
  log "安装 Docker（阿里云镜像源）"
  curl -fsSL https://get.docker.com | bash -s -- --mirror Aliyun
fi
systemctl enable --now docker >/dev/null 2>&1 || true
docker compose version >/dev/null

# ---------- 3. .env（随机 VNC 密码） ----------
if [[ ! -f .env ]]; then
  VNC_PASS="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 20)"
  printf 'VNC_PASSWD=%s\nSNOWLUMA_UID=1000\nSNOWLUMA_GID=1000\n' "$VNC_PASS" > .env
  chmod 600 .env
  log ".env 已生成，VNC 密码：$VNC_PASS"
fi

# ---------- 4. 拉镜像（失败自动切 DaoCloud 镜像） ----------
if ! docker compose pull; then
  log "Docker Hub 拉取失败，切换 DaoCloud 镜像源重试"
  sed -i \
    -e 's#image: soulter/astrbot:latest#image: m.daocloud.io/docker.io/soulter/astrbot:latest#' \
    -e 's#image: motricseven7/snowluma:latest#image: m.daocloud.io/docker.io/motricseven7/snowluma:latest#' \
    docker-compose.yml
  docker compose pull
fi

# ---------- 5. 启动 ----------
docker compose up -d
log "等待 25 秒让容器初始化..."
sleep 25
docker compose ps
log "完成。查看日志：docker compose logs -f --tail=100"
