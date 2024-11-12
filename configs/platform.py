class PlatformConfig:
    def __init__(self, config_dict: dict = None) -> None:
        if config_dict is not None:
            self.path = config_dict.get('path')
            self.server = config_dict.get('server')
            self.login = config_dict.get('login')
            self.password = config_dict.get('password')

    def set_path(self, path):
        self.path = path
        return self

    def get_path(self):
        return self.path

    def set_server(self, server):
        self.server = server
        return self

    def get_server(self):
        return self.server

    def set_login(self, login):
        self.login = login
        return self

    def get_login(self):
        return self.login

    def set_password(self, password):
        self.password = password
        return self

    def get_password(self):
        return self.password
