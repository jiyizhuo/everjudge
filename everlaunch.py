# -*- coding: utf-8 -*-
# EverJudge Launcher
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: BSD 3-Clause License
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

# This is the main launcher of the whole EverJudge Project.
# Please use this script to launch the EverJudge Project.

import click
import logging
import sys

from everjudge.api import (
    create_application,
    set_main_application,
    get_main_application,
    create_plugin_manager,
    set_plugin_manager,
    get_plugin_manager,
    create_logger
)

_logger = logging.getLogger("EverJudge Launcher")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    _logger.setLevel(level)


@click.group()
@click.version_option(version='0.1.0', prog_name='EverJudge')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@cli.command()
@click.option('--host', '-h', default='0.0.0.0', show_default=True, help='Host to bind to')
@click.option('--port', '-p', default=8080, show_default=True, type=int, help='Port to listen on')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--workers', '-w', default=1, type=int, help='Number of worker processes (not implemented yet)')
@click.pass_context
def start(ctx: click.Context, host: str, port: int, debug: bool, workers: int) -> None:
    verbose = ctx.obj.get('verbose', False)
    setup_logging(verbose or debug)
    
    _logger.info("=" * 60)
    _logger.info("EverJudge Online Judge System")
    _logger.info("Version: 0.1.0")
    _logger.info("=" * 60)
    _logger.info(f"Starting EverJudge on {host}:{port}")
    _logger.info(f"Debug mode: {debug}")
    _logger.info(f"Workers: {workers}")
    _logger.info("=" * 60)
    
    try:
        _logger.info("Creating application...")
        app = create_application(
            name="EverJudge",
            host=host,
            port=port,
            debug=debug
        )
        set_main_application(app)
        
        _logger.info("Creating plugin manager...")
        plugin_manager = create_plugin_manager()
        set_plugin_manager(plugin_manager)
        
        _logger.info("Loading plugins...")
        get_plugin_manager().load_plugins()
        
        _logger.info("Starting main loop...")
        _logger.info("=" * 60)
        _logger.info(f"EverJudge is now running at http://{host}:{port}")
        _logger.info("Press Ctrl+C to stop the server")
        _logger.info("=" * 60)
        
        get_main_application().mainloop()
        
    except KeyboardInterrupt:
        _logger.info("")
        _logger.info("=" * 60)
        _logger.info("Received interrupt signal. Shutting down...")
        _logger.info("=" * 60)
        sys.exit(0)
    except Exception as e:
        _logger.error(f"Failed to start EverJudge: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    click.echo("=" * 60)
    click.echo("EverJudge Online Judge System")
    click.echo("=" * 60)
    click.echo("Version: 0.1.0")
    click.echo("License: BSD 3-Clause License")
    click.echo("Copyright (c) 2025, jiyizhuo")
    click.echo("")
    click.echo("Author: Ayanami_404 <jiyizhuo2011@hotmail.com>")
    click.echo("Maintainer: Project EverJudge")
    click.echo("=" * 60)


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    click.echo("EverJudge Status:")
    click.echo("  Application: " + ("Running" if get_main_application() else "Not running"))
    click.echo("  Plugin Manager: " + ("Active" if get_plugin_manager() else "Not initialized"))
    
    if get_plugin_manager():
        supported_langs = get_plugin_manager().get_supported_languages()
        click.echo(f"  Supported Languages: {', '.join(supported_langs) if supported_langs else 'None'}")


@cli.command()
@click.argument('language')
@click.option('--file-name', '-f', required=True, help='Source file name')
@click.option('--exec-name', '-e', required=True, help='Executable name')
@click.option('--input-folder', '-i', default='./inputs', help='Input files folder')
@click.option('--output-folder', '-o', default='./outputs', help='Output files folder')
@click.pass_context
def test(ctx: click.Context, language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str) -> None:
    from plugins.main.api import create_language_provider, create_judger, JudgeResult
    
    click.echo(f"Testing {language} provider...")
    click.echo(f"  File: {file_name}")
    click.echo(f"  Executable: {exec_name}")
    click.echo(f"  Input folder: {input_folder}")
    click.echo(f"  Output folder: {output_folder}")
    
    try:
        provider = create_language_provider(language, file_name, exec_name, input_folder, output_folder)
        if not provider:
            click.echo(f"Error: Unsupported language '{language}'", err=True)
            sys.exit(1)
        
        judger = create_judger("standard")
        judger.register_provider(language, provider)
        
        click.echo("Running tests...")
        result = judger.judge(language, group=0)
        
        click.echo(f"Result: {result.value}")
        
        if result == JudgeResult.AC:
            click.echo("Test passed!")
            sys.exit(0)
        else:
            click.echo("Test failed!")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def db():
    """Database management commands"""
    pass


@db.command()
@click.option('--reset', '-r', is_flag=True, help='Drop existing tables before creating')
@click.option('--sample-data', '-s', is_flag=True, help='Create sample data after initialization')
@click.pass_context
def init(ctx: click.Context, reset: bool, sample_data: bool) -> None:
    from everjudge.api import create_application, set_main_application
    from plugins.main.config_loader import Config
    from plugins.main.db_init import init_database, create_sample_data
    
    try:
        Config.load()
        Config.ensure_directories()
        
        click.echo("Creating database if not exists...")
        Config.create_database_if_not_exists()
        
        app = create_application("EverJudge", "0.0.0.0", 8080, False)
        set_main_application(app)
        
        flask_app = app.get_flask_instance()
        flask_config = Config.get_flask_config()
        for key, value in flask_config.items():
            flask_app.config[key] = value
        
        from plugins.main.database import db
        db.init_app(flask_app)
        
        click.echo("Initializing database...")
        with flask_app.app_context():
            init_database(flask_app, drop_existing=reset)
        
        if sample_data:
            click.echo("Creating sample data...")
            with flask_app.app_context():
                create_sample_data(flask_app)
        
        click.echo("Database initialization completed successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@db.command()
@click.pass_context
def reset(ctx: click.Context) -> None:
    from everjudge.api import create_application, set_main_application
    from plugins.main.config_loader import Config
    from plugins.main.db_init import reset_database
    
    try:
        Config.load()
        
        click.echo("Creating database if not exists...")
        Config.create_database_if_not_exists()
        
        app = create_application("EverJudge", "0.0.0.0", 8080, False)
        set_main_application(app)
        
        flask_app = app.get_flask_instance()
        flask_config = Config.get_flask_config()
        for key, value in flask_config.items():
            flask_app.config[key] = value
        
        from plugins.main.database import db
        db.init_app(flask_app)
        
        if click.confirm("This will delete all data. Are you sure?"):
            click.echo("Resetting database...")
            with flask_app.app_context():
                reset_database(flask_app)
            click.echo("Database reset completed successfully!")
        else:
            click.echo("Operation cancelled.")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@db.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    from everjudge.api import create_application, set_main_application
    from plugins.main.config_loader import Config
    from plugins.main.db_init import get_database_info
    
    try:
        Config.load()
        
        click.echo("Creating database if not exists...")
        Config.create_database_if_not_exists()
        
        app = create_application("EverJudge", "0.0.0.0", 8080, False)
        set_main_application(app)
        
        flask_app = app.get_flask_instance()
        flask_config = Config.get_flask_config()
        for key, value in flask_config.items():
            flask_app.config[key] = value
        
        from plugins.main.database import db
        db.init_app(flask_app)
        
        click.echo("Database Information:")
        click.echo("=" * 40)
        
        info = get_database_info(flask_app)
        for key, value in info.items():
            click.echo(f"  {key.replace('_', ' ').title()}: {value}")
        
        click.echo("=" * 40)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
