import argparse
import datetime
import json
import os
import random
import re
import time
import signal
from urllib.parse import urljoin, urlparse
import requests
from fake_useragent import UserAgent
from urllib3.exceptions import LocationParseError
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


main_logo = ''' 
      [91m_[0m[93m_[0m[92m_[0m           [96m_[0m[94m_[0m[95m_[0m                       [91m_[0m[93m_[0m[92m_[0m           [96m_[0m[94m_[0m[95m_[0m     
     [91m/[0m[93m\[0m[92m_[0m[96m_[0m[94m\[0m         [95m/[0m[91m\[0m  [93m\[0m          [92m_[0m[96m_[0m[94m_[0m        [95m/[0m[91m\[0m  [93m\[0m         [92m|[0m[96m\[0m[94m_[0m[95m_[0m[91m\[0m    
    [93m/[0m[92m:[0m[96m:[0m[94m|[0m  [95m|[0m       [91m/[0m[93m:[0m[92m:[0m[96m\[0m  [94m\[0m        [95m/[0m[91m\[0m  [93m\[0m      [92m/[0m[96m:[0m[94m:[0m[95m\[0m  [91m\[0m        [93m|[0m[92m:[0m[96m|[0m  [94m|[0m   
   [95m/[0m[91m:[0m[93m|[0m[92m:[0m[96m|[0m  [94m|[0m      [95m/[0m[91m:[0m[93m/[0m[92m\[0m[96m:[0m[94m\[0m  [95m\[0m       [91m\[0m[93m:[0m[92m\[0m  [96m\[0m    [94m/[0m[95m:[0m[91m/[0m[93m\[0m [92m\[0m  [96m\[0m       [94m|[0m[95m:[0m[91m|[0m  [93m|[0m   
  [92m/[0m[96m:[0m[94m/[0m[95m|[0m[91m:[0m[93m|[0m  [92m|[0m[96m_[0m[94m_[0m   [95m/[0m[91m:[0m[93m/[0m  [92m\[0m[96m:[0m[94m\[0m  [95m\[0m      [91m/[0m[93m:[0m[92m:[0m[96m\[0m[94m_[0m[95m_[0m[91m\[0m  [93m_[0m[92m\[0m[96m:[0m[94m\[0m[95m~[0m[91m\[0m [93m\[0m  [92m\[0m      [96m|[0m[94m:[0m[95m|[0m[91m_[0m[93m_[0m[92m|[0m[96m_[0m[94m_[0m 
 [95m/[0m[91m:[0m[93m/[0m [92m|[0m[96m:[0m[94m|[0m [95m/[0m[91m\[0m[93m_[0m[92m_[0m[96m\[0m [94m/[0m[95m:[0m[91m/[0m[93m_[0m[92m_[0m[96m/[0m [94m\[0m[95m:[0m[91m\[0m[93m_[0m[92m_[0m[96m\[0m  [94m_[0m[95m_[0m[91m/[0m[93m:[0m[92m/[0m[96m\[0m[94m/[0m[95m_[0m[91m_[0m[93m/[0m [92m/[0m[96m\[0m [94m\[0m[95m:[0m[91m\[0m [93m\[0m [92m\[0m[96m_[0m[94m_[0m[95m\[0m     [91m/[0m[93m:[0m[92m:[0m[96m:[0m[94m:[0m[95m\[0m[91m_[0m[93m_[0m[92m\[0m
 [96m\[0m[94m/[0m[95m_[0m[91m_[0m[93m|[0m[92m:[0m[96m|[0m[94m/[0m[95m:[0m[91m/[0m  [93m/[0m [92m\[0m[96m:[0m[94m\[0m  [95m\[0m [91m/[0m[93m:[0m[92m/[0m  [96m/[0m [94m/[0m[95m\[0m[91m/[0m[93m:[0m[92m/[0m  [96m/[0m    [94m\[0m[95m:[0m[91m\[0m [93m\[0m[92m:[0m[96m\[0m [94m\[0m[95m/[0m[91m_[0m[93m_[0m[92m/[0m    [96m/[0m[94m:[0m[95m/[0m[91m~[0m[93m~[0m[92m/[0m[96m~[0m   
     [94m|[0m[95m:[0m[91m/[0m[93m:[0m[92m/[0m  [96m/[0m   [94m\[0m[95m:[0m[91m\[0m  [93m/[0m[92m:[0m[96m/[0m  [94m/[0m  [95m\[0m[91m:[0m[93m:[0m[92m/[0m[96m_[0m[94m_[0m[95m/[0m      [91m\[0m[93m:[0m[92m\[0m [96m\[0m[94m:[0m[95m\[0m[91m_[0m[93m_[0m[92m\[0m     [96m/[0m[94m:[0m[95m/[0m  [91m/[0m     
     [93m|[0m[92m:[0m[96m:[0m[94m/[0m  [95m/[0m     [91m\[0m[93m:[0m[92m\[0m[96m/[0m[94m:[0m[95m/[0m  [91m/[0m    [93m\[0m[92m:[0m[96m\[0m[94m_[0m[95m_[0m[91m\[0m       [93m\[0m[92m:[0m[96m\[0m[94m/[0m[95m:[0m[91m/[0m  [93m/[0m     [92m\[0m[96m/[0m[94m_[0m[95m_[0m[91m/[0m      
     [93m/[0m[92m:[0m[96m/[0m  [94m/[0m       [95m\[0m[91m:[0m[93m:[0m[92m/[0m  [96m/[0m      [94m\[0m[95m/[0m[91m_[0m[93m_[0m[92m/[0m        [96m\[0m[94m:[0m[95m:[0m[91m/[0m  [93m/[0m                 
     [92m\[0m[96m/[0m[94m_[0m[95m_[0m[91m/[0m         [93m\[0m[92m/[0m[96m_[0m[94m_[0m[95m/[0m                     [91m\[0m[93m/[0m[92m_[0m[96m_[0m[94m/[0m                  
'''
infoabt = ''' 
\033[95m  ****************************\033[0m
\033[96m   github.com/noarche/Noisy   \033[0m
\033[94m      [91mT[0m[93mr[0m[92ma[0m[96mf[0m[94mf[0m[95mi[0m[91mc[0m [93mO[0m[92mb[0m[96mf[0m[94mu[0m[95ms[0m[91mc[0m[93ma[0m[92mt[0m[96mi[0m[94mo[0m[95mn[0m    \033[0m
\033[95m  ****************************\033[0m
\033[96m   Build Date: [91mA[0m[93mu[0m[92mg[0m[96mu[0m[94ms[0m[95mt[0m [91m1[0m[93m0[0m [92m2[0m[96m0[0m[94m2[0m[95m4[0m
 [91mS[0m[93me[0m[92ml[0m[96me[0m[94mc[0m[95mt[0m [91mt[0m[93mh[0m[92me[0m [96mc[0m[94mo[0m[95mn[0m[91mf[0m[93mi[0m[92mg[0m [96my[0m[94mo[0m[95mu[0m [91mw[0m[93ma[0m[92mn[0m[96mt[0m [94mt[0m[95mo[0m [91mr[0m[93mu[0m[92mn[0m[96m,[0m [94mE[0m[95ma[0m[91ms[0m[93my[0m [92mt[0m[96mo[0m [94mb[0m[95ml[0m[91me[0m[93mn[0m[92md[0m [96mi[0m[94ms[0m [95mb[0m[91me[0m[93ms[0m[92mt[0m[96m.[0m [94mA[0m[95ml[0m[91ml[0m [93mo[0m[92mt[0m[96mh[0m[94me[0m[95mr[0m [91mq[0m[93mu[0m[92me[0m[96ms[0m[94mt[0m[95mi[0m[91mo[0m[93mn[0m[92ms[0m
[96ma[0m[94mr[0m[95me[0m [91mo[0m[93mp[0m[92mt[0m[96mi[0m[94mo[0m[95mn[0m[91ma[0m[93ml[0m [92mt[0m[96mo[0m [94mc[0m[95mu[0m[91ms[0m[93mt[0m[92mo[0m[96mm[0m[94mi[0m[95mz[0m[91me[0m [93my[0m[92mo[0m[96mu[0m[94mr[0m [95me[0m[91mx[0m[93mp[0m[92me[0m[96mr[0m[94mi[0m[95me[0m[91mn[0m[93mc[0m[92me[0m [96m&[0m [94mO[0m[95mK[0m [91mt[0m[93mo[0m [92ms[0m[96mk[0m[94mi[0m[95mp[0m [91mi[0m[93mf[0m [92mu[0m[96mn[0m[94ms[0m[95mu[0m[91mr[0m[93me[0m[92m.[0m
 \033[36m   To filter links enter string to filter. Not reccomended. Leave blank to continue.\033[0m
  \033[32m   Domain Only? Not recomended. Leave blank to continue.\033[0m
 \033[32m   Enter minimum time to wait. fast is 0 (reccomended: 0)\033[0m
 \033[32m   Enter maximum time to wait. fast is 1 (reccomended: 4)\033[0m
 \033[92m   A random number between these two numbers will be used.\033[0m
 \033[96m   Enter depth, the number of links to visit on that domain before switching. A random number between 0 and your input will be used each time. Leave blank to continue.\033[0m
'''


