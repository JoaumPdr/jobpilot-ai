"""Regressões da configuração local do launcher e do hook da Alethe."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts import jobpilot_codex

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts/JobPilot-Codex.ps1"
POLICY = "ALETHE_ORCHESTRATE_POLICY"
PLAYBOOKS = "ALETHE_ORCHESTRATE_PLAYBOOKS"
HOME = "ALETHE_ORCHESTRATE_HOME"
SESSION = "jobpilot-test-session"


@pytest.fixture
def project(tmp_path, monkeypatch):
    local = tmp_path / "local"
    appdata = tmp_path / "roaming"
    project = local / "Alethe/JobPilot-AI"
    project.mkdir(parents=True)
    appdata.mkdir()
    policy = {
        "version": 1,
        "onboarded": True,
        "backend": "skill",
        "providerSwitch": "never",
    }
    (project / "alethe-orchestrate.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    shutil.copyfile(
        jobpilot_codex.ALETHE_SCRIPTS.parent / "playbooks.yaml",
        project / "alethe-playbooks.yaml",
    )
    for name in (PLAYBOOKS, HOME, "ALETHE_PASSIVE", "ALETHE_ORCHESTRATE_WORKER"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(appdata))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    monkeypatch.setenv("CODEX_SESSION_ID", SESSION)
    monkeypatch.setenv("JOBPILOT_CODEX_STARTED_AT", str(time.time() - 60))
    monkeypatch.setenv(POLICY, str(project / "alethe-orchestrate.json"))
    return project


def test_check_resolves_optional_paths_without_changing_environment(project):
    before = dict(os.environ)
    result = jobpilot_codex.validate_session(project, check_hooks=True)
    assert os.environ == before
    assert result["paths"] == {
        "policy": str(project / "alethe-orchestrate.json"),
        "playbooks": str(project / "alethe-playbooks.yaml"),
        "home": str(project / "orchestrations"),
    }
    assert result["hooks"]["status"] == "pending"


@pytest.mark.parametrize(
    ("variable", "filename", "message"),
    [
        (POLICY, None, "Política efetiva"),
        (PLAYBOOKS, "external.yaml", "Playbooks efetivos"),
        (PLAYBOOKS, "missing.yaml", "Playbooks efetivos"),
        (HOME, "external-state", "Diretório de estado efetivo"),
    ],
)
def test_check_rejects_fallback_and_external_paths(
    project, monkeypatch, variable, filename, message
):
    if filename is None:
        monkeypatch.delenv(variable)
    else:
        external = project.parent / filename
        if filename == "external.yaml":
            shutil.copyfile(project / "alethe-playbooks.yaml", external)
        monkeypatch.setenv(variable, str(external))
    with pytest.raises(ValueError, match=message):
        jobpilot_codex.validate_session(project, check_hooks=True)


@pytest.mark.parametrize(
    "filename", ["alethe-orchestrate.json", "alethe-playbooks.yaml"]
)
def test_check_rejects_invalid_project_files(project, filename):
    (project / filename).write_text("invalid: [", encoding="utf-8")
    with pytest.raises(ValueError):
        jobpilot_codex.validate_session(project, check_hooks=True)


def run_passive_hook(project: Path) -> Path:
    """Executa o hook real com um evento sintético e um transcript inexistente."""
    event = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": SESSION,
        "cwd": str(project),
        "transcript_path": str(project / "no-transcript.jsonl"),
    }
    subprocess.run(
        [sys.executable, "-B", "-S", str(jobpilot_codex.ALETHE_SCRIPTS / "hook.py")],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        check=True,
        timeout=20,
    )
    return next((project / "orchestrations/passive").glob(f"{SESSION}-*.json"))


def test_check_confirms_real_hook_with_inferred_paths(project):
    state = run_passive_hook(project)
    result = jobpilot_codex.validate_session(project, check_hooks=True)
    assert result["hooks"]["status"] == "confirmed"
    assert str(state) in result["hooks"]["detail"]


@pytest.mark.parametrize("scenario", ["stale", "foreign_playbooks", "global_state"])
def test_check_does_not_confirm_unrelated_hook_evidence(project, monkeypatch, scenario):
    if scenario == "foreign_playbooks":
        books = project / "alethe-playbooks.yaml"
        alternate = project.parent / "alternate.yaml"
        alternate.write_text(
            books.read_text(encoding="utf-8").replace(
                "checkEveryMinutes: 15", "checkEveryMinutes: 23"
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv(PLAYBOOKS, str(alternate))
    state = run_passive_hook(project)
    if scenario == "stale":
        cutoff = float(os.environ["JOBPILOT_CODEX_STARTED_AT"])
        os.utime(state, (cutoff - 1, cutoff - 1))
    elif scenario == "foreign_playbooks":
        monkeypatch.delenv(PLAYBOOKS)
    else:
        global_passive = Path(os.environ["APPDATA"]) / "Alethe/orchestrations/passive"
        global_passive.mkdir(parents=True)
        shutil.copyfile(state, global_passive / state.name)
    evidence = jobpilot_codex.validate_session(project, check_hooks=True)["hooks"]
    assert evidence["status"] == ("pending" if scenario == "stale" else "wrong")


@pytest.mark.skipif(os.name != "nt", reason="O launcher usa PowerShell no Windows.")
def test_launcher_check_session_preserves_inherited_resolution(project, monkeypatch):
    pending = powershell("check-session")
    assert pending.returncode == 2, pending.stderr
    assert "Hook Alethe (pending)" in pending.stderr
    run_passive_hook(project)
    confirmed = powershell("check-session")
    assert confirmed.returncode == 0, confirmed.stderr
    assert "Hook Alethe (confirmed)" in confirmed.stderr
    monkeypatch.delenv(POLICY)
    assert powershell("check-session").returncode == 1


@pytest.mark.skipif(os.name != "nt", reason="O launcher usa PowerShell no Windows.")
@pytest.mark.parametrize(
    "supports_flag, with_arguments", [(True, True), (True, False), (False, False)]
)
def test_launcher_starts_only_with_no_daemon_and_preserves_args(
    project, monkeypatch, supports_flag, with_arguments
):
    if not shutil.which("node.exe"):
        pytest.skip("A simulação local da distribuição npm usa Node.")
    shim = project / "bin"
    entry = shim / "node_modules/@openai/codex/bin/codex.js"
    entry.parent.mkdir(parents=True)
    (shim / "codex.cmd").write_text("@exit /b 99\n", encoding="utf-8")
    entry.write_text(
        "const args = process.argv.slice(2);\n"
        "if (args[0] === '--help') {\n"
        f"  console.log({json.dumps('      --no-daemon  Run without daemon' if supports_flag else 'Old Codex')});\n"
        "} else {\n"
        "  console.log(JSON.stringify({args, policy: process.env.ALETHE_ORCHESTRATE_POLICY, "
        "playbooks: process.env.ALETHE_ORCHESTRATE_PLAYBOOKS, home: process.env.ALETHE_ORCHESTRATE_HOME, "
        "argumentTransport: process.env.JOBPILOT_CODEX_ARGUMENTS, "
        "startedAt: process.env.JOBPILOT_CODEX_STARTED_AT}));\n"
        "}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PATH", str(shim) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv(POLICY, str(project / "external.json"))
    invocation = "& '.\\scripts\\JobPilot-Codex.ps1'"
    if with_arguments:
        invocation = (
            """$forward = @('start', '-m', 'gpt-6.2-sol', '-c', 'key="value with spaces"', '--', '', 'a & b')\n"""
            + invocation
            + " @forward"
        )
    result = powershell(invocation)
    if supports_flag:
        assert result.returncode == 0, result.stderr
        launch = json.loads(result.stdout)
        forwarded = (
            ["-m", "gpt-6.2-sol", "-c", 'key="value with spaces"', "--", "", "a & b"]
            if with_arguments
            else []
        )
        assert launch["args"] == ["--no-daemon", *forwarded]
        assert Path(launch["policy"]) == project / "alethe-orchestrate.json"
        assert Path(launch["playbooks"]) == project / "alethe-playbooks.yaml"
        assert Path(launch["home"]) == project / "orchestrations"
        assert "argumentTransport" not in launch
        assert float(launch["startedAt"]) <= time.time()
    else:
        assert result.returncode == 1
        assert "--no-daemon" in result.stderr
        assert result.stdout == ""


def powershell(command: str) -> subprocess.CompletedProcess:
    """Roda o launcher em um processo local sem perfil de usuário."""
    if command == "check-session":
        command = f"& '{LAUNCHER}' check-session"
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "RemoteSigned",
            "-Command",
            command + "\nexit $LASTEXITCODE",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
