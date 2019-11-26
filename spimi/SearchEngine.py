import re
from Query import Query
from Tree import Tree
from utils import intersect, block_to_dictionary, BLOCK_ENTRY_PATTERN, block_entry_generator, BM25, merge_postings_lists
from math import log

class SearchEngine(object):
    
    def __init__(self, blocks, documents):
        self.blocks = blocks
        self.index = SearchEngine.sorted_blocks_to_BST(blocks)
        self.documents = documents
        self.number_of_tokens = 0
        for length in self.documents.values():
            self.number_of_tokens += length

    def search(self, query):

        # If the query is empty
        if len(query) <= 0:
            return []

        documents_to_rank = {}
        
        sum_of_idfs = 0

        # Find all the postings list for the terms in the query
        for term in query:
            postings = self.find_postings(term)

            for posting in postings:
                documents_to_rank.setdefault(posting[0], []).append((term, posting[1]))

            if (len(postings) > 0):
                sum_of_idfs += log(10, len(self.documents) / len(postings))

        ranked_documents = {}

        for document_to_rank, terms_freq in documents_to_rank.items():
            for term_freq in terms_freq:
                rsv_d = BM25(sum_of_idfs, term_freq[1], self.documents[document_to_rank], self.number_of_tokens/len(self.documents), 1.2, 0.75)
                if document_to_rank in ranked_documents:
                    ranked_documents[document_to_rank] += rsv_d
                else:
                    ranked_documents[document_to_rank] = rsv_d

        sorted_ranked_documents = sorted(ranked_documents.items(), key=lambda x: x[1], reverse=True)

        return sorted_ranked_documents[:10]

    def find_postings(self, term):
        # Find in which block the term can potentially be
        block = SearchEngine.find_block(self.index, term)
        dictionary = block_to_dictionary(block)
        if term in dictionary:
            return dictionary[term]
        else:
            return []
        

    @staticmethod
    def find_block(root, term):
        """Finds in which block the term would potentially be.
        
        Arguments:
            root {Tree} -- Root of the block tree
            term {string} -- Term to find the corresponding block
        
        Returns:
            (string, file) -- Tupple with first term and block
        """
        # If term is the first term of the root block
        if term == root.content[0]:
            return root.content[1]
        # If term is within the last block
        if term > root.content[0] and root.right is None:
            return root.content[1]
        # If term is within the root block
        elif term > root.content[0] and term < root.right.content[0]:
            return root.content[1]
        # If term is less the the first term of the root block
        elif term < root.content[0]:
            return SearchEngine.find_block(root.left, term)
        # If term is greater then the first term and 
        # greater then first term of right block
        elif term > root.content[0]:
            return SearchEngine.find_block(root.right, term)

    @staticmethod
    def first_term(block):
        m = re.search(BLOCK_ENTRY_PATTERN, SearchEngine.first_line(block))
        return m.group(1)

    @staticmethod
    def first_line(block):  
        with open(block.name) as disk_block:
            return disk_block.readline()

    def calculate_metrics(self):
        number_terms = 0
        number_postings = 0
        for block in self.blocks:
            block_entry_stream = block_entry_generator(block)
            try:
                while True:
                    entry = next(block_entry_stream)
                    number_terms += 1
                    number_postings += len(entry[1])
            except StopIteration:
                # Block as been processed
                continue
        return (number_terms, number_postings)


    @staticmethod
    def sorted_blocks_to_BST(blocks):
        if not blocks:
            return None
        
        # Find the middle for the root of the tree
        middle = int((len(blocks)) / 2)

        # Make the middle the root
        root = Tree((SearchEngine.first_term(blocks[middle]), blocks[middle]))

        # Left subtree of root has all terms < blocks[middle]
        root.left = SearchEngine.sorted_blocks_to_BST(blocks[:middle])

        # Right subtree of root has all terms > blocks[middle]
        root.right = SearchEngine.sorted_blocks_to_BST(blocks[middle+1:])

        return root