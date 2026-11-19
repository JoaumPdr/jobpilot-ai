param([string]$Action = 'start')

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $root '.agents/skills/alethe/scripts/orchestrate.py'
$callerDirectory = (Get-Location).ProviderPath
$forward = $args
$tiers = @('cheap', 'standard', 'strong')

function Invoke-AletheJson {
    param([string[]]$Command)

    $output = & $python -B $runner @Command
    if ($LASTEXITCODE -ne 0) {
        throw "A Alethe recusou o comando $($Command -join ' ')."
    }
    return ($output | Out-String | ConvertFrom-Json)
}

function Assert-ExplicitWorkers {
    param([string]$PlanPath, [string[]]$Providers)

    if ([string]::IsNullOrWhiteSpace($PlanPath) -or $PlanPath.StartsWith('-')) {
        throw 'Informe o caminho do plano imediatamente após o subcomando da Alethe.'
    }
    $plan = Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($plan.workers -isnot [array] -or $plan.workers.Count -eq 0) {
        throw 'O plano precisa declarar pelo menos um worker.'
    }
    foreach ($worker in $plan.workers) {
        if ($worker.tier -isnot [string] -or $worker.tier -cnotin $tiers) {
            throw "Worker '$($worker.id)' precisa declarar tier: cheap, standard ou strong."
        }
        if ($worker.provider -isnot [string] -or $worker.provider -cnotin $Providers) {
            throw "Worker '$($worker.id)' precisa declarar um provedor habilitado na política do projeto."
        }
        if (-not (Get-Command $worker.provider -CommandType Application -ErrorAction SilentlyContinue)) {
            throw "Provedor '$($worker.provider)' indisponível no PATH."
        }
    }
}

