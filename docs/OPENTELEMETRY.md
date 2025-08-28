# OpenTelemetry Integration

This project uses OpenTelemetry for observability, enabling logging, tracing, and metrics collection. All data can be sent to the OpenTelemetry collector when it's running.

---

## Setup for OpenTelemetry

### 1. Start the OpenTelemetry Collector

The project includes a collector configuration file. To start the collector, use Docker:

```bash
docker run --rm -it \
  -v $(pwd)/otel-collector-config.yaml:/etc/otelcol/config.yaml \
  -p 4317:4317 -p 4318:4318 \
  otel/opentelemetry-collector:latest
```

The collector will:
- Listen on port 4317 (gRPC) and 4318 (HTTP)

---

## OpenTelemetry Integration

### 1. Logging Integration

#### Features
- **Structured Logging**: Logs include OpenTelemetry context (e.g., trace IDs).
- **Centralized Collection**: Logs are sent to the OpenTelemetry collector.
- **Console Output**: Logs are displayed locally for development.

#### Configuration
The logging setup is defined in `src/loggers/logging_config.py`:
- **Service Name**: `my-local-ai-agent`
- **Version**: `1.0.0`
- **Environment**: `development`
- **Collector Endpoint**: `http://localhost:4317`
- **Log Level**: `INFO`

#### Usage

##### Basic Logging
```python
from loggers.logging_config import get_logger

logger = get_logger(__name__)
logger.info("This log will be sent to OpenTelemetry collector when it's running")
```

##### In Your Modules
```python
from loggers.logging_config import get_logger

logger = get_logger(__name__)

def some_function():
    logger.info("Function started")
    # Your code here
    logger.info("Function completed")
```

#### Testing the Setup
Run the test script to verify logging is working:
```bash
python3 -m src.test_logging
```

---

### 2. Traces Integration

#### Features
- **Distributed Tracing**: Tracks requests across services.
- **Context Propagation**: Automatically propagates trace context.
- **Collector Integration**: Sends trace data to the OpenTelemetry collector.

#### Configuration
The tracing setup is defined in `src/tracing/tracing_config.py`:
- **Service Name**: `my-local-ai-agent`
- **Version**: `1.0.0`
- **Environment**: `development`
- **Collector Endpoint**: `http://localhost:4317`

#### Usage

##### Basic Tracing
```python
from tracing.tracing_config import get_tracer

tracer = get_tracer(__name__)

with tracer.start_as_current_span("example-span"):
    print("This operation is being traced")
```

##### In Your Modules
```python
from tracing.tracing_config import get_tracer

tracer = get_tracer(__name__)

def some_function():
    with tracer.start_as_current_span("some_function"):
        # Your code here
        print("Tracing some_function")
```

#### Testing the Setup
Run the test script to verify tracing is working:
```bash
python3 -m src.test_tracing
```

---

### 3. Metrics Integration

#### Features
- **Custom Metrics**: Define and collect application-specific metrics.
- **Automatic Instrumentation**: Collects runtime metrics (e.g., CPU, memory).
- **Collector Integration**: Sends metrics data to the OpenTelemetry collector.

#### Configuration
The metrics setup is defined in `src/metrics/metrics_config.py`:
- **Service Name**: `my-local-ai-agent`
- **Version**: `1.0.0`
- **Environment**: `development`
- **Collector Endpoint**: `http://localhost:4317`

#### Usage

##### Basic Metrics
```python
from metrics.metrics_config import get_meter

meter = get_meter(__name__)
counter = meter.create_counter("example_counter")

counter.add(1, {"key": "value"})
```

##### In Your Modules
```python
from metrics.metrics_config import get_meter

meter = get_meter(__name__)
histogram = meter.create_histogram("example_histogram")

def some_function():
    histogram.record(42, {"key": "value"})
```

#### Testing the Setup
Run the test script to verify metrics collection is working:
```bash
python3 -m src.test_metrics
```

---

## Data Flow

1. **Application** generates logs, traces, and metrics.
2. **OpenTelemetry SDK** processes and formats the data.
3. **OTLP Exporter** sends data to the collector via gRPC (when the collector is running).
4. **Console Handlers** display logs locally for development.
5. **OpenTelemetry Collector** receives and exports data (when running).

---

## Benefits of OpenTelemetry

- **Unified Observability**: Single interface for logs, traces, and metrics.
- **Structured Data**: Enhanced context for debugging and monitoring.
- **Vendor Agnostic**: OpenTelemetry is widely supported and vendor-neutral.
- **Local Development**: Console output for immediate feedback.

---

## Next Steps

1. Start the OpenTelemetry collector.
2. Run your application.
3. Logs, traces, and metrics will automatically be sent to the collector.
4. View collected data in the console or export it to your preferred backend.
