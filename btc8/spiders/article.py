import re
import logging
from urllib.parse import urljoin
from decimal import Decimal
from scrapy.spiders import CrawlSpider
from scrapy_splash import SplashRequest
from btc8.items import Btc8ArticleItem
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalbitcoinsSpider(CrawlSpider):
    name = "btc8"
    allowed_domains = ["8btc.com"]
    start_urls = [
        'https://www.8btc.com/sitemap?page=1',
    ]
    visited_urls = []

    def parse(self, response):
        if response.url not in self.visited_urls:
            self.visited_urls.append(response.url)
            current_page = int(response.url.split("=")[-1])
            for ad_row in response.xpath('//ul[@class="bbt-list"]/li'):
                item = Btc8ArticleItem()
                url = ad_row.xpath('.//a/@href').extract_first()
                title = ad_row.xpath('.//a/text()').extract_first().strip()
                create_time = ad_row.xpath('.//a/span/text()').extract_first().strip()
                item["url"] = 'https://www.8btc.com' + url
                item["title"] = title
                item["create_time"] = create_time
                # yield item
                yield self._create_article_request('https://www.8btc.com' + url, item)

            not_more = response.xpath('//*[@id="app"]/div[2]/div/div/div/div/button[2][@disabled="disabled"]')
            if not not_more:
                page = current_page + 1
                yield response.follow("https://www.8btc.com/sitemap?page="+str(page), callback=self.parse)

    def _create_article_request(self, article_url, item):
        return SplashRequest(article_url, self._parse_profile,
                             meta={'item': item, 'article_url': article_url},
                             args={'timeout': 90}
                             )

    def _parse_profile(self, response):
        item = response.meta['item']
        if not response.body:
            logger.info('Reload the page again: {}'.format(response.meta['article_url']))
            article_url = response.meta['article_url']
            yield self._create_article_request(article_url, item)
            return

        item['text'] = response.xpath('//div[@class="bbt-html"]/text()').extract()
        yield item

