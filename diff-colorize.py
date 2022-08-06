#!/usr/bin/env python

import sys
import os
import fileinput
import functools

has_256_color = (os.environ.get('TERM', None) == 'xterm-256color')

index_color      = int(os.environ.get('DIFF_INDEX_COLOR',
	 32 if has_256_color else 36))
old_mode_color   = int(os.environ.get('DIFF_OLD_MODE_COLOR',
	 88 if has_256_color else 31))
new_mode_color   = int(os.environ.get('DIFF_NEW_MODE_COLOR',
	 28 if has_256_color else 32))
removed_color    = int(os.environ.get('DIFF_REMOVED_COLOR',
	160 if has_256_color else 31))
added_color      = int(os.environ.get('DIFF_ADDED_COLOR',
	  2 if has_256_color else 32))
hunk_start_color = int(os.environ.get('DIFF_HUNK_START_COLOR',
	 32 if has_256_color else 36))

RESET_FORMAT = '\033[0m'
COLOR_FORMAT_256 = '\033[38;5;%um'
COLOR_FORMAT_16 = '\033[38;%um'
COLOR_FORMAT = COLOR_FORMAT_256 if has_256_color else COLOR_FORMAT_16
BEGIN_REVERSE_FORMAT = '\033[7m'
END_REVERSE_FORMAT = '\033[27m'

USAGE = """
diff-colorize 1.1 by Peter Hosey

Usage: diff ... | diff-colorize
   or:            diff-colorize < foo.diff

Reads unified or git-style diff data from standard input, colorizes it, and writes the result to standard output.

You can customize the color numbers used by setting these variables in your environment:
* DIFF_INDEX_COLOR (lines starting with "Index: " or "diff --git ")
* DIFF_OLD_MODE_COLOR (lines starting with "old mode"; these only appear in git-style diffs)
* DIFF_NEW_MODE_COLOR (lines starting with "new mode"; these only appear in git-style diffs)
* DIFF_REMOVED_COLOR (lines starting with "-")
* DIFF_ADDED_COLOR (lines starting with "+")
* DIFF_HUNK_START_COLOR (lines starting with "@@")
""".strip()

def interleave(*sequences):
	"Generator that yields one object from each sequence in turn."
	
	def zip_pad(*iterables, **kw):
		"Downloaded from http://code.activestate.com/recipes/497007/"
		from itertools import chain
		if kw:
			assert len(kw) == 1
			pad = kw["pad"]
		else:
			pad = None
		done = [len(iterables)-1]
		def pad_iter():
			if not done[0]:
				return
			done[0] -= 1
			while 1:
				yield pad
		iterables = [chain(seq, pad_iter()) for seq in iterables]
		return zip(*iterables)

	for objects in zip_pad(*sequences):
		for obj in objects:
			if obj is not None:
				yield obj

@functools.total_ordering
class Substring(object):
	def __init__(self, a, a_start, a_stop, b, b_start, b_stop):
		self.a = a
		self.a_start = a_start
		self.a_stop = a_stop
		self.b = b
		self.b_start = b_start
		self.b_stop = b_stop

	def before_a_substring(self):
		return self.a[:self.a_start]
	def before_b_substring(self):
		return self.b[:self.b_start]
	def substring(self):
		return ''.join(self.a[self.a_start:self.a_stop])
	a_substring = substring
	b_substring = substring
	def after_a_substring(self):
		return self.a[self.a_stop:]
	def after_b_substring(self):
		return self.b[self.b_stop:]

	def __hash__(self):
		return hash(self.substring())
	def __lt__(self, other):
		return self.a_start < other.a_start
	def __eq__(self, other):
		return self.substring() == other.substring()
	def __str__(self):
		return self.substring()
	def __repr__(self):
		return 'Substring(%r)' % (self.substring(),)
		return 'Substring(%r from %r, %r, %r, %r, %r, %r)' % (
			self.substring(),
			self.a, self.a_start, self.a_stop,
			self.b, self.b_start, self.b_stop,
			)

