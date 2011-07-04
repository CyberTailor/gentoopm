#!/usr/bin/python
#	vim:fileencoding=utf-8
# (c) 2011 Michał Górny <mgorny@gentoo.org>
# Released under the terms of the 2-clause BSD license.

import paludis

from gentoopm.basepm.pkg import PMKeyedPackageDict, PMPackage, PMPackageMetadata
from gentoopm.util import IterDictWrapper

class PaludisCategory(PMKeyedPackageDict):
	key_name = 'CATEGORY'
	def __init__(self, category, parent):
		PMKeyedPackageDict.__init__(self, str(category), parent)

	def __iter__(self):
		repo = self.parent
		for p in repo._repo.package_names(self.key, []):
			yield PaludisPackage(p, self)

	@property
	def packages(self):
		"""
		A convenience wrapper for the package list.
		"""
		return IterDictWrapper(self)

class PaludisPackage(PMKeyedPackageDict):
	key_name = 'PN'
	def __init__(self, qpn, parent):
		PMKeyedPackageDict.__init__(self, str(qpn.package), parent)
		self._qpn = qpn

	def __iter__(self):
		repo = self.parent.parent
		for p in repo._repo.package_ids(self._qpn, []):
			yield PaludisID(p, self)

	@property
	def versions(self):
		"""
		A convenience wrapper for the version list.
		"""
		return IterDictWrapper(self)

class PaludisID(PMPackage):
	key_name = 'PVR'
	def __init__(self, pkg, parent):
		self._pkg = pkg
		PMPackage.__init__(self, str(pkg.version), parent)

	@property
	def metadata(self):
		return PaludisMetadata(self._pkg)

class PaludisMetadata(PMPackageMetadata):
	def __init__(self, pkg):
		self._pkg = pkg

	def __getitem__(self, key):
		m = self._pkg.find_metadata(key)
		if m is None:
			return ''
		m = m.parse_value()
		if isinstance(m, paludis.StringSetIterable) \
				or isinstance(m, paludis.KeywordNameIterable):
			return ' '.join([str(x) for x in m])
		elif isinstance(m, paludis.AllDepSpec):
			raise NotImplementedError('Parsing %s is not supported yet.' % key)
		else:
			return str(m)