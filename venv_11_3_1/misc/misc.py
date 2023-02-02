"""Miscellaneous Methods for PyAEDT."""
import os
import warnings


def list_installed_ansysem():
    """Return a list of installed AEDT versions on ``ANSYSEM_ROOT``."""
    aedt_env_var_prefix = "ANSYSEM_ROOT"
    version_list = sorted([x for x in os.environ if x.startswith(aedt_env_var_prefix)], reverse=True)
    aedt_env_var_sv_prefix = "ANSYSEMSV_ROOT"
    version_list += sorted([x for x in os.environ if x.startswith(aedt_env_var_sv_prefix)], reverse=True)

    if not version_list:
        warnings.warn(
            "No installed versions of AEDT are found in the system environment variables ``ANSYSEM_ROOTxxx``."
        )

    return version_list
