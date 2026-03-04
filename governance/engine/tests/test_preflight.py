"""Tests for governance.engine.preflight — project.yaml pre-flight validation."""

import json
import textwrap

import pytest

from governance.engine.preflight import (
    PreflightResult,
    _discover_templates,
    _extract_languages,
    _language_to_template_name,
    validate_project_yaml,
)


# ---------------------------------------------------------------------------
# _extract_languages
# ---------------------------------------------------------------------------


class TestExtractLanguages:
    def test_single_language_string(self):
        assert _extract_languages({"language": "python"}) == ["python"]

    def test_languages_list(self):
        assert _extract_languages({"languages": ["python", "json"]}) == ["python", "json"]

    def test_languages_takes_precedence(self):
        data = {"language": "go", "languages": ["python", "json"]}
        assert _extract_languages(data) == ["python", "json"]

    def test_no_language_field(self):
        assert _extract_languages({"name": "test"}) == []

    def test_empty_language_string(self):
        assert _extract_languages({"language": ""}) == []

    def test_none_language(self):
        assert _extract_languages({"language": None}) == []

    def test_lowercases(self):
        assert _extract_languages({"languages": ["Python", "JSON"]}) == ["python", "json"]


# ---------------------------------------------------------------------------
# _language_to_template_name
# ---------------------------------------------------------------------------


class TestLanguageToTemplateName:
    def test_direct_match(self):
        assert _language_to_template_name("python") == "python"

    def test_typescript_maps_to_node(self):
        assert _language_to_template_name("typescript") == "node"

    def test_javascript_maps_to_node(self):
        assert _language_to_template_name("javascript") == "node"

    def test_csharp_maps(self):
        assert _language_to_template_name("c#") == "csharp"

    def test_markdown_maps_to_markdown_json(self):
        assert _language_to_template_name("markdown") == "markdown-json"

    def test_json_maps_to_markdown_json(self):
        assert _language_to_template_name("json") == "markdown-json"

    def test_unknown_returns_itself(self):
        assert _language_to_template_name("rust") == "rust"


# ---------------------------------------------------------------------------
# _discover_templates
# ---------------------------------------------------------------------------


class TestDiscoverTemplates:
    def test_finds_templates(self, tmp_path):
        # Create template dirs with project.yaml
        (tmp_path / "governance" / "templates" / "python").mkdir(parents=True)
        (tmp_path / "governance" / "templates" / "python" / "project.yaml").touch()
        (tmp_path / "governance" / "templates" / "node").mkdir(parents=True)
        (tmp_path / "governance" / "templates" / "node" / "project.yaml").touch()
        # Dir without project.yaml should be excluded
        (tmp_path / "governance" / "templates" / "empty").mkdir(parents=True)

        result = _discover_templates(tmp_path)
        assert result == ["node", "python"]

    def test_no_templates_dir(self, tmp_path):
        assert _discover_templates(tmp_path) == []


# ---------------------------------------------------------------------------
# validate_project_yaml — file missing
# ---------------------------------------------------------------------------


class TestValidateMissingFile:
    def test_missing_file_is_error(self, tmp_path):
        result = validate_project_yaml(tmp_path / "nonexistent.yaml")
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].check == "file_missing"


# ---------------------------------------------------------------------------
# validate_project_yaml — YAML syntax
# ---------------------------------------------------------------------------


