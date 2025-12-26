# -*- coding: utf-8 -*-
# EverJudge Main
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: GPL3
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.
from flask import render_template

from everjudge.api import *

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

get_main_application().register_blueprint(main_blueprint)
