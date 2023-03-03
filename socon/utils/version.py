# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-BSD3-Clause-Django
# Copyright (c) 2023, Stephane Capponi and Others

import functools
import subprocess

from pathlib import PurePath


def get_version(version: tuple = None) -> str:
    """Return a PEP 440-compliant version number from VERSION."""
    version = get_complete_version(version)

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|rc}N - for alpha, beta, and rc releases

    main = get_main_version(version)

    sub = ""
    if version[3] == "alpha" and version[4] == 0:
        git_changeset = get_git_changeset()
        sub = ".dev"
        if git_changeset:
            sub = f"{sub}{git_changeset}"

    elif version[3] != "final":
        mapping = {"alpha": "a", "beta": "b", "rc": "rc"}
        sub = mapping[version[3]] + str(version[4])

    return main + sub


def get_main_version(version: tuple = None) -> str:
    """Return main version (X.Y[.Z]) from VERSION."""
    version = get_complete_version(version)
    parts = 2 if version[2] == 0 else 3
    return ".".join(str(x) for x in version[:parts])


def get_complete_version(version: tuple = None) -> tuple:
    """
    Return a tuple of the socon version. If version argument is non-empty,
    check for correctness of the tuple provided.
    """
    if version is None:
        from socon import VERSION as version
    else:
        assert len(version) == 5
        assert version[3] in ("alpha", "beta", "rc", "final")

    return version


def get_docs_version(version: tuple = None) -> str:
    """
    Get the version of the documentation. Return dev if the version
    is not a final one
    """
    version = get_complete_version(version)
    if version[3] != "final":
        return "dev"
    else:
        return "{0[0]}.{0[1]}".format(version[:2])


@functools.lru_cache()
def get_git_changeset() -> str:
    """Return the short hash of the latest git changeset"""
    try:
        repo_dir = PurePath(__file__).parents[1]
    except NameError:
        # Repository may not be found if __file__ is undefined, e.g. in a frozen
        # module.
        return None
    git_log = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=repo_dir,
        universal_newlines=True,
    )
    return git_log.stdout
