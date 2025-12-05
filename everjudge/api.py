# -*- coding: utf-8 -*-
# api.py
# The main Application Programming Interface for EverJudge.
# @version: 0.1.0

from flask import Blueprint, Flask

import everjudge_share
import functools
import logging
import pathlib
import tomllib as toml

_logger = logging.getLogger("EverJudge API")
_logger.setLevel(logging.INFO)

class Application(object):
    def __init__(self, name: str, host: str="0.0.0.0", port: int=80, debug: bool=False):
        self._flask_instance = Flask(name)
        self._host = host
        self._port = port
        self._debug = debug
        return

    def mainloop(self) -> None:
        self._flask_instance.run(host=self._host, port=self._port, debug=self._debug)
        return

    def register_route(self, rule: str) -> callable:
        def _register(func: callable, endpoint: str=None, methods: list=None) -> callable:
            if methods is None:
                methods = ["GET"]
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_=self._flask_instance.route(rule, endpoint=endpoint, methods=methods)(func)
                return func_(*args, **kwargs)
            return wrapper
        return _register

    def register_blueprint(self, blueprint: Blueprint) -> None:
        self._flask_instance.register_blueprint(blueprint)
        return

    def get_flask_instance(self) -> Flask:
        return self._flask_instance


def create_application(name: str, host: str="0.0.0.0", port: int=80, debug: bool=False) -> Application:
    return Application(name, host, port, debug)

def set_main_application(app_: Application) -> None:
    everjudge_share.app = app_
    return

def get_main_application() -> Application | None:
    return everjudge_share.app

def _load_plugin(name: str):
    try:
        m = __import__(f"plugins.{name}")
        _logger.info(f"Loaded plugin {name}.")
    except ImportError:
        raise ImportError(f"Unable to load plugin {name}.")
    return m


class PluginManager(object):
    def __init__(self):
        self._plugins: tuple[str, ...] = ()
        self._plugins_required: tuple[str, ...] = ()

    def load_plugins(self) -> None:
        for plugin in pathlib.Path("./plugins").iterdir():
            if plugin.is_dir():
                m = _load_plugin(plugin.name)
                with open(f"./plugins/{plugin.name}/plugin.toml", "rb") as f:
                    t=toml.load(f)
                    # print(t)
                    self._plugins += (t["info"]["id"],)
                    self._plugins_required += (t["info"]["id"],)
                    self._plugins_required += tuple(t["dependencies"]["dependencies"])

        return

    def check_dependencies(self) -> None:
        for plugin in self._plugins_required:
            if plugin not in self._plugins:
                _logger.error(f"Plugin {plugin} is required by {self._plugins}, but not installed.")
                raise ImportError(f"Plugin {plugin} is required by {self._plugins}, but not installed.")

def create_plugin_manager() -> PluginManager:
    return PluginManager()

def set_plugin_manager(pluginmgr_: PluginManager) -> None:
    everjudge_share.pluginmgr = pluginmgr_
    return

def get_plugin_manager() -> PluginManager | None:
    return everjudge_share.pluginmgr

def create_blueprint(name:str, root: str, template_folder: str = "templates") -> Blueprint:
    blueprint = Blueprint(name, __name__, url_prefix=root, template_folder=template_folder)
    return blueprint

def create_logger(name: str, level: int = logging.INFO, format_: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(format_)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger
