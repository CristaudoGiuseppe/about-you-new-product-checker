import requests, json, random, csv, time, threading
from threading import Thread, Lock
from datetime import datetime
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed

# "----------------------------------"
# @author Criss
# version = '0.0.1'
# "----------------------------------"

# NEXT VERSION
# - PROXY SUPPORT
# - CHECK IMAGE
# - CHECK STOCK
# - MIGLIORARE WEBHOOK

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def string_builder(string, type, id_task):
    if type == "success":
        return '['+str(datetime.now()).split(' ')[1]+'] [ABOUTYOUMONITOR] [' + str(id_task) + '] ' + bcolors.OKGREEN + string + bcolors.ENDC
    elif type == "warning":
        return '['+str(datetime.now()).split(' ')[1]+'] [ABOUTYOUMONITOR] [' + str(id_task) + '] ' +  bcolors.WARNING + string + bcolors.ENDC
    else:
        return '['+str(datetime.now()).split(' ')[1]+'] [ABOUTYOUMONITOR] [' + str(id_task) + '] ' + bcolors.FAIL + string + bcolors.ENDC

def load_proxies():

    proxies_vector = []

    with open("aboutyou/proxies.txt", 'r') as fp:
        all_proxies = fp.read().split('\n')

        if all_proxies == ['']:
            print(string_builder('No proxies found, running localhost..', 'warning', 1))
        else:
            for line in all_proxies:
                try:
                    proxy_parts = line.split(':')
                    ip, port, user, password = proxy_parts[0], proxy_parts[1], proxy_parts[2], proxy_parts[3]
                    tempProxy = {
                        'http': f'http://{user}:{password}@{ip}:{port}',
                        'https': f'http://{user}:{password}@{ip}:{port}'
                    }
                    proxies_vector.append(tempProxy)
                except:
                    pass

            print(string_builder('Loaded ' + str(len(proxies_vector)) + ' proxies.', 'warning', 1))
    
    return proxies_vector

def carica_pid_from_file():

    pid_vector = []

    with open('aboutyou/pid.csv', 'r') as csv_file:
        csv_key = csv.DictReader(csv_file)

        for line in csv_key:
            pid = line['PID']
            pid_vector.append(pid)
    return pid_vector

class monitor_aboutyou(Thread):

    writeMutex = Lock()
    webhookMutex = Lock()
    num_threads = 10
    keywors = ['nike', 'dunk']
    delay = 1
    webhook = "https://discord.com/api/webhooks/844976184676581387/1OKohtdX3sVZvqmVSHdNeUfYo4JywgeC0g3X9v-Hw_qtgirbsb3saFoGga13mwDFpTBp"

    headers = {
        'authority': 'www.aboutyou.it',
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'it-IT,it;q=0.9',
        'cache-control': 'max-age=0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    }

    found_pid = carica_pid_from_file()
    proxies_vector = load_proxies()

    def pick_proxy(self):
        index = random.randrange(len(monitor_aboutyou.proxies_vector))
        self.proxy_to_use = monitor_aboutyou.proxies_vector[index]
        self.session.proxies = self.proxy_to_use
        monitor_aboutyou.proxies_vector.remove(self.proxy_to_use)

    def __init__(self, id_thread):
        Thread.__init__(self)
        self.id_thread = id_thread
        self.session = requests.session()

    def write_csv(self, pid, link):
        monitor_aboutyou.writeMutex.acquire()
        with open('aboutyou/pid.csv', 'a', newline = '') as file:
            succesWriter = csv.writer(file)
            succesWriter.writerow([str(pid), str(link)])
        monitor_aboutyou.writeMutex.release()

    def check_keywords(self, link):
        words = link.split('-')
        for word in monitor_aboutyou.keywors:
            if word in words:
                print(string_builder('FOUND HYPE PRODUCT','success', self.id_thread))
                return True
        return False
    
    def send_webhook(self, pid, link):
        monitor_aboutyou.webhookMutex.acquire()
        embed = DiscordEmbed(title = 'NEW ABOUT YOU PRODUCT FOUND!', color = 808080)
        embed.add_embed_field(name = 'PID', value = str(pid), inline = False)
        embed.add_embed_field(name = 'LINK', value = str(link), inline = False)
        #inserire nome prodotto
        #inserire immagine

        embed.set_footer(text = 'COP HOUSE MONITOR')

        webhook = DiscordWebhook(url = monitor_aboutyou.webhook)
        webhook.add_embed(embed)

        try:
            #time.sleep(monitor_aboutyou.delay)
            webhook.execute()
            if (self.check_keywords(link)):
                content = "@everyone"
                everyone = DiscordWebhook(url = monitor_aboutyou.webhook, content = content)
                try:
                    everyone.execute()
                except:
                    time.sleep(monitor_aboutyou.delay)
                    everyone.execute()
        except:
            print(string_builder('WEBHOOK ERROR RETRYING', 'failed', self.id_thread))
            try:
                time.sleep(monitor_aboutyou.delay)
                webhook.execute()
                if (self.check_keywords(link)):
                    content = "@everyone"
                    everyone = DiscordWebhook(url = monitor_aboutyou.webhook, content = content)
                    try:
                        everyone.execute()
                    except:
                        time.sleep(monitor_aboutyou.delay)
                        everyone.execute()
            except:
                print(string_builder('WEBHOOK ERROR', 'failed', self.id_thread))

        monitor_aboutyou.webhookMutex.release()

    def complete_task(self, pid, link):
        self.write_csv(pid, link)
        self.send_webhook(pid, link)

    def find_product_info(self, link, pid):
        print("NEED TO BE IMPROVED")

    def check_pid(self, pid):
        if(str(pid) not in monitor_aboutyou.found_pid):
            temp_link = "https://www.aboutyou.it/p/nike-sb/sneaker-bassa-chron-" + str(pid)
            r = self.session.get(temp_link, headers = monitor_aboutyou.headers)
            if(r.status_code == 200):
                temp = str(r.text).split('"urlManager":')[1].split(',"disableSSR"')[0] + "}"
                tempJson = json.loads(str(temp))
                link = str(tempJson['href'])
                if(link != 'https://www.aboutyou.it/about/brand/nike-sb?npr=1'):
                    print(string_builder('SUCCESSFULLY GOT NEW PRODUCT','success', self.id_thread))
                    self.complete_task(pid, link)
                else:
                    print(string_builder('MISSING PID', 'warning', self.id_thread))
        else:
            print(string_builder('PID ALREADY SCRAPED', 'warning', self.id_thread))

    def run(self):
        #while true e controllo continuamente
        print(monitor_aboutyou.found_pid)
        for probPid in range(6676000, 6676999):
            self.check_pid(probPid)
            time.sleep(monitor_aboutyou.delay)


def main():
    t = monitor_aboutyou(1)
    t.start()

main()


""" temp = "https://www.aboutyou.cz/p/nike-sportswear/tenisky-nike-dunk-low-se-6676235"
WORDS = temp.split('-')
keywors = ['nike', 'dunk']
for word in keywors:
    if word in WORDS:
        print(True)
        break
print(False) """
