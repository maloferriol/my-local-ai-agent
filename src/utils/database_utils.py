## to make it work for the first time
# import nltk
# nltk.download('words')

from nltk.corpus import words
from random import sample

class DatabaseUtils:
    def generate_random_name( n : int = 3 ) -> str:
        """Generates a random name by sampling n words from the nltk words corpus.
        
        Args:
        n (int): Number of words to sample. Default is 3.

        Returns:
        str: A random name consisting of n words in lowercase joined by hyphens.
        """
        return '-'.join(sample(words.words(), n)).lower()