print(main_logo)

print(infoabt)

UA = UserAgent(min_percentage=15.1)
REQUEST_COUNTER = -1
SYS_RANDOM = random.SystemRandom()

total_bandwidth = 0
visited_responsive_urls = 0

def handle_interrupt(signum, frame):
    print(f"\n{Fore.RED}Process interrupted by user! Returning to main menu...{Style.RESET_ALL}")
    main()

def exit_script(signum, frame):
    print(f"\n{Fore.RED}Exiting the script.{Style.RESET_ALL}")
    exit(0)

class Crawler:
    def __init__(self):
        self._config = {}
        self._links = []
        self._start_time = None
        self._visit_counter = 0
        self._valid_string = None
        self._blacklist = set()
        self._domain_only = False

    def set_valid_string(self, valid_string):
        self._valid_string = valid_string

    def set_domain_only(self, domain_only):
        self._domain_only = domain_only

    def _filter_links(self):
        if self._valid_string:
            self._links = [link for link in self._links if self._valid_string in link]

        if self._domain_only:
            self._links = list(set(self._links))  # Remove duplicates
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
        global total_bandwidth, visited_responsive_urls
        random_user_agent = UA.random
        headers = {"user-agent": random_user_agent}
        try:
            response = requests.get(url, headers=headers, timeout=4)
            if response:
                content_length = len(response.content)
                total_bandwidth += content_length
                visited_responsive_urls += 1
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
    print(f"{Fore.GREEN}[91mR[0m[93me[0m[92ms[0m[96mp[0m[94mo[0m[95mn[0m[91ms[0m[93mi[0m[92mv[0m[96me[0m [94mL[0m[95mi[0m[91mn[0m[93mk[0m: {url}{Style.RESET_ALL}")

