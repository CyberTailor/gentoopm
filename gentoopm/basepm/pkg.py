#!/usr/bin/python
#	vim:fileencoding=utf-8
# (c) 2011 Michał Górny <mgorny@gentoo.org>
# Released under the terms of the 2-clause BSD license.

import collections
from abc import abstractmethod, abstractproperty

from gentoopm.util import ABCObject

class PMKeyedPackageBase(ABCObject):
	"""
	Base class for key-identified package sets.
	"""

	def __init__(self, key, parent):
		self._key = key
		self._parent = parent

	@property
	def parent(self):
		"""
		A parent (higher level) PMKeyedPackageDict or None if top-level.
		"""
		return self._parent

	@property
	def key(self):
		"""
		The key for this level of PMKeyedPackageDict.
		"""
		return self._key

	@abstractproperty
	def key_name(self):
		"""
		The metadata key name for this key.
		"""
		pass

	@property
	def keys(self):
		"""
		The set of keys uniquely identifying the package set (i.e. the parent
		keys and this one).
		"""
		key_names = []
		keys = []
		o = self
		while o and o.key is not None:
			keys.insert(0, o.key)
			key_names.insert(0, o.key_name)
			o = o.parent
		t = collections.namedtuple('%sKeyTuple' % self.__class__.__name__,
				' '.join(key_names))
		return t(*keys)

class PMPackageSet(ABCObject):
	@abstractmethod
	def __iter__(self):
		"""
		Iterate over the packages (or sets) in a set.
		"""

	@property
	def flattened(self):
		"""
		Flatten the package set and iterate over it. Yield PMPackages.
		"""

		for i in self:
			if isinstance(i, PMKeyedPackageDict):
				for hi in i.flattened:
					yield hi
			else:
				yield i

	def filter(self, *args, **kwargs):
		"""
		Filter the packages based on keys passed as arguments. Positional
		arguments refer to keys by their level (with first arg being the
		top-level key), None means match-all. Keyword arguments refer to keys
		by their names.

		If an argument doesn't match any key (i.e. too many args are passed),
		a KeyError or IndexError will be raised. If the same key is referred
		through positional and keyword arguments, a TypeError will be raised.

		The filtering will result in an iterable of PMKeyedPackageDicts
		or PMPackages, depending on whether the filtering criteria are able
		to uniquely identify packages.

		The '==' operator is used to match packages. To extend matching, you
		can provide a class with __eq__() redefined as an argument.
		"""

		myargs = collections.defaultdict(lambda: None, enumerate(args))
		mykwargs = collections.defaultdict(lambda: None, **kwargs)

		i = 0
		try:
			el = next(iter(self))
		except StopIteration:
			pass
		else:
			k = el.key_name
			if myargs[i] is not None:
				if mykwargs[k] is not None:
					raise TypeError('args[%d] and kwargs[%s] refer to the same key.' % \
							(i, k))
				m = myargs[i]
			else:
				m = mykwargs[k]

			newargs = args[1:]
			newkwargs = kwargs.copy()
			try:
				del newkwargs[k]
			except KeyError:
				pass

		for el in self:
			if m is None or m == el.key:
				if newargs or newkwargs:
					for i in el.filter(*newargs, **newkwargs):
						yield i
				else:
					yield el

class PMKeyedPackageDict(PMKeyedPackageBase, PMPackageSet):
	"""
	A dict-like object representing a set of packages matched by a N-level key.
	If it's a last-level key, the dict evaluates to PMPackage subclass
	instances. Otherwise, it evaluates to lower-level PMKeyedPackageDicts.

	Usually, the highest level PMKeyedPackageDict is PMRepository. Then dicts
	refer to the category, package name and finally version (where they
	transform into PMPackages).
	"""

	@abstractmethod
	def __iter__(self):
		"""
		Iterate over child PMKeyedPackageDicts or PMPackages when bottom-level.
		"""
		pass

	def __getitem__(self, key):
		"""
		Get a sub-item matching the key.
		"""
		for i in self:
			if i.key == key:
				return i
		else:
			raise KeyError('No packages match keyset: (%s)' % \
					', '.join(self.keys + [key]))

class PMPackage(PMKeyedPackageBase):
	"""
	An abstract class representing a single, uniquely-keyed package
	in the package tree.
	"""

	@property
	def flattened(self):
		"""
		A convenience property. Returns the package itself, as an iterator.
		"""
		yield self

	def filter(self, *args, **kwargs):
		"""
		A convenience method. Raises an IndexError if args is not empty,
		or an KeyError if kwargs is not empty. Otherwise, returns itself
		as an iterator.
		"""

		if args:
			raise IndexError('Unused positional arguments: %s' % args)
		if kwargs:
			raise KeyError('Unused keyword arguments: %s' % kwargs)
		yield self

	@abstractproperty
	def metadata(self):
		"""
		Return PMPackageMetadata object for the package.
		"""
		pass

# Keep a list common to all PMs.
metadata_keys = (
	# mandatory ebuild-defined variables (as per PMS 7.2)
	'DESCRIPTION', 'HOMEPAGE', 'SRC_URI',
	'LICENSE', 'SLOT', 'KEYWORDS', 'IUSE',
	# optional ebuild-defined variables (PMS 7.3)
	'EAPI',
	'DEPEND', 'RDEPEND', 'PDEPEND',
	'RESTRICT', 'PROPERTIES',
	'REQUIRED_USE',
	# deprecated ebuild-defined vars (not in PMS anymore)
	'PROVIDE',
	# magic ebuild-defined vars (PMS 7.4)
	'INHERITED', 'DEFINED_PHASES'
)

class PMPackageMetadata(ABCObject):
	"""
	A dict-like object providing access to a package's metadata.
	"""

	@abstractmethod
	def __getitem__(self, key):
		"""
		Get the value of metadata key. Return it as a string, or an empty
		string when unset.
		"""
		pass

	def __iter__(self):
		"""
		Iterate over possible metadata keys.
		"""
		return iter(metadata_keys)
