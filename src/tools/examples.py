import random
import logging

# Get your logger instance for this module
logger = logging.getLogger('tools_logger')


def get_weather(city: str) -> str:
  """
  Get the current temperature for a city

  Args:
      city (str): The name of the city

  Returns:
      str: The current temperature
  """
  temperatures = list(range(-10, 35))

  temp = random.choice(temperatures)

  return f'The temperature in {city} is {temp}°C'

def get_weather_conditions(city: str) -> str:
  """
  Get the weather conditions for a city

  Args:
      city (str): The name of the city

  Returns:
      str: The current weather conditions
  """
  conditions = ['sunny', 'cloudy', 'rainy', 'snowy', 'foggy']
  return random.choice(conditions)