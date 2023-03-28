class Plugin:
    def __init__(self):
        self.commands = {}

    def handle_message(self, msg):
        for command, function in self.commands.items():
            if msg.find(f"PRIVMSG {CHANNEL} :{command}") != -1:
                return function()