def longest_common_substring(a, b):
	"""Returns the longest common substring between a and b, which can be any finite indexable sliceable sequences, as a Substring object. Returns None if there is no substring between the sequences.

Clarified and slightly modified (to use a special Substring object) from http://en.wikibooks.org/w/index.php?title=Algorithm_implementation/Strings/Longest_common_substring&oldid=1419225#Python
"""
	a_len = len(a)
	b_len = len(b)
	lengths = [[0] * (b_len + 1) for i in range(a_len + 1)]
	substrings = set()
	greatest_length = current_run_length = 0
	for a_idx in range(a_len):
		for b_idx in range(b_len):
			if a[a_idx] == b[b_idx]:
				current_run_length = lengths[a_idx][b_idx] + 1
				lengths[a_idx+1][b_idx+1] = current_run_length
				if current_run_length > greatest_length:
					greatest_length = current_run_length
					substrings.clear()
				if current_run_length == greatest_length:
					# substrings.add(a[a_idx - current_run_length + 1:a_idx + 1])
					substrings.add(Substring(a, a_idx - current_run_length + 1, a_idx + 1, b, b_idx - current_run_length + 1, b_idx + 1))
	else:
		if current_run_length > 0:
			substrings.add(Substring(a, a_idx - current_run_length + 1, a_idx + 1, b, b_idx - current_run_length + 1, b_idx + 1))
	try:
		return substrings.pop()
	except KeyError:
		return None

def common_subsequence(a, b):
	"Returns all common substrings between a and b, which can be any finite indexable sliceable sequences, as Substring objects. Determines this by recursively calling itself on slices of a and b before and after each longest common substring."
	# Inspired by http://en.wikibooks.org/w/index.php?title=Algorithm_Implementation/Strings/Longest_common_subsequence&oldid=1912924#Python
	def LCS_length_matrix(a, b):
		matrix = [[0] * (len(b) + 1) for i in range(len(a) + 1)]
		for i, a_ch in enumerate(a):
			for j, b_ch in enumerate(b):
				if a_ch == b_ch:
					matrix[i + 1][j + 1] = matrix[i][j] + 1
				else:
					matrix[i + 1][j + 1] = max(matrix[i + 1][j], matrix[i][j + 1])
		return matrix

	def recursive_build_subsequence(a, b, matrix=None, i=None, j=None):
		if matrix is None:
			matrix = LCS_length_matrix(a, b)
		if i is None:
			i = len(a)
		if j is None:
			j = len(b)

		if i == 0 or j == 0:
			return []
		elif a[i - 1] == b[j - 1]:
			return recursive_build_subsequence(a, b, matrix, i - 1, j - 1) + [Substring(a, i - 1, i, b, j - 1, j)]
		else:
			if matrix[i][j - 1] > matrix[i - 1][j]:
				return recursive_build_subsequence(a, b, matrix, i, j - 1)
			else:
				return recursive_build_subsequence(a, b, matrix, i - 1, j)

	return recursive_build_subsequence(a, b)

