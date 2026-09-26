"""An external shell must not inherit another Git or Helm workspace identity."""

from dockyard.service import Service


def test_git_and_helm_override_environment_is_isolated(tmp_path, monkeypatch):
    overrides = {
        "GIT_DIR": "/unrelated/repository/.git",
        "GIT_WORK_TREE": "/unrelated/repository",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.sshCommand",
        "GIT_CONFIG_VALUE_0": "unrelated-command",
        "GIT_CONFIG_GLOBAL": "/unrelated/config",
        "GIT_CONFIG_NOSYSTEM": "0",
        "GIT_TERMINAL_PROMPT": "1",
        "HELM_KUBECONTEXT": "unrelated-context",
        "HELM_NAMESPACE": "unrelated-namespace",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)
    env = Service(tmp_path).environment()
    for key in overrides.keys() - {
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_TERMINAL_PROMPT",
    }:
        assert key not in env
    assert env["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    for key, value in overrides.items():
        # Constructing an environment never edits the host process environment.
        assert __import__("os").environ[key] == value


def test_scanner_uses_private_offline_defaults_without_telemetry(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIVY_CONFIG", "/unrelated/scanner.yaml")
    monkeypatch.setenv("TRIVY_CACHE_DIR", "/unrelated/cache")
    monkeypatch.setenv("TRIVY_DISABLE_TELEMETRY", "false")
    service = Service(tmp_path)
    env = service.environment()
    assert "TRIVY_CONFIG" not in env
    assert env["TRIVY_CACHE_DIR"] == str(service.tools / "trivy")
    for key in (
        "TRIVY_DISABLE_TELEMETRY",
        "TRIVY_OFFLINE_SCAN",
        "TRIVY_SKIP_VERSION_CHECK",
        "TRIVY_SKIP_DB_UPDATE",
        "TRIVY_SKIP_JAVA_DB_UPDATE",
        "TRIVY_SKIP_CHECK_UPDATE",
        "TRIVY_SKIP_VEX_REPO_UPDATE",
    ):
        assert env[key] == "true"
