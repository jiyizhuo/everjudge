# -*- coding: utf-8 -*-
# database.py
# Database models for EverJudge
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: BSD 3-Clause License
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

from datetime import datetime
from enum import Enum
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class JudgeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    RUNTIME_ERROR = "runtime_error"
    COMPILATION_ERROR = "compilation_error"
    SYSTEM_ERROR = "system_error"
    PRESENTATION_ERROR = "presentation_error"


class ContestStatus(Enum):
    UPCOMING = "upcoming"
    RUNNING = "running"
    ENDED = "ended"
    CANCELLED = "cancelled"


class ContestType(Enum):
    ICPC = "icpc"
    IOI = "ioi"
    OI = "oi"
    CUSTOM = "custom"


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    submissions = db.relationship('Submission', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    input_format = db.Column(db.Text)
    output_format = db.Column(db.Text)
    constraints = db.Column(db.Text)
    sample_input = db.Column(db.Text)
    sample_output = db.Column(db.Text)
    hint = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=5, nullable=False)
    problem_set_id = db.Column(db.Integer, db.ForeignKey('problem_sets.id'), nullable=False)
    time_limit = db.Column(db.Integer, default=1000, nullable=False)
    memory_limit = db.Column(db.Integer, default=256, nullable=False)
    total_submissions = db.Column(db.Integer, default=0, nullable=False)
    accepted_submissions = db.Column(db.Integer, default=0, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    tags = db.Column(db.String(500))

    problem_set = db.relationship('ProblemSet', backref='problems', lazy=True)
    test_cases = db.relationship('TestCase', backref='problem', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='problem', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='problem', lazy=True, cascade='all, delete-orphan')

    def update_statistics(self) -> None:
        self.total_submissions = Submission.query.filter_by(problem_id=self.id).count()
        self.accepted_submissions = Submission.query.filter_by(
            problem_id=self.id,
            status=JudgeStatus.ACCEPTED
        ).count()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'input_format': self.input_format,
            'output_format': self.output_format,
            'constraints': self.constraints,
            'sample_input': self.sample_input,
            'sample_output': self.sample_output,
            'hint': self.hint,
            'difficulty': self.difficulty,
            'problem_set_id': self.problem_set_id,
            'time_limit': self.time_limit,
            'memory_limit': self.memory_limit,
            'total_submissions': self.total_submissions,
            'accepted_submissions': self.accepted_submissions,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_visible': self.is_visible,
            'tags': self.tags.split(',') if self.tags else []
        }

    def __repr__(self) -> str:
        return f'<Problem {self.id}: {self.title}>'


class ProblemSet(db.Model):
    __tablename__ = 'problem_sets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)

    creator = db.relationship('User', backref='problem_sets', lazy=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_visible': self.is_visible
        }

    def __repr__(self) -> str:
        return f'<ProblemSet {self.id}: {self.name}>'


class TestCase(db.Model):
    __tablename__ = 'test_cases'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    test_number = db.Column(db.Integer, nullable=False)
    is_sample = db.Column(db.Boolean, default=False, nullable=False)
    score = db.Column(db.Integer, default=1, nullable=False)
    input_file = db.Column(db.String(255), nullable=False)
    output_file = db.Column(db.String(255), nullable=False)
    interactor_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'test_number': self.test_number,
            'is_sample': self.is_sample,
            'score': self.score,
            'input_file': self.input_file,
            'output_file': self.output_file,
            'interactor_file': self.interactor_file,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f'<TestCase {self.test_number} for Problem {self.problem_id}>'


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    source_code = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(JudgeStatus), default=JudgeStatus.PENDING, nullable=False)
    execution_time = db.Column(db.Integer)
    memory_usage = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    judged_at = db.Column(db.DateTime)
    test_cases_passed = db.Column(db.Integer, default=0)
    total_test_cases = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'problem_id': self.problem_id,
            'language': self.language,
            'status': self.status.value,
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'error_message': self.error_message,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'judged_at': self.judged_at.isoformat() if self.judged_at else None,
            'test_cases_passed': self.test_cases_passed,
            'total_test_cases': self.total_test_cases
        }

    def __repr__(self) -> str:
        return f'<Submission {self.id} by User {self.user_id} for Problem {self.problem_id}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussions.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    problem = db.relationship('Problem', back_populates='comments', lazy=True)
    contest = db.relationship('Contest', backref='comments', lazy=True)
    discussion = db.relationship('Discussion', backref='comments', lazy=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'contest_id': self.contest_id,
            'discussion_id': self.discussion_id,
            'user_id': self.user_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted
        }

    def __repr__(self) -> str:
        return f'<Comment {self.id} by User {self.user_id}>'


