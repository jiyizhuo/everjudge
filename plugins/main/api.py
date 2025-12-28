# -*- coding: utf-8 -*-
# EverJudge Main API
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: BSD 3-Clause License
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

# This is the main API of the whole EverJudge.
# Due to security problems, please make sure you're using this API instead of using the EverJudge API directly.

from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass

import abc
import logging
import subprocess
import os

_logger = logging.getLogger("EverJudge Main API")


class JudgeResult(Enum):
    AC = "Accepted"
    WA = "Wrong Answer"
    TLE = "Time Limit Exceeded"
    MLE = "Memory Limit Exceeded"
    RE = "Runtime Error"
    CE = "Compilation Error"
    SE = "System Error"
    PE = "Presentation Error"


@dataclass
class TestCase:
    input_file: str
    output_file: str
    time_limit: int
    memory_limit: int


class LanguageProvider(abc.ABC):
    def __init__(self, language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str):
        self.lang = language
        self.file_name = file_name
        self.exec_name = exec_name
        self.input_ = input_folder
        self.output_ = output_folder
        self._compiled = False
        _logger.debug(f"LanguageProvider initialized for language: {language}")

    @abc.abstractmethod
    def compile(self) -> tuple[bool, str]:
        pass

    @abc.abstractmethod
    def interpret(self, group: int = 0) -> tuple[bool, str]:
        pass

    @abc.abstractmethod
    def judge(self, group: int = 0) -> JudgeResult:
        pass

    def get_compile_command(self) -> str:
        return ""

    def get_run_command(self) -> str:
        return ""

    def is_compiled(self) -> bool:
        return self._compiled

    def set_compiled(self, compiled: bool) -> None:
        self._compiled = compiled


class PureTextProvider(LanguageProvider):
    def compile(self) -> tuple[bool, str]:
        _logger.debug(f"PureTextProvider: Skipping compilation for {self.file_name}")
        self.set_compiled(True)
        return True, "No compilation needed for pure text"

    def interpret(self, group: int = 0) -> tuple[bool, str]:
        _logger.debug(f"PureTextProvider: Interpreting {self.file_name} with group {group}")
        try:
            input_file = os.path.join(self.input_, f"{group}.in")
            output_file = os.path.join(self.output_, f"{group}.out")
            
            if not os.path.exists(input_file):
                return False, f"Input file {input_file} not found"
            
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                content = infile.read()
                outfile.write(content)
            
            _logger.info(f"PureTextProvider: Successfully interpreted group {group}")
            return True, "Execution completed"
        except Exception as e:
            _logger.error(f"PureTextProvider: Error during interpretation: {e}")
            return False, str(e)

    def judge(self, group: int = 0) -> JudgeResult:
        _logger.debug(f"PureTextProvider: Judging group {group}")
        try:
            success, message = self.interpret(group)
            if success:
                _logger.info(f"PureTextProvider: Group {group} accepted")
                return JudgeResult.AC
            else:
                _logger.warning(f"PureTextProvider: Group {group} failed: {message}")
                return JudgeResult.RE
        except Exception as e:
            _logger.error(f"PureTextProvider: Error during judging: {e}")
            return JudgeResult.SE


