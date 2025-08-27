# OpenTelemetry Logging Integration

This project now uses OpenTelemetry for logging. All logs are sent to the OpenTelemetry collector when it's running.

## Features

- **Structured Logging**: Enhanced logging with OpenTelemetry context
- **Centralized Collection**: All logs sent to OpenTelemetry collector
- **Console Output**: Logs also displayed in console for local development

## Setup

### 1. Start the OpenTelemetry Collector (Optional)

The project includes a collector configuration file. When you're ready to collect logs, start it using Docker:

```bash
docker run --rm -it \
  -v $(pwd)/otel-collector-config.yaml:/etc/otelcol/config.yaml \
  -p 4317:4317 -p 4318:4318 \
  otel/opentelemetry-collector:latest
```

The collector will:
- Listen on port 4317 (gRPC) and 4318 (HTTP)
- Export logs to both console (debug) and file (`./otel/telemetry.json`)

### 2. Run Your Application

The OpenTelemetry logging setup is automatically configured when you import from `loggers.logging_config`. Your application will automatically:

- Send logs to the collector (when it's running)
- Display logs in the console for local development

## Usage

### Basic Logging

```python
from loggers.logging_config import get_logger

logger = get_logger(__name__)
logger.info("This log will be sent to OpenTelemetry collector when it's running")
```

### In Your Modules

```python
from loggers.logging_config import get_logger

logger = get_logger(__name__)

def some_function():
    logger.info("Function started")
    # Your code here
    logger.info("Function completed")
```

### Test the Setup

Run the test script to verify logging is working:

```bash
python3 -m src.test_logging
```

## Configuration

The OpenTelemetry logging setup is configured in `src/loggers/logging_config.py`:

- **Service Name**: `my-local-ai-agent`
- **Version**: `1.0.0`
- **Environment**: `development`
- **Collector Endpoint**: `http://localhost:4317`
- **Log Level**: `INFO`

## Data Flow

1. **Application** generates log messages
2. **OpenTelemetry SDK** processes and formats the logs
3. **OTLP Exporter** sends logs to the collector via gRPC (when collector is running)
4. **Console Handler** displays logs locally for development
5. **OpenTelemetry Collector** receives and exports logs (when running)

## Benefits

- **Unified Logging**: Single logging interface across your application
- **Structured Logging**: Enhanced logs with service context
- **Easy Integration**: Simple setup with automatic configuration
- **Vendor Agnostic**: OpenTelemetry is vendor-neutral and widely supported
- **Local Development**: Console output for immediate feedback

## Current Status

- ✅ OpenTelemetry logging setup configured
- ✅ All modules updated to use OpenTelemetry logging
- ✅ Console output working for local development
- ⏳ Collector integration ready (when you start the collector)

## Next Steps

When you're ready to collect logs:
1. Start the OpenTelemetry collector
2. Run your application
3. Logs will automatically be sent to the collector
4. View collected logs in the console or file output
