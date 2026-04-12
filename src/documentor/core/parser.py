import os
import pathspec
from typing import List, Dict, Optional
from documentor.core.config import Config

class Parser:
    def __init__(self, config: Config):
        self.config = config
        self.ignore_spec = self._build_ignore_spec()

    def _build_ignore_spec(self) -> pathspec.PathSpec:
        """Builds a pathspec from config and .gitignore if present."""
        patterns = self.config.ignore_patterns.copy() + ["documentor.yaml", "documentor-lock.yaml"]

        if os.path.exists(".gitignore"):
            with open(".gitignore", "r", encoding="utf-8") as f:
                patterns.extend(f.readlines())

        return pathspec.PathSpec.from_lines('gitignore', patterns)

    def is_ignored(self, path: str) -> bool:
        reasons = [
                self.ignore_spec.match_file(path), # matches ignore spec
                os.path.isfile(path) and os.path.getsize(path) <= self.config.ignore_above_size_kb * 1024 # exceeds ignore threshold
        ]
        return any(reasons)

    def extract_context(self, target: Optional[str] = None) -> List[Dict[str, str]]:
        """Extracts file content for LLM context, respecting ignore patterns."""
        context = []
        base_dir = "." if target is None else str(target)

        if os.path.isfile(base_dir):
            if not self.ignore_spec.match_file(base_dir):
                content = self.read_file(base_dir)
                if content:
                    context.append({"path": base_dir, "content": content})
            return context

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [
                d for d in dirs
                if not self.ignore_spec.match_file(os.path.relpath(os.path.join(root, d), base_dir))
            ]

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)
                if not self.is_ignored(rel_path):
                    content = self.read_file(file_path)
                    if content is not None:
                        context.append({"path": rel_path, "content": content})

        return context

    def get_total_context_size_kb(self, target: Optional[str] = None) -> int:
        """Calculates total size of all non-ignored files in KB."""
        total_size_bytes = 0
        base_dir = "." if target is None else str(target)

        if os.path.isfile(base_dir):
            if not self.ignore_spec.match_file(base_dir):
                total_size_bytes += os.path.getsize(base_dir)
            return total_size_bytes // 1024

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [
                d for d in dirs
                if not self.ignore_spec.match_file(os.path.relpath(os.path.join(root, d), base_dir))
            ]

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)
                if not self.is_ignored(rel_path):
                    try:
                        total_size_bytes += os.path.getsize(file_path)
                    except OSError:
                        pass

        return total_size_bytes // 1024

    def list_files_for_agent(self, target: Optional[str] = None) -> List[str]:
        """Lists all non-ignored file paths for agent exploration."""
        file_list = []
        base_dir = "." if target is None else str(target)

        if os.path.isfile(base_dir):
            if not self.ignore_spec.match_file(base_dir):
                file_list.append(base_dir)
            return file_list

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [
                d for d in dirs
                if not self.ignore_spec.match_file(os.path.relpath(os.path.join(root, d), base_dir))
            ]

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)

                if not self.ignore_spec.match_file(rel_path):
                    file_list.append(rel_path)

        return file_list

    def read_file(self, file_path: str) -> Optional[str]:
        """Reads a file, returning None if binary or unreadable."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            return None # skip binary files
        except Exception:
            return None
