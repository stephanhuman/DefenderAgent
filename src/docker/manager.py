"""Docker container management"""

from typing import Optional, Dict, Any
import docker
from docker.models.containers import Container
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DockerManager:
    """Manage Docker containers for coding tasks"""

    def __init__(self):
        """Initialize Docker manager"""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def get_or_create_container(
        self,
        image: str = "defender-agent:latest",
        name: str = "defender-agent",
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> Container:
        """
        Get existing container or create a new one.

        Args:
            image: Docker image name
            name: Container name
            volumes: Volume mappings
            environment: Environment variables

        Returns:
            Docker container object
        """
        try:
            # Try to get existing container
            container = self.client.containers.get(name)
            logger.info(f"Found existing container: {name}")

            # Start if not running
            if container.status != "running":
                container.start()
                logger.info(f"Started container: {name}")

            return container

        except docker.errors.NotFound:
            logger.info(f"Creating new container: {name}")
            return self._create_container(image, name, volumes, environment)

    def _create_container(
        self,
        image: str,
        name: str,
        volumes: Optional[Dict[str, Dict[str, str]]],
        environment: Optional[Dict[str, str]]
    ) -> Container:
        """Create a new container"""
        container = self.client.containers.run(
            image=image,
            name=name,
            volumes=volumes or {},
            environment=environment or {},
            detach=True,
            tty=True,
            stdin_open=True,
            network_mode="bridge"
        )

        logger.info(f"Created container: {name} ({container.short_id})")
        return container

    def execute_command(
        self,
        container: Container,
        command: str,
        workdir: Optional[str] = None
    ) -> tuple[int, str]:
        """
        Execute command in container.

        Args:
            container: Docker container
            command: Command to execute
            workdir: Working directory

        Returns:
            Tuple of (exit_code, output)
        """
        logger.info(f"Executing command: {command}")

        exec_result = container.exec_run(
            cmd=command,
            workdir=workdir,
            stdout=True,
            stderr=True
        )

        output = exec_result.output.decode("utf-8")
        exit_code = exec_result.exit_code

        if exit_code != 0:
            logger.warning(f"Command failed with exit code {exit_code}")
        else:
            logger.info("Command executed successfully")

        return exit_code, output

    def stop_container(self, container: Container) -> None:
        """Stop a container"""
        logger.info(f"Stopping container: {container.name}")
        container.stop()

    def remove_container(self, container: Container, force: bool = False) -> None:
        """Remove a container"""
        logger.info(f"Removing container: {container.name}")
        container.remove(force=force)

    def get_container_stats(self, container: Container) -> Dict[str, Any]:
        """Get container statistics"""
        stats = container.stats(stream=False)
        return stats

    def get_container_logs(
        self,
        container: Container,
        tail: int = 100
    ) -> str:
        """Get container logs"""
        logs = container.logs(tail=tail, timestamps=True)
        return logs.decode("utf-8")

    def list_containers(self, all_containers: bool = False) -> list:
        """List all containers"""
        containers = self.client.containers.list(all=all_containers)
        return containers

    def build_image(
        self,
        path: str,
        tag: str,
        dockerfile: str = "Dockerfile"
    ) -> None:
        """
        Build Docker image.

        Args:
            path: Build context path
            tag: Image tag
            dockerfile: Dockerfile name
        """
        logger.info(f"Building image: {tag}")

        image, build_logs = self.client.images.build(
            path=path,
            tag=tag,
            dockerfile=dockerfile,
            rm=True
        )

        for log in build_logs:
            if "stream" in log:
                logger.debug(log["stream"].strip())

        logger.info(f"Successfully built image: {tag}")

    def cleanup(self) -> None:
        """Clean up Docker resources"""
        logger.info("Cleaning up Docker resources...")

        # Remove stopped containers
        containers = self.client.containers.list(
            all=True,
            filters={"status": "exited"}
        )
        for container in containers:
            if container.name.startswith("defender-agent"):
                logger.info(f"Removing stopped container: {container.name}")
                container.remove()

        # Prune unused volumes
        self.client.volumes.prune()

        logger.info("Docker cleanup completed")
