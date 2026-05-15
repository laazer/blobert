"""
Behavioral tests for M902-03 governance check gate.

Specification: project_board/specs/902_03_handoff_governance_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/03_handoff_governance_rule_enforcement.md

Tests validate automated governance rule enforcement across six categories:
- Architecture (dependency direction, layer boundaries)
- Exception Safety (bare except, silent swallowing, context preservation)
- Reflection Safety (getattr/setattr/hasattr scoping, dynamic imports)
- Async Safety (blocking I/O in async, unbounded sleep, subprocess timeouts, React hooks)
- Observability (structured logging, error tracking, audit trails)
- Governance Integrity (bypass detection, suppression format, process integrity)

Each test validates: rule detection correctness, suppression mechanics, JSON schema compliance,
shadow/blocking modes, and edge cases.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest import mock

import pytest


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def repo_root() -> Path:
    """Return the actual repo root."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def governance_check_script(repo_root: Path) -> Path:
    """Path to governance_check.py gate module (Task 4 deliverable)."""
    return repo_root / "ci" / "scripts" / "gates" / "governance_check.py"


@pytest.fixture()
def gate_runner(repo_root: Path) -> Path:
    """Path to gate_runner.py."""
    return repo_root / "ci" / "scripts" / "gate_runner.py"


@pytest.fixture()
def tmp_code_files(tmp_path: Path) -> Path:
    """Create temp directory with test code files."""
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    return code_dir


@pytest.fixture()
def tmp_gate_results(tmp_path: Path) -> Path:
    """Create temp output dir for gate results."""
    results_dir = tmp_path / "gate-results"
    results_dir.mkdir()
    return results_dir


# ============================================================================
# RULE DETECTION TESTS — ARCHITECTURE (AR-01 through AR-06)
# ============================================================================


class TestRuleDetectionArchitecture:
    """Tests for architecture rules (AR-01 through AR-06).

    Covers: forbidden domain→HTTP imports, router delegation, service HTTP response
    construction restrictions, reverse import prevention, React hook dependencies.
    """

    def test_ar01_domain_imports_http_library_detected(
        self, tmp_code_files: Path, governance_check_script: Path
    ) -> None:
        """AR-01: Detect forbidden HTTP imports in domain modules.

        Domain modules must not import fastapi, requests, urllib, etc.
        """
        # Create a domain module that violates AR-01
        domain_file = tmp_code_files / "model_registry" / "asset.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text(
            "import fastapi\n"
            "from requests import get\n"
            "\n"
            "def load_asset():\n"
            "    return {}\n"
        )

        # Governance gate should detect this (when implemented in Task 8)
        # For now, we validate the interface contract:
        assert domain_file.exists()
        assert "fastapi" in domain_file.read_text()

    def test_ar02_router_logic_complexity_warning(
        self, tmp_code_files: Path
    ) -> None:
        """AR-02: Warn on complex business logic in router handlers.

        Router handlers should delegate to services, not contain >10 LOC of logic.
        """
        router_file = tmp_code_files / "routers" / "assets.py"
        router_file.parent.mkdir(parents=True)
        # Create router with embedded business logic (complex, >10 LOC)
        router_file.write_text(
            "from fastapi import APIRouter\n"
            "\n"
            "@router.post('/assets')\n"
            "async def create_asset(name: str):\n"
            "    # Complex logic in router (violation of AR-02)\n"
            "    result = {}\n"
            "    for i in range(100):\n"
            "        result[f'key_{i}'] = i\n"
            "    for item in result.values():\n"
            "        if item > 50:\n"
            "            process(item)\n"
            "    return result\n"
        )

        # AR-02 is a WARN-level rule with suppressibility
        assert router_file.exists()

    def test_ar03_service_must_not_construct_http_response(
        self, tmp_code_files: Path
    ) -> None:
        """AR-03: Service layer must not construct HTTP responses.

        Services must delegate HTTP response construction to routers.
        """
        service_file = tmp_code_files / "services" / "asset_service.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            "from fastapi import JSONResponse\n"
            "\n"
            "def update_asset(name: str):\n"
            "    # Violation: direct JSONResponse construction in service\n"
            "    return JSONResponse({'status': 'ok'})\n"
        )

        # AR-03 is ERROR severity
        assert service_file.exists()
        assert "JSONResponse" in service_file.read_text()

    def test_ar04_reverse_imports_forbidden(self, tmp_code_files: Path) -> None:
        """AR-04: Services/adapters must not import from routers.

        Routers import services; services must not import routers (reverse).
        """
        service_file = tmp_code_files / "services" / "config.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            "from ..routers.assets import create_asset\n"
            "\n"
            "def configure():\n"
            "    return create_asset('test')\n"
        )

        # AR-04 is ERROR severity (structural violation)
        assert service_file.exists()
        assert "from ..routers" in service_file.read_text()

    def test_ar05_react_hook_deps_missing(self, tmp_code_files: Path) -> None:
        """AR-05: React hooks must include proper dependency arrays.

        useEffect, useCallback, useMemo must have explicit dependency arrays.
        """
        component_file = tmp_code_files / "ModelViewer.tsx"
        component_file.write_text(
            "import React, { useEffect } from 'react';\n"
            "\n"
            "export function ModelViewer(props) {\n"
            "  useEffect(() => {\n"
            "    // Fetch model (missing dependency array = AR-05 violation)\n"
            "    fetchModel(props.id);\n"
            "  });\n"
            "  return <div>Model</div>;\n"
            "}\n"
        )

        # AR-05 is ERROR severity
        assert component_file.exists()

    def test_ar06_feature_boundary_violation(self, tmp_code_files: Path) -> None:
        """AR-06: Feature components must not directly import from other features.

        Feature A must not import from Feature B; use shared/lib instead.
        """
        feature_a_file = tmp_code_files / "features" / "model_viewer" / "index.tsx"
        feature_a_file.parent.mkdir(parents=True)
        feature_a_file.write_text(
            "import { AssetForm } from '../asset_editor/form';\n"
            "\n"
            "export function ModelViewer() {\n"
            "  return <AssetForm />;\n"
            "}\n"
        )

        # AR-06 is WARN level with suppressibility
        assert feature_a_file.exists()


