"""
Prometheus metrics for monitoring the Poker Helper application.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from functools import wraps
import time
from typing import Callable, Any


# Application info
APP_INFO = Info('poker_helper', 'Poker MTT Helper application info')
APP_INFO.info({
    'version': '1.0.0',
    'name': 'poker-mtt-helper',
})

# Request metrics
REQUEST_COUNT = Counter(
    'poker_helper_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'poker_helper_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# WebSocket metrics
WEBSOCKET_CONNECTIONS = Gauge(
    'poker_helper_websocket_connections',
    'Current number of WebSocket connections'
)

WEBSOCKET_FRAMES_TOTAL = Counter(
    'poker_helper_websocket_frames_total',
    'Total WebSocket frames processed',
    ['status']  # success, error, no_table
)

# CV Processing metrics
CV_PROCESSING_TIME = Histogram(
    'poker_helper_cv_processing_seconds',
    'CV processing time in seconds',
    ['operation'],  # detect_cards, detect_table, ocr, full_pipeline
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

CV_DETECTIONS = Counter(
    'poker_helper_cv_detections_total',
    'Total CV detections',
    ['type', 'success']  # type: cards, table, text; success: true/false
)

CARDS_DETECTED = Histogram(
    'poker_helper_cards_detected',
    'Number of cards detected per frame',
    buckets=[0, 1, 2, 3, 4, 5, 6, 7]
)

# GTO Engine metrics
GTO_RECOMMENDATIONS = Counter(
    'poker_helper_gto_recommendations_total',
    'Total GTO recommendations generated',
    ['action', 'position', 'is_push_fold']
)

GTO_PROCESSING_TIME = Histogram(
    'poker_helper_gto_processing_seconds',
    'GTO engine processing time',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

# Training metrics
TRAINING_IMAGES = Gauge(
    'poker_helper_training_images_total',
    'Total training images in dataset',
    ['labeled']  # true/false
)

TRAINING_STATUS = Gauge(
    'poker_helper_training_in_progress',
    'Whether training is currently in progress'
)

# Model metrics
MODEL_LOADED = Gauge(
    'poker_helper_model_loaded',
    'Whether the YOLO model is loaded',
    ['model_name']
)

MODEL_INFERENCE_TIME = Histogram(
    'poker_helper_model_inference_seconds',
    'Model inference time',
    ['model'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)


# Helper decorators
def track_request_time(endpoint: str):
    """Decorator to track request timing."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                REQUEST_LATENCY.labels(method="POST", endpoint=endpoint).observe(duration)
                REQUEST_COUNT.labels(method="POST", endpoint=endpoint, status=status).inc()
        return wrapper
    return decorator


def track_cv_time(operation: str):
    """Decorator to track CV processing time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                CV_PROCESSING_TIME.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


# Metrics endpoint handler
async def metrics_endpoint() -> Response:
    """Return Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Helper functions for recording metrics
def record_websocket_frame(status: str):
    """Record a WebSocket frame processing event."""
    WEBSOCKET_FRAMES_TOTAL.labels(status=status).inc()


def record_cv_detection(detection_type: str, success: bool, num_items: int = 0):
    """Record a CV detection event."""
    CV_DETECTIONS.labels(type=detection_type, success=str(success).lower()).inc()
    if detection_type == "cards":
        CARDS_DETECTED.observe(num_items)


def record_gto_recommendation(action: str, position: str, is_push_fold: bool):
    """Record a GTO recommendation."""
    GTO_RECOMMENDATIONS.labels(
        action=action,
        position=position,
        is_push_fold=str(is_push_fold).lower()
    ).inc()


def set_model_loaded(model_name: str, loaded: bool):
    """Set model loaded status."""
    MODEL_LOADED.labels(model_name=model_name).set(1 if loaded else 0)


def update_training_dataset_stats(total: int, labeled: int):
    """Update training dataset statistics."""
    TRAINING_IMAGES.labels(labeled="true").set(labeled)
    TRAINING_IMAGES.labels(labeled="false").set(total - labeled)
