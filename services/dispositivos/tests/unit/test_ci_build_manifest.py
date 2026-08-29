import unittest
from pathlib import Path


class DispositivosBuildWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow_path = next(
            parent / ".github/workflows/dispositivos-build.yml"
            for parent in Path(__file__).resolve().parents
            if (parent / ".github/workflows/dispositivos-build.yml").is_file()
        )
        cls.workflow = cls.workflow_path.read_text(encoding="utf-8")
        cls.classifier = (
            cls.workflow_path.parent.parent
            / "scripts/dispositivos_build_gate.js"
        ).read_text(encoding="utf-8")

    def test_classifies_dispositivos_runtime_build_inputs_before_building(self):
        for path in (
            '"services/dispositivos/"',
            '"compose.dispositivos.yml"',
            '"config/settings.py"',
            '"docker/django/Dockerfile"',
            '"docker/django/entrypoint.py"',
            '"requirements.txt"',
            '"requirements/"',
        ):
            self.assertIn(path, self.classifier)

        self.assertIn("classify_changes:", self.workflow)
        self.assertIn("needs: classify_changes", self.workflow)
        self.assertIn("dispositivos_build_gate:", self.workflow)

    def test_builds_the_exact_source_checkout_and_records_its_identity(self):
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            self.workflow,
        )
        self.assertIn("git status --porcelain", self.workflow)
        self.assertIn("git archive --format=tar", self.workflow)
        self.assertIn("source_tree_sha256", self.workflow)

    def test_emits_manifest_without_registry_or_deployment_operations(self):
        self.assertIn("docker build --file docker/django/Dockerfile", self.workflow)
        self.assertIn("actions/upload-artifact@v7.0.1", self.workflow)
        self.assertIn("runtime-inputs.txt", self.workflow)
        self.assertIn("base_image_repo_digests", self.workflow)
        self.assertIn('docker pull "$base_image_ref"', self.workflow)
        self.assertIn("dpkg-query -W | sort", self.workflow)
        self.assertNotIn("docker push", self.workflow)
        self.assertNotIn("docker login", self.workflow)
        self.assertNotIn("environment:", self.workflow)