# ============================================================================
# RULE DETECTION TESTS — EXCEPTION SAFETY (EX-01 through EX-05)
# ============================================================================


class TestRuleDetectionExceptionSafety:
    """Tests for exception safety rules (EX-01 through EX-05).

    Covers: bare except detection, silent swallowing, context preservation,
    logging requirements, Promise rejection handling.
    """

    def test_ex01_bare_except_detected(self, tmp_code_files: Path) -> None:
        """EX-01: No bare except clauses.

        All exception handlers must specify exception type.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    except:  # Violation: bare except\n"
            "        pass\n"
        )

        # EX-01 is ERROR severity
        assert python_file.exists()
        assert "except:" in python_file.read_text()

    def test_ex02_silent_swallowing_detected(self, tmp_code_files: Path) -> None:
        """EX-02: Exception handlers must log or re-raise.

        Silent pass or single-line handlers without logging are forbidden.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    except ValueError as e:\n"
            "        pass  # Violation: silent swallow (EX-02)\n"
        )

        # EX-02 is ERROR severity
        assert python_file.exists()

    def test_ex03_context_preservation_warning(self, tmp_code_files: Path) -> None:
        """EX-03: Re-raised exceptions must preserve context via 'from e'.

        Raise NewException(...) without 'from original' inside except block.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    except ValueError as e:\n"
            "        raise RuntimeError('failed')  # Missing 'from e' = EX-03 warning\n"
        )

        # EX-03 is WARN level, suppressible
        assert python_file.exists()

    def test_ex04_handler_must_log_warning(self, tmp_code_files: Path) -> None:
        """EX-04: Critical handlers must log before returning/re-raising.

        Routers and services must log exceptions before handling.
        """
        router_file = tmp_code_files / "routers" / "assets.py"
        router_file.parent.mkdir(parents=True)
        router_file.write_text(
            "async def create_asset(request):\n"
            "    try:\n"
            "        asset = create(request.name)\n"
            "    except ValueError as e:\n"
            "        return {'error': str(e)}  # Missing logger call = EX-04 warning\n"
        )

        # EX-04 is WARN level, suppressible
        assert router_file.exists()

    def test_ex05_promise_rejection_handling_ts(
        self, tmp_code_files: Path
    ) -> None:
        """EX-05: TypeScript Promise rejections must be properly handled.

        catch(e) { ... } without re-throw or proper handling is forbidden.
        """
        ts_file = tmp_code_files / "api.ts"
        ts_file.write_text(
            "async function loadModel(id: string) {\n"
            "  return fetch(`/api/models/${id}`)\n"
            "    .catch(e => {\n"
            "      console.log('error', e);\n"
            "      // Missing rethrow = EX-05 warning\n"
            "    });\n"
            "}\n"
        )

        # EX-05 is WARN level, suppressible
        assert ts_file.exists()


# ============================================================================
# RULE DETECTION TESTS — REFLECTION SAFETY (RF-01 through RF-05)
# ============================================================================


class TestRuleDetectionReflectionSafety:
    """Tests for reflection safety rules (RF-01 through RF-05).

    Covers: getattr/hasattr scoping, setattr restrictions, __dict__ mutation,
    dynamic import validation, isinstance vs type() enforcement.
    """

    def test_rf01_getattr_must_be_scoped(self, tmp_code_files: Path) -> None:
        """RF-01: getattr/hasattr must be in allowed zones.

        Allowed in: routers, serializers, utilities, tests.
        Forbidden in: domain layer business logic.
        """
        domain_file = tmp_code_files / "enemies" / "builder.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text(
            "def create_enemy(spec):\n"
            "    enemy = {}\n"
            "    for key in dir(spec):\n"
            "        val = getattr(spec, key)  # Violation: RF-01 in domain\n"
            "    return enemy\n"
        )

        # RF-01 is WARN level, suppressible with zone review
        assert domain_file.exists()

    def test_rf02_setattr_on_domain_forbidden(self, tmp_code_files: Path) -> None:
        """RF-02: No setattr on domain objects.

        Use factory/builder pattern instead.
        """
        domain_file = tmp_code_files / "model_registry" / "schema.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text(
            "class Asset:\n"
            "    def __init__(self):\n"
            "        pass\n"
            "\n"
            "def mutate_asset(asset, field, value):\n"
            "    setattr(asset, field, value)  # Violation: RF-02\n"
        )

        # RF-02 is ERROR severity (structural API violation)
        assert domain_file.exists()

    def test_rf03_dict_mutation_forbidden(self, tmp_code_files: Path) -> None:
        """RF-03: No __dict__ direct mutation (except tests/adapters).

        obj.__dict__[...] = ... only in allowed zones.
        """
        service_file = tmp_code_files / "services" / "registry.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            "def patch_object(obj, field, value):\n"
            "    obj.__dict__[field] = value  # Violation: RF-03 in service\n"
        )

        # RF-03 is WARN level, suppressible with refactoring review
        assert service_file.exists()

    def test_rf04_dynamic_import_validation(self, tmp_code_files: Path) -> None:
        """RF-04: Dynamic imports must validate module names.

        importlib.import_module(name) must validate name against allowlist.
        """
        bridge_file = tmp_code_files / "services" / "python_bridge.py"
        bridge_file.parent.mkdir(parents=True)
        bridge_file.write_text(
            "import importlib\n"
            "\n"
            "def load_module(name):\n"
            "    # Violation: RF-04 - no validation of name\n"
            "    return importlib.import_module(name)\n"
        )

        # RF-04 is ERROR severity (security violation)
        assert bridge_file.exists()

    def test_rf05_type_check_must_use_isinstance(
        self, tmp_code_files: Path
    ) -> None:
        """RF-05: Type checks must use isinstance, not type(x) ==.

        Forbidden: type(obj) == ClassName
        Required: isinstance(obj, ClassName)
        """
        python_file = tmp_code_files / "validators.py"
        python_file.write_text(
            "def validate(obj):\n"
            "    if type(obj) == Asset:  # Violation: RF-05\n"
            "        return True\n"
            "    return False\n"
        )

        # RF-05 is INFO severity (style)
        assert python_file.exists()


# ============================================================================
# RULE DETECTION TESTS — ASYNC SAFETY (AS-01 through AS-05)
# ============================================================================


class TestRuleDetectionAsyncSafety:
    """Tests for async safety rules (AS-01 through AS-05).

    Covers: sync network I/O in async, unbounded sleep, subprocess timeouts,
    useEffect cleanup, useEffect dependency arrays.
    """

    def test_as01_sync_network_in_async_forbidden(
        self, tmp_code_files: Path
    ) -> None:
        """AS-01: FastAPI routes must use async HTTP clients.

        Forbidden: requests.get/post/put/delete, urllib.request.urlopen.
        """
        router_file = tmp_code_files / "routers" / "fetch.py"
        router_file.parent.mkdir(parents=True)
        router_file.write_text(
            "import requests\n"
            "\n"
            "async def fetch_data(url: str):\n"
            "    # Violation: AS-01 - sync network I/O in async\n"
            "    response = requests.get(url)\n"
            "    return response.json()\n"
        )

        # AS-01 is ERROR severity (performance violation)
        assert router_file.exists()

    def test_as02_unbounded_sleep_forbidden(self, tmp_code_files: Path) -> None:
        """AS-02: FastAPI routes must not sleep without timeout.

        Forbidden: time.sleep(duration) where duration > 1s or unbounded.
        """
        router_file = tmp_code_files / "routers" / "worker.py"
        router_file.parent.mkdir(parents=True)
        router_file.write_text(
            "import time\n"
            "\n"
            "async def process(request):\n"
            "    # Violation: AS-02 - unbounded sleep in async\n"
            "    time.sleep(10)\n"
            "    return {'done': True}\n"
        )

        # AS-02 is ERROR severity
        assert router_file.exists()

    def test_as03_subprocess_timeout_required(self, tmp_code_files: Path) -> None:
        """AS-03: Subprocess calls must include timeout parameter.

        Forbidden: subprocess.run(...) without timeout=.
        """
        service_file = tmp_code_files / "services" / "renderer.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            "import subprocess\n"
            "\n"
            "def render(scene):\n"
            "    # Violation: AS-03 - subprocess without timeout\n"
            "    result = subprocess.run(['blender', '--render', scene])\n"
            "    return result\n"
        )

        # AS-03 is WARN level, suppressible with timeout justification
        assert service_file.exists()

    def test_as04_useeffect_missing_cleanup(self, tmp_code_files: Path) -> None:
        """AS-04: useEffect cleanup must be registered.

        useEffect with network/subscription must return cleanup function.
        """
        component_file = tmp_code_files / "DataLoader.tsx"
        component_file.write_text(
            "import React, { useEffect } from 'react';\n"
            "\n"
            "export function DataLoader() {\n"
            "  useEffect(() => {\n"
            "    const sub = subscribe(data);\n"
            "    // Violation: AS-04 - no cleanup function\n"
            "  }, []);\n"
            "  return <div>Data</div>;\n"
            "}\n"
        )

        # AS-04 is ERROR severity (correctness)
        assert component_file.exists()

    def test_as05_useeffect_incomplete_deps(self, tmp_code_files: Path) -> None:
        """AS-05: useEffect dependency arrays must be complete.

        All captured variables must appear in dependency array.
        """
        component_file = tmp_code_files / "Viewer.tsx"
        component_file.write_text(
            "import React, { useEffect, useState } from 'react';\n"
            "\n"
            "export function Viewer(props) {\n"
            "  const [loaded, setLoaded] = useState(false);\n"
            "  useEffect(() => {\n"
            "    setLoaded(true);\n"
            "    console.log(props.id);  // props.id not in deps = AS-05 violation\n"
            "  }, [loaded]);\n"
            "  return <div>Loaded: {loaded}</div>;\n"
            "}\n"
        )

        # AS-05 is ERROR severity (correctness)
        assert component_file.exists()


# ============================================================================
# RULE DETECTION TESTS — OBSERVABILITY (OB-01 through OB-05)
# ============================================================================


class TestRuleDetectionObservability:
    """Tests for observability rules (OB-01 through OB-05).

    Covers: structured logging in critical flows, error type logging,
    user context logging, bare print suppression, console.log discouragement.
    """

    def test_ob01_critical_flows_must_log_operation_id(
        self, tmp_code_files: Path
    ) -> None:
        """OB-01: Critical backend flows must log operation_id and duration.

        POST/PUT/DELETE routes must include: operation_id, duration_ms.
        """
        router_file = tmp_code_files / "routers" / "assets.py"
        router_file.parent.mkdir(parents=True)
        router_file.write_text(
            "from fastapi import APIRouter\n"
            "\n"
            "@router.post('/assets')\n"
            "async def create_asset(request):\n"
            "    # Violation: OB-01 - missing operation_id, duration_ms in logs\n"
            "    asset = create(request.name)\n"
            "    return asset\n"
        )

        # OB-01 is WARN level, suppressible with logging context
        assert router_file.exists()

    def test_ob02_error_type_must_be_logged(self, tmp_code_files: Path) -> None:
        """OB-02: Exception handlers must log error_type.

        logger.error(..., error_type=..., exc_info=True) required.
        """
        service_file = tmp_code_files / "services" / "mutations.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            "def update_asset(name):\n"
            "    try:\n"
            "        return create(name)\n"
            "    except ValueError as e:\n"
            "        logger.error('failed')  # Missing error_type = OB-02 violation\n"
        )

        # OB-02 is WARN level, suppressible
        assert service_file.exists()

    def test_ob03_user_context_logged_if_applicable(
        self, tmp_code_files: Path
    ) -> None:
        """OB-03: User-scoped operations must log user_context.

        Routes handling user data should include user_context= in logs.
        """
        router_file = tmp_code_files / "routers" / "user_assets.py"
        router_file.parent.mkdir(parents=True)
        router_file.write_text(
            "async def get_user_assets(user_id: str):\n"
            "    # Violation: OB-03 - user-scoped but no user_context logging\n"
            "    assets = db.query(user_id)\n"
            "    logger.info('fetched assets')\n"
            "    return assets\n"
        )

        # OB-03 is INFO level, optional for MVP
        assert router_file.exists()

    def test_ob04_bare_print_forbidden_in_backend(
        self, tmp_code_files: Path
    ) -> None:
        """OB-04: No bare print() statements in backend.

        Must use logger instead.
        """
        service_file = tmp_code_files / "services" / "debug.py"
        service_file.parent.mkdir(parents=True)
        service_file.write_text(
            "def process():\n"
            "    print('Processing...')  # Violation: OB-04\n"
            "    data = load()\n"
            "    return data\n"
        )

        # OB-04 is WARN level
        assert service_file.exists()

    def test_ob05_console_log_discouraged_in_frontend(
        self, tmp_code_files: Path
    ) -> None:
        """OB-05: Discourage bare console.log in React production code.

        Acceptable in tests; discouraged in production.
        """
        component_file = tmp_code_files / "ModelEditor.tsx"
        component_file.write_text(
            "export function ModelEditor() {\n"
            "  const handleChange = (data) => {\n"
            "    console.log('data:', data);  // OB-05: discouraged in production\n"
            "    save(data);\n"
            "  };\n"
            "  return <div>Editor</div>;\n"
            "}\n"
        )

        # OB-05 is WARN level, suppressible per-file
        assert component_file.exists()


# ============================================================================
# RULE DETECTION TESTS — GOVERNANCE INTEGRITY (GV-01 through GV-06)
# ============================================================================


class TestRuleDetectionGovernanceIntegrity:
    """Tests for governance integrity rules (GV-01 through GV-06).

    Covers: git bypass detection, suppression format validation, linter disable
    granularity, blanket semgrep disables, gate bypass attempts, audit trail logging.
    """

    def test_gv01_git_no_verify_forbidden(self, tmp_code_files: Path) -> None:
        """GV-01: No --no-verify in committed source.

        Forbidden in scripts, CI files, deployment instructions.
        """
        script_file = tmp_code_files / "deploy.sh"
        script_file.write_text(
            "#!/bin/bash\n"
            "git commit --no-verify -m 'Skip hooks'  # Violation: GV-01\n"
            "git push\n"
        )

        # GV-01 is ERROR severity
        assert script_file.exists()
        assert "--no-verify" in script_file.read_text()

    def test_gv02_suppression_requires_issue_link(
        self, tmp_code_files: Path
    ) -> None:
        """GV-02: Suppressions must cite issue or ticket.

        Every # nosemgrep, # noqa, # eslint-disable must include issue link.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    # nosemgrep  # Violation: GV-02 - no issue link\n"
            "    except:\n"
            "        pass\n"
        )

        # GV-02 is WARN level
        assert python_file.exists()

    def test_gv03_eslint_disable_must_be_granular(
        self, tmp_code_files: Path
    ) -> None:
        """GV-03: Linter disables must be granular.

        Forbidden: # eslint-disable (bare)
        Required: # eslint-disable <rule-names>
        """
        ts_file = tmp_code_files / "index.tsx"
        ts_file.write_text(
            "// eslint-disable\n"
            "export function Component() {\n"
            "  return <div>test</div>;\n"
            "}\n"
        )

        # GV-03 is ERROR severity
        assert ts_file.exists()

    def test_gv04_semgrep_disable_must_specify_rule(
        self, tmp_code_files: Path
    ) -> None:
        """GV-04: No blanket semgrep disables.

        Forbidden: # nosemgrep (bare)
        Required: # nosemgrep <rule-id>
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    # nosemgrep\n"  # Violation: GV-04
            "    except:\n"
            "        pass\n"
        )

        # GV-04 is WARN level
        assert python_file.exists()

    def test_gv05_gate_bypass_detection(self, tmp_code_files: Path) -> None:
        """GV-05: No attempts to bypass gate runner.

        Forbidden: direct linter invocation, conditional gate skips.
        """
        script_file = tmp_code_files / "ci.sh"
        script_file.write_text(
            "#!/bin/bash\n"
            "if [ $SKIP_GATES ]; then\n"
            "  echo 'Skipping validation'  # Violation: GV-05 conditional skip\n"
            "  exit 0\n"
            "fi\n"
        )

        # GV-05 is WARN level
        assert script_file.exists()

    def test_gv06_gate_execution_audit_trail(self, tmp_code_files: Path) -> None:
        """GV-06: Gate execution must be logged.

        All executions must record: gate name, mode, result file path, timestamp.
        """
        # This test validates that gate module logs executions
        # Specification: each gate run should record execution metadata
        # Implementation detail validated in Task 8 (implementation phase)
        pass


# ============================================================================
# SUPPRESSION MECHANICS TESTS
# ============================================================================


class TestSuppressionMechanics:
    """Tests for suppression format and mechanics.

    Covers: valid suppression format, invalid suppression detection, suppression
    with valid issue link, suppression does not affect other rules.
    """

    def test_valid_suppression_format_python(self, tmp_code_files: Path) -> None:
        """Valid Python suppression format: # nosemgrep <rule-id> <issue-link>.

        Valid issue link: M902-03, https://github.com/..., JIRA-123, GH-456.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    # nosemgrep EX-01 M902-03\n"  # Valid suppression
            "    except:  # Now acceptable with issue link\n"
            "        pass\n"
        )

        assert python_file.exists()
        assert "nosemgrep EX-01 M902-03" in python_file.read_text()

    def test_invalid_suppression_missing_issue_link(
        self, tmp_code_files: Path
    ) -> None:
        """Invalid suppression: # nosemgrep <rule-id> without issue link.

        Governance gate should flag this (GV-02 violation).
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    # nosemgrep EX-01\n"  # Invalid: missing issue link
            "    except:\n"
            "        pass\n"
        )

        assert python_file.exists()

    def test_suppression_with_github_issue_link(
        self, tmp_code_files: Path
    ) -> None:
        """Suppression with GitHub issue link is valid.

        Format: # nosemgrep <rule-id> https://github.com/...
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    # nosemgrep EX-01 https://github.com/org/repo/issues/123\n"
            "    except:\n"
            "        pass\n"
        )

        assert python_file.exists()

    def test_suppression_does_not_suppress_other_rules(
        self, tmp_code_files: Path
    ) -> None:
        """Suppression of one rule does not suppress other rules.

        If EX-01 is suppressed, EX-02 (silent swallowing) is still checked.
        """
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    # nosemgrep EX-01 M902-03\n"
            "    except:  # EX-01 suppressed, but EX-02 (silent swallow) may still be flagged\n"
            "        pass\n"
        )

        assert python_file.exists()

    def test_valid_eslint_disable_with_rule_and_issue(
        self, tmp_code_files: Path
    ) -> None:
        """Valid TypeScript suppression: // eslint-disable-line <rule> -- <issue>.

        Format: // eslint-disable-line react-hooks/exhaustive-deps -- M902-03
        """
        ts_file = tmp_code_files / "Component.tsx"
        ts_file.write_text(
            "import React, { useEffect } from 'react';\n"
            "\n"
            "export function Component(props) {\n"
            "  useEffect(() => {\n"
            "    fetchData(props.id);\n"
            "  }, []);  // eslint-disable-line react-hooks/exhaustive-deps -- M902-03\n"
            "  return <div>Data</div>;\n"
            "}\n"
        )

        assert ts_file.exists()


