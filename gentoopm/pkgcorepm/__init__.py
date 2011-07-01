#!/usr/bin/python
#	vim:fileencoding=utf-8
# (c) 2011 Michał Górny <mgorny@gentoo.org>
# Released under the terms of the 2-clause BSD license.

from pkgcore.config import load_config

from gentoopm.basepm import PackageManager
from gentoopm.pkgcorepm.repo import PkgCoreRepoDict

class PkgCorePM(PackageManager):
	name = 'pkgcore'

	def reload_config(self):
		self._config = load_config()

	@property
	def repositories(self):
		return PkgCoreRepoDict(self._config)
