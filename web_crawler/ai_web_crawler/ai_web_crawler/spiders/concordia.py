# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.linkextractors import LinkExtractor


class ConcordiaSpider(scrapy.Spider):
    name = 'concordia'
    allowed_domains = ['concordia.ca']
    start_urls = ['https://www.concordia.ca/research.html']
    number = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def parse(self, response):
        ConcordiaSpider.number += 1

        # Get the main content of the website that is ignoring
        # the navigation bar and the footer
        main_content = response.xpath('//section[@id="content-main"]')
        
        # Large portion of text while be located in paragraphs
        paragraphs = main_content.xpath('//p//text()').getall()

        # Headings also contains text that is worth indexing
        headers = main_content.xpath('//h1//text()').getall()
        for i in range(2,7):
            headers.extend(main_content.xpath('//h'+str(i)+'//text()').getall())
        
        with open('../../corpora/concordia/' + str(ConcordiaSpider.number), 'w') as file:
            content = ' '.join(paragraphs).strip() + ' '.join(headers).strip()
            content = content.replace('\n', ' ')
            file.write(content)
            file.flush()

        with open('../../corpora/concordia/links/links', 'a') as file:
            file.write(str(ConcordiaSpider.number-1) + ':' + response.url + '\n')
            file.flush()

        # Make sure to extract only text from important pages
        link_extractor = LinkExtractor(
            allow=('.*news.*', '.*research.*', '.*next-gen.*'), 
            deny=('.*/lifestyle-addiction/tools/scientific-monitoring.html.*'), 
            allow_domains=self.allowed_domains, 
            unique=True, 
            strip=True
        )
        
        # Check before extracting the links
        for link in link_extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse)

    