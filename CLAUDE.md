# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is cctbx

The Computational Crystallography Toolbox (cctbx) is a large scientific computing project (~1M lines of code) for macromolecular structure determination and crystallographic analysis. It is the open-source core of the Phenix project. The codebase consists of 45+ modular packages that bind C++ classes to Python, organized to promote code reuse. Major modules include:

- **libtbx** — build system, utilities, test runner foundation
- **scitbx** — scientific toolbox (linear algebra, array manipulation, math)
- **cctbx** — core crystallography (miller indices, crystal symmetry, structure factors)
- **iotbx** — I/O for crystallography file formats (PDB, mmCIF, MTZ, etc.)
- **mmtbx** — macromolecular toolbox (maps, refinement, validation)
- **smtbx** — small-molecule toolbox
- **rstbx** — spotfinder / rotation image processing
- **xfel / simtbx** — X-ray free electron laser and simulation tools
- **gltbx / wxtbx / qttbx** — OpenGL graphics and GUI frameworks
- **fable** — Fortran-to-C++ translator

## Build System

cctbx uses a custom **libtbx**-based build system (SCons underneath). After building, all commands are available via the activated environment.

```bash
# Initial setup (downloads sources + builds)
python libtbx/auto_build/bootstrap.py base build --nproc=4
# or with conda for dependencies:
python libtbx/auto_build/bootstrap.py --use-conda base build --nproc=4

# After first build, activate the environment:
source ./build/setpaths.sh        # Linux/macOS
./build/setpaths.bat              # Windows

# Reconfigure to add/remove modules:
libtbx.configure cctbx iotbx scitbx mmtbx

# Rebuild (from build/ directory):
libtbx.scons -j 4

# Update sources and rebuild:
python libtbx/auto_build/bootstrap.py hot update build --nproc=4
```

## Running Tests

Tests live in `<module>/regression/` and are named `tst_<feature>.py`. Each module has a `run_tests.py` that registers all its tests.

```bash
# Run all tests for a module
libtbx.run_tests_parallel module=cctbx nproc=4

# Run multiple modules
libtbx.run_tests_parallel module=scitbx module=cctbx module=iotbx nproc=4

# Include slow tests (>30s, marked as tst_list_slow in run_tests.py)
libtbx.run_tests_parallel module=cctbx slow_tests=True nproc=4

# Run a single test file
libtbx.python path/to/tst_xxx.py
# or
python -m pytest path/to/tst_xxx.py  # if pytest is installed
```

New test files **must** be registered in the module's `run_tests.py` to be discovered.

## Code Quality Checks

```bash
# Check for common style issues (integer division, tabs, trailing whitespace,
# unused imports, bare except statements)
libtbx.find_clutter --verbose

# Auto-fix clutter issues
libtbx.clean_clutter

# Find unused imports
libtbx.find_unused_imports_crude .

# Compile-check all Python files
libtbx.py_compile_all -v .
```

CI runs `libtbx.find_clutter --verbose` and `libtbx.py_compile_all -v .` on every PR (`.github/workflows/syntax.yml`).

## Coding Conventions

From CONTRIBUTING.md — these differ from standard Python conventions:

- **Indent 2 spaces** (not 4). Follow the style of the file you're editing.
- **Nested imports** are preferred over top-level imports to avoid startup overhead in this large codebase. Import at function/method scope unless genuinely needed at module level.
- **Never `import *`** except in `__init__.py` files.
- **No `isinstance()`** — use duck typing and interface contracts.
- **Printing**: Use `print(x, file=log)`, implement `show(out=None)` methods. Avoid unconditional printing that bypasses log control.
- **`bare except`** is forbidden; use `except Exception`.
- **Assertions** should include values: `assert a > b, "%f > %f" % (a, b)`.
- **No new external dependencies** without discussion — installation complexity is a major concern.
- **Check for existing utilities** before implementing: `scitbx.constants`, `libtbx.test_utils.approx_equal()`, etc.

## Test Writing Guidelines

- One functionality per test file.
- Keep runtime under 30s; absolute max 60s (mark slow tests in `tst_list_slow`).
- Generate test data at runtime; avoid committing large data files. For small molecules, embed PDB/mmCIF strings directly in the test. Reuse regression models like `model_1yjp`.
- Use `libtbx.test_utils.approx_equal()` for floating-point comparison.
- Use `libtbx.easy_run.call()` for subprocess calls (not `fully_buffered`).
- For optional modules: use inline imports and guard with `libtbx.env.has_module("phenix")`.
- Use exceptions for error signalling; don't parse stdout to detect failures.

## C++/Python Binding Pattern

C++ classes are wrapped with Boost.Python. The pattern is:
- C++ source in `<module>/include/` and `<module>/src/`
- Python bindings in `<module>/boost_python/`
- Python interface layer in `<module>/` (`.py` files that import the compiled extension)
- SConscript files drive compilation

## CI

- **`.github/workflows/quick.yml`** — main build+test CI on Linux, macOS, Windows using conda
- **`.github/workflows/syntax.yml`** — linting and compile checks on Python 3.9–3.14
- **`azure-pipelines.yml`** — extended CI pipeline