class CProvider(LanguageProvider):
    def __init__(self, language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str, compiler: str = "gcc"):
        super().__init__(language, file_name, exec_name, input_folder, output_folder)
        self.compiler = compiler
        self.compile_flags = ["-O2", "-Wall"]

    def get_compile_command(self) -> str:
        flags = " ".join(self.compile_flags)
        return f"{self.compiler} {flags} {self.file_name} -o {self.exec_name}"

    def compile(self) -> tuple[bool, str]:
        _logger.debug(f"CProvider: Compiling {self.file_name}")
        try:
            cmd = self.get_compile_command()
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.set_compiled(True)
                _logger.info(f"CProvider: Successfully compiled {self.file_name}")
                return True, "Compilation successful"
            else:
                error_msg = result.stderr or result.stdout
                _logger.error(f"CProvider: Compilation failed: {error_msg}")
                return False, error_msg
        except subprocess.TimeoutExpired:
            _logger.error(f"CProvider: Compilation timeout for {self.file_name}")
            return False, "Compilation timeout"
        except Exception as e:
            _logger.error(f"CProvider: Compilation error: {e}")
            return False, str(e)

    def interpret(self, group: int = 0) -> tuple[bool, str]:
        _logger.debug(f"CProvider: Interpreting {self.file_name} with group {group}")
        if not self.is_compiled():
            success, message = self.compile()
            if not success:
                return False, f"Compilation failed: {message}"

        try:
            input_file = os.path.join(self.input_, f"{group}.in")
            output_file = os.path.join(self.output_, f"{group}.out")
            
            if not os.path.exists(input_file):
                return False, f"Input file {input_file} not found"
            
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                result = subprocess.run(
                    f"./{self.exec_name}",
                    stdin=infile,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
            
            if result.returncode != 0:
                _logger.warning(f"CProvider: Execution failed with return code {result.returncode}")
                return False, f"Runtime error: {result.stderr}"
            
            _logger.info(f"CProvider: Successfully interpreted group {group}")
            return True, "Execution completed"
        except subprocess.TimeoutExpired:
            _logger.warning(f"CProvider: Execution timeout for group {group}")
            return False, "Time limit exceeded"
        except Exception as e:
            _logger.error(f"CProvider: Execution error: {e}")
            return False, str(e)

    def judge(self, group: int = 0) -> JudgeResult:
        _logger.debug(f"CProvider: Judging group {group}")
        try:
            success, message = self.interpret(group)
            if success:
                _logger.info(f"CProvider: Group {group} accepted")
                return JudgeResult.AC
            else:
                if "timeout" in message.lower():
                    return JudgeResult.TLE
                elif "compilation" in message.lower():
                    return JudgeResult.CE
                else:
                    return JudgeResult.RE
        except Exception as e:
            _logger.error(f"CProvider: Error during judging: {e}")
            return JudgeResult.SE


class CppProvider(LanguageProvider):
    def __init__(self, language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str, compiler: str = "g++"):
        super().__init__(language, file_name, exec_name, input_folder, output_folder)
        self.compiler = compiler
        self.compile_flags = ["-O2", "-Wall", "-std=c++17"]

    def get_compile_command(self) -> str:
        flags = " ".join(self.compile_flags)
        return f"{self.compiler} {flags} {self.file_name} -o {self.exec_name}"

    def compile(self) -> tuple[bool, str]:
        _logger.debug(f"CppProvider: Compiling {self.file_name}")
        try:
            cmd = self.get_compile_command()
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.set_compiled(True)
                _logger.info(f"CppProvider: Successfully compiled {self.file_name}")
                return True, "Compilation successful"
            else:
                error_msg = result.stderr or result.stdout
                _logger.error(f"CppProvider: Compilation failed: {error_msg}")
                return False, error_msg
        except subprocess.TimeoutExpired:
            _logger.error(f"CppProvider: Compilation timeout for {self.file_name}")
            return False, "Compilation timeout"
        except Exception as e:
            _logger.error(f"CppProvider: Compilation error: {e}")
            return False, str(e)

    def interpret(self, group: int = 0) -> tuple[bool, str]:
        _logger.debug(f"CppProvider: Interpreting {self.file_name} with group {group}")
        if not self.is_compiled():
            success, message = self.compile()
            if not success:
                return False, f"Compilation failed: {message}"

        try:
            input_file = os.path.join(self.input_, f"{group}.in")
            output_file = os.path.join(self.output_, f"{group}.out")
            
            if not os.path.exists(input_file):
                return False, f"Input file {input_file} not found"
            
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                result = subprocess.run(
                    f"./{self.exec_name}",
                    stdin=infile,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
            
            if result.returncode != 0:
                _logger.warning(f"CppProvider: Execution failed with return code {result.returncode}")
                return False, f"Runtime error: {result.stderr}"
            
            _logger.info(f"CppProvider: Successfully interpreted group {group}")
            return True, "Execution completed"
        except subprocess.TimeoutExpired:
            _logger.warning(f"CppProvider: Execution timeout for group {group}")
            return False, "Time limit exceeded"
        except Exception as e:
            _logger.error(f"CppProvider: Execution error: {e}")
            return False, str(e)

    def judge(self, group: int = 0) -> JudgeResult:
        _logger.debug(f"CppProvider: Judging group {group}")
        try:
            success, message = self.interpret(group)
            if success:
                _logger.info(f"CppProvider: Group {group} accepted")
                return JudgeResult.AC
            else:
                if "timeout" in message.lower():
                    return JudgeResult.TLE
                elif "compilation" in message.lower():
                    return JudgeResult.CE
                else:
                    return JudgeResult.RE
        except Exception as e:
            _logger.error(f"CppProvider: Error during judging: {e}")
            return JudgeResult.SE


class PythonProvider(LanguageProvider):
    def __init__(self, language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str, python_cmd: str = "python3"):
        super().__init__(language, file_name, exec_name, input_folder, output_folder)
        self.python_cmd = python_cmd

    def get_run_command(self) -> str:
        return f"{self.python_cmd} {self.file_name}"

    def compile(self) -> tuple[bool, str]:
        _logger.debug(f"PythonProvider: Checking syntax for {self.file_name}")
        try:
            result = subprocess.run(
                [self.python_cmd, "-m", "py_compile", self.file_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.set_compiled(True)
                _logger.info(f"PythonProvider: Syntax check passed for {self.file_name}")
                return True, "Syntax check passed"
            else:
                error_msg = result.stderr or result.stdout
                _logger.error(f"PythonProvider: Syntax error: {error_msg}")
                return False, error_msg
        except subprocess.TimeoutExpired:
            _logger.error(f"PythonProvider: Syntax check timeout for {self.file_name}")
            return False, "Syntax check timeout"
        except Exception as e:
            _logger.error(f"PythonProvider: Syntax check error: {e}")
            return False, str(e)

    def interpret(self, group: int = 0) -> tuple[bool, str]:
        _logger.debug(f"PythonProvider: Interpreting {self.file_name} with group {group}")
        if not self.is_compiled():
            success, message = self.compile()
            if not success:
                return False, f"Syntax check failed: {message}"

        try:
            input_file = os.path.join(self.input_, f"{group}.in")
            output_file = os.path.join(self.output_, f"{group}.out")
            
            if not os.path.exists(input_file):
                return False, f"Input file {input_file} not found"
            
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                result = subprocess.run(
                    [self.python_cmd, self.file_name],
                    stdin=infile,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
            
            if result.returncode != 0:
                _logger.warning(f"PythonProvider: Execution failed with return code {result.returncode}")
                return False, f"Runtime error: {result.stderr}"
            
            _logger.info(f"PythonProvider: Successfully interpreted group {group}")
            return True, "Execution completed"
        except subprocess.TimeoutExpired:
            _logger.warning(f"PythonProvider: Execution timeout for group {group}")
            return False, "Time limit exceeded"
        except Exception as e:
            _logger.error(f"PythonProvider: Execution error: {e}")
            return False, str(e)

    def judge(self, group: int = 0) -> JudgeResult:
        _logger.debug(f"PythonProvider: Judging group {group}")
        try:
            success, message = self.interpret(group)
            if success:
                _logger.info(f"PythonProvider: Group {group} accepted")
                return JudgeResult.AC
            else:
                if "timeout" in message.lower():
                    return JudgeResult.TLE
                elif "syntax" in message.lower():
                    return JudgeResult.CE
                else:
                    return JudgeResult.RE
        except Exception as e:
            _logger.error(f"PythonProvider: Error during judging: {e}")
            return JudgeResult.SE


class JavaProvider(LanguageProvider):
    def __init__(self, language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str, java_cmd: str = "javac", run_cmd: str = "java"):
        super().__init__(language, file_name, exec_name, input_folder, output_folder)
        self.java_cmd = java_cmd
        self.run_cmd = run_cmd
        self.class_name = None

    def get_compile_command(self) -> str:
        return f"{self.java_cmd} {self.file_name}"

    def get_run_command(self) -> str:
        if self.class_name:
            return f"{self.run_cmd} {self.class_name}"
        return f"{self.run_cmd} {self.exec_name}"

    def compile(self) -> tuple[bool, str]:
        _logger.debug(f"JavaProvider: Compiling {self.file_name}")
        try:
            cmd = self.get_compile_command()
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.set_compiled(True)
                self.class_name = Path(self.file_name).stem
                _logger.info(f"JavaProvider: Successfully compiled {self.file_name}")
                return True, "Compilation successful"
            else:
                error_msg = result.stderr or result.stdout
                _logger.error(f"JavaProvider: Compilation failed: {error_msg}")
                return False, error_msg
        except subprocess.TimeoutExpired:
            _logger.error(f"JavaProvider: Compilation timeout for {self.file_name}")
            return False, "Compilation timeout"
        except Exception as e:
            _logger.error(f"JavaProvider: Compilation error: {e}")
            return False, str(e)

    def interpret(self, group: int = 0) -> tuple[bool, str]:
        _logger.debug(f"JavaProvider: Interpreting {self.file_name} with group {group}")
        if not self.is_compiled():
            success, message = self.compile()
            if not success:
                return False, f"Compilation failed: {message}"

        try:
            input_file = os.path.join(self.input_, f"{group}.in")
            output_file = os.path.join(self.output_, f"{group}.out")
            
            if not os.path.exists(input_file):
                return False, f"Input file {input_file} not found"
            
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                result = subprocess.run(
                    self.get_run_command().split(),
                    stdin=infile,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
            
            if result.returncode != 0:
                _logger.warning(f"JavaProvider: Execution failed with return code {result.returncode}")
                return False, f"Runtime error: {result.stderr}"
            
            _logger.info(f"JavaProvider: Successfully interpreted group {group}")
            return True, "Execution completed"
        except subprocess.TimeoutExpired:
            _logger.warning(f"JavaProvider: Execution timeout for group {group}")
            return False, "Time limit exceeded"
        except Exception as e:
            _logger.error(f"JavaProvider: Execution error: {e}")
            return False, str(e)

    def judge(self, group: int = 0) -> JudgeResult:
        _logger.debug(f"JavaProvider: Judging group {group}")
        try:
            success, message = self.interpret(group)
            if success:
                _logger.info(f"JavaProvider: Group {group} accepted")
                return JudgeResult.AC
            else:
                if "timeout" in message.lower():
                    return JudgeResult.TLE
                elif "compilation" in message.lower():
                    return JudgeResult.CE
                else:
                    return JudgeResult.RE
        except Exception as e:
            _logger.error(f"JavaProvider: Error during judging: {e}")
            return JudgeResult.SE


class Judger(abc.ABC):
    def __init__(self, languages: Optional[List[str]] = None):
        self.lang = languages if languages else []
        self._providers: Dict[str, LanguageProvider] = {}
        _logger.debug(f"Judger initialized with languages: {self.lang}")

    @abc.abstractmethod
    def register_provider(self, language: str, provider: LanguageProvider) -> None:
        pass

    @abc.abstractmethod
    def get_provider(self, language: str) -> Optional[LanguageProvider]:
        pass

    @abc.abstractmethod
    def judge(self, language: str, group: int = 0) -> JudgeResult:
        pass

    @abc.abstractmethod
    def judge_all(self, language: str, groups: List[int]) -> List[JudgeResult]:
        pass

    def get_supported_languages(self) -> List[str]:
        return list(self._providers.keys())

    def is_language_supported(self, language: str) -> bool:
        return language in self._providers


class StandardJudger(Judger):
    def __init__(self, languages: Optional[List[str]] = None):
        super().__init__(languages)
        _logger.info("StandardJudger initialized")

    def register_provider(self, language: str, provider: LanguageProvider) -> None:
        _logger.info(f"Registering provider for language: {language}")
        self._providers[language] = provider

    def get_provider(self, language: str) -> Optional[LanguageProvider]:
        if language in self._providers:
            _logger.debug(f"Retrieved provider for language: {language}")
            return self._providers[language]
        _logger.warning(f"Provider not found for language: {language}")
        return None

    def judge(self, language: str, group: int = 0) -> JudgeResult:
        _logger.info(f"Judging language: {language}, group: {group}")
        provider = self.get_provider(language)
        if not provider:
            _logger.error(f"No provider found for language: {language}")
            return JudgeResult.SE

        try:
            result = provider.judge(group)
            _logger.info(f"Judging completed for language: {language}, group: {group}, result: {result.value}")
            return result
        except Exception as e:
            _logger.error(f"Error during judging: {e}")
            return JudgeResult.SE

    def judge_all(self, language: str, groups: List[int]) -> List[JudgeResult]:
        _logger.info(f"Judging language: {language}, groups: {groups}")
        results = []
        for group in groups:
            result = self.judge(language, group)
            results.append(result)
        _logger.info(f"Judging completed for language: {language}, results: {[r.value for r in results]}")
        return results


def create_language_provider(language: str, file_name: str, exec_name: str, input_folder: str, output_folder: str, **kwargs) -> Optional[LanguageProvider]:
    provider_map = {
        "c": CProvider,
        "cpp": CppProvider,
        "python": PythonProvider,
        "python3": PythonProvider,
        "java": JavaProvider,
        "text": PureTextProvider,
    }

    language_lower = language.lower()
    provider_class = provider_map.get(language_lower)

    if not provider_class:
        _logger.error(f"Unsupported language: {language}")
        return None

    _logger.info(f"Creating language provider for: {language}")
    return provider_class(language, file_name, exec_name, input_folder, output_folder, **kwargs)


def create_judger(judger_type: str = "standard", languages: Optional[List[str]] = None) -> Optional[Judger]:
    judger_map = {
        "standard": StandardJudger,
    }

    judger_class = judger_map.get(judger_type.lower())

    if not judger_class:
        _logger.error(f"Unsupported judger type: {judger_type}")
        return None

    _logger.info(f"Creating judger of type: {judger_type}")
    return judger_class(languages)
