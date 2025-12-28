# -*- coding: utf-8 -*-
# config_loader.py
# Configuration loader for EverJudge
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: BSD 3-Clause License
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib as toml
except ImportError:
    try:
        import tomli as toml
    except ImportError:
        raise ImportError("tomllib or tomli is required for parsing TOML files")


class Config:
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls, config_path: str = "./plugins/main/config.toml") -> None:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "rb") as f:
            cls._config = toml.load(f)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = cls._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        return cls._config.get("server", {})

    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        return cls._config.get("database", {})

    @classmethod
    def get_judge_config(cls) -> Dict[str, Any]:
        return cls._config.get("judge", {})

    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        return cls._config.get("logging", {})

    @classmethod
    def get_security_config(cls) -> Dict[str, Any]:
        return cls._config.get("security", {})

    @classmethod
    def get_language_config(cls, language: str) -> Optional[Dict[str, Any]]:
        languages = cls._config.get("language", {})
        return languages.get(language)

    @classmethod
    def get_upload_config(cls) -> Dict[str, Any]:
        return cls._config.get("upload", {})

    @classmethod
    def get_features_config(cls) -> Dict[str, Any]:
        return cls._config.get("features", {})

    @classmethod
    def get_database_uri(cls) -> str:
        db_config = cls.get_database_config()
        db_type = db_config.get("type", "sqlite")

        if db_type == "sqlite":
            db_path = db_config.get("path", "./data/everjudge.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite:///{db_path}"

        elif db_type == "mysql" or db_type == "mariadb":
            username = db_config.get("username", "")
            password = db_config.get("password", "")
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 3306)
            database = db_config.get("database_name", "everjudge")
            mysql_config = db_config.get("mysql", {})
            charset = mysql_config.get("charset", "utf8mb4")
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset={charset}"

        elif db_type == "postgresql":
            username = db_config.get("username", "")
            password = db_config.get("password", "")
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 5432)
            database = db_config.get("database_name", "everjudge")
            postgresql_config = db_config.get("postgresql", {})
            sslmode = postgresql_config.get("sslmode", "disable")
            return f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode={sslmode}"

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @classmethod
    def create_database_if_not_exists(cls) -> None:
        db_config = cls.get_database_config()
        db_type = db_config.get("type", "sqlite")

        if db_type == "mysql" or db_type == "mariadb":
            import pymysql
            username = db_config.get("username", "")
            password = db_config.get("password", "")
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 3306)
            database = db_config.get("database_name", "everjudge")
            mysql_config = db_config.get("mysql", {})
            charset = mysql_config.get("charset", "utf8mb4")

            try:
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    charset=charset
                )
                cursor = connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()
                connection.close()
            except Exception as e:
                raise RuntimeError(f"Failed to create database: {e}")

    @classmethod
    def get_flask_config(cls) -> Dict[str, Any]:
        flask_config = {}

        server_config = cls.get_server_config()
        flask_config["DEBUG"] = server_config.get("debug", False)

        db_config = cls.get_database_config()
        flask_config["SQLALCHEMY_DATABASE_URI"] = cls.get_database_uri()
        flask_config["SQLALCHEMY_TRACK_MODIFICATIONS"] = db_config.get("echo", False)
        flask_config["SQLALCHEMY_ECHO"] = db_config.get("echo", False)
        flask_config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": db_config.get("pool_size", 5),
            "pool_timeout": db_config.get("pool_timeout", 30),
            "pool_recycle": db_config.get("pool_recycle", 3600),
        }

        security_config = cls.get_security_config()
        flask_config["SECRET_KEY"] = security_config.get("secret_key", "dev-secret-key")
        flask_config["SESSION_COOKIE_SECURE"] = not server_config.get("debug", True)
        flask_config["PERMANENT_SESSION_LIFETIME"] = security_config.get("session_lifetime", 86400)
        flask_config["MAX_CONTENT_LENGTH"] = security_config.get("max_content_length", 10485760)

        upload_config = cls.get_upload_config()
        flask_config["UPLOAD_FOLDER"] = upload_config.get("upload_dir", "./uploads")
        flask_config["MAX_CONTENT_LENGTH"] = upload_config.get("max_file_size", 10485760)

        return flask_config

    @classmethod
    def ensure_directories(cls) -> None:
        directories = [
            cls.get("judge.temp_dir", "./temp"),
            cls.get("judge.input_dir", "./inputs"),
            cls.get("judge.output_dir", "./outputs"),
            cls.get("upload.upload_dir", "./uploads"),
        ]

        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

        db_path = cls.get("database.path", "./data/everjudge.db")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        logging_config = cls.get_logging_config()
        if logging_config.get("file_enabled", False):
            log_path = logging_config.get("file_path", "./logs/everjudge.log")
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
