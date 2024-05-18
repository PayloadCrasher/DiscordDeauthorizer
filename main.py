import json
import ctypes
from threading import Thread
from datetime import datetime

import requests
from colorama import Fore, init
from concurrent.futures import ThreadPoolExecutor

init()

done = 0
success = 0
failure = 0
skipped = 0

class Console:
    @staticmethod
    def success(content: str):
        print(f'{Fore.LIGHTBLACK_EX}{datetime.now().strftime("%H:%M:%S")}{Fore.RESET} [{Fore.GREEN}+{Fore.RESET}] {content}')

    @staticmethod
    def failure(content: str):
        print(f'{Fore.LIGHTBLACK_EX}{datetime.now().strftime("%H:%M:%S")}{Fore.RESET} [{Fore.RED}!{Fore.RESET}] {content}')

class Cleaner:
    def __init__(self):
        self.config = json.load(open('config.json', 'r'))

    def title(self):
        global done, success, failure, skipped
        ctypes.windll.kernel32.SetConsoleTitleW(f"Done: {done} | Deauthorized: {success} | Failures: {failure} | Skipped: {skipped}")

    def headers(self, token: str) -> dict:
        return {
            'authority': 'discord.com',
            'accept': '*/*',
            'authorization': token,
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InVrLVVBIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTIyLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6Mjc1NTY1LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ==',
        }

    def fetch(self, token: str) -> dict:
        global done, success, failure, skipped
        response = requests.get('https://discord.com/api/v9/oauth2/tokens', headers=self.headers(token))
        if response.ok:
            apps = response.json()
            Console.success(f'Fetched {Fore.MAGENTA}{len(apps)}{Fore.RESET} app(s) for {Fore.MAGENTA}{token[:31]}***{Fore.RESET} token')
            return apps
        else:
            failure += 1
            self.title()
            Console.failure(f'Failed while getting authorized applications for {Fore.MAGENTA}{token[:31]}***{Fore.RESET} token -> {response.json()}')
            return None

    def deauthorize(self, token: str):
        global done, success, failure, skipped
        apps = self.fetch(token)
        if apps:
            a = 0
            for app in apps:
                if int(app['application']['id']) not in self.config['APPS_TO_IGNORE']:
                    response = requests.delete(f'https://discord.com/api/v9/oauth2/tokens/{app["id"]}', headers=self.headers(token))
                    if response.ok:
                        a += 1
                        success += 1
                        Console.success(f'Deauthorized the application {Fore.MAGENTA}{app["application"]["name"]}{Fore.RESET} ({Fore.MAGENTA}{app["id"]}{Fore.RESET}) for {Fore.MAGENTA}{token[:31]}***{Fore.RESET} token [{Fore.MAGENTA}{a}{Fore.RESET}/{Fore.MAGENTA}{len(apps)}{Fore.RESET}]')
                    else:
                        failure += 1
                        Console.failure(response.text)
                else:
                    skipped += 1
                    Console.success(f'Skipping {Fore.MAGENTA}{app["application"]["name"]}{Fore.RESET} ({Fore.MAGENTA}{app["id"]}{Fore.RESET}) for {Fore.MAGENTA}{token[:31]}***{Fore.RESET} token')
                self.title()
            done += 1
            self.title()

def start(token: str):
    cleaner_instance = Cleaner()
    thread = Thread(target=cleaner_instance.deauthorize, args=(token,))
    thread.start()
    thread.join()

if __name__ == '__main__':
    tokens = open("tokens.txt", "r").read().splitlines()
    config = json.load(open('config.json', 'r'))
    with ThreadPoolExecutor(max_workers=config['THREADS']) as executor:
        executor.map(start, tokens)
