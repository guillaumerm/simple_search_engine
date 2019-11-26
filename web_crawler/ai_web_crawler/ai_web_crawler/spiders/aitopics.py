# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
import json
import re
from collections import Counter

class AitopicsSpider(scrapy.Spider):
    name = 'aitopics'
    allowed_domains = ['aitopics.org']
    start_urls = ['https://aitopics.org/search?filters=store:%23artificialintelligence']
    page = 0
    number = 1
    concept_tags = Counter()

    def parse(self, response):
        AitopicsSpider.page += 1
        self.tags = set()

        link_extractor = LinkExtractor(allow=('https://aitopics.org/doc/news:.*/concept-tags-cloud'), allow_domains=self.allowed_domains, unique=True, strip=True)
        
        # Extracts tags
        for link in link_extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse_tags)

        # Proceed on next page
        yield scrapy.Request(AitopicsSpider.start_urls[0] + '&start=' + str(AitopicsSpider.page*10), callback=self.parse)

    def parse_tags(self, response):
        AitopicsSpider.number += 1
        tags = json.loads(re.search('\[.*\]', response.xpath('//div/script/text()')[0].get()).group(0))
        with open('../aitopics/' + str(AitopicsSpider.number), 'w') as file:
            file.write(' '.join(tag['concept-tag'] for tag in tags))
            file.flush()


        