$previous = @{}
$enteredRoot = $false
$result = 1
try {
    if ($Action -notin @('start', 'check', 'check-session', 'alethe')) {
        throw 'Ação inválida. Use start (padrão), check, check-session ou alethe.'
    }
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw 'LOCALAPPDATA indisponível. Consulte docs/ALETHE_INSTRUCOES.md.'
    }
    $policyRoot = Join-Path $env:LOCALAPPDATA 'Alethe/JobPilot-AI'
    $policyPath = Join-Path $policyRoot 'alethe-orchestrate.json'
    $playbooksPath = Join-Path $policyRoot 'alethe-playbooks.yaml'
    foreach ($path in @($policyPath, $playbooksPath, $runner)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Arquivo necessário ausente: $path. Consulte docs/ALETHE_INSTRUCOES.md."
        }
    }

    $venvScripts = Join-Path $root '.venv/Scripts'
    $venvPython = Join-Path $venvScripts 'python.exe'
    $projectEnv = @{
        ALETHE_ORCHESTRATE_POLICY = $policyPath
        ALETHE_ORCHESTRATE_PLAYBOOKS = $playbooksPath
        ALETHE_ORCHESTRATE_HOME = (Join-Path $policyRoot 'orchestrations')
    }
    if ($Action -eq 'check-session') {
        foreach ($name in $projectEnv.Keys) {
            if ([Environment]::GetEnvironmentVariable($name, 'Process') -ne $projectEnv[$name]) {
                throw "A sessão não herdou $name do JobPilot AI. Reabra o Codex pelo launcher."
            }
        }
    }
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        # O hook do plugin também invoca python pelo PATH do processo.
        $projectEnv.PATH = $venvScripts + [IO.Path]::PathSeparator + $env:PATH
    }
    foreach ($name in $projectEnv.Keys) {
        $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $projectEnv[$name], 'Process')
    }
    $python = (Get-Command python -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1).Source
    if (-not $python) {
        throw 'Python indisponível. Execute uv sync na raiz do projeto e tente novamente.'
    }

    Push-Location -LiteralPath $root
    $enteredRoot = $true
    $effective = Invoke-AletheJson @('policy', 'show')
    if ($effective.path -ne $policyPath -or -not $effective.policy.onboarded -or
        $effective.policy.backend -ne 'skill' -or
        $effective.policy.providerSwitch -notin @('ask', 'never')) {
        throw 'A política carregada precisa ser a do projeto, com backend skill e sem troca automática de provedor.'
    }

    $playbook = Invoke-AletheJson @('playbook', 'direct', '--json')
    if ($playbook.profile -ne 'base') {
        throw 'O perfil esperado para o JobPilot AI é Base.'
    }

    if ($Action -eq 'alethe') {
        $command = $forward | Select-Object -First 1
        # A CLI aceita abreviações das opções longas. Bloqueie também seus prefixos.
        $pathOverrides = @($forward | Where-Object {
            $flag = ($_ -split '=', 2)[0]
            $flag.StartsWith('--') -and $flag.Length -gt 2 -and
                ('--policy'.StartsWith($flag) -or '--file'.StartsWith($flag))
        })
        if (-not $command -or $pathOverrides.Count) {
            throw 'Informe um subcomando da Alethe sem substituir os caminhos da configuração.'
        }
        if ($command -in @('validate', 'dry-run', 'run')) {
            if ($forward.Count -lt 2 -or $forward[1].StartsWith('-')) {
                throw 'Informe o caminho do plano imediatamente após o subcomando da Alethe.'
            }
            $planPath = [IO.Path]::Combine($callerDirectory, $forward[1])
            $providers = @($effective.policy.providerOrder | Where-Object {
                $_ -notin $effective.policy.conserveProviders
            })
            Assert-ExplicitWorkers $planPath $providers
            $forward[1] = $planPath
        }
        & $python -B $runner @forward
        $result = $LASTEXITCODE
    } else {
        $doctor = Invoke-AletheJson @('doctor')
        if (-not $doctor.policy.valid -or -not $doctor.playbooks.valid -or
            $doctor.policyPath -ne $policyPath -or $doctor.playbooks.path -ne $playbooksPath) {
            throw 'Falha na validação da política ou dos playbooks do projeto.'
        }
        $allowedProviders = @($doctor.providers | Where-Object {
            $_.provider -in $effective.policy.providerOrder -and
            $_.provider -notin $effective.policy.conserveProviders
        })
        [Console]::Error.WriteLine("Política Alethe: $($doctor.policyPath)")
        [Console]::Error.WriteLine("Playbooks: $($doctor.playbooks.path)")
        [Console]::Error.WriteLine("Perfil: $($playbook.profile). Validação estrutural: OK.")
        if ($allowedProviders.Count -eq 0) {
            [Console]::Error.WriteLine('Nenhum provedor habilitado para workers.')
        }
        foreach ($provider in $allowedProviders) {
            $name = $provider.provider
            $availability = if ($provider.installed) { 'detectado' } else { 'indisponível' }
            $login = if ($true -eq $provider.loggedIn) { 'confirmada' }
                elseif ($false -eq $provider.loggedIn) { 'ausente' }
                else { 'não verificada' }
            [Console]::Error.WriteLine("Provedor $name ${availability}. Autenticação: $login.")
            foreach ($tier in $tiers) {
                $defaults = $playbook.tiers.$tier.$name
                $override = $effective.policy.modelTiers.$tier.$name
                $model = if ($override.model) { $override.model } else { $defaults.model }
                $effort = if ($override.effort) { $override.effort } else { $defaults.effort }
                if (-not $model -or -not $effort) {
                    throw "Tier '$tier' incompleto para '$name'."
                }
                [Console]::Error.WriteLine("  ${tier}: $model / $effort")
            }
        }
        if ($Action -eq 'start') {
            $codex = Get-Command codex -CommandType Application -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if (-not $codex) {
                throw 'Codex CLI indisponível no PATH.'
            }
            & $codex.Source @forward
            $result = $LASTEXITCODE
        } else {
            $result = 0
        }
    }
} catch {
    [Console]::Error.WriteLine("JobPilot AI: $($_.Exception.Message)")
} finally {
    if ($enteredRoot) { Pop-Location }
    foreach ($name in $previous.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process')
    }
}
exit $result
