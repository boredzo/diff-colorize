#!/usr/bin/env python

import os

INDEX_COLOR      = int(os.environ.get('DIFF_INDEX_COLOR', 32))
REMOVED_COLOR    = int(os.environ.get('DIFF_REMOVED_COLOR', 203))
ADDED_COLOR      = int(os.environ.get('DIFF_ADDED_COLOR', 2))
HUNK_START_COLOR = int(os.environ.get('DIFF_HUNK_START_COLOR', 32))

RESET_FORMAT = '\033[0m'
COLOR_FORMAT = '\033[38;5;%um'
BEGIN_REVERSE_FORMAT = '\033[7m'
END_REVERSE_FORMAT = '\033[27m'

class OrderedDict(dict):
	def __init__(self, input=None):
		if input is None:
			self.keys = []
			super(OrderedDict, self).__init__()
		elif isinstance(input, dict):
			self.keys = list(input)
			super(OrderedDict, self).__init__(input)
		else:
			self.keys = [k for k, v in input]
			super(OrderedDict, self).__init__(input)
	def __iter__(self):
		return iter(self.keys)
	def __setitem__(self, k, v):
		if k not in self:
			self.keys.append(k)
		super(OrderedDict, self).__setitem__(k, v)
	def __delitem__(self, k):
		super(OrderedDict, self).__delitem__(k)
		self.keys.remove(k)

prefixes = OrderedDict()
prefixes['---'] = (
	COLOR_FORMAT % (REMOVED_COLOR,)
	+ BEGIN_REVERSE_FORMAT 
	+ '---'
	+ END_REVERSE_FORMAT
)
prefixes['+++'] = (
	COLOR_FORMAT % (ADDED_COLOR,)
	+ BEGIN_REVERSE_FORMAT 
	+ '+++'
	+ END_REVERSE_FORMAT
)
prefixes['-'] = (
	COLOR_FORMAT % (REMOVED_COLOR,)
	+ BEGIN_REVERSE_FORMAT 
	+ '-'
	+ END_REVERSE_FORMAT
)
prefixes['+'] = (
	COLOR_FORMAT % (ADDED_COLOR,)
	+ BEGIN_REVERSE_FORMAT 
	+ '+'
	+ END_REVERSE_FORMAT
)
prefixes['Index: '] = COLOR_FORMAT % (INDEX_COLOR,) + 'Index: '
prefixes['diff --git '] = COLOR_FORMAT % (INDEX_COLOR,) + 'diff --git '
prefixes['@@'] = (
	COLOR_FORMAT % (HUNK_START_COLOR,)
	+ BEGIN_REVERSE_FORMAT
	+ '@@'
)

import sys
import fileinput

for line in fileinput.input():
	for prefix_to_test in prefixes:
		if line.startswith(prefix_to_test):
			sys.stdout.write(prefixes[prefix_to_test])
			line = line[len(prefix_to_test):]

	sys.stdout.write(line)

	sys.stdout.write(RESET_FORMAT)

print RESET_FORMAT
