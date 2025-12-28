# -*- coding: utf-8 -*-
# EverJudge Main
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: GPL3
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

import datetime
import logging
from flask import render_template, request
from flask_migrate import Migrate

from everjudge.api import *
from .config_loader import Config
from .database import db
from .db_init import init_database

_logger = logging.getLogger("EverJudge Main")

migrate = Migrate()

main_blueprint = create_blueprint("main", "/")

@main_blueprint.route("/")
def root():
    from .database import User, Problem, Contest, Leaderboard, Submission, Discussion

    # 从数据库获取公告数据（使用置顶讨论作为公告）
    announcements = []
    try:
        pinned_discussions = Discussion.query.filter_by(is_pinned=True).order_by(Discussion.created_at.desc()).limit(5).all()
        announcements = [
            {'title': d.title, 'date': d.created_at.strftime('%Y-%m-%d')}
            for d in pinned_discussions
        ]
    except Exception as e:
        _logger.error(f"Error fetching announcements: {e}")

    # 从数据库获取统计数据
    stats = {
        'total_users': 0,
        'total_submissions': 0
    }
    try:
        stats['total_users'] = User.query.count()
        stats['total_submissions'] = Submission.query.count()
    except Exception as e:
        _logger.error(f"Error fetching stats: {e}")

    # 从数据库获取最近的题目
    recent_problems = []
    try:
        problems = Problem.query.filter_by(is_visible=True).order_by(Problem.created_at.desc()).limit(6).all()
        recent_problems = [
            {
                'id': p.id,
                'title': p.title,
                'difficulty': p.difficulty,
                'time_limit': p.time_limit,
                'memory_limit': p.memory_limit,
                'acceptance_rate': round(p.accepted_submissions / p.total_submissions * 100, 1) if p.total_submissions > 0 else 0.0
            }
            for p in problems
        ]
    except Exception as e:
        _logger.error(f"Error fetching recent problems: {e}")

    # 从数据库获取比赛数据
    contests = []
    try:
        contest_list = Contest.query.filter_by(is_visible=True).order_by(Contest.start_time).limit(5).all()
        contests = [
            {
                'title': c.title,
                'start_time': c.start_time.strftime('%Y-%m-%d %H:%M'),
                'status': c.status.value
            }
            for c in contest_list
        ]
    except Exception as e:
        _logger.error(f"Error fetching contests: {e}")

    # 从数据库获取用户排名
    top_users = []
    try:
        leaderboard_entries = Leaderboard.query.order_by(Leaderboard.total_score.desc()).limit(5).all()
        top_users = [
            {'username': entry.user.username if entry.user else 'Unknown', 'rating': entry.total_score}
            for entry in leaderboard_entries
        ]
    except Exception as e:
        _logger.error(f"Error fetching top users: {e}")

    return render_template('index.html', 
                           announcements=announcements, 
                           stats=stats, 
                           recent_problems=recent_problems,
                           contests=contests,
                           top_users=top_users)

