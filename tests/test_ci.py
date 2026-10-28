"""The CI toolchain probe must match what `make check` actually needs.

A probe that hard-fails on a tool the Makefile treats as optional kills the
job before the gate ever runs, which is how ai-check stayed red while
`make check` was green locally.
"""
import re
import unittest

from tests.util import REPO

WORKFLOW = REPO / ".github/workflows/ai-check.yml"
MAKEFILE = REPO / "Makefile"


def probed_tools():
    """Tool names the Toolchain step runs `--version` on."""
    text = WORKFLOW.read_text()
    step = text.split("name: Toolchain", 1)[1].split("name:", 1)[0]
    return re.findall(r"^\s*(\S+) --version$", step, re.MULTILINE)


def optional_tools():
    """Tools the Makefile guards with `command -v`, i.e. may be absent."""
    return set(re.findall(r"command -v (\S+) >/dev/null", MAKEFILE.read_text()))


class CiToolchain(unittest.TestCase):

    def test_probe_is_not_empty(self):
        self.assertTrue(probed_tools(), "Toolchain step probes nothing")

    def test_probe_does_not_require_an_optional_tool(self):
        optional = optional_tools()
        clashes = [t for t in probed_tools() if t in optional]
        self.assertEqual(
            clashes, [],
            f"{clashes} are optional in the Makefile (guarded by command -v) "
            f"but the CI probe hard-fails without them, so the Gate step "
            f"never runs",
        )

    def test_probe_covers_the_tools_the_gate_hard_requires(self):
        probed = set(probed_tools())
        for tool in ("shellcheck", "jq"):
            self.assertIn(tool, probed, f"{tool} is used unguarded by check")

    def test_shfmt_is_optional_in_the_makefile(self):
        # Guards the premise of the test above.
        self.assertIn("shfmt", optional_tools())


if __name__ == "__main__":
    unittest.main()
