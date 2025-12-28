# -*- coding: utf-8 -*-
# EverJudge Main API
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: GPL3
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

# This is the main API of the whole EverJudge.
# Due to security problems, please make sure you're using this API instead of using the EverJudge API directly.

from pathlib import Path

import abc

class LanguageProvider(abc.ABC):
    def __init__(self, language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str):
        self.lang=language
        self.file_name=file_name
        self.exec_name=exec_name
        self.input_=input_folder
        self.output_=output_folder
    
    @abc.abstractmethod
    def compile(self):
        pass

    @abc.abstractmethod
    def interpret(self, group: int=0):
        pass
    
    @abc.abstractmethod
    def judge(self, group: int=0):
        pass


class PureTextProvider(LanguageProvider):
    def compile(self):
        return f"cat 0< {self.file_name} 1> {self.exec_name}"
    
    def interpret(self, group: int=0):
        return f"cat 0< {self.file_name} 1> {self.exec_name}"
    
    def judge(self, group: int=0):
        pass



class Judger(abc.ABC):
    def __init__(self, languages: list | None=None):
        if not languages:
            self.lang=[]
        else:
            self.lang=languages
        
