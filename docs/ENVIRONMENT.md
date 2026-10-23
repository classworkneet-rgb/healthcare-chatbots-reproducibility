# Runtime

Analysis and workbook writing: Python >= 3.10, standard library only.
No network or third-party dependencies are used by the one-command check.
The package was prepared using Python 3.13.5 on Linux.
Hosted CI is configured for Python 3.10, 3.12 and 3.13 on Ubuntu and Windows;
configuration alone is not evidence those hosted jobs have passed.

Git and the official GitHub CLI are needed only for publishing, not analysis.
GitHub Actions checkout/setup-python downloads require network during runner setup;
the subsequent analytical checks run with site packages disabled.
