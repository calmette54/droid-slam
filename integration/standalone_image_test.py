"""Runs the //standalone container image with testcontainers."""

import os
import unittest

import docker
from python.runfiles import Runfiles
from testcontainers.core.container import DockerContainer

# Must match repo_tags of //standalone:load_host_image.
IMAGE = "hello-world:integration-test"


def setUpModule():
    """Loads the image built by Bazel into the container daemon."""
    try:
        client = docker.from_env()
        client.ping()
    except docker.errors.DockerException as e:
        raise RuntimeError(
            "No container daemon reachable; set DOCKER_HOST (see integration/BUILD.bazel)"
        ) from e
    tarball = Runfiles.Create().Rlocation(os.environ["IMAGE_TARBALL"])
    with open(tarball, "rb") as f:
        client.images.load(f)


class StandaloneImageTest(unittest.TestCase):
    def run_image(self, *args):
        """Runs the image to completion; returns (exit code, stdout, stderr)."""
        with DockerContainer(IMAGE).with_command(list(args)) as container:
            result = container.get_wrapped_container().wait(timeout=60)
            stdout, stderr = container.get_logs()
        return result["StatusCode"], stdout.decode(), stderr.decode()

    def test_default_greeting(self):
        self.assertEqual(self.run_image(), (0, "Hello, world!\n", ""))

    def test_name_and_language(self):
        self.assertEqual(self.run_image("Alice", "fr"), (0, "Bonjour, Alice!\n", ""))

    def test_unsupported_language(self):
        code, stdout, stderr = self.run_image("Alice", "xx")
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("unsupported language: xx", stderr)


if __name__ == "__main__":
    unittest.main()
