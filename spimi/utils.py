import re
BLOCK_ENTRY_PATTERN = '(.*):((.*;?)*)'

def block_entry_generator(block):
    """Returns an stream of the entry for a given block
    
    Arguments:
        block {file} -- Block from the disk
    """
    with open(block.name, 'r') as disk_block:
        line = disk_block.readline()
        while line:
            m = re.search(BLOCK_ENTRY_PATTERN, line)
            if m is not None:
                yield (m.group(1), list(map(eval, m.group(2).split(';'))))
            line = disk_block.readline()

def has_digits(s):
    m = re.search('\d', s)
    return m is not None

def block_to_dictionary(block):
    dictionary = {}
    with open(block.name, 'r') as disk_block:
        block_content = disk_block.readlines()
        for line in block_content:
            m = re.search(BLOCK_ENTRY_PATTERN, line)
            if m is not None:
                dictionary[m.group(1)] = [eval(value) for value in m.group(2).split(';')]
        
    return dictionary

def intersect(posting_list_one, posting_list_two):

    if len(posting_list_one) < len(posting_list_two): 
        shortest = posting_list_one
        longest = posting_list_two
    else: 
        shortest = posting_list_two
        longest = posting_list_one

    intersection = []
    longest_iterator = iter(longest)
    shortest_iterator = iter(shortest)

    try:
        p1 = next(shortest_iterator)
        p2 = next(longest_iterator)
        p1_docID = int(p1[0])
        p2_docID = int(p2[0])
        while(True):
            if p1_docID == p2_docID:
                intersection.append(p1_docID)
                p1 = next(shortest_iterator)
                p2 = next(longest_iterator)
                p1_docID = int(p1[0])
                p2_docID = int(p2[0])
            elif p1_docID < p2_docID:
                p1 = next(shortest_iterator)
                p1_docID = int(p1[0])
            else:
                p2 = int(next(longest_iterator))
                p2_docID = int(p2[0])
    except StopIteration as identifier:
        pass

    return intersection

def merge_postings_lists(posting_list_one, posting_list_two):
    if len(posting_list_one) == 0:
        return posting_list_two
    
    if len(posting_list_two) == 0:
        return posting_list_one

    if len(posting_list_one) < len(posting_list_two):
        shortest_iterator = iter(posting_list_one)
        longest_iterator = iter(posting_list_two)
    else:
        shortest_iterator = iter(posting_list_two)
        longest_iterator = iter(posting_list_one)

    union = []

    try:
        p1 = next(shortest_iterator)
        p2 = next(longest_iterator)

        while True:
                
            if docID(p1) == docID(p2):
                union.append(p1)
                while(docID(p1) == docID(p2)):
                    p2 = next(longest_iterator)

                p1 = next(shortest_iterator)
            elif docID(p1) < docID(p2):
                union.append(p1)
                p1 = next(shortest_iterator)
                p2 = p2
            elif docID(p1) > docID(p2):
                union.append(p2)
                p2 = next(longest_iterator)
                p1 = p1
    except StopIteration:
        # Handles making sure that all postings from
        # both lists have been iterated through.
        if docID(union[-1]) == docID(p1):
            try:
                while True:
                    union.append(p2)
                    p2 = next(longest_iterator)
            except StopIteration as identifier:
                pass
        elif docID(union[-1]) == docID(p2):
            try:
                while True:
                    union.append(p1)
                    p1 = next(shortest_iterator)
            except StopIteration:
                pass
        else:
            # By the design of the algorithm we only append
            # one posting from either list hence both list
            # could not be completely iterated through at
            # the same time.
            raise SystemError()
    return union

def docID(posting):
    return int(posting[0])

def tf(posting):
    return int(posting[1])

def BM25(sum_idfs, tf_td, L_d, L_ave, k_1, b):
    """[summary]
    
    Arguments:
        idfs {[type]} -- Inverse document frequencies of each terms in the query
        tf_td {int} -- Term frequency of the term t in document d
        L_d {int} -- Length of the document d
        L_ave {int} -- Average length of document from collection
        k_1 {int} -- Fine tuning parameter
        b {numeric} -- Determines the scaling by document length 0 <= b <= 1
    
    Returns:
        [type] -- [description]
    """
    return sum_idfs*(((k_1 + 1) * tf_td) / (k_1 * ((1 - b) + b * (L_d/L_ave)) + tf_td))