def common_and_distinct_substrings(a, b):
	"Takes two strings, a and b, tokenizes them, and returns a linked list whose nodes contain runs of either common or unique tokens."
	def tokenize(a):
		"Each token is an identifier, a number, or a single character."
		import re
		# Word in identifier, word in macro name (MACRO_NAME), binary number, hex number, decimal or octal number, operator, other punctuation.
		token_exp = re.compile('[_A-Z]*[_a-z0-9]+:?|_??[A-Z0-9]+:?|0b[01]+|0[xX][0-9A-Fa-f]+|[0-9]+|[-+*|&^/%\[\]<=>,]|[()\\\\;`{}]')
		start = 0
		for match in token_exp.finditer(a):
			for ch in a[start:match.start()]:
				yield ch
			yield match.group(0)
			start = match.end()

		remainder = a[start:]
		if remainder:
			yield remainder

	a = list(tokenize(a))
	b = list(tokenize(b))

	class DualPayloadLinkedListNode(object):
		"This linked list gives each node two next pointers."
		def __init__(self, a, b, differ=None):
			self.a = a
			self.b = b
			self.next = None
			if differ is None:
				differ = (self.a != self.b)
			self.differ = differ
		def __iter__(self):
			def walk_linked_list(x):
				while x is not None:
					yield x
					x = x.next
			return walk_linked_list(self)
		def __repr__(self):
			return repr([('(%r, %r)' % (x.a, x.b)) if x.differ else repr(x.a) for x in self])

	# Linked-list nodes for common substrings will have a single Substring object in both payloads.
	# Nodes for difference runs will have a string in each payload.
	empty_substring = Substring(a, 0, 0, b, 0, 0)
	chunks_head = DualPayloadLinkedListNode(empty_substring, empty_substring, False)
	# This node is used when the input strings have no common substrings. When they do have common substrings, this node will be replaced with a real node.
	chunks_head.next = DualPayloadLinkedListNode(empty_substring, empty_substring, False)
	# Not chunks_head.next, since it will be replaced.
	chunks_tail = chunks_head
	for sub in sorted(common_subsequence(a, b)):
		last_sub = chunks_tail.a
		a_dif_run = ''.join(a[last_sub.a_stop:sub.a_start])
		b_dif_run = ''.join(b[last_sub.b_stop:sub.b_start])
		if a_dif_run or b_dif_run:
			chunks_tail.next = DualPayloadLinkedListNode(a_dif_run, b_dif_run, True)
			chunks_tail = chunks_tail.next
		chunks_tail.next = DualPayloadLinkedListNode(sub, sub, False)
		chunks_tail = chunks_tail.next
	else:
		# Get what comes after the last substring, if anything.
		last_sub = chunks_tail.a
		a_dif_run = ''.join(a[last_sub.a_stop:])
		b_dif_run = ''.join(b[last_sub.b_stop:])
		if a_dif_run or b_dif_run:
			chunks_tail.next = DualPayloadLinkedListNode(a_dif_run, b_dif_run, True)

	return chunks_head.next

# Everything in the unified diff format is identified by a prefix. The prefixes are:
# 'Index: ':    File marker (unified diff)
# 'diff --git': File marker (git-style diff)
# 'old mode':   File permissions mode before change
# 'new mode':   File permissions mode after change
# '---':        Defining '-' (giving the name and modification date of the file before change)
# '+++':        Defining '+' (giving the name and modification date of the file after change)
# '-':          Line before change (i.e., removed)
# '+':          Line after change (i.e., added)
# ' ':          Line that hasn't changed
# '@@':         Hunk start (@@ -start,length +start, length @@)
#
# We need to look for these prefixes in order, in order to handle '---'/'+++' before '-'/'+'. Hence the OrderedDict.
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

# Each value includes not only the terminal-config characters, but also the key, somewhere within it (possibly between two terminal-config strings).
# Theoretically, you could replace the key with some other string or leave it out entirely, if you wanted to, but I wouldn't recommend it.
prefixes = OrderedDict()
prefixes['---'] = (
	COLOR_FORMAT % (removed_color,)
	+ BEGIN_REVERSE_FORMAT 
	+ '---'
	+ END_REVERSE_FORMAT
)
prefixes['+++'] = (
	COLOR_FORMAT % (added_color,)
	+ BEGIN_REVERSE_FORMAT 
	+ '+++'
	+ END_REVERSE_FORMAT
)
prefixes['-'] = (
	COLOR_FORMAT % (removed_color,)
	+ BEGIN_REVERSE_FORMAT 
	+ '-'
	+ END_REVERSE_FORMAT
)
prefixes['+'] = (
	COLOR_FORMAT % (added_color,)
	+ BEGIN_REVERSE_FORMAT 
	+ '+'
	+ END_REVERSE_FORMAT
)
prefixes['old mode'] = ( # Git-style diffs only
	COLOR_FORMAT % (old_mode_color,)
	+ BEGIN_REVERSE_FORMAT 
	+ 'old mode'
	+ END_REVERSE_FORMAT
)
prefixes['new mode'] = ( # Git-style diffs only
	COLOR_FORMAT % (new_mode_color,)
	+ BEGIN_REVERSE_FORMAT 
	+ 'new mode'
	+ END_REVERSE_FORMAT
)
prefixes['Index: '] = COLOR_FORMAT % (index_color,) + 'Index: '
prefixes['diff --git '] = COLOR_FORMAT % (index_color,) + 'diff --git '
prefixes['@@'] = (
	COLOR_FORMAT % (hunk_start_color,)
	+ BEGIN_REVERSE_FORMAT
	+ '@@'
)

