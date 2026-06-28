#!/usr/bin/env bash
# 把 dist-content/ 上传到 R2 桶（key = 相对 dist-content 的路径）。
# 可断点续传：跳过 .r2-upload.log 里已 OK 的 key。
# 对 Cloudflare API 限流(971)做退避重试，并发压低以免触发限流。
set -uo pipefail
cd "$(dirname "$0")/.."
set -a; source .env.local; set +a
export CI=1 WRANGLER_SEND_METRICS=false

BUCKET="${1:-chinese-classics}"
PAR="${2:-6}"
export WR="$(pwd)/node_modules/.bin/wrangler"
LOG="$(pwd)/.r2-upload.log"
touch "$LOG"

# 已成功的 key 集合
grep '^OK ' "$LOG" | sed 's/^OK //' | sort -u > "$(pwd)/.r2-ok.txt"

cd dist-content
# 待传 = 全部文件 - 已成功
comm -23 <(find . -type f | sed 's|^\./||' | sort) <(sort -u "$(pwd)/../.r2-ok.txt") > "$(pwd)/../.r2-pending.txt"
TOTAL=$(wc -l < "$(pwd)/../.r2-pending.txt" | tr -d ' ')
echo "待传: $TOTAL 个（并发 $PAR）"

cat "$(pwd)/../.r2-pending.txt" | xargs -P "$PAR" -I {} sh -c '
  key="$1"; n=0
  while [ $n -lt 6 ]; do
    if "$WR" r2 object put "$0/$key" --file "$key" --remote >/dev/null 2>&1; then
      echo "OK $key" >> "$2"; exit 0
    fi
    n=$((n+1)); sleep $((n*3))
  done
  echo "FAIL $key" >> "$2"
' "$BUCKET" {} "$LOG"

echo "本轮结束。累计 OK $(grep -c '^OK' "$LOG") / FAIL(去重待重试) $(comm -23 <(grep '^FAIL' "$LOG"|sed 's/^FAIL //'|sort -u) <(grep '^OK' "$LOG"|sed 's/^OK //'|sort -u) | wc -l | tr -d ' ')"
