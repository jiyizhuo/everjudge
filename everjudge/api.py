# -*- coding: utf-8 -*-
# api.py
# The main Application Programming Interface for EverJudge.
# @version: 0.1.0

# Warning: We DO NOT recommend common plugins to use this API directly.
# Please use the APIs in the "main" plugins instead.

from collections import deque # For topological sort while loading plugins.
from flask import Blueprint, Flask # Flask.

import everjudge_share # The global object.
import functools # For "wraps".
import importlib # For loading plugins.
import logging # The logging library. We do not want to be silent, do we?
import pathlib # The path & file library.
try:
    import tomllib as toml # Using the built-in TOML parser.
except ImportError:
    try:
        import tomli as toml # Using the site-package "tomli" to parse TOML files.
    except:
        raise # We've messed it up.

_logger = logging.getLogger("EverJudge API") # Quite bad. Why can't we get rid of this?
_logger.setLevel(logging.INFO)

class Application(object):
    def __init__(self, name: str, host: str="0.0.0.0", port: int=80, debug: bool=False):
        self._flask_instance = Flask(name, template_folder="./templates/")
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
    _logger.info(f"Creating application '{name}'")
    return Application(name, host, port, debug)

def set_main_application(app_: Application) -> None: # We've moved it back in order to finish the EverLaunch.
    everjudge_share.app = app_
    return

def get_main_application() -> Application | None:
    app = everjudge_share.app
    if app:
        _logger.debug("Retrieved main application instance")
    else:
        _logger.warning("Main application instance is None")
    return app

def _load_plugin(name: str):
    try:
        m = importlib.import_module(f"plugins.{name}")
        _logger.info(f"Loaded plugin {name}.")
    except ImportError:
        raise ImportError(f"Unable to load plugin {name}.")
    return m


class PluginManager(object):
    def __init__(self):
        self._plugins: dict[str, str] = {}
        self._plugins_required: list[str] = []

    def load_plugins(self) -> None:
        for plugin in pathlib.Path("./plugins").iterdir():
            if plugin.is_dir():
                # m = _load_plugin(plugin.name)
                with open(f"./plugins/{plugin.name}/plugin.toml", "rb") as f:
                    t=toml.load(f)
                    # print(t) # A simple debug message.
                    self._plugins[t["info"]["id"]] = plugin.name
                    self._plugins_required.append(t["info"]["id"])
                    self._plugins_required += t["dependencies"]["dependencies"]
        # Build dependency graph and compute topological order
        dep_graph: dict[str, set[str]] = {}
        in_degree: dict[str, int] = {}
        plugin_info: dict[str, dict] = {}

        # Collect plugin metadata and build dependency graph
        for plugin in pathlib.Path("./plugins").iterdir():
            if plugin.is_dir():
                try:
                    with open(f"./plugins/{plugin.name}/plugin.toml", "rb") as f:
                        t = toml.load(f)
                        pid = t["info"]["id"]
                        deps = t["dependencies"]["dependencies"]
                        plugin_info[pid] = {"dir": plugin.name, "deps": deps}
                        dep_graph[pid] = set(deps)
                        in_degree[pid] = 0
                except Exception:
                    _logger.warning(f"Skip invalid plugin directory: {plugin.name}")
                    continue

        # Compute in-degrees
        for pid, deps in dep_graph.items():
            for d in deps:
                if d in in_degree:
                    in_degree[d] += 1
                else:
                    # Missing dependency will be caught later
                    in_degree[d] = 1

        # Topological sort using Kahn's algorithm
        queue = deque([pid for pid, deg in in_degree.items() if deg == 0])
        topo_order = []

        while queue:
            cur = queue.popleft()
            topo_order.append(cur)
            for dep in dep_graph.get(cur, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        # Detect cycles or missing dependencies
        if len(topo_order) != len(in_degree):
            _logger.error("Circular or missing dependencies detected among plugins.")
            raise ImportError("Circular or missing dependencies detected among plugins.")

        # Load plugins in topological order
        for pid in topo_order:
            info = plugin_info[pid]
            self._plugins[pid] = info["dir"]
            self._plugins_required.append(pid)
            self._plugins_required.extend(info["deps"])
            _load_plugin(info["dir"])

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
    _logger.debug(f"Creating logger '{name}' with level={logging.getLevelName(level)}")
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(format_)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    _logger.info(f"Logger '{name}' created successfully")
    return logger
