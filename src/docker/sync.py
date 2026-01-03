"""Code synchronization between host and Docker container"""

import tarfile
import io
from pathlib import Path
from typing import Optional
from docker.models.containers import Container
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CodeSynchronizer:
    """Synchronize code between host and Docker container"""

    def __init__(self, container: Container):
        """
        Initialize code synchronizer.

        Args:
            container: Docker container
        """
        self.container = container

    def copy_to_container(
        self,
        source_path: Path,
        dest_path: str,
        exclude_patterns: Optional[list[str]] = None
    ) -> None:
        """
        Copy files from host to container.

        Args:
            source_path: Source path on host
            dest_path: Destination path in container
            exclude_patterns: Patterns to exclude
        """
        logger.info(f"Copying {source_path} to container:{dest_path}")

        if not source_path.exists():
            raise ValueError(f"Source path does not exist: {source_path}")

        # Create tar archive
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tar.add(
                str(source_path),
                arcname=source_path.name,
                filter=lambda info: self._tar_filter(info, exclude_patterns)
            )

        tar_stream.seek(0)

        # Copy to container
        self.container.put_archive(dest_path, tar_stream)
        logger.info("Copy completed")

    def copy_from_container(
        self,
        source_path: str,
        dest_path: Path
    ) -> None:
        """
        Copy files from container to host.

        Args:
            source_path: Source path in container
            dest_path: Destination path on host
        """
        logger.info(f"Copying container:{source_path} to {dest_path}")

        # Get tar archive from container
        tar_stream, _ = self.container.get_archive(source_path)

        # Extract tar archive
        tar_bytes = b''.join(tar_stream)
        tar_file = io.BytesIO(tar_bytes)

        with tarfile.open(fileobj=tar_file, mode='r') as tar:
            tar.extractall(dest_path.parent)

        logger.info("Copy completed")

    def sync_bidirectional(
        self,
        host_path: Path,
        container_path: str,
        exclude_patterns: Optional[list[str]] = None
    ) -> None:
        """
        Bidirectional sync between host and container.

        Args:
            host_path: Path on host
            container_path: Path in container
            exclude_patterns: Patterns to exclude
        """
        logger.info("Starting bidirectional sync...")

        # Copy to container
        self.copy_to_container(host_path, container_path, exclude_patterns)

        logger.info("Bidirectional sync completed")

    @staticmethod
    def _tar_filter(
        tarinfo: tarfile.TarInfo,
        exclude_patterns: Optional[list[str]]
    ) -> Optional[tarfile.TarInfo]:
        """Filter files for tar archive"""
        if not exclude_patterns:
            return tarinfo

        # Check if file should be excluded
        for pattern in exclude_patterns:
            if pattern in tarinfo.name:
                logger.debug(f"Excluding: {tarinfo.name}")
                return None

        return tarinfo

    def get_default_exclude_patterns(self) -> list[str]:
        """Get default exclude patterns"""
        return [
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".DS_Store",
            ".env"
        ]
