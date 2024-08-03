import argparse
import datetime
import json
import logging
import random
import re
import time
from urllib.parse import urljoin, urlparse
import requests
from fake_useragent import UserAgent
from urllib3.exceptions import LocationParseError

UA = UserAgent(min_percentage=15.1)
REQUEST_COUNTER = -1
SYS_RANDOM = random.SystemRandom()

class Crawler:
    def __init__(self):
        self._config = {}
        self._links = []
        self._start_time = None

    class CrawlerTimedOut(Exception):
        pass

    @staticmethod
    def _request(url):
        random_user_agent = UA.random
        headers = {"user-agent": random_user_agent}
        try:
            return requests.get(url, headers=headers, timeout=5)
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

    @staticmethod
    def _normalize_link(link, root_url):
        try:
            parsed_url = urlparse(link)
        except ValueError:
            return None
        parsed_root_url = urlparse(root_url)
        if link.startswith("//"):
            return "{}://{}{}".format(parsed_root_url.scheme, parsed_url.netloc, parsed_url.path)
        if not parsed_url.scheme:
            return urljoin(root_url, link)
        return link

    @staticmethod
    def _is_valid_url(url):
        regex = re.compile(
            r"^(?:http|ftp)s?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return re.match(regex, url) is not None

    def _is_blacklisted(self, url):
        return any(blacklisted_url in url for blacklisted_url in self._config.get("blacklisted_urls", []))

    def _should_accept_url(self, url):
        return url and self._is_valid_url(url) and not self._is_blacklisted(url)

    def _extract_urls(self, body, root_url):
        pattern = r"href=[\"'](?!#)(.*?)[\"'].*?"
        urls = re.findall(pattern, str(body))
        normalize_urls = [self._normalize_link(url, root_url) for url in urls]
        return list(filter(self._should_accept_url, normalize_urls))

    def _remove_and_blacklist(self, link):
        self._config.setdefault("blacklisted_urls", []).append(link)
        if link in self._links:
            self._links.remove(link)

    def _browse_from_links(self, depth=0):
        if depth >= self._config.get("max_depth", 0) or not self._links:
            logging.debug("Hit a dead end, moving to the next root URL")
            return
        if self._is_timeout_reached():
            raise self.CrawlerTimedOut

        random_link = SYS_RANDOM.choice(self._links)
        try:
            logging.info(f"Visiting {random_link}")
            response = self._request(random_link)
            if response is None:
                self._remove_and_blacklist(random_link)
                return

            sub_page = response.content
            sub_links = self._extract_urls(sub_page, random_link)

            time.sleep(SYS_RANDOM.uniform(self._config.get("min_sleep", 1), self._config.get("max_sleep", 3)))

            if len(sub_links) > 1:
                self._links.extend(sub_links)
            else:
                self._remove_and_blacklist(random_link)
        except (requests.exceptions.RequestException, UnicodeDecodeError) as e:
            logging.debug(f"Exception on URL: {random_link}, removing from list and trying again! Error: {e}")
            self._remove_and_blacklist(random_link)

        self._browse_from_links(depth + 1)

    def load_config_file(self, file_path):
        with open(file_path, "r") as config_file:
            config = json.load(config_file)
            self.set_config(config)

    def set_config(self, config):
        self._config = config

    def set_option(self, option, value):
        self._config[option] = value

    def _is_timeout_reached(self):
        timeout = self._config.get("timeout")
        if timeout is False:
            return False
        end_time = self._start_time + datetime.timedelta(seconds=timeout)
        return datetime.datetime.now() >= end_time

    def crawl(self):
        self._start_time = datetime.datetime.now()

        while True:
            url = SYS_RANDOM.choice(self._config.get("root_urls", []))
            try:
                response = self._request(url)
                if response is None:
                    continue

                body = response.content
                self._links = self._extract_urls(body, url)
                logging.debug(f"Found {len(self._links)} links")
                self._browse_from_links()
            except (requests.exceptions.RequestException, UnicodeDecodeError, MemoryError, LocationParseError) as e:
                logging.warning(f"Error processing URL {url}: {e}")
            except self.CrawlerTimedOut:
                logging.info("Timeout has been reached, exiting")
                return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=str, help="logging level", default="info")
    parser.add_argument("--config", type=str, required=True, help="config file")
    parser.add_argument("--timeout", type=int, help="for how long the crawler should be running, in seconds", default=False)
    parser.add_argument("--min_sleep", type=int, help="Minimum sleep before clicking another link.", default=1)
    parser.add_argument("--max_sleep", type=int, help="Maximum sleep before clicking another link.", default=3)
    args = parser.parse_args()

    level = getattr(logging, args.log.upper())
    logging.basicConfig(level=level)

    crawler = Crawler()
    crawler.load_config_file(args.config)

    if args.timeout:
        crawler.set_option("timeout", args.timeout)
    if args.min_sleep:
        crawler.set_option("min_sleep", args.min_sleep)
    if args.max_sleep:
        crawler.set_option("max_sleep", args.max_sleep)
    crawler.crawl()

if __name__ == "__main__":
    main()
