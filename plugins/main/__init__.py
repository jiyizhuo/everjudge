# -*- coding: utf-8 -*-
# EverJudge Main
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: GPL3
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

import logging
from flask import render_template, request

from everjudge.api import *
from .config_loader import Config
from .database import db
from .db_init import init_database

_logger = logging.getLogger("EverJudge Main")

main_blueprint = create_blueprint("main", "/")

@main_blueprint.route("/")
def root():
    # This is an example data
    # Will remove later

    # 模拟公告数据
    announcements = [
        {'title': 'EverJudge v1.0 正式上线！', 'date': '2025-03-15'},
        {'title': '欢迎加入 EverJudge 社区', 'date': '2025-03-15'},
        {'title': '关于难度评级系统的说明 (0-9)', 'date': '2025-03-14'},
    ]

    # 模拟统计数据
    stats = {
        'total_users': 1024,
        'total_submissions': 8964
    }

    # 模拟题目数据
    recent_problems = [
        {'id': 1001, 'title': 'A+B Problem', 'difficulty': 0, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 98.5},
        {'id': 1002, 'title': '斐波那契数列', 'difficulty': 2, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 85.2},
        {'id': 1003, 'title': '快速排序实现', 'difficulty': 4, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 62.0},
        {'id': 1004, 'title': '最短路径', 'difficulty': 6, 'time_limit': 2000, 'memory_limit': 512, 'acceptance_rate': 34.5},
        {'id': 1005, 'title': '动态规划进阶', 'difficulty': 8, 'time_limit': 3000, 'memory_limit': 512, 'acceptance_rate': 12.1},
        {'id': 1006, 'title': '复杂的图论难题', 'difficulty': 9, 'time_limit': 5000, 'memory_limit': 1024, 'acceptance_rate': 2.3},
    ]

    # 模拟比赛数据
    contests = [
        {'title': 'EverJudge 开幕赛', 'start_time': '2025-03-20 19:00', 'status': 'upcoming'},
        {'title': '新手入门场', 'start_time': '2025-03-18 14:00', 'status': 'running'},
    ]

    # 模拟用户排名
    top_users = [
        {'username': 'Ayanami', 'rating': 3000},
        {'username': 'admin', 'rating': 2500},
        {'username': 'user1', 'rating': 2100},
        {'username': 'guest', 'rating': 1500},
        {'username': 'newbie', 'rating': 1200},
    ]

    return render_template('index.html', 
                           announcements=announcements, 
                           stats=stats, 
                           recent_problems=recent_problems,
                           contests=contests,
                           top_users=top_users)

