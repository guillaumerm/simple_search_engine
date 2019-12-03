from SearchEngine import SearchEngine
from Query import Query
import pickle

# ai_index_documents_length = eval(open('../indices/AIindex/documents_length.txt').read())
# AIindex = SearchEngine([open('../indices/AIindex/BLOCK262'), open('../indices/AIindex/BLOCK263'), open('../indices/AIindex/BLOCK264'), open('../indices/AIindex/BLOCK265')], ai_index_documents_length)
# document_frequencies = AIindex.document_frequencies()

# with open('../indices/AIindex/document_frequencies.txt', 'w') as file:
#     file.write(str(document_frequencies))

document_frequencies = eval(open('../indices/AIindex/document_frequencies.txt').read())

concordia_ai_documents_length = eval(open('../indices/ConcordiaAI/documents_length.txt').read())
ConcordiaAI = SearchEngine([open('../indices/ConcordiaAI/BLOCK119'), open('../indices/ConcordiaAI/BLOCK120'), open('../indices/ConcordiaAI/BLOCK121'), open('../indices/ConcordiaAI/BLOCK122'), open('../indices/ConcordiaAI/BLOCK123')], concordia_ai_documents_length)

while True:
    try:
        k = int(input('Enter number of returns:'))
        query = Query(input('Enter query:'))
    except Exception as ex:
        print(ex.args[0])
        continue
    results = ConcordiaAI.search(query, document_frequencies, k)
    print('-----BM25 Ranking-----\n')
    print(results[0])
    print('-----BM25 Ranking with AITopics Document Frequencies-----\n')
    print(results[2])
    print('\n-----Tf-idf Ranking-----\n')
    print(results[1])
    print('\n-----Tf-idf Ranking with AITopics Document Frequencies-----\n')
    print(results[3])