from prometheus_client import Counter, Histogram, Gauge

moderation_latency_seconds = Histogram(
    "moderation_latency_seconds",
    "Time taken for Gemini moderation before invoice extraction",
)

extraction_latency_seconds = Histogram(
    "extraction_latency_seconds",
    "Time taken for Gemini to extract invoice data from an image",
)

token_cost_usd_total = Counter(
    "token_cost_usd_total",
    "Estimated cumulative cost in USD from Gemini API usage",
)

auto_approvals_total = Counter(
    "auto_approvals_total",
    "Total documents that were auto-approved without human review",
)

documents_total = Counter(
    "documents_total",
    "Total documents ingested",
)

pending_review_queue_size = Gauge(
    "pending_review_queue_size",
    "Current number of documents awaiting human review",
)