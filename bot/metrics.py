from prometheus_client import Counter, Histogram, Info

BOT_INFO = Info("bot", "Bot information")
BOT_INFO.info({"version": "0.1.0", "name": "roundfather_bot"})

REQUEST_COUNT = Counter(
    "bot_requests_total",
    "Total bot requests",
    ["handler", "message_type"],
)

REQUEST_LATENCY = Histogram(
    "bot_request_latency_seconds",
    "Request latency in seconds",
    ["handler"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

VIDEO_PROCESSING_COUNT = Counter(
    "bot_video_processing_total",
    "Total video processing attempts",
    ["status"],
)

VIDEO_PROCESSING_LATENCY = Histogram(
    "bot_video_processing_latency_seconds",
    "Video processing latency in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

PREMIUM_PAYMENTS = Counter(
    "bot_premium_payments_total",
    "Total premium payments",
    ["package", "status"],
)
