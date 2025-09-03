import random
import logging

# from openinference.semconv.trace import SpanAttributes
# from opentelemetry import trace

# Get your logger instance for this module
logger = logging.getLogger("tools_logger")

# tracer = trace.get_tracer(__name__)


# @tracer.start_as_current_span(
#     name="get_weather",
#     attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "TOOL"},
# )
def get_weather(city: str) -> str:
    """
    Get the current temperature for a city

    Args:
        city (str): The name of the city

    Returns:
        str: The current temperature
    """
    # # Get the current span from the context
    # current_span = trace.get_current_span()

    # # Add attributes to the span
    # current_span.set_attribute("input.city", city)

    temperatures = list(range(-10, 35))

    temp = random.choice(temperatures)

    print('I AM HERE', __file__, "get_weather")

    return f"The temperature in {city} is {temp}°C"


# @tracer.start_as_current_span(
#     name="get_weather_conditions",
#     attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "TOOL"},
# )
def get_weather_conditions(city: str) -> str:
    """
    Get the weather conditions for a city

    Args:
        city (str): The name of the city

    Returns:
        str: The current weather conditions
    """
    # Get the current span from the context
    # current_span = trace.get_current_span()

    # # Add attributes to the span
    # current_span.set_attribute("input.city", city)
    print('I AM HERE', __file__, "get_weather_conditions")

    conditions = ["sunny", "cloudy", "rainy", "snowy", "foggy"]
    return random.choice(conditions)
