import argparse
import datetime
import json
import logging
import random
import re
import time
import os
from urllib.parse import urljoin, urlparse
import requests
from fake_useragent import UserAgent
from urllib3.exceptions import LocationParseError

UA = UserAgent(min_percentage=15.1)
REQUEST_COUNTER = -1
SYS_RANDOM = random.SystemRandom()


total_bandwidth = 0

main_logo = '''

                                                              
\033[92m  ░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓███████▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m
\033[92m  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \033[0m
\033[92m  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \033[0m
\033[92m  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓██████▓▒░ ░▒▓██████▓▒░  \033[0m
\033[92m  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░     \033[0m
\033[92m  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░     \033[0m
\033[92m  ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░▒▓███████▓▒░   ░▒▓█▓▒░     \033[0m

                                                          
      \033[95m****************************\033[0m
      \033[96m github.com/noarche/Noisy   \033[0m
      \033[94m    Traffic Obfuscation     \033[0m
      \033[95m****************************\033[0m

\033[94m Visit the github for more information. \033[0m

'''
print(main_logo)
class Crawler:
    def __init__(self):
        self._config = {}
        self._links = []
        self._start_time = None

    class CrawlerTimedOut(Exception):
        pass

    @staticmethod
    def _request(url):
        global total_bandwidth
        random_user_agent = UA.random
        headers = {"user-agent": random_user_agent}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response:
                total_bandwidth += len(response.content)
                print_bandwidth_usage()
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"\033[91mRequest failed: {e}\033[0m")
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
        return any(blacklisted_url in url for blacklisted_url in self._config["blacklisted_urls"])

    def _should_accept_url(self, url):
        return url and self._is_valid_url(url) and not self._is_blacklisted(url)

    def _extract_urls(self, body, root_url):
        pattern = r"href=[\"'](?!#)(.*?)[\"'].*?"
        urls = re.findall(pattern, str(body))
        normalize_urls = [self._normalize_link(url, root_url) for url in urls]
        return list(filter(self._should_accept_url, normalize_urls))

    def _remove_and_blacklist(self, link):
        self._config["blacklisted_urls"].append(link)
        del self._links[self._links.index(link)]

    def _browse_from_links(self, depth=0):
        max_depth = SYS_RANDOM.randint(1, self._config["max_depth"])
        is_depth_reached = depth >= max_depth
        if not self._links or is_depth_reached:
            logging.debug("Hit a dead end, moving to the next root URL")
            return
        if self._is_timeout_reached():
            raise self.CrawlerTimedOut
        random_link = SYS_RANDOM.choice(self._links)
        try:
            logging.info("\033[96mVisiting {}\033[0m".format(random_link))
            response = self._request(random_link)
            if response:
                sub_page = response.content
                sub_links = self._extract_urls(sub_page, random_link)
                time.sleep(SYS_RANDOM.randrange(self._config["min_sleep"], self._config["max_sleep"]))
                if len(sub_links) > 1:
                    self._links = self._extract_urls(sub_page, random_link)
                else:
                    self._remove_and_blacklist(random_link)
        except (requests.exceptions.RequestException, UnicodeDecodeError):
            logging.debug("Exception on URL: {}, removing from list and trying again!".format(random_link))
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
        is_timeout_set = self._config["timeout"] is not False
        end_time = self._start_time + datetime.timedelta(seconds=self._config["timeout"])
        is_timed_out = datetime.datetime.now() >= end_time
        return is_timeout_set and is_timed_out

    def crawl(self):
        self._start_time = datetime.datetime.now()
        while True:
            url = SYS_RANDOM.choice(self._config["root_urls"])
            try:
                response = self._request(url)
                if response:
                    body = response.content
                    self._links = self._extract_urls(body, url)
                    logging.debug("found {} links".format(len(self._links)))
                    self._browse_from_links()
            except (requests.exceptions.RequestException, UnicodeDecodeError):
                logging.warning("\033[95mError connecting to root url: {}\033[0m".format(url))
            except MemoryError:
                logging.warning("\033[91mError: content at url: {} is exhausting the memory\033[0m".format(url))
            except LocationParseError:
                logging.warning("\033[93mError encountered during parsing of: {}\033[0m".format(url))
            except self.CrawlerTimedOut:
                logging.info("\033[91mTimeout has exceeded, exiting")
                return

def print_bandwidth_usage():
    global total_bandwidth
    # Convert bytes to megabytes
    mb_used = total_bandwidth / (1024 * 1024)
    # Print the total bandwidth used, overwriting the previous line
    print(f"\r\033[32mTotal Bandwidth Used:\033[0m \033[93m{mb_used:.2f}\033[0m \033[32mMB\033[0m", end="", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", metavar="-l", type=str, help="logging level", default="info")
    parser.add_argument("--config", metavar="-c", type=str, help="config file")
    parser.add_argument("--timeout", metavar="-t", type=int, help="for how long the crawler should be running, in seconds", default=False)
    parser.add_argument("--min_sleep", metavar="-min", type=int, help="Minimum sleep before clicking another link.")
    parser.add_argument("--max_sleep", metavar="-max", type=int, help="Maximum sleep before clicking another link.")
    args = parser.parse_args()

    level = getattr(logging, args.log.upper())
    logging.basicConfig(level=level)

    crawler = Crawler()

    config_file = args.config if args.config else os.path.join(os.path.dirname(__file__), 'config.json')
    
    try:
        crawler.load_config_file(config_file)
    except FileNotFoundError:
        logging.error("Config file not found: {}".format(config_file))
        return

    if args.timeout:
        crawler.set_option("timeout", args.timeout)
    if args.min_sleep:
        crawler.set_option("min_sleep", args.min_sleep)
    if args.max_sleep:
        crawler.set_option("max_sleep", args.max_sleep)
    crawler.crawl()

if __name__ == "__main__":
    main()
