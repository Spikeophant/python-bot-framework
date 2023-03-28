import socket
import importlib
import os
import sys
import time
import json
from threading import Thread

# Read configuration from file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

NICKNAME = config['nickname']
PLUGINS_DIR = config['plugins_dir']
NETWORKS = config['networks']


class IRCBot:
    def __init__(self, networks, nickname, channels):
        self.networks = networks
        self.nickname = nickname
        self.plugins = []

    def load_plugins(self):
        sys.path.insert(0, os.path.abspath(PLUGINS_DIR))
        for plugin_file in os.listdir(PLUGINS_DIR):
            if plugin_file.endswith(".py") and plugin_file != "plugin.py":
                plugin_name = plugin_file[:-3]
                plugin_module = importlib.import_module(plugin_name)
                plugin_instance = plugin_module.Plugin()
                if isinstance(plugin_instance, Plugin):
                    # Pass the Last.fm API key to LastFMPlugin
                    if isinstance(plugin_instance, LastFMPlugin):
                        plugin_instance.api_key = self.lastfm_api_key
                    self.plugins.append(plugin_instance)

    def connect(self, network):
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect((network['server'], network['port']))
        irc.send(bytes(f"NICK {self.nickname}\r\n", "UTF-8"))
        irc.send(bytes(f"USER {self.nickname} 0 * :{self.nickname}\r\n", "UTF-8"))

        for channel in network['channels']:
            irc.send(bytes(f"JOIN {channel}\r\n", "UTF-8"))

        return irc

    def process_message(self, irc, network, msg):
        for plugin in self.plugins:
            response = plugin.handle_message(msg)
            if response:
                self.send_message(irc, network, response)

    def send_message(self, irc, network, msg):
        irc.send(bytes(f"PRIVMSG {network['channel']} :{msg}\r\n", "UTF-8"))

    def run(self):
        self.load_plugins()
        threads = []

        for network in self.networks:
            irc = self.connect(network)

            def irc_thread():
                while True:
                    msg = irc.recv(2048).decode("UTF-8")
                    if msg.find("PING :") != -1:
                        irc.send(bytes(f"PONG :{msg.split()[1]}\r\n", "UTF-8"))
                    else:
                        self.process_message(irc, network, msg)

            thread = Thread(target=irc_thread)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


if __name__ == "__main__":
    bot = IRCBot(NETWORKS, NICKNAME)
    bot.run()
