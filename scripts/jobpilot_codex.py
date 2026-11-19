"""Diagnóstico local da Alethe e inicialização isolada do Codex no Windows."""

import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ALETHE_SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/alethe/scripts"


def validate_session(project: Path, *, check_hooks: bool) -> dict:
    """Valida a resolução da Alethe no ambiente recebido pelo processo."""
    sys.path.insert(0, str(ALETHE_SCRIPTS))
    import hook
    import orchestrate as alethe

    project = project.resolve()
    expected_policy = project / "alethe-orchestrate.json"
    expected_playbooks = project / alethe.USER_PLAYBOOKS_FILE
    expected_home = project / "orchestrations"
    policy_path = alethe.default_policy_path().resolve()
    playbooks_path = alethe.effective_playbooks_path(policy_path).resolve()
    home = alethe.orchestrations_home().resolve()
    hook_home = Path(hook.orchestrations_home()).resolve()
    for label, actual, expected in (
        ("Política efetiva", policy_path, expected_policy),
        ("Playbooks efetivos", playbooks_path, expected_playbooks),
        ("Diretório de estado efetivo", home, expected_home),
        ("Diretório de estado resolvido pelo hook", hook_home, expected_home),
    ):
        if actual != expected:
            raise ValueError(f"{label}: {actual}. Caminho esperado: {expected}.")

    if not policy_path.is_file():
        raise ValueError(f"Política do projeto ausente: {policy_path}.")
    try:
        policy = alethe.load_policy(policy_path)
        settings = alethe.playbook_settings(policy_path)
    except alethe.PlanError as error:
        raise ValueError(str(error)) from error
    if (
        not policy["onboarded"]
        or policy["backend"] != "skill"
        or policy["providerSwitch"] not in ("ask", "never")
        or policy["trust"]["allowUnsafe"]
    ):
        raise ValueError(
            "A política exige onboarding, backend skill, troca de provedor controlada e allowUnsafe desabilitado."
        )
    if settings["profile"] != "base":
        raise ValueError("O perfil esperado para o JobPilot AI é Base.")

    evidence = None
    if check_hooks:
        session = os.environ.get("CODEX_SESSION_ID")
        started = os.environ.get("JOBPILOT_CODEX_STARTED_AT")
        appdata = os.environ.get("APPDATA")
        global_home = (
            Path(appdata or Path.home() / "AppData/Roaming") / "Alethe/orchestrations"
        )
        evidence = hook_evidence(
            alethe.session_state_filename(session) if session else None,
            started,
            home,
            global_home,
            settings["passive"]["checkEveryMinutes"],
        )
    return {
        "paths": {
            "policy": str(policy_path),
            "playbooks": str(playbooks_path),
            "home": str(home),
        },
        "policy": policy,
        "profile": settings["profile"],
        "tiers": settings["tiers"],
        "hooks": evidence,
    }


def hook_evidence(
    filename: str | None,
    started: str | None,
    home: Path,
    global_home: Path,
    interval: int,
) -> dict[str, str]:
    """Procura evidência recente do hook passivo para o ID da sessão atual."""
    if not filename or not started:
        return {
            "status": "pending",
            "detail": "Faltam o ID da sessão ou o horário de início do launcher.",
        }
    try:
        cutoff = float(started)
    except ValueError:
        cutoff = math.nan
    if not math.isfinite(cutoff) or not 0 < cutoff <= time.time():
        return {
            "status": "pending",
            "detail": "Horário de início do launcher inválido.",
        }

    project_state = home / "passive" / filename
    global_state = global_home / "passive" / filename
    try:
        if (
            global_state != project_state
            and global_state.is_file()
            and global_state.stat().st_mtime >= cutoff
        ):
            return {
                "status": "wrong",
                "detail": f"Estado desta execução encontrado no diretório global: {global_state}.",
            }
        if project_state.is_file() and project_state.stat().st_mtime >= cutoff:
            check = json.loads(project_state.read_text(encoding="utf-8")).get(
                "check", {}
            )
            if check.get("briefPrinted") is True:
                if check.get("checkEveryMinutes") != interval:
                    return {
                        "status": "wrong",
                        "detail": "O intervalo registrado pelo hook diverge dos playbooks do projeto.",
                    }
                return {
                    "status": "confirmed",
                    "detail": f"Estado do hook passivo desta execução: {project_state}.",
                }
    except (AttributeError, OSError, ValueError) as error:
        return {
            "status": "pending",
            "detail": f"Não foi possível validar o estado do hook: {error}.",
        }
    return {
        "status": "pending",
        "detail": "Sem registro recente do hook passivo para esta sessão.",
    }


def codex_command(executable: Path) -> list[str]:
    """Obtém o comando nativo ou a entrada Node da distribuição oficial npm."""
    if executable.suffix.lower() != ".cmd":
        return [str(executable)]
    entry = executable.parent / "node_modules/@openai/codex/bin/codex.js"
    bundled_node = executable.parent / "node.exe"
    node = str(bundled_node) if bundled_node.is_file() else shutil.which("node.exe")
    if not entry.is_file() or not node:
        raise ValueError(
            "Não foi possível localizar o Codex npm e o Node pelo shim .cmd. Use a instalação oficial."
        )
    # Evita a reinterpretação das aspas e dos argumentos vazios pelo cmd.exe.
    return [node, str(entry)]


def start_codex(executable: Path, arguments: list[str]) -> int:
    """Inicia o Codex com servidor embutido, usando seu ambiente local."""
    command = codex_command(executable)
    try:
        help_result = subprocess.run(
            [*command, "--help"],
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=15,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(
            "O Codex CLI não respondeu a --help para confirmar suporte a --no-daemon."
        ) from error
    if help_result.returncode or not re.search(
        r"(?m)^\s+--no-daemon(?:\s|$)", help_result.stdout
    ):
        raise ValueError(
            "Este Codex CLI não confirmou suporte a --no-daemon em --help. Confira a instalação ou a versão."
        )
    flags_end = arguments.index("--") if "--" in arguments else len(arguments)
    if "--no-daemon" not in arguments[:flags_end]:
        arguments = ["--no-daemon", *arguments]
    env = {**os.environ, "JOBPILOT_CODEX_STARTED_AT": str(time.time())}
    return subprocess.call([*command, *arguments], env=env)


def main() -> int:
    """Expõe o diagnóstico e o lançamento ao script PowerShell."""
    try:
        action, target = sys.argv[1:3]
        if action == "start":
            arguments = json.loads(os.environ.pop("JOBPILOT_CODEX_ARGUMENTS"))
            return start_codex(Path(target), arguments)
        print(
            json.dumps(
                validate_session(Path(target), check_hooks=action == "check-session")
            )
        )
        return 0
    except (OSError, ValueError) as error:
        print(f"JobPilot AI: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
