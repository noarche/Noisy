import argparse
import datetime
import json
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
     \033[96m Build Date: August 8 2024 \033[0m
 \033[34m Skip arguments for the default config\033[0m
 \033[36m To filter links enter string to filter.\033[0m
 \033[32m Enter minimum time to wait.\033[0m
 \033[32m Enter maximum time to wait.\033[0m
 \033[92m A random number between these two numbers will be used.\033[0m

 \033[34m Visit the github for more information.\033[0m

'''


print(main_logo)

print(infoabt)


class Crawler:
    def __init__(self):
        self._config = {}
        self._links = []
        self._start_time = None
        self._visit_counter = 0  
        self._valid_string = None  
        self._blacklist = set()  

    def set_valid_string(self, valid_string):
        self._valid_string = valid_string

    def _filter_links(self):

        if self._valid_string:
            self._links = [link for link in self._links if self._valid_string in link]

    def _normalize_link(self, link, root_url):
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

    def _request(self, url):
        global total_bandwidth
        random_user_agent = UA.random
        headers = {"user-agent": random_user_agent}
        try:
            response = requests.get(url, headers=headers, timeout=4)
            if response:
                content_length = len(response.content)
                total_bandwidth += content_length
                print_responsive_link(url)
                print_bandwidth_usage(content_length)
            return response
        except requests.exceptions.RequestException:
            return None

    def _is_valid_url(self, url):

        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _is_blacklisted(self, url):
        return url in self._blacklist

    def _contains_unwanted_strings(self, url):
        unwanted_strings = ['.ico', '.png', '.jpg', '.webp', '.webm', '.pdf', '.doc', '.docx', '.svg', '.jpeg', '.json', '.onion', '.i2p', '.safetensors', '.rar', '.zip', '.gguf', '.ggml', '.shp', '.gif', '.avi', '.mp3', '.wav', '.mkv', '.mp4', '.m4a', '.flac', '.ogg', '.opus', '.avif', '.hc', '.tc', '.xyz', '.exe', '.msi', '.tar', '.7z', '.tif', '.css', '.csv']
        return any(unwanted_string in url for unwanted_string in unwanted_strings)

    def _remove_and_blacklist(self, url):
        self._blacklist.add(url)
        self._links = [link for link in self._links if link != url]

    def _should_accept_url(self, url):
        valid_string_condition = not self._valid_string or (self._valid_string and self._valid_string in url)
        return (
            url 
            and self._is_valid_url(url) 
            and not self._is_blacklisted(url) 
            and not self._contains_unwanted_strings(url)
            and valid_string_condition
        )

    def _extract_urls(self, body, root_url):
        pattern = r"href=[\"'](?!#)(.*?)[\"'].*?"
        urls = re.findall(pattern, str(body))
        normalize_urls = [self._normalize_link(url, root_url) for url in urls]
        return list(filter(self._should_accept_url, normalize_urls))

    def _browse_from_links(self, depth=0):
        max_depth = SYS_RANDOM.randint(1, self._config["max_depth"])
        is_depth_reached = depth >= max_depth
        if not self._links or is_depth_reached:
            return
        if self._is_timeout_reached():
            raise self.CrawlerTimedOut
        random_link = SYS_RANDOM.choice(self._links)
        try:
            response = self._request(random_link)
            if response:
                sub_page = response.content
                sub_links = self._extract_urls(sub_page, random_link)
                time.sleep(SYS_RANDOM.randrange(self._config["min_sleep"], self._config["max_sleep"]))
                if len(sub_links) > 1:
                    self._links = sub_links
                else:
                    self._remove_and_blacklist(random_link)
                self.save_links(sub_links)
                self._visit_counter += 1
                if self._visit_counter % 10 == 0:
                    self._filter_links()  
        except (requests.exceptions.RequestException, UnicodeDecodeError):
            self._remove_and_blacklist(random_link)
        self._browse_from_links(depth + 1)

    def load_config_file(self, file_path):
        with open(file_path, "r") as config_file:
            config = json.load(config_file)
            self.set_config(config)
        self._filter_links()  

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
                    self._browse_from_links()
                else:
                    time.sleep(SYS_RANDOM.randrange(self._config["min_sleep"], self._config["max_sleep"]))
            except (requests.exceptions.RequestException, LocationParseError):
                continue

    def save_links(self, links):
        with open('output_links.txt', 'a') as file:
            for link in links:
                file.write(link + '\n')

def print_responsive_link(url):
    print(f"\033[92mResponsive Link: {url}\033[0m")

def print_bandwidth_usage(content_length=0):
    global total_bandwidth
    total_bandwidth += content_length
    print(f"\033[95mTotal Bandwidth Used: {total_bandwidth / (1024 * 1024):.2f} MB\033[0m", end='\r')

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

    valid_string = input("\033[32mEnter a valid string (e.g., .gov, .edu, .net) or leave blank to skip:\033[0m ").strip()
    if valid_string:
        crawler.set_valid_string(valid_string)

    min_sleep = input("\033[32mEnter min sleep time in seconds or leave blank to continue:\033[0m ").strip()
    max_sleep = input("\033[32mEnter max sleep time in seconds or leave blank to continue:\033[0m ").strip()

    if min_sleep.isdigit() and max_sleep.isdigit():
        crawler.set_option("min_sleep", int(min_sleep))
        crawler.set_option("max_sleep", int(max_sleep))

    crawler.crawl()

if __name__ == "__main__":
    main()


