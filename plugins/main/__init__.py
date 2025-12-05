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
    return render_template("_page.html")

get_main_application().register_blueprint(main_blueprint)
