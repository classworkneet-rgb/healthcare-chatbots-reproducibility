# Publishing and archiving a version

1. Create the public GitHub repository and push this folder's contents. Inspect its
   Actions tab and confirm that every job for the uploaded commit passes.
2. Confirm the actual creators, author approvals, reuse rights and any journal
   anonymity restrictions. Add the approved license files and `CITATION.cff`.
3. After intended edits, rerun the analysis, review the changes, and regenerate the
   manifest with `python 03_code/update_manifest.py --confirm-reviewed-changes`.
   Run `python check_reproduction.py` and commit the complete result.
4. Sign into Zenodo, connect GitHub and enable this repository in Zenodo before
   creating the release. Confirm the archival creator and license metadata there.
5. Create the reviewed tag and publish a GitHub Release. The Zenodo integration
   archives the release. Inspect the resulting record and verify its version DOI
   and downloadable contents; do not treat a reserved DOI as a published record.
6. Cite the version DOI and exact Git commit in the manuscript/data-availability
   statement. Keep an editable GitHub link as an additional access route.

Official instructions:
- https://help.zenodo.org/docs/github/enable-repository/
- https://help.zenodo.org/docs/github/archive-software/github-upload/
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files

Preparing this folder does not create a GitHub repository, publish a release, mint a
DOI or approve an author/license declaration. The publishing kit's local script
requires your normal GitHub CLI authentication and never requests a token in chat.