@main_blueprint.route("/problems")
def problems():
    # 获取查询参数
    search = request.args.get('search', '')
    difficulty = request.args.get('difficulty', '')
    set_filter = request.args.get('set', '')
    solved = request.args.get('solved', '') == 'true'
    sort_by = request.args.get('sort', 'id')
    page = int(request.args.get('page', 1))
    
    # 模拟题目数据库
    all_problems = [
        {'id': 1001, 'title': 'A+B Problem', 'difficulty': 0, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 98.5, 'tags': ['基础', '输入输出'], 'is_new': True},
        {'id': 1002, 'title': '斐波那契数列', 'difficulty': 2, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 85.2, 'tags': ['递归', '数学'], 'is_new': True},
        {'id': 1003, 'title': '快速排序实现', 'difficulty': 4, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 62.0, 'tags': ['排序', '数组'], 'is_new': False},
        {'id': 1004, 'title': '最短路径', 'difficulty': 6, 'time_limit': 2000, 'memory_limit': 512, 'acceptance_rate': 34.5, 'tags': ['图论', '搜索'], 'is_new': False},
        {'id': 1005, 'title': '动态规划进阶', 'difficulty': 8, 'time_limit': 3000, 'memory_limit': 512, 'acceptance_rate': 12.1, 'tags': ['动态规划', '数学'], 'is_new': False},
        {'id': 1006, 'title': '复杂的图论难题', 'difficulty': 9, 'time_limit': 5000, 'memory_limit': 1024, 'acceptance_rate': 2.3, 'tags': ['图论', '搜索', '困难'], 'is_new': False},
        {'id': 1007, 'title': '字符串处理', 'difficulty': 3, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 78.5, 'tags': ['字符串', '基础'], 'is_new': True},
        {'id': 1008, 'title': '二叉树遍历', 'difficulty': 5, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 55.3, 'tags': ['树', '递归'], 'is_new': False},
        {'id': 1009, 'title': '背包问题', 'difficulty': 7, 'time_limit': 2000, 'memory_limit': 512, 'acceptance_rate': 28.7, 'tags': ['动态规划', '搜索'], 'is_new': False},
        {'id': 1010, 'title': '数论基础', 'difficulty': 4, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 65.2, 'tags': ['数学', '数论'], 'is_new': True},
        {'id': 1011, 'title': '线段树入门', 'difficulty': 8, 'time_limit': 2000, 'memory_limit': 512, 'acceptance_rate': 18.4, 'tags': ['数据结构', '动态规划'], 'is_new': False},
        {'id': 1012, 'title': '网络流', 'difficulty': 9, 'time_limit': 3000, 'memory_limit': 1024, 'acceptance_rate': 5.6, 'tags': ['图论', '困难'], 'is_new': False},
        {'id': 1013, 'title': '模拟队列', 'difficulty': 1, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 92.1, 'tags': ['数据结构', '基础'], 'is_new': True},
        {'id': 1014, 'title': '栈的应用', 'difficulty': 2, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 88.3, 'tags': ['数据结构', '基础'], 'is_new': True},
        {'id': 1015, 'title': '哈希表', 'difficulty': 3, 'time_limit': 1000, 'memory_limit': 256, 'acceptance_rate': 76.8, 'tags': ['数据结构', '搜索'], 'is_new': False},
    ]
    
    # 筛选题目
    filtered_problems = all_problems.copy()
    
    # 搜索筛选
    if search:
        search_lower = search.lower()
        filtered_problems = [p for p in filtered_problems 
                           if search_lower in p['title'].lower() 
                           or search_lower in str(p['id'])
                           or any(search_lower in tag.lower() for tag in p['tags'])]
    
    # 难度筛选
    if difficulty:
        min_diff, max_diff = map(int, difficulty.split('-'))
        filtered_problems = [p for p in filtered_problems 
                           if min_diff <= p['difficulty'] <= max_diff]
    
    # 题库筛选（模拟 TODO: 替换为真实数据库查询）
    # 题库是独立的分类系统，不与难度挂钩
    if set_filter:
        if set_filter == 'basic':
            filtered_problems = [p for p in filtered_problems if p['id'] in [1001, 1002, 1007, 1013, 1014, 1015]]
        elif set_filter == 'advanced':
            filtered_problems = [p for p in filtered_problems if p['id'] in [1003, 1008, 1010]]
        elif set_filter == 'contest':
            filtered_problems = [p for p in filtered_problems if p['id'] in [1004, 1005, 1006, 1009, 1011, 1012]]
    
    # 已解决筛选（模拟 TODO: 替换为真实数据库查询）
    if solved:
        filtered_problems = [p for p in filtered_problems if p['id'] in [1001, 1002, 1007]]
    
    # 排序
    if sort_by == 'difficulty':
        filtered_problems.sort(key=lambda x: x['difficulty'])
    elif sort_by == 'acceptance':
        filtered_problems.sort(key=lambda x: x['acceptance_rate'], reverse=True)
    else:
        filtered_problems.sort(key=lambda x: x['id'])
    
    # 分页
    per_page = 10
    total_problems = len(filtered_problems)
    total_pages = (total_problems + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    problems = filtered_problems[start_idx:end_idx]
    
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
                           problems=problems,
                           total_problems=total_problems,
                           current_page=page,
                           total_pages=total_pages,
                           page_numbers=page_numbers)


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
        _logger.info("Database initialized")

        init_database(flask_app)
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