class Contest(db.Model):
    __tablename__ = 'contests'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    contest_type = db.Column(db.Enum(ContestType), default=ContestType.CUSTOM, nullable=False)
    status = db.Column(db.Enum(ContestStatus), default=ContestStatus.UPCOMING, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    registration_start = db.Column(db.DateTime)
    registration_end = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    allow_registration = db.Column(db.Boolean, default=True, nullable=False)

    creator = db.relationship('User', backref='contests', lazy=True)
    problems = db.relationship('Problem', secondary='contest_problems', backref='contests', lazy=True)
    participants = db.relationship('User', secondary='contest_participants', backref='participated_contests', lazy=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'contest_type': self.contest_type.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'registration_start': self.registration_start.isoformat() if self.registration_start else None,
            'registration_end': self.registration_end.isoformat() if self.registration_end else None,
            'duration_minutes': self.duration_minutes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_visible': self.is_visible,
            'allow_registration': self.allow_registration
        }

    def __repr__(self) -> str:
        return f'<Contest {self.id}: {self.title}>'


class ContestProblem(db.Model):
    __tablename__ = 'contest_problems'

    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    problem_order = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, default=100, nullable=False)

    __table_args__ = (db.UniqueConstraint('contest_id', 'problem_id', name='unique_contest_problem'),)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'contest_id': self.contest_id,
            'problem_id': self.problem_id,
            'problem_order': self.problem_order,
            'score': self.score
        }

    def __repr__(self) -> str:
        return f'<ContestProblem {self.problem_id} in Contest {self.contest_id}>'


class ContestParticipant(db.Model):
    __tablename__ = 'contest_participants'

    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_score = db.Column(db.Integer, default=0, nullable=False)
    problems_solved = db.Column(db.Integer, default=0, nullable=False)
    penalty_time = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (db.UniqueConstraint('contest_id', 'user_id', name='unique_contest_participant'),)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'contest_id': self.contest_id,
            'user_id': self.user_id,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'total_score': self.total_score,
            'problems_solved': self.problems_solved,
            'penalty_time': self.penalty_time
        }

    def __repr__(self) -> str:
        return f'<ContestParticipant User {self.user_id} in Contest {self.contest_id}>'


class Discussion(db.Model):
    __tablename__ = 'discussions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_comment_at = db.Column(db.DateTime)

    author = db.relationship('User', backref='discussions', lazy=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'user_id': self.user_id,
            'is_pinned': self.is_pinned,
            'is_locked': self.is_locked,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_comment_at': self.last_comment_at.isoformat() if self.last_comment_at else None
        }

    def __repr__(self) -> str:
        return f'<Discussion {self.id}: {self.title}>'


class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    total_score = db.Column(db.Integer, default=0, nullable=False)
    problems_solved = db.Column(db.Integer, default=0, nullable=False)
    submissions_count = db.Column(db.Integer, default=0, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='leaderboard', uselist=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'total_score': self.total_score,
            'problems_solved': self.problems_solved,
            'submissions_count': self.submissions_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    def __repr__(self) -> str:
        return f'<Leaderboard User {self.user_id}>'
