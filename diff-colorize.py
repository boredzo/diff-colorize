#!/usr/bin/env python

RESET_FORMAT = '\033[0m'
COLOR_FORMAT = '\033[38;5;%um'
BEGIN_REVERSE_FORMAT = '\033[7m'
END_REVERSE_FORMAT = '\033[27m'

INDEX_COLOR = 32
REMOVED_COLOR = 203
ADDED_COLOR = 2

prefixes_to_invert = ['---', '+++', '-', '+']

import sys
import fileinput

for line in fileinput.input():
	if line.startswith('Index: ') or line.startswith('diff --git '):
		color = INDEX_COLOR
	elif line.startswith('-'):
		color = REMOVED_COLOR
	elif line.startswith('+'):
		color = ADDED_COLOR
	else:
		color = None

	if color is not None:
		sys.stdout.write(COLOR_FORMAT % (color,))
		for prefix in prefixes_to_invert:
			if line.startswith(prefix):
				sys.stdout.write(BEGIN_REVERSE_FORMAT)
				sys.stdout.write(prefix)
				sys.stdout.write(END_REVERSE_FORMAT)
				line = line[len(prefix):]
				break
	else:
		sys.stdout.write(RESET_FORMAT)

	sys.stdout.write(line)

print RESET_FORMAT
