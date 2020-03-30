from core import *
import discord


class Bot(discord.Client):
    command_dictionary = {}
    initialization_sequence = []
    on_ready_sequence = []

    def __init__(self, data_path):
        initialize_log(data_path)
        super().__init__()

        self.data_path = data_path
        self.config_path = self.data_path + '\\config.txt'
        self.config_variables = {}
        self.load_config()

        # Register Default Config Values if they don't exist
        self.register_config_variable('prefix', 'a!')
        self.register_config_variable('user_perm_int', 0)
        self.register_config_variable('mod_perm_int', 8192)
        self.register_config_variable('admin_perm_int', 8)

        for func in Bot.initialization_sequence:
            func(self)

        log("[Bot] Class constructed.")

    async def on_ready(self):
        for func in Bot.on_ready_sequence:
            func(self)

        log("[Bot] Bot is now ready.")

    async def on_message(self, message):
        if message.content.startswith(self.value('prefix')) and message.author != self.user:
            # TODO: implement permissions checking
            log(f"[{str(message.author)}] {message.content}")

            content = message.content[len(self.value('prefix')):]
            try:
                command, argument = content.split(' ', 1)
            except ValueError:
                command = content
                argument = ''

            try:
                permission = Bot.command_dictionary[command].permission.value
                check = ['user_perm_int', 'mod_perm_int', 'admin_perm_int'][permission - 1]
                if message.author.guild_permissions.is_superset(discord.Permissions(self.value(check))):
                    await Bot.command_dictionary[command](self, message, argument)
                else:
                    log(f"[Bot] {message.author.name} has insufficient perms to execute {command}")
            except KeyError:
                # Invalid Command
                pass

    def value(self, name):
        return self.config_variables[name]

    def register_config_variable(self, name, value, overwrite=False):
        if name not in self.config_variables or overwrite:
            self.config_variables[name] = value
            self.save_config()

    def load_config(self):
        # TODO: refactor function to allow ignoring saved configuration (would also stop saving of config)
        if not os.path.exists(self.config_path):
            log("[Bot] No config file found, generating a default.")
            open(self.config_path, 'w').close()
        else:
            with open(self.config_path) as config:
                data = config.read()
                try:
                    self.config_variables.update(eval(data))
                except SyntaxError:
                    log("[Bot] Could not read configuration file, falling back to default configs.")
        self.save_config()

    def save_config(self):
        with open(self.config_path, 'w') as config:
            config.write(str(self.config_variables))
            config.flush()

    @staticmethod
    def register_command(func):
        if 'permission' not in dir(func):
            func = level_user(func)
        Bot.command_dictionary[func.__name__] = func

        # log(f"[Bot] Registered function {func.__name__}")
        # TODO: refactor log process if possible to be available at this point

    @staticmethod
    def queue_init(func):
        Bot.initialization_sequence.append(func)

    @staticmethod
    def queue_on_ready(func):
        Bot.on_ready_sequence.append(func)