class TestValidateYamlSyntax:
    def test_invalid_yaml(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text("name: [\ninvalid yaml")
        result = validate_project_yaml(path)
        assert result.valid is False
        assert any(f.check == "yaml_syntax" for f in result.errors)

    def test_non_dict_yaml(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text("- item1\n- item2\n")
        result = validate_project_yaml(path)
        assert result.valid is False
        assert any("mapping" in f.message for f in result.errors)


# ---------------------------------------------------------------------------
# validate_project_yaml — valid file
# ---------------------------------------------------------------------------


class TestValidateValidFile:
    def test_minimal_valid(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text('name: "test"\nlanguage: "python"\n')
        result = validate_project_yaml(path, governance_root=tmp_path)
        # No schema file means a warning, but no errors from syntax
        syntax_errors = [f for f in result.errors if f.check == "yaml_syntax"]
        assert syntax_errors == []

    def test_valid_with_languages(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(textwrap.dedent("""\
            name: "test"
            languages:
              - python
              - json
        """))
        result = validate_project_yaml(path, governance_root=tmp_path)
        assert result.languages == ["python", "json"]


# ---------------------------------------------------------------------------
# validate_project_yaml — duplicate keys
# ---------------------------------------------------------------------------


class TestValidateDuplicateKeys:
    def test_detects_duplicate_top_level_keys(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(textwrap.dedent("""\
            name: "test"
            conventions:
              git:
                commit_style: "conventional"
            conventions:
              git:
                commit_style: "freeform"
        """))
        result = validate_project_yaml(path, governance_root=tmp_path)
        dup_findings = [f for f in result.findings if f.check == "duplicate_key"]
        assert len(dup_findings) == 1
        assert "conventions" in dup_findings[0].message


# ---------------------------------------------------------------------------
# validate_project_yaml — both language and languages
# ---------------------------------------------------------------------------


class TestValidateBothLanguageFields:
    def test_warns_on_both(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(textwrap.dedent("""\
            name: "test"
            language: "python"
            languages:
              - python
              - json
        """))
        result = validate_project_yaml(path, governance_root=tmp_path)
        lang_warnings = [f for f in result.warnings if f.check == "language_field"]
        assert len(lang_warnings) == 1


# ---------------------------------------------------------------------------
# validate_project_yaml — template coverage
# ---------------------------------------------------------------------------


class TestValidateTemplateCoverage:
    def _setup_templates(self, tmp_path, template_names):
        """Create minimal template dirs."""
        for name in template_names:
            d = tmp_path / "governance" / "templates" / name
            d.mkdir(parents=True)
            (d / "project.yaml").touch()

    def test_all_templates_available(self, tmp_path):
        self._setup_templates(tmp_path, ["python", "markdown-json"])
        path = tmp_path / "project.yaml"
        path.write_text(textwrap.dedent("""\
            name: "test"
            languages:
              - python
              - markdown
              - json
        """))
        result = validate_project_yaml(path, governance_root=tmp_path)
        assert sorted(result.templates_available) == ["markdown-json", "python"]
        assert result.templates_missing == []
        template_warnings = [f for f in result.warnings if f.check == "template_coverage"]
        assert template_warnings == []

    def test_missing_template_warns(self, tmp_path):
        self._setup_templates(tmp_path, ["python"])
        path = tmp_path / "project.yaml"
        path.write_text(textwrap.dedent("""\
            name: "test"
            languages:
              - python
              - rust
        """))
        result = validate_project_yaml(path, governance_root=tmp_path)
        assert "rust" in result.templates_missing
        template_warnings = [f for f in result.warnings if f.check == "template_coverage"]
        assert len(template_warnings) == 1
        assert "rust" in template_warnings[0].message

    def test_typescript_resolves_to_node(self, tmp_path):
        self._setup_templates(tmp_path, ["node"])
        path = tmp_path / "project.yaml"
        path.write_text('name: "test"\nlanguage: "typescript"\n')
        result = validate_project_yaml(path, governance_root=tmp_path)
        assert result.templates_available == ["node"]
        assert result.templates_missing == []


# ---------------------------------------------------------------------------
# validate_project_yaml — orphaned keys detection
# ---------------------------------------------------------------------------


class TestValidateOrphanedKeys:
    def test_detects_orphaned_children(self, tmp_path):
        # The indented keys after "# repository:" parse as children of `governance`
        # in YAML, but the pattern is suspicious — they look like they belong to
        # the commented-out `repository:` parent.
        path = tmp_path / "project.yaml"
        path.write_text(textwrap.dedent("""\
            name: "test"
            governance:
              policy_profile: "default"
            # repository:
              auto_merge: true
        """))
        result = validate_project_yaml(path, governance_root=tmp_path)
        orphan_findings = [f for f in result.findings if f.check == "orphaned_keys"]
        assert len(orphan_findings) >= 1

    def test_no_false_positive_on_normal_comments(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(textwrap.dedent("""\
            name: "test"
            # This is just a comment
            language: "python"
        """))
        result = validate_project_yaml(path, governance_root=tmp_path)
        orphan_findings = [f for f in result.findings if f.check == "orphaned_keys"]
        assert orphan_findings == []


# ---------------------------------------------------------------------------
# validate_project_yaml — schema validation
# ---------------------------------------------------------------------------


class TestValidateSchema:
    def _setup_schema(self, tmp_path):
        """Create a minimal project schema."""
        schema_dir = tmp_path / "governance" / "schemas"
        schema_dir.mkdir(parents=True)
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "language": {"type": "string"},
                "languages": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "additionalProperties": False,
        }
        (schema_dir / "project.schema.json").write_text(json.dumps(schema))

    def test_valid_against_schema(self, tmp_path):
        self._setup_schema(tmp_path)
        path = tmp_path / "project.yaml"
        path.write_text('name: "test"\nlanguage: "python"\n')
        result = validate_project_yaml(path, governance_root=tmp_path)
        schema_errors = [f for f in result.errors if f.check == "schema"]
        assert schema_errors == []

    def test_invalid_against_schema(self, tmp_path):
        self._setup_schema(tmp_path)
        path = tmp_path / "project.yaml"
        path.write_text('name: "test"\nunknown_field: true\n')
        result = validate_project_yaml(path, governance_root=tmp_path)
        schema_errors = [f for f in result.errors if f.check == "schema"]
        assert len(schema_errors) >= 1


# ---------------------------------------------------------------------------
# PreflightResult
# ---------------------------------------------------------------------------


class TestPreflightResult:
    def test_empty_result_is_valid(self):
        r = PreflightResult()
        assert r.valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_error_makes_invalid(self):
        r = PreflightResult()
        r.add("error", "test", "something broke")
        assert r.valid is False

    def test_warning_keeps_valid(self):
        r = PreflightResult()
        r.add("warning", "test", "heads up")
        assert r.valid is True

    def test_to_dict(self):
        r = PreflightResult()
        r.languages = ["python"]
        r.add("warning", "test", "note")
        d = r.to_dict()
        assert d["valid"] is True
        assert d["languages"] == ["python"]
        assert len(d["findings"]) == 1

    def test_summary_no_findings(self):
        r = PreflightResult()
        assert "All checks passed" in r.summary()

    def test_summary_with_errors(self):
        r = PreflightResult()
        r.add("error", "yaml_syntax", "bad yaml")
        assert "ERRORS" in r.summary()
