from lib import *

THEORY("Environments", """
<table><tr><th>Environment</th><th>Purpose</th><th>Data</th></tr>
<tr><td>Local</td><td>write code</td><td>tiny sample</td></tr>
<tr><td>Dev</td><td>try changes together</td><td>synthetic or masked</td></tr>
<tr><td>Staging</td><td>rehearse a release</td><td>production-like</td></tr>
<tr><td>Production</td><td>the real thing</td><td>real, access controlled</td></tr></table>
""")
FAQ("What does set -euo pipefail do?", "<p>Stops a script on an error (-e), on an unset variable (-u), and when any part of a pipeline fails (pipefail). Without it, failures can pass silently.</p>")
FAQ("Merge vs rebase?", "<p>Merge keeps history as it happened, adding a merge commit. Rebase replays your commits on top of another branch, giving a straight history. Don't rebase commits others are already using.</p>")
FAQ("Container vs virtual machine?", "<p>A VM includes a full operating system. A container shares the host kernel and packages only the app and its dependencies, so it's lighter and starts faster.</p>")
FAQ("Why do you put dependency install before copying code in a Dockerfile?", "<p>Layers are cached, and a change rebuilds everything after it. Code changes often and dependencies rarely, so this keeps most builds fast.</p>")
FAQ("How do you handle secrets?", "<p>Use a secrets manager or injected environment variables, never Git or images. If a key leaks, rotate it, since Git history retains it.</p>")
FAQ("How do you test a data pipeline?", "<p>Unit tests for transforms with small fixtures and edge cases, integration tests on a test database, and data quality checks on real runs.</p>")
FAQ("Scenario: disk full on a server. What do you do?", "<p>Use df -h to confirm, then du -sh * to find what's large. Often it's old logs or temp files. Clear them safely, then add rotation and an alert so that it doesn't recur.</p>")
FAQ("Scenario: a script reports success, but the output file is empty. What might be wrong?", "<p>An earlier step probably failed and the script carried on, or a pipeline hid the error. Add set -euo pipefail, and check row counts as a final step.</p>")
FAQ("Scenario: you committed an API key by accident. What now?", "<p>Rotate the key immediately, since it must be treated as compromised. Then remove it from the code, and from history if needed, and add a secret scanner to CI.</p>")
