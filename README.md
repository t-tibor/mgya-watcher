# mgya-watcher

Monitors [mgya.org](https://www.mgya.org/oktatas/302) training pages for available seats and sends a Telegram notification when spots open up.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram Bot API token |
| `TELEGRAM_CHAT_ID` | Yes | — | Chat or user ID to send notifications to |
| `TARGET_URL` | No | `https://www.mgya.org/oktatas/302` | Training page URL to monitor |
| `POLL_INTERVAL_MINUTES` | No | `5` | How often to check (in minutes) |

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the bot token
4. Send a message to your bot, then call `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`

### 2. Run Locally

```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
pip install .
python main.py
```

### 3. Docker

```bash
docker build -t mgya-watcher .
docker run --rm \
  -e TELEGRAM_BOT_TOKEN="your-token" \
  -e TELEGRAM_CHAT_ID="your-chat-id" \
  mgya-watcher
```

### 4. Kubernetes Deployment

Edit the Secret in `k8s/deployment.yaml` with your Telegram credentials, then:

```bash
# Build and push the image to your registry
docker build -t your-registry/mgya-watcher:latest .
docker push your-registry/mgya-watcher:latest

# Update the image in deployment.yaml, then apply
kubectl apply -f k8s/deployment.yaml
```

The pod polls every 5 minutes by default. Change `POLL_INTERVAL_MINUTES` in the Deployment to adjust.
