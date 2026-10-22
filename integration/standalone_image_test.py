"""Runs the //standalone container image with testcontainers."""

import os
import unittest

import docker
from python.runfiles import Runfiles
from testcontainers.core.container import DockerContainer

# Must match repo_tags of //standalone:load_host_image.
IMAGE = "droid-slam:integration-test"


def setUpModule():
    """Loads the image built by Bazel into the container daemon."""
    try:
        # Loading the image (PyTorch + CUDA libraries) takes minutes.
        client = docker.from_env(timeout=1800)
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
        container = DockerContainer(IMAGE)
        if args:
            container = container.with_command(list(args))
        with container:
            result = container.get_wrapped_container().wait(timeout=300)
            stdout, stderr = container.get_logs()
        return result["StatusCode"], stdout.decode(), stderr.decode()

    def test_demo_help(self):
        # Imports torch, lietorch and droid_backends: the runtime is complete.
        code, stdout, stderr = self.run_image()
        self.assertEqual(code, 0, stderr)
        self.assertIn("--imagedir", stdout)

    def test_missing_images(self):
        code, _, stderr = self.run_image("--imagedir=/nonexistent", "--calib=calib/eth.txt")
        self.assertNotEqual(code, 0)
        self.assertIn("No such file or directory: '/nonexistent'", stderr)


if __name__ == "__main__":
    unittest.main()
