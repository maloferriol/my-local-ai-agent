"""
Weather-related tool implementations.

This module contains tools for getting weather information.
"""

import random
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


def get_weather_impl(city: str) -> str:
    """
    Implementation for getting the current temperature for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current temperature
    """
    # Get the current span from the context
    current_span = trace.get_current_span()

    # Add attributes to the span
    current_span.set_attribute("input.city", city)

    temperatures = list(range(-10, 35))
    temp = random.choice(temperatures)

    return f"The temperature in {city} is {temp}°C"


def get_weather_conditions_impl(city: str) -> str:
    """
    Implementation for getting the weather conditions for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current weather conditions
    """
    # Get the current span from the context
    current_span = trace.get_current_span()

    # Add attributes to the span
    current_span.set_attribute("input.city", city)

    conditions = ["sunny", "cloudy", "rainy", "snowy", "foggy"]
    return random.choice(conditions)
