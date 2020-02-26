#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xarray-base Ocean Analysis library

The successor of Vacumm.
"""
# Copyright or © or Copr. Shom/Ifremer/Actimar
#
# stephane.raynaud@shom.fr, charria@ifremer.fr, wilkins@actimar.fr
#
# This software is a computer program whose purpose is to [describe
# functionalities and technical features of your software].
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

import importlib
import os
import re
import warnings

import appdirs
import configobj
import validate

__project__ = "xoa"
__version__ = "0.1.0"
__release__ = "0"
__date__ = "2020-02-04"
__author__ = "Shom/Ifremer/Actimar"
__email__ = (
    "stephane.raynaud@actimarshom.fr, charria@ifremer.fr, wilkins@actimar.fr"
)
__copyright__ = "Copyright (c) 2020 Shom/Ifremer/Actimar"
__description__ = __doc__

_RE_OPTION_MATCH = re.compile(r"^(\w+)\W(\w+)$").match

#: Specifications of configuration options
CONFIG_INI = """
[plot]
cmapdiv = string(default="cmo.balance") # defaut diveging colormap
cmappos = string(default="cmo.amp")     # default positive colormap
cmapneg = string(default="cmo.tempo_r") # default negative colormap
cmapcyc = string(default="cmo.phase")   # default cyclic colormap
"""

#: Default xoa user configuration file
DEFAULT_USER_CONFIG_FILE = os.path.join(
    appdirs.user_data_dir("xoa"), "xoa.cfg"
)

_REQUIREMENTS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "requirements.txt"
)

_CACHE = {}


class XoaError(Exception):
    pass


class XoaConfigError(XoaError):
    pass


class XoaWarning(UserWarning):
    pass


def xoa_warn(message):
    """Issue a :class:`XoaWarning` warning"""
    warnings.warn(message, XoaWarning, stacklevel=2)


def load_options(cfgfile=None):
    if "cfgspecs" not in _CACHE:
        _CACHE["cfgspecs"] = configobj.ConfigObj(
            CONFIG_INI.split("\n"),
            list_values=False,
            interpolation=False,
            raise_errors=True,
            file_error=True,
        )
    if "options" not in _CACHE:
        _CACHE["options"] = configobj.ConfigObj(
            (
                DEFAULT_USER_CONFIG_FILE
                if os.path.exists(DEFAULT_USER_CONFIG_FILE)
                else None
            ),
            configspec=_CACHE["cfgspecs"],
            file_error=False,
            raise_errors=True,
            list_values=True,
        )
    if cfgfile:
        _CACHE["options"].merge(
            configobj.Configobj(
                cfgfile, file_error=True, raise_errors=True, list_values=True
            )
        )
    _CACHE["options"].validate(validate.Validator(), copy=True)


def _get_options_():
    if "options" not in _CACHE:
        load_options()
    return _CACHE["options"]


def get_option(section, option=None):
    """Get a config option

    Example
    -------
    >>> xoa.get_option('plot', 'cmapdiv')
    "cmo.balance"
    >>> xoa.get_option('plot.cmapdiv')
    "cmo.balance"
    """
    options = _get_options_()
    if option is None:
        m = _RE_OPTION_MATCH(option)
        if m:
            section, option = m.groups()
        else:
            raise XoaConfigError(
                "You must provide an option name to get_option"
            )
    try:
        value = options[section][option]
    except Exception:
        return XoaConfigError(f"Invalid section/option: {section}/{option}")
    return value


class set_options(object):
    """Set configuration options


    Example
    -------
    ::
        # Classic: for the session
        xoa.set_option('plot', cmapdiv='cmo.balance', cmappos='cmo.amp')

        # Context: temporary
        with xoa.set_options('plot', cmapdiv='cmo.balance'):
            print(xoa.get_option('plot.cmapdiv'))

    """

    def __init__(self, section, **options):
        self.old_options = _get_options_()
        options = configobj.ConfigObj(self.old_options)
        for option, value in options.items():
            options[section][option] = value
        options.validate(validate.Validator())
        _CACHE["options"] = options

    def __enter__(self):
        return _CACHE["options"]

    def __exit__(self, type, value, traceback):
        _CACHE["options"] = self.old_options


def show_options(specs=False):
    """Print current xoa configuration

    Parameters
    ----------
    specs: bool
        Print option specifications instead
    """
    if specs:
        print(CONFIG_INI.strip("\n"))
    else:
        print("\n".join(_get_options_().write()).strip("\n"))


def _parse_requirements_(reqfile):
    re_match_specs_match = re.compile(r"^(\w+)(\W+.+)?$").match
    reqs = {}
    with open(reqfile) as f:
        for line in f:
            line = line.strip().strip("\n")
            if line and not line.startswith("#"):
                m = re_match_specs_match(line)
                if m:
                    reqs[m.group(1)] = m.group(2)
    return reqs


def show_versions():
    """Print the versions of xoa and of some dependencies"""
    print("- xoa:", __version__)
    for package in _parse_requirements_(_REQUIREMENTS_FILE):
        pp = importlib.import_module(package)
        if hasattr(pp, "__version__"):
            print(f"- {package}: {pp.__version__}")


def show_info(opt_specs=True):
    """Print xoa related info"""
    print("# VERSIONS")
    show_versions()
    print("\n# FILES AND DIRECTORIES")
    print("xoa library dir:", os.path.dirname(__file__))
    print("default config file:", DEFAULT_USER_CONFIG_FILE)
    print("\n# OPTIONS")
    show_options(specs=opt_specs)