@main_blueprint.route("/problems")
def problems():
    from .database import Problem, ProblemSet, Submission, JudgeStatus, db

    # 获取查询参数
    search = request.args.get('search', '')
    difficulty = request.args.get('difficulty', '')
    set_filter = request.args.get('set', '')
    solved = request.args.get('solved', '') == 'true'
    sort_by = request.args.get('sort', 'id')
    page = int(request.args.get('page', 1))
    
    # 构建基础查询
    query = Problem.query.filter_by(is_visible=True)
    
    # 搜索筛选
    if search:
        search_lower = search.lower()
        query = query.filter(
            db.or_(
                Problem.title.ilike(f'%{search_lower}%'),
                Problem.id == int(search) if search.isdigit() else False,
                Problem.tags.ilike(f'%{search_lower}%')
            )
        )
    
    # 难度筛选
    if difficulty:
        min_diff, max_diff = map(int, difficulty.split('-'))
        query = query.filter(Problem.difficulty.between(min_diff, max_diff))
    
    # 题库筛选
    if set_filter:
        if set_filter.isdigit():
            query = query.filter_by(problem_set_id=int(set_filter))
        else:
            problem_set = ProblemSet.query.filter_by(name=set_filter).first()
            if problem_set:
                query = query.filter_by(problem_set_id=problem_set.id)
    
    # 已解决筛选（TODO: 需要获取当前登录用户ID）
    if solved:
        pass
    
    # 排序
    if sort_by == 'difficulty':
        query = query.order_by(Problem.difficulty.asc())
    elif sort_by == 'acceptance':
        query = query.order_by(
            db.case(
                (Problem.total_submissions == 0, 0),
                else_=Problem.accepted_submissions / Problem.total_submissions
            ).desc()
        )
    else:
        query = query.order_by(Problem.id.asc())
    
    # 分页
    per_page = 10
    total_problems = query.count()
    total_pages = (total_problems + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * per_page
    problems = query.offset(start_idx).limit(per_page).all()
    
    # 转换为字典格式
    problems_data = [
        {
            'id': p.id,
            'title': p.title,
            'difficulty': p.difficulty,
            'time_limit': p.time_limit,
            'memory_limit': p.memory_limit,
            'acceptance_rate': round(p.accepted_submissions / p.total_submissions * 100, 1) if p.total_submissions > 0 else 0.0,
            'tags': p.tags.split(',') if p.tags else [],
            'is_new': (datetime.datetime.utcnow() - p.created_at).days <= 7
        }
        for p in problems
    ]
    
    # 生成页码
    page_numbers = []
    if total_pages <= 7:
        page_numbers = list(range(1, total_pages + 1))
    else:
        if page <= 4:
            page_numbers = [1, 2, 3, 4, 5, '...', total_pages]
        elif page >= total_pages - 3:
            page_numbers = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        else:
            page_numbers = [1, '...', page - 1, page, page + 1, '...', total_pages]
    
    return render_template('problems.html',
                           problems=problems_data,
                           total_problems=total_problems,
                           current_page=page,
                           total_pages=total_pages,
                           page_numbers=page_numbers)


@main_blueprint.route("/problems/<int:problem_id>")
def problem_detail(problem_id):
    from .database import Problem, Submission, JudgeStatus, TestCase

    problem = Problem.query.filter_by(id=problem_id, is_visible=True).first_or_404()
    
    sample_cases = TestCase.query.filter_by(problem_id=problem.id, is_sample=True).all()
    
    acceptance_rate = round(problem.accepted_submissions / problem.total_submissions * 100, 1) if problem.total_submissions > 0 else 0.0
    
    recent_submissions = []
    try:
        submissions = Submission.query.filter_by(problem_id=problem.id).order_by(Submission.submitted_at.desc()).limit(10).all()
        recent_submissions = [
            {
                'id': s.id,
                'user_id': s.user_id,
                'language': s.language,
                'status': s.status.value,
                'execution_time': s.execution_time,
                'memory_usage': s.memory_usage,
                'submitted_at': s.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for s in submissions
        ]
    except Exception as e:
        _logger.error(f"Error fetching submissions: {e}")

    return render_template('problem_detail.html',
                           problem=problem,
                           sample_cases=sample_cases,
                           acceptance_rate=acceptance_rate,
                           recent_submissions=recent_submissions)


def initialize_plugin():
    try:
        _logger.info("Initializing EverJudge main plugin...")

        Config.load()
        _logger.info("Configuration loaded successfully")

        Config.ensure_directories()
        _logger.info("Required directories created")

        app = get_main_application()
        if app is None:
            _logger.warning("Main application not found, skipping initialization")
            return

        flask_app = app.get_flask_instance()
        flask_config = Config.get_flask_config()
        for key, value in flask_config.items():
            flask_app.config[key] = value

        _logger.info("Flask configuration applied")

        db.init_app(flask_app)
        migrate.init_app(flask_app, db)
        _logger.info("Database initialized with migration support")

        _logger.info("EverJudge main plugin initialized successfully")

    except Exception as e:
        _logger.error(f"Failed to initialize EverJudge main plugin: {e}", exc_info=True)
        raise


def register_plugin():
    initialize_plugin()
    app = get_main_application()
    if app is not None:
        app.register_blueprint(main_blueprint)
    else:
        _logger.warning("Main application not found, skipping blueprint registration")


register_plugin()
