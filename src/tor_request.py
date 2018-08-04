import requests
import os
from stem import SocketError
from stem.control import Controller
from stem.process import launch_tor_with_config

TOR_COMMAND = os.environ.get("TOR_CMD", r"C:\Users\Ron\Tor Browser\Browser\TorBrowser\Tor\tor.exe")


class TorRequest(object):
    def __init__(self,
                 proxy_port=9050,
                 ctrl_port=9051,
                 password=None):

        self.proxy_port = proxy_port
        self.ctrl_port = ctrl_port
        self._tor_proc = None

        self._refresh()

        self.ctrl = Controller.from_port(port=self.ctrl_port)
        self.ctrl.authenticate(password=password)

        self.session = requests.Session()
        self.session.proxies.update({
            'http': 'socks5h://localhost:%d' % self.proxy_port,
            'https:': 'socks5h://localhost:%d' % self.proxy_port,
        })

    def _tor_process_exists(self):
        try:
            ctrl = Controller.from_port(port=self.ctrl_port)
            ctrl.close()
            return True
        except SocketError:
            return False

    def _launch_tor(self):
        return launch_tor_with_config(tor_cmd=TOR_COMMAND, config={
            'SocksPort': str(self.proxy_port),
            'ControlPort': str(self.ctrl_port)
        }, take_ownership=True)

    def close(self):
        self.session.close()
        self.ctrl.close()
        if self._tor_proc is not None:
            self._tor_proc.terminate()

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    def get_with_refresh(self, *args, **kwargs):
        self._refresh()
        return self.session.get(*args, **kwargs)

    def _refresh(self):
        if not self._tor_process_exists():
            self._tor_proc = self._launch_tor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
