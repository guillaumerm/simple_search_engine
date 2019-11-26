from nltk import word_tokenize
import re
from utils import has_digits

class Query(object):

    def __init__(self, query):
        self.tokens = [token.lower() for token in set(word_tokenize(query)) if not has_digits(token)]

    def __len__(self):
        """The length of the tokens in the query
        
        Returns:
            [type] -- [description]
        """
        return len(self.tokens)

    def __sizeof__(self):
        return len(self.tokens)

    def __iter__(self):
        self.n = 0
        return self

    def __getitem__(self, index):
        return self.tokens[index]

    def __next__(self):
        if self.n < len(self.tokens):
            next_term = self.tokens[self.n]
            self.n += 1
            return next_term
        else:
            raise StopIteration