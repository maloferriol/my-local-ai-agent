import random
import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.semconv.attributes import service_attributes
from opentelemetry.sdk.resources import Resource

resource = Resource.create(
    {
        service_attributes.SERVICE_NAME: "my-local-ai-agent",
        service_attributes.SERVICE_VERSION: "1.0.0",
    }
)


# Set up the OTLP exporter and tracer provider
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Get your logger instance for this module
logger = logging.getLogger("tools_logger")

tracer = trace.get_tracer(__name__)


def get_weather(city: str) -> str:
    """
    Get the current temperature for a city

    Args:
        city (str): The name of the city

    Returns:
        str: The current temperature
    """
    with tracer.start_as_current_span("get_weather"):
        temperatures = list(range(-10, 35))

        temp = random.choice(temperatures)

        return f"The temperature in {city} is {temp}°C"


def get_weather_conditions(city: str) -> str:
    """
    Get the weather conditions for a city

    Args:
        city (str): The name of the city

    Returns:
        str: The current weather conditions
    """
    with tracer.start_as_current_span("get_weather_conditions"):
        conditions = ["sunny", "cloudy", "rainy", "snowy", "foggy"]
        return random.choice(conditions)
