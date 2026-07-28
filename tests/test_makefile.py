'''
Makefile integrity tests.

`make` is not installed on the development machine, so the Makefile
cannot be executed here. That is not a problem for the platform, because
every target is a thin wrapper over a `python -m` call that can be run
directly. It is a problem for the Makefile itself: an error in it would
only surface for whoever first runs `make` on a machine that has it.
These tests close that gap by checking statically what `make` would
discover at run time:
   every target dependency names a real target
   every `python -m MODULE` reference resolves to an importable module
   every recipe line is indented with a real tab, not spaces
   no recipe contains a literal backslash-n from a bad string escape
   the documented `make help` list matches the targets that exist

Two genuine escaping bugs were caught this way during Sprint 6.
'''

import importlib.util
import re
import shlex
from pathlib import Path

import pytest

MAKEFILE = Path('Makefile')

TARGET_PATTERN = re.compile(r'^([a-zA-Z][a-zA-Z0-9_-]*):(.*)$')
MODULE_PATTERN = re.compile(r'\$\(PYTHON\)\s+-m\s+([\w.]+)')

# Targets that only print, and so reference no module.
PRINT_ONLY_TARGETS = {'help', 'clean'}


def _read_lines():
   if not MAKEFILE.exists():
      pytest.skip('Makefile is not present')

   return MAKEFILE.read_text(encoding='utf-8').split('\n')


def _parse_targets(lines):
   targets = {}
   current = None

   for line in lines:
      match = TARGET_PATTERN.match(line)

      if match:
         current = match.group(1)
         targets[current] = {
            'dependencies': match.group(2).split(),
            'recipes': []
         }
      elif line.startswith('\t') and current:
         targets[current]['recipes'].append(line[1:])

   return targets


@pytest.fixture(scope='module')
def lines():
   return _read_lines()


@pytest.fixture(scope='module')
def targets(lines):
   return _parse_targets(lines)


def test_makefile_exists():
   assert MAKEFILE.exists()


def test_targets_are_parsed(targets):
   assert len(targets) >= 20


def test_every_dependency_names_a_real_target(targets):
   missing = [
      f'{name} -> {dependency}'
      for name, info in targets.items()
      for dependency in info['dependencies']
      if dependency not in targets
   ]

   assert missing == [], f'dependencies with no target: {missing}'


def test_every_referenced_module_is_importable(targets):
   unresolved = []

   for name, info in targets.items():
      for recipe in info['recipes']:
         for module in MODULE_PATTERN.findall(recipe):
            try:
               found = importlib.util.find_spec(module) is not None
            except (ImportError, ValueError):
               found = False

            if not found:
               unresolved.append(f'{name} -> {module}')

   assert unresolved == [], f'unresolvable modules: {unresolved}'


def test_recipes_use_tab_indentation(lines):
   # A recipe indented with spaces makes GNU make fail outright.
   #
   # Two kinds of space-indented line are legitimate and excluded: the
   # body of an ifeq conditional, and the continuation of a line that
   # ended with a backslash such as the .PHONY list.
   space_indented = []

   for index, line in enumerate(lines):
      if not line.startswith('    '):
         continue

      stripped = line.lstrip()
      if stripped.startswith(('#', 'PYTHON')):
         continue

      previous = lines[index - 1] if index else ''
      if previous.rstrip().endswith('\\'):
         continue

      space_indented.append((index + 1, line))

   assert space_indented == [], (
      f'space-indented lines that may be recipes: {space_indented}'
   )


def test_no_literal_backslash_escapes(lines):
   # A literal backslash-n would be read as a prerequisite named "n".
   offenders = [
      (number, line.strip()[:60])
      for number, line in enumerate(lines, 1)
      if r'\n' in line or r'\t' in line
   ]

   assert offenders == [], f'literal escapes found: {offenders}'


def test_recipe_lines_tokenise(targets):
   # Catches unbalanced quotes, which make would pass to the shell.
   broken = []

   for name, info in targets.items():
      for recipe in info['recipes']:
         body = recipe.lstrip('-@')

         if '$(PYTHON)' not in body:
            continue

         try:
            shlex.split(body.replace('$(PYTHON)', 'python'))
         except ValueError as error:
            broken.append(f'{name}: {error}')

   assert broken == [], f'recipes that do not tokenise: {broken}'


def test_help_documents_every_runnable_target(lines, targets):
   # Every target a user would invoke should appear in `make help`.
   help_text = '\n'.join(
      line for line in lines if line.strip().startswith('@echo')
   )

   documented = set(re.findall(r'make (\w+)', help_text))
   runnable = {
      name for name in targets
      if name not in {'help'} and not name.startswith('.')
   }

   undocumented = runnable - documented

   assert undocumented == set(), (
      f'targets missing from make help: {sorted(undocumented)}'
   )


def test_phony_declares_every_target(lines, targets):
   # A target missing from .PHONY would be skipped by make if a file of
   # that name ever appeared. The list drifted out of date twice while
   # targets were being added, so it is asserted rather than trusted.
   collecting = False
   declared = set()

   for line in lines:
      if line.startswith('.PHONY:'):
         collecting = True
         declared.update(line.split(':', 1)[1].replace('\\', '').split())
         if not line.rstrip().endswith('\\'):
            break
         continue

      if collecting:
         declared.update(line.replace('\\', '').split())
         if not line.rstrip().endswith('\\'):
            break

   undeclared = set(targets) - declared

   assert undeclared == set(), (
      f'targets missing from .PHONY: {sorted(undeclared)}'
   )


def test_every_non_print_target_does_something(targets):
   empty = [
      name for name, info in targets.items()
      if not info['recipes']
      and not info['dependencies']
      and name not in PRINT_ONLY_TARGETS
   ]

   assert empty == [], f'targets with no recipe and no dependencies: {empty}'


def test_all_target_covers_the_core_pipeline(targets):
   # `make all` should take a clean checkout to a full set of outputs.
   assert 'all' in targets

   dependencies = targets['all']['dependencies']

   for expected in ('load', 'ratios', 'screener', 'test'):
      assert expected in dependencies, (
         f'make all does not depend on {expected}'
      )
