"""Adversarial tests: encoded instruction vectors (base64, HTML, data URIs)."""

import pytest

from governance.engine.security_prefilter import SecurityPrefilter
from governance.engine.tests.adversarial.vectors import ENCODED_INSTRUCTION_VECTORS


@pytest.fixture
def prefilter():
    return SecurityPrefilter()


class TestEncodedInstructionDetection:
    """Verify that encoded instruction vectors are detected."""

    @pytest.mark.parametrize(
        "vector",
        ENCODED_INSTRUCTION_VECTORS,
        ids=[v["description"] for v in ENCODED_INSTRUCTION_VECTORS],
    )
    def test_detects_encoded(self, prefilter, vector):
        findings = prefilter.scan(vector["content"])
        assert len(findings) > 0, (
            f"Failed to detect: {vector['description']}\n"
            f"Content: {vector['content'][:100]}"
        )


class TestEncodedVariants:
    """Test additional encoding-based attack patterns."""

    def test_data_uri_in_image_tag(self, prefilter):
        content = '<img src="data:text/html,<script>alert(1)</script>">'
        findings = prefilter.scan(content)
        assert len(findings) > 0

    def test_javascript_link(self, prefilter):
        content = "[Click me](javascript:void(0))"
        findings = prefilter.scan(content)
        assert len(findings) > 0

    def test_nested_script_in_markdown(self, prefilter):
        content = """## Normal heading

Some text about the feature.

<script>
  // This should not be in markdown
  fetch('/api/secrets').then(r => r.text()).then(console.log)
</script>

More normal text.
"""
        findings = prefilter.scan(content)
        assert len(findings) > 0

    def test_high_entropy_payload_detected(self, prefilter):
        # This is base64 for "malicious encoded payload test string with extra entropy"
        content = "bWFsaWNpb3VzIGVuY29kZWQgcGF5bG9hZCB0ZXN0IHN0cmluZyB3aXRoIGV4dHJhIGVudHJvcHk="
        findings = prefilter.scan(content)
        # Should detect high-entropy base64-like string
        assert len(findings) > 0


class TestDetectionRates:
    """Track aggregate detection rates across all vectors."""

    def test_overall_detection_rate(self, prefilter):
        from governance.engine.tests.adversarial.vectors import ALL_MALICIOUS_VECTORS

        detected = 0
        total = len(ALL_MALICIOUS_VECTORS)

        for vector in ALL_MALICIOUS_VECTORS:
            findings = prefilter.scan(vector["content"])
            if len(findings) > 0:
                detected += 1

        detection_rate = detected / total if total > 0 else 0.0
        # We expect at least 90% detection rate
        assert detection_rate >= 0.90, (
            f"Detection rate {detection_rate:.1%} is below 90% threshold. "
            f"Detected {detected}/{total} vectors."
        )