if __name__ == "__main__":
	if sys.stdin.isatty():
		# Standard input is a TTY, meaning that the user ran 'diff-colorize' at the shell prompt, without redirecting anything into it. Print usage info and exit.
		sys.exit(USAGE)

	# Buffers to support interleaving old and new lines that were contiguous runs.
	buffer_old = [] # '-' lines
	buffer_new = [] # '+' lines

	from string import whitespace

	def flush_buffers(buffer_old, buffer_new):
		"Flush the buffers, interleaving the lines and highlighting differences between them."
		def print_single_line(buffered_line):
			prefix = '-' if buffered_line.startswith('-') else '+'
			buffered_line = buffered_line[len(prefix):]

			sys.stdout.write(prefixes[prefix])
			sys.stdout.write(buffered_line)
			sys.stdout.write(RESET_FORMAT)

		last_line_if_old = None
		for buffered_line in interleave(buffer_old, buffer_new):
			if buffered_line.startswith('-'):
				if last_line_if_old is not None:
					print_single_line(last_line_if_old)
				last_line_if_old = buffered_line
			else:
				if last_line_if_old is None:
					# No old line immediately preceding this, so just print it.
					print_single_line(buffered_line)
				else:
					old_line = last_line_if_old
					new_line = buffered_line

					old_line_output = [prefixes['-']]
					new_line_output = [prefixes['+']]

					differenced_lines = common_and_distinct_substrings(old_line[1:], new_line[1:])
					lines_have_any_non_whitespace_part_in_common = False
					for node in differenced_lines:
						if not node.differ:
							if str(node.a) not in whitespace:
								lines_have_any_non_whitespace_part_in_common = True
								break

					for node in differenced_lines:
						if lines_have_any_non_whitespace_part_in_common and node.differ:
							old_line_output.append(BEGIN_REVERSE_FORMAT)
							old_line_output.append(str(node.a))
							old_line_output.append(END_REVERSE_FORMAT)

							new_line_output.append(BEGIN_REVERSE_FORMAT)
							new_line_output.append(str(node.b))
							new_line_output.append(END_REVERSE_FORMAT)
						else:
							old_line_output.append(str(node.a))
							new_line_output.append(str(node.b))

					last_line_if_old = None
					sys.stdout.writelines(''.join(old_line_output))
					sys.stdout.writelines(''.join(new_line_output))
		else:
			if last_line_if_old is not None:
				print_single_line(last_line_if_old)

		del buffer_old[:]
		del buffer_new[:]

	for line in fileinput.input():
		if line.startswith('-') and not line.startswith('---'):
			buffer_old.append(line)
			continue
		elif line.startswith('+') and not line.startswith('+++'):
			buffer_new.append(line)
			continue
		else:
			flush_buffers(buffer_old, buffer_new)

		for prefix_to_test in prefixes:
			if line.startswith(prefix_to_test):
				sys.stdout.write(prefixes[prefix_to_test])
				line = line[len(prefix_to_test):]

		sys.stdout.write(line)

		sys.stdout.write(RESET_FORMAT)
	else:
		flush_buffers(buffer_old, buffer_new)
