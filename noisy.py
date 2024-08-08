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

'''

infoabt = ''' 

      \033[95m****************************\033[0m
      \033[96m github.com/noarche/Noisy   \033[0m
      \033[94m    Traffic Obfuscation     \033[0m
      \033[95m****************************\033[0m
     \033[96m Build Date: August 6 2024 \033[0m
 \033[34m use no arguements for the default config\033[0m
 \033[31m Available arguments for other configs:\033[0m
 \033[32m config configHighBandwidth.json\033[0m
 \033[32m config configLowBandwidth.json\033[0m
 \033[32m config configLowBandwidthFast.json\033[0m

 \033[34m Visit the github for more information.\033[0m

'''


print(main_logo)

print(infoabt)

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
            response = requests.get(url, headers=headers, timeout=3)
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

    @staticmethod
    def _contains_unwanted_strings(url):
        unwanted_strings = ['.ico', '.png', '.jpg', '.webp', '.webm', '.pdf', '.doc', '.docx', '.svg', '.jpeg', '.json', '.onion', '.i2p', '.safetensors', '.rar', '.zip', '.gguf', '.ggml', '.shp', '.gif', '.avi', '.mp3', '.wav', '.mkv', '.mp4', '.m4a', '.flac', '.ogg', '.opus', '.avif', '.hc', '.tc', '.xyz', '.exe', '.msi', '.tar', '.7z', '.tif', '.css', '.csv']
        return any(unwanted_string in url.lower() for unwanted_string in unwanted_strings)

    def _is_blacklisted(self, url):
        return any(blacklisted_url in url for blacklisted_url in self._config["blacklisted_urls"])

    def _should_accept_url(self, url):
        return (
            url 
            and self._is_valid_url(url) 
            and not self._is_blacklisted(url) 
            and not self._contains_unwanted_strings(url)
        )

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
                self.save_links(sub_links)  # Save the found links to a file
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
                else:
                    time.sleep(SYS_RANDOM.randrange(self._config["min_sleep"], self._config["max_sleep"]))
            except (requests.exceptions.RequestException, LocationParseError):
                logging.error(f"\033[91mInvalid URL: {url}\033[0m")
                continue

    def save_links(self, links):
        with open('output_links.txt', 'a') as file:
            for link in links:
                file.write(link + '\n')

def print_bandwidth_usage():
    global total_bandwidth
    print(f"\033[34mTotal Bandwidth Used: {total_bandwidth / (1024 * 1024):.2f} MB\033[0m", end='\r')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="?", help="Path to a configuration file")
    args = parser.parse_args()

    crawler = Crawler()
    if args.config:
        crawler.load_config_file(args.config)
    else:
        with open("config.json", "r") as default_config_file:
            default_config = json.load(default_config_file)
            crawler.set_config(default_config)
    crawler.crawl()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()