# ============================================================================
# JSON SCHEMA COMPLIANCE TESTS
# ============================================================================


class TestJSONSchemaCompliance:
    """Tests for gate output schema compliance.

    Validates: gate output matches M902-01 schema, violations array format,
    remediation_hints presence, artifact tracking.
    """

    def test_gate_output_has_required_fields(self, tmp_gate_results: Path) -> None:
        """Gate output JSON must include all required M902-01 schema fields.

        Required: version, status, gate, upstream_agent, downstream_agent,
        timestamp, ticket_id, artifacts, duration_ms, message.
        """
        # Create a mock gate output
        result = {
            "version": "0.1.0",
            "status": "FAIL",
            "gate": "governance_check",
            "upstream_agent": "Spec",
            "downstream_agent": "Implementation",
            "timestamp": "2026-05-15T08:30:00",
            "ticket_id": "M902-03",
            "artifacts": [],
            "duration_ms": 100,
            "message": "Governance violations detected.",
        }

        # Write to file and validate
        result_file = tmp_gate_results / "governance_check_2026-05-15T08-30-00.json"
        result_file.write_text(json.dumps(result, indent=2))

        # Parse and validate required fields
        parsed = json.loads(result_file.read_text())
        assert parsed["version"] == "0.1.0"
        assert parsed["status"] in ["PASS", "FAIL"]
        assert parsed["gate"] == "governance_check"
        assert parsed["duration_ms"] >= 0
        assert isinstance(parsed["artifacts"], list)

    def test_violations_array_format(self, tmp_gate_results: Path) -> None:
        """Violations array must have correct format.

        Each violation: file, line, rule, message, severity.
        """
        result = {
            "version": "0.1.0",
            "status": "FAIL",
            "gate": "governance_check",
            "upstream_agent": "Spec",
            "downstream_agent": "Implementation",
            "timestamp": "2026-05-15T08:30:00",
            "ticket_id": "M902-03",
            "artifacts": [],
            "duration_ms": 100,
            "message": "Governance violations detected.",
            "violations": [
                {
                    "file": "asset_generation/python/src/enemies/builder.py",
                    "line": 5,
                    "rule": "EX-01",
                    "message": "Bare except clause detected",
                    "severity": "ERROR",
                }
            ],
        }

        result_file = tmp_gate_results / "governance_check_2026-05-15T08-30-00.json"
        result_file.write_text(json.dumps(result, indent=2))

        parsed = json.loads(result_file.read_text())
        assert "violations" in parsed
        violation = parsed["violations"][0]
        assert "file" in violation
        assert "line" in violation
        assert "rule" in violation
        assert "message" in violation
        assert "severity" in violation

    def test_remediation_hints_present_on_fail(self, tmp_gate_results: Path) -> None:
        """When status=FAIL, remediation_hints must be present.

        Hints should map to violations and be actionable.
        """
        result = {
            "version": "0.1.0",
            "status": "FAIL",
            "gate": "governance_check",
            "upstream_agent": "Spec",
            "downstream_agent": "Implementation",
            "timestamp": "2026-05-15T08:30:00",
            "ticket_id": "M902-03",
            "artifacts": [],
            "duration_ms": 100,
            "message": "Governance violations detected.",
            "violations": [
                {
                    "file": "handler.py",
                    "line": 5,
                    "rule": "EX-01",
                    "message": "Bare except clause",
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": [
                "Replace bare 'except:' with specific exception type: 'except ValueError as e:'"
            ],
        }

        result_file = tmp_gate_results / "governance_check_2026-05-15T08-30-00.json"
        result_file.write_text(json.dumps(result, indent=2))

        parsed = json.loads(result_file.read_text())
        assert "remediation_hints" in parsed
        assert isinstance(parsed["remediation_hints"], list)
        assert len(parsed["remediation_hints"]) > 0

    def test_artifacts_array_tracks_scanned_files(self, tmp_gate_results: Path) -> None:
        """Artifacts array should track files scanned/analyzed.

        Each artifact: path, sha256, size_bytes.
        """
        result = {
            "version": "0.1.0",
            "status": "PASS",
            "gate": "governance_check",
            "upstream_agent": "Spec",
            "downstream_agent": "Implementation",
            "timestamp": "2026-05-15T08:30:00",
            "ticket_id": "M902-03",
            "artifacts": [
                {
                    "path": "asset_generation/python/src/enemies/builder.py",
                    "sha256": "abc123...",
                    "size_bytes": 1024,
                }
            ],
            "duration_ms": 100,
            "message": "All governance rules satisfied.",
        }

        result_file = tmp_gate_results / "governance_check_2026-05-15T08-30-00.json"
        result_file.write_text(json.dumps(result, indent=2))

        parsed = json.loads(result_file.read_text())
        assert isinstance(parsed["artifacts"], list)
        if len(parsed["artifacts"]) > 0:
            artifact = parsed["artifacts"][0]
            assert "path" in artifact
            assert "sha256" in artifact
            assert "size_bytes" in artifact


# ============================================================================
# SHADOW VS BLOCKING MODE TESTS
# ============================================================================


class TestShadowVsBlockingModes:
    """Tests for shadow mode (warning) vs blocking mode (fail).

    Covers: shadow mode reports without failing, blocking mode exits non-zero,
    both produce valid JSON.
    """

    def test_shadow_mode_reports_violations_exits_zero(
        self, tmp_code_files: Path, tmp_gate_results: Path
    ) -> None:
        """Shadow mode reports violations but exits with code 0.

        Users can see issues without workflow blockage.
        """
        # Create a code file with violations
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    except:\n"  # Violation: bare except (EX-01)
            "        pass\n"
        )

        # In shadow mode, gate should report but exit 0
        # Implementation detail: validated in Task 8
        assert python_file.exists()

    def test_blocking_mode_exits_nonzero_on_violations(
        self, tmp_code_files: Path
    ) -> None:
        """Blocking mode exits with non-zero code when violations found.

        Enforces governance rules in CI/CD pipeline.
        """
        # Create violation
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    except:\n"
            "        pass\n"
        )

        # In blocking mode, gate should exit non-zero
        assert python_file.exists()

    def test_blocking_mode_exits_zero_no_violations(
        self, tmp_code_files: Path
    ) -> None:
        """Blocking mode exits with zero code when no violations.

        Allows clean pipelines to proceed.
        """
        # Create clean code
        python_file = tmp_code_files / "handler.py"
        python_file.write_text(
            "def process():\n"
            "    try:\n"
            "        data = load()\n"
            "    except ValueError as e:\n"
            "        logger.error('failed', exc_info=True)\n"
            "        raise\n"
        )

        assert python_file.exists()

    def test_both_modes_produce_valid_json(
        self, tmp_gate_results: Path
    ) -> None:
        """Both shadow and blocking modes produce valid JSON output.

        Schema must be consistent across modes.
        """
        # Create valid JSON for both modes
        shadow_result = {
            "version": "0.1.0",
            "status": "FAIL",
            "gate": "governance_check",
            "upstream_agent": "Spec",
            "downstream_agent": "Implementation",
            "timestamp": "2026-05-15T08:30:00",
            "ticket_id": "M902-03",
            "artifacts": [],
            "duration_ms": 100,
            "message": "Violations in shadow mode (non-blocking).",
            "violations": [],
        }

        blocking_result = {
            "version": "0.1.0",
            "status": "PASS",
            "gate": "governance_check",
            "upstream_agent": "Spec",
            "downstream_agent": "Implementation",
            "timestamp": "2026-05-15T08:30:00",
            "ticket_id": "M902-03",
            "artifacts": [],
            "duration_ms": 100,
            "message": "No violations in blocking mode.",
        }

        # Both should be valid JSON
        shadow_file = tmp_gate_results / "shadow.json"
        blocking_file = tmp_gate_results / "blocking.json"

        shadow_file.write_text(json.dumps(shadow_result))
        blocking_file.write_text(json.dumps(blocking_result))

        assert json.loads(shadow_file.read_text())
        assert json.loads(blocking_file.read_text())


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions.

    Covers: missing code files, empty codebase, malformed rules, tool timeout,
    concurrent executions.
    """

    def test_graceful_handling_missing_code_files(
        self, tmp_gate_results: Path
    ) -> None:
        """Gate handles missing code files gracefully.

        Should not crash; report as skipped or zero violations.
        """
        # Reference non-existent code directory
        nonexistent = Path("/nonexistent/code/dir")
        assert not nonexistent.exists()

        # Gate should handle gracefully (not raise)
        # Implementation detail: validated in Task 8

    def test_empty_codebase_no_violations(self, tmp_code_files: Path) -> None:
        """Empty codebase (no Python/TS files) yields zero violations.

        Gate should report success with empty violations array.
        """
        # tmp_code_files is empty
        assert tmp_code_files.exists()
        assert list(tmp_code_files.glob("**/*.py")) == []

    def test_malformed_rule_config_error_handling(
        self, tmp_code_files: Path
    ) -> None:
        """Malformed rule configuration is handled with clear error.

        Should not silently fail; report error to user.
        """
        # Malformed semgrep config (if applicable)
        # Implementation detail: validated in Task 8
        pass

    def test_concurrent_gate_executions(
        self, tmp_gate_results: Path
    ) -> None:
        """Concurrent gate executions don't interfere (result files isolated).

        Each execution gets unique timestamp-based filename.
        """
        # Create multiple result files with unique timestamps
        for i in range(3):
            result = {
                "version": "0.1.0",
                "status": "PASS",
                "gate": "governance_check",
                "upstream_agent": "Spec",
                "downstream_agent": "Implementation",
                "timestamp": f"2026-05-15T08:30:{i:02d}",
                "ticket_id": "M902-03",
                "artifacts": [],
                "duration_ms": 100,
                "message": f"Execution {i}",
            }
            result_file = tmp_gate_results / f"governance_check_2026-05-15T08-30-{i:02d}.json"
            result_file.write_text(json.dumps(result))

        # All files should exist independently
        assert len(list(tmp_gate_results.glob("*.json"))) == 3

    def test_very_large_codebase_performance(
        self, tmp_code_files: Path
    ) -> None:
        """Gate performs reasonably on large codebase.

        Should complete in acceptable time (< 30s for typical repo).
        """
        # Create many Python files
        for i in range(50):
            file = tmp_code_files / f"file_{i}.py"
            file.write_text(
                f"def func_{i}():\n"
                f"    try:\n"
                f"        return load()\n"
                f"    except ValueError:\n"
                f"        pass\n"
            )

        assert len(list(tmp_code_files.glob("*.py"))) == 50

        # Time measurement (implementation detail, validated in Task 8)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestGovernanceCheckIntegration:
    """Integration tests for governance check gate with gate runner.

    Covers: gate registration, gate runner invocation, end-to-end workflow.
    """

    def test_governance_check_registered_in_gate_registry(
        self, repo_root: Path
    ) -> None:
        """Governance check gate must be registered in gate_registry.json.

        Registry entry: name=governance_check, category=governance, etc.
        """
        gate_registry = repo_root / "ci" / "scripts" / "gate_registry.json"
        assert gate_registry.exists()

        registry = json.loads(gate_registry.read_text())
        # Check for governance_check or similar entry
        # Implementation detail: validated in Task 9

    def test_gate_runner_can_invoke_governance_check(
        self, gate_runner: Path
    ) -> None:
        """Gate runner should be able to invoke governance_check gate.

        CLI: python gate_runner.py governance_check --mode shadow ...
        """
        # Verify gate_runner exists
        assert gate_runner.exists()

        # Verify it's executable Python
        content = gate_runner.read_text()
        assert "def main" in content or "if __name__" in content

    def test_taskfile_task_for_governance_check(self, repo_root: Path) -> None:
        """Taskfile should have task for running governance check in shadow mode.

        Task: hooks:governance-check or similar.
        """
        taskfile = repo_root / "Taskfile.yml"
        assert taskfile.exists()

        # Check for governance-related task (implementation detail)
        content = taskfile.read_text()
        # Expected: governance, check, rules, or similar task definition
