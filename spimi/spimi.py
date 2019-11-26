import os
from bs4 import BeautifulSoup
from nltk import word_tokenize, FreqDist
import heapq
import re
from pathlib import Path
from SearchEngine import SearchEngine
from Query import Query
from utils import block_entry_generator, merge_postings_lists, has_digits

# Current number of Reuters article in the block
block_current_size = 0

# Maximum for SPIMI block size is 500 documents.
block_max_size = 500

# Maximum for MERGE block size is 25000 terms.
final_block_max_size = 25000

block_number = 1

documents_length = {}

def document_generator(directory):
    """Generates a document generator from a given directory
    
    Arguments:
        directory {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    global block_current_size
    file_stream = os.scandir(directory)
    while True:
        try:
            directory_entry = next(file_stream)
        except StopIteration:
            return None

        # If the file does not end with .sgm skip it as it does not contain reuters articles
        #if not directory_entry.name.endswith('.sgm'):
        #    continue

        file = open(directory + '/' + directory_entry.name, encoding="UTF-8")

        docID = os.path.basename(file.name)

        # Removes new line and split them in articles
        document = file.read().replace('\n', ' ')
        #reuters = file_content.split('</REUTERS>')

        document = BeautifulSoup(document, 'html.parser').get_text()
        
        # Streaming the docID and document
        yield (docID, document)

        # After yielding the above document the SPIMI must have
        # field its block with this article hence increase the size
        # by one
        block_current_size += 1

def tokens_generator(directory):
    global documents_length
    document_stream = document_generator(directory)
    while True:
        document_tuple = next(document_stream)

        if document_tuple is None:
            return None

        # For some cases NLTK was returning duplicates. Since we are building a boolean
        # retrieval index we only need if the type is found in the document.
        
        # Non-positional index
        tokens = FreqDist(word_tokenize(document_tuple[1].lower()))
        documents_length[document_tuple[0]] = tokens.N()
        
        for token, freq in tokens.items():
            # No numbers
            if has_digits(token):
                continue
                
            yield (token, document_tuple[0], freq)

        # Positional index
        # tokens = word_tokenize(document_tuple[1])
        # for token_index in range(len(tokens)):

            # No numbers lossy compression
        #    if has_digits(tokens[token_index]):
        #        token_index += 1
        #        continue

            # 30 Stop words
        #    if tokens[token_index] in stop_words:
        #        token_index += 1
        #        continue

        #    yield (tokens[token_index].lower(), (document_tuple[0], token_index+1))

def new_file():
    global block_number

    if not os.path.exists('./DISK'): 
        os.mkdir('./DISK')

    # Create "Block" ie file
    file_path = Path('./DISK/BLOCK' + str(block_number))
    file_path.touch()
    
    file = open('./DISK/BLOCK' + str(block_number))
    file.close()
    block_number += 1

    return file

def write_block_to_disk(sorted_terms, dictionary, output_file):
    with open(output_file.name, 'w') as block:
        for term in sorted_terms:
            block.write(term + ":" + ';'.join(str(docID) for docID in dictionary[term]) + '\n')
        block.flush()

def write_final_block_to_disk(sorted_dictionary, output_file):
    with open(output_file.name, 'w') as block:
        for dictionary_entry in sorted_dictionary:
            block.write(dictionary_entry[0] + ":" + ';'.join(str(docID) for docID in dictionary_entry[1]) + '\n')  
        block.flush()
    
def add_to_dictionary(dictionary, term):
    """Add a term to the dictionary and initiates its postings list.
    
    Arguments:
        dictionary {hash} -- Dictionary of terms pointing to a postings list
        term {string} -- Term that we add to the dictionary
    
    Returns:
        list -- Postings list
    """
    dictionary[term] = []
    return dictionary[term]

def add_to_postings_list(posting_lists, docID):
    return posting_lists.append(docID)

def get_postings_list(dictionary, term):
    """Returns the postings list from a dictionary
    
    Arguments:
        dictionary {hash} -- Dictionary of terms pointing to a postings list
        term {string} -- Term for which we must return its postings list
    
    Returns:
        list -- Postings list
    """
    return dictionary[term]

def sort_terms(dictionary):
    """Returns the sorted terms from a dictionary
    
    Arguments:
        dictionary {hash} -- Dictionary that contains terms refering to posting lists.
    
    Returns:
        List -- List of sorted alphabetically
    """
    return sorted(dictionary.keys())

def term(token):
    return token[0]

def docID(token):
    return token[1]

def SPIMI_invert(token_stream):
    global block_current_size
    dictionary = {}
    output_file = new_file()
    token_stream_ended = False
    try:
        while (block_current_size < block_max_size) :
            token = next(token_stream)
            if term(token) not in dictionary: postings_list = add_to_dictionary(dictionary, term(token))
            else: postings_list = get_postings_list(dictionary, term(token))
            add_to_postings_list(postings_list, (docID(token), token[2]))
    except:
        #Token stream as ended
        token_stream_ended = True
    finally:
        # Make sure to write the block to the disk even if the token stream as ended
        sorted_terms = sort_terms(dictionary)
        write_block_to_disk(sorted_terms, dictionary, output_file)
    return output_file, token_stream_ended

def merge_blocks(unmerged_blocks, merged_blocks):
    
    # Streams for the entries for the unmerge blocks
    unmerged_block_streams = []

    # Add the streams
    for unmerged_block in unmerged_blocks:
        unmerged_block_streams.append(block_entry_generator(unmerged_block))

    # Buffer for the first entry of each block. Using a min-heap to 
    # improve the merging of K sorted unmerged blocks.
    unmerged_block_entries = []

    # Add the first line from each blocks.
    for unmerged_block_stream_index in range(len(unmerged_block_streams)):
        entry = next(unmerged_block_streams[unmerged_block_stream_index])
        heapq.heappush(unmerged_block_entries, (entry[0], entry[1], unmerged_block_stream_index))

    current_final_block_size = 0

    # Merge until all unmerged_blocks are merged

    empty_unmerged_block_streams = 0

    final_block = []
    
    while not empty_unmerged_block_streams == len(unmerged_blocks):
        output_file = new_file()

        while current_final_block_size < final_block_max_size and len(unmerged_block_entries) > 0:
            smallest_heap_entry = heapq.heappop(unmerged_block_entries)

            minimum_unmerged_block_entry = (smallest_heap_entry[0], smallest_heap_entry[1])

            # Collection of unmerged block that needs update
            minimum_unmerged_block_entries_indices = [smallest_heap_entry[2]]

            try:
                # Merge all the entries that have the same terms
                next_smallest_heap_entry = heapq.heappop(unmerged_block_entries)
                while(next_smallest_heap_entry[0] == minimum_unmerged_block_entry[0]):
                    minimum_unmerged_block_entry = (term(minimum_unmerged_block_entry), merge_postings_lists(minimum_unmerged_block_entry[1], next_smallest_heap_entry[1]))
                    minimum_unmerged_block_entries_indices.append(next_smallest_heap_entry[2])
                    next_smallest_heap_entry = heapq.heappop(unmerged_block_entries)
            except IndexError:
                # The batch of entries are merged.
                next_smallest_heap_entry = None

            # If the heap entry is not equal to the smallest entry put it back in the heap
            if (next_smallest_heap_entry is not None and next_smallest_heap_entry[0] != minimum_unmerged_block_entry[0]):
                heapq.heappush(unmerged_block_entries, next_smallest_heap_entry)
                next_smallest_heap_entry = None

            final_block.append(minimum_unmerged_block_entry)
            minimum_unmerged_block_entry = None
            current_final_block_size += 1

            # Update the block entries for the unmerged blocks
            for minimum_unmerged_block_entries_index in minimum_unmerged_block_entries_indices:
                try:
                    entry = next(unmerged_block_streams[minimum_unmerged_block_entries_index])
                    heapq.heappush(unmerged_block_entries, (entry[0], entry[1], minimum_unmerged_block_entries_index))
                except StopIteration:
                    # Count number of blocks that are done merging
                    empty_unmerged_block_streams += 1
                    pass
        
        write_final_block_to_disk(final_block, output_file)

        # Reset final block size to 0
        current_final_block_size = 0
        final_block = []
        
        merged_blocks.append(output_file)
            
def SPIMI_index_construction(corpus_location):
    global block_current_size
    document_stream = document_generator(corpus_location)
    blocks = []
    postings_stream = tokens_generator(corpus_location)
    
    token_stream_ended = False

    # Construct index blocks until token stream ends
    while not token_stream_ended:
        block, token_stream_ended = SPIMI_invert(postings_stream)

        if block is not None:
            blocks.append(block)
        
        # Emulate reseting the content of the block size
        block_current_size = 0

    merged_blocks = []

    merge_blocks(blocks, merged_blocks)

    # Closing the blocks
    for block in blocks:
        block.close()

    print('The final blocks are:\n')
    for merged_block in merged_blocks:
        print(merged_block.name)

    return merged_blocks

    def SPIMI_index_construction(self, corpus_location):
        self.block_current_size
        document_stream = self.document_generator(corpus_location)
        blocks = []
        postings_stream = tokens_generator(corpus_location)
        
        token_stream_ended = False

        # Construct index blocks until token stream ends
        while not token_stream_ended:
            block, token_stream_ended = SPIMI_invert(postings_stream)

            if block is not None:
                blocks.append(block)
            
            # Emulate reseting the content of the block size
            block_current_size = 0

        merged_blocks = []

        merge_blocks(blocks, merged_blocks)

        # Closing the blocks
        for block in blocks:
            block.close()

        print('The final blocks are:\n')
        for merged_block in merged_blocks:
            print(merged_block.name)

        return merged_blocks

    

index = SearchEngine(SPIMI_index_construction('/Users/guillaume/Projects/Python/comp_479_project/aitopics/'), documents_length)

while True:
    try:
        query = Query(input('Enter query:'))
    except Exception as ex:
        print(ex.args[0])
        continue
    print(index.search(query))