def print_bandwidth_usage(content_length=0):
    global total_bandwidth, visited_responsive_urls
    total_bandwidth += content_length
    print(f"{Fore.MAGENTA}[91mT[0m[93mo[0m[92mt[0m[96ma[0m[94ml[0m [95mB[0m[91ma[0m[93mn[0m[92md[0m[96mw[0m[94mi[0m[95md[0m[91mt[0m[93mh[0m [92mU[0m[96ms[0m[94me[0m[95md[0m: {total_bandwidth / (1024 * 1024):.2f} MB | [91mR[0m[93me[0m[92ms[0m[96mp[0m[94mo[0m[95mn[0m[91ms[0m[93mi[0m[92mv[0m[96me[0m [94mU[0m[95mR[0m[91mL[0m[93ms[0m [92mV[0m[96mi[0m[94ms[0m[95mi[0m[91mt[0m[93me[0m[92md[0m: {visited_responsive_urls}{Style.RESET_ALL}", end='\r')

def load_configs():
    config_dir = 'configs'
    configs = [f for f in os.listdir(config_dir) if f.endswith('.json')]
    print(f"{Fore.YELLOW}[91mA[0m[93mv[0m[92ma[0m[96mi[0m[94ml[0m[95ma[0m[91mb[0m[93ml[0m[92me[0m [96mC[0m[94mo[0m[95mn[0m[91mf[0m[93mi[0m[92mg[0m[96mu[0m[94mr[0m[95ma[0m[91mt[0m[93mi[0m[92mo[0m[96mn[0m[94ms[0m:{Style.RESET_ALL}")
    for i, config in enumerate(configs):
        print(f"{Fore.CYAN}{i + 1}. {config}{Style.RESET_ALL}")
    return configs

def main():
    signal.signal(signal.SIGINT, exit_script)
    
    configs = load_configs()
    if not configs:
        print(f"{Fore.RED}No configuration files found in 'configs' directory.{Style.RESET_ALL}")
        return

    config_choice = input(f"{Fore.BLUE}Choose a configuration by number:{Style.RESET_ALL} ").strip()
    try:
        config_choice = int(config_choice) - 1
        if 0 <= config_choice < len(configs):
            selected_config = configs[config_choice]
        else:
            print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
            return
    except ValueError:
        print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")
        return

    config_path = os.path.join('configs', selected_config)
    crawler = Crawler()
    crawler.load_config_file(config_path)

    valid_string = input(f"{Fore.RED}Enter a valid string (e.g., .gov, .edu, .net) or leave blank to skip:{Style.RESET_ALL} ").strip()
    if valid_string:
        crawler.set_valid_string(valid_string)

    domain_only = input(f"{Fore.RED}Domain only mode? (0 for no, 1 for yes, default is no):{Style.RESET_ALL} ").strip()
    if domain_only == "1":
        crawler.set_domain_only(True)

    min_sleep = input(f"{Fore.GREEN}Enter min sleep time in seconds or leave blank to continue:{Style.RESET_ALL} ").strip()
    max_sleep = input(f"{Fore.GREEN}Enter max sleep time in seconds or leave blank to continue:{Style.RESET_ALL} ").strip()

    if min_sleep.isdigit() and max_sleep.isdigit():
        crawler.set_option("min_sleep", int(min_sleep))
        crawler.set_option("max_sleep", int(max_sleep))

    depth = input(f"{Fore.GREEN}Enter the maximum depth of hits:{Style.RESET_ALL} ").strip()
    if depth.isdigit():
        crawler.set_option("max_depth", int(depth))

    signal.signal(signal.SIGINT, handle_interrupt)
    crawler.crawl()

if __name__ == "__main__":
    main()
