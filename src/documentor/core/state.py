import os
import hashlib
import subprocess
from datetime import datetime
from typing import List, Optional, Literal
import yaml
from pydantic import BaseModel, Field
from pathlib import Path

from documentor.core.config import Config

class PersistedDocState(BaseModel):
    doc_path: str
    tracking_type: Literal["file", "project"]
    source_refs: List[str]
    last_source_hash: str
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def to_ds(self):
        kwargs = self.model_dump()
        kwargs['doc_path'] = Path(kwargs['doc_path'].replace('\\','/'))
        ds = DocState(**kwargs)
        return ds

class DocState(BaseModel):
    doc_path: Path
    tracking_type: Literal["file", "project"]
    source_refs: List[str]
    last_source_hash: str
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def to_pds(self):
        kwargs = self.model_dump()
        kwargs['doc_path'] = str(kwargs['doc_path'])
        pds = PersistedDocState(**kwargs)
        return pds

class PersistedProjectState(BaseModel):
    last_project_hash: str
    managed_docs: List[PersistedDocState] = []

    def to_ps(self):
        kwargs = self.model_dump()
        kwargs['managed_docs'] = [d.to_ds() for d in self.managed_docs]
        return ProjectState(**kwargs)

class ProjectState(BaseModel):
    last_project_hash: str
    managed_docs: List[DocState] = []

    def to_pps(self):
        kwargs = self.model_dump()
        kwargs['managed_docs'] = [d.to_pds() for d in self.managed_docs]
        return PersistedProjectState(**kwargs)

class StateManager:
    def __init__(self, config: Config):
        self.config = config
        self.lock_file = "documentor-lock.yaml"
        self.state = self.load_state()

    def load_state(self) -> ProjectState:
        """Loads state from the lockfile, returns empty state if not found."""
        if self.statefile_exists():
            try:
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    data = yaml.full_load(f) or {}
                return PersistedProjectState(**data).to_ps()
            except Exception:
                pass
        return ProjectState(last_project_hash="")

    def save_state(self):
        """Saves current state to the lockfile."""
        with open(self.lock_file, "w", encoding="utf-8") as f:
            yaml.dump(self.state.to_pps().model_dump(), f, default_flow_style=False, sort_keys=False)

    def get_current_hash(self, paths: Optional[List[str]] = None) -> str:
        """Computes current hash for given paths or the entire project."""
        if paths:
            return self._hash_files(paths)

        if self.config.use_git:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                head_sha = result.stdout.strip()

                status_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                uncommitted_changes = status_result.stdout.strip()
                if not uncommitted_changes:
                    return head_sha

                # tracked changes (staged and unstaged)
                diff_result = subprocess.run(
                    ["git", "diff", "HEAD", "--", ".", ":!documentor.yaml", ":!documentor-lock.yaml"],
                    capture_output=True,
                    check=True
                )

                # untracked files
                untracked_result = subprocess.run(
                    ["git", "ls-files", "--others", "--exclude-standard", "--", ".", ":!documentor.yaml", ":!documentor-lock.yaml"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                untracked_files = untracked_result.stdout.strip().splitlines()
                untracked_hash = self._hash_files(untracked_files) if untracked_files else ""

                combined_payload = diff_result.stdout + untracked_hash.encode()
                diff_hash = hashlib.md5(combined_payload).hexdigest()

                head_sha_with_dirty = f"{head_sha}-dirty-{diff_hash}"
                return head_sha_with_dirty

            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError("Git is not available or this is not a git repository. Cannot compute project hash.")

        return self._hash_project()

    def _hash_files(self, paths: List[str]) -> str:
        """Computes MD5 hash of a list of files."""
        hasher = hashlib.md5()
        for path in sorted(paths):
            if os.path.exists(path) and os.path.isfile(path):
                with open(path, "rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
        return hasher.hexdigest()

    def _hash_project(self) -> str:
        """Computes MD5 hash of the entire project directory (respecting ignores)."""
        hasher = hashlib.md5()
        from documentor.core.parser import Parser
        parser = Parser(self.config)
        context = parser.extract_context()

        # sorting for consistent hash
        for item in sorted(context, key=lambda x: x["path"]):
            hasher.update(item["path"].encode("utf-8"))
            hasher.update(item["content"].encode("utf-8"))
        return hasher.hexdigest()

    def update_doc_state(self, doc_path: Path, tracking_type: Optional[Literal["file", "project"]] = None, source_refs: Optional[List[str]] = None):
        """Updates or adds a DocState entry."""
        current_hash = self.get_current_hash(source_refs if tracking_type == "file" else None)

        existing_doc = next((ds for ds in self.state.managed_docs if ds.doc_path == doc_path), None)
        if existing_doc:
            tracking_type = existing_doc.tracking_type if tracking_type is None else tracking_type
            source_refs = existing_doc.source_refs if source_refs is None else source_refs
        else:
            tracking_type = tracking_type or "project"
            source_refs = source_refs or ["."]
            
        new_doc_state = DocState(
            doc_path=doc_path,
            tracking_type=tracking_type,
            source_refs=source_refs,
            last_source_hash=current_hash,
            updated_at=datetime.now().isoformat()
        )

        for i, ds in enumerate(self.state.managed_docs):
            if ds.doc_path == doc_path:
                self.state.managed_docs[i] = new_doc_state
                break
        else:
            self.state.managed_docs.append(new_doc_state)

        self.state.last_project_hash = self.get_current_hash()
        self.save_state()

    def get_stale_docs(self) -> List[DocState]:
        """Returns a list of DocState objects that are out of sync with their sources."""
        stale = []
        for ds in self.state.managed_docs:
            current_hash = self.get_current_hash(ds.source_refs if ds.tracking_type == "file" else None)
            if current_hash != ds.last_source_hash:
                stale.append(ds)
        return stale

    def statefile_exists(self) -> bool:
        """Checks if the state lockfile exists."""
        return os.path.exists(self.lock_file)
    
    def clear_statefile(self):
        """Deletes the existing state lockfile."""
        if self.statefile_exists():
            os.remove(self.lock_file)
