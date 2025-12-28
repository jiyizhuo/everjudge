# -*- coding: utf-8 -*-
# db_init.py
# Database initialization module for EverJudge
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: BSD 3-Clause License
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

import logging
import os
from typing import Optional

from .database import db, User, Problem, TestCase, Submission, Comment, Leaderboard, UserRole, ProblemSet, Contest, ContestType, ContestStatus, Discussion
from .config_loader import Config

_logger = logging.getLogger("EverJudge Database")


def is_database_initialized(app) -> bool:
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            return len(existing_tables) > 0
    except Exception as e:
        _logger.warning(f"Failed to check database initialization status: {e}")
        return False


def init_database(app, drop_existing: bool = False, force_init: bool = False) -> None:
    try:
        _logger.info("Initializing database...")

        with app.app_context():
            if drop_existing:
                _logger.warning("Dropping all existing tables...")
                db.drop_all()
                _logger.info("All tables dropped")
                db.create_all()
            else:
                db.create_all()
                _logger.info("Database tables created successfully")

            if force_init or drop_existing:
                create_default_admin(app)
                create_default_leaderboard_entries(app)
            else:
                _logger.info("Skipping default data creation (use --force to create)")

            _logger.info("Database initialization completed")

    except Exception as e:
        _logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def create_default_admin(app) -> None:
    try:
        with app.app_context():
            admin_config = Config.get_admin_config()
            default_username = admin_config.get("default_username", "admin")
            admin = User.query.filter_by(username=default_username).first()

            if admin is None:
                _logger.info("Creating default admin user...")
                admin = User(
                    username=default_username,
                    email=admin_config.get("default_email", "admin@everjudge.local"),
                    role=UserRole.ADMIN,
                    is_active=True
                )
                admin.set_password(admin_config.get("default_password", "admin123"))
                db.session.add(admin)
                db.session.commit()
                _logger.info(f"Default admin user created (username: {default_username}, password: {admin_config.get('default_password', 'admin123')})")
                _logger.warning("Please change the default admin password after first login!")
            else:
                _logger.info("Admin user already exists")

    except Exception as e:
        _logger.error(f"Failed to create default admin: {e}", exc_info=True)
        raise


def create_default_leaderboard_entries(app) -> None:
    try:
        with app.app_context():
            users = User.query.all()

            for user in users:
                leaderboard_entry = Leaderboard.query.filter_by(user_id=user.id).first()

                if leaderboard_entry is None:
                    _logger.debug(f"Creating leaderboard entry for user {user.username}...")
                    leaderboard_entry = Leaderboard(
                        user_id=user.id,
                        total_score=0,
                        problems_solved=0,
                        submissions_count=0
                    )
                    db.session.add(leaderboard_entry)

            db.session.commit()
            _logger.info("Leaderboard entries created for all users")

    except Exception as e:
        _logger.error(f"Failed to create leaderboard entries: {e}", exc_info=True)
        raise


def reset_database(app) -> None:
    _logger.warning("Resetting database...")
    init_database(app, drop_existing=True)
    _logger.info("Database reset completed")


def get_database_info(app) -> dict:
    try:
        with app.app_context():
            info = {
                "users": User.query.count(),
                "problem_sets": ProblemSet.query.count(),
                "problems": Problem.query.count(),
                "test_cases": TestCase.query.count(),
                "submissions": Submission.query.count(),
                "comments": Comment.query.count(),
                "discussions": Discussion.query.count(),
                "contests": Contest.query.count(),
                "leaderboard_entries": Leaderboard.query.count()
            }
            return info

    except Exception as e:
        _logger.error(f"Failed to get database info: {e}", exc_info=True)
        return {}


def create_sample_data(app) -> None:
    try:
        with app.app_context():
            _logger.info("Creating sample data...")

            admin_config = Config.get_admin_config()
            default_username = admin_config.get("default_username", "admin")
            admin = User.query.filter_by(username=default_username).first()
            if not admin:
                _logger.warning("Admin user not found, skipping sample data creation")
                return

            problem_set = ProblemSet.query.filter_by(name="默认题库").first()
            if problem_set is None:
                problem_set = ProblemSet(
                    name="默认题库",
                    description="系统默认题库",
                    created_by=admin.id,
                    is_visible=True
                )
                db.session.add(problem_set)
                db.session.commit()
                _logger.info("Default problem set created")

            sample_problems = [
                {
                    "title": "A+B Problem",
                    "description": "Given two integers A and B, calculate their sum.",
                    "input_format": "Two integers A and B separated by a space.",
                    "output_format": "Output the sum of A and B.",
                    "constraints": "1 <= A, B <= 1000",
                    "sample_input": "1 2",
                    "sample_output": "3",
                    "difficulty": 1,
                    "time_limit": 1000,
                    "memory_limit": 256
                },
                {
                    "title": "Hello World",
                    "description": "Write a program that outputs \"Hello, World!\".",
                    "input_format": "No input.",
                    "output_format": "Output \"Hello, World!\".",
                    "constraints": "None",
                    "sample_input": "",
                    "sample_output": "Hello, World!",
                    "difficulty": 0,
                    "time_limit": 1000,
                    "memory_limit": 256
                }
            ]

            test_cases_dir = Config.get("judge.input_dir", "./inputs")
            if not os.path.exists(test_cases_dir):
                os.makedirs(test_cases_dir, exist_ok=True)

            for problem_data in sample_problems:
                existing_problem = Problem.query.filter_by(title=problem_data["title"]).first()
                if existing_problem is None:
                    problem = Problem(
                        title=problem_data["title"],
                        description=problem_data["description"],
                        input_format=problem_data["input_format"],
                        output_format=problem_data["output_format"],
                        constraints=problem_data["constraints"],
                        sample_input=problem_data["sample_input"],
                        sample_output=problem_data["sample_output"],
                        difficulty=problem_data["difficulty"],
                        time_limit=problem_data["time_limit"],
                        memory_limit=problem_data["memory_limit"],
                        problem_set_id=problem_set.id,
                        created_by=admin.id
                    )
                    db.session.add(problem)
                    db.session.flush()

                    problem_test_dir = os.path.join(test_cases_dir, str(problem.id))
                    if not os.path.exists(problem_test_dir):
                        os.makedirs(problem_test_dir, exist_ok=True)

                    input_file = os.path.join(problem_test_dir, "1.in")
                    output_file = os.path.join(problem_test_dir, "1.out")

                    with open(input_file, 'w', encoding='utf-8') as f:
                        f.write(problem_data["sample_input"])
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(problem_data["sample_output"])

                    test_case = TestCase(
                        problem_id=problem.id,
                        test_number=1,
                        is_sample=True,
                        score=1,
                        input_file=input_file,
                        output_file=output_file
                    )
                    db.session.add(test_case)

            db.session.commit()
            _logger.info("Sample data created successfully")

    except Exception as e:
        _logger.error(f"Failed to create sample data: {e}", exc_info=True)
        raise
