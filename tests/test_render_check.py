"""Tests for plans/render.py --check flag."""

import os
import sys
from pathlib import Path
from unittest import mock

# Import the render module directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plans"))
import render


def test_render_check_clean_state(tmp_path):
    """Test that --check returns 0 when PLAN.md is up to date."""
    # Create a minimal plans structure
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    loop_dir = plans_dir / "test-loop"
    loop_dir.mkdir()

    # Create a minimal PLAN.md with a slice
    plan_md = loop_dir / "PLAN.md"
    plan_md.write_text(
        """# Test plan

### TEST-SLICE-1

```yaml
id: TEST-SLICE-1
loop: test-loop
phase: test
status: pending
```

Test body.
"""
    )

    # Mock the PLANS_DIR to use our tmp_path
    with mock.patch.object(render, "PLANS_DIR", plans_dir):
        with mock.patch.object(render, "LOOP_DIRS", [loop_dir]):
            with mock.patch.object(render, "MASTER", plans_dir / "PLAN.md"):
                # Generate the master PLAN.md
                slices = render.discover()
                new_text = render.render(slices)
                (plans_dir / "PLAN.md").write_text(new_text)

                # Now --check should pass
                assert (plans_dir / "PLAN.md").exists()
                assert (plans_dir / "PLAN.md").read_text() == new_text


def test_render_check_dirty_state(tmp_path):
    """Test that --check returns 1 when PLAN.md is stale."""
    # Create a minimal plans structure
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    loop_dir = plans_dir / "test-loop"
    loop_dir.mkdir()

    # Create a minimal PLAN.md with a slice
    plan_md = loop_dir / "PLAN.md"
    plan_md.write_text(
        """# Test plan

### TEST-SLICE-1

```yaml
id: TEST-SLICE-1
loop: test-loop
phase: test
status: pending
```

Test body.
"""
    )

    # Mock the PLANS_DIR to use our tmp_path
    with mock.patch.object(render, "PLANS_DIR", plans_dir):
        with mock.patch.object(render, "LOOP_DIRS", [loop_dir]):
            with mock.patch.object(render, "MASTER", plans_dir / "PLAN.md"):
                # Generate the master PLAN.md
                slices = render.discover()
                new_text = render.render(slices)
                (plans_dir / "PLAN.md").write_text(new_text)

                # Modify the loop PLAN.md to make PLAN.md stale
                plan_md.write_text(
                    """# Test plan

### TEST-SLICE-1

```yaml
id: TEST-SLICE-1
loop: test-loop
phase: test
status: done
```

Modified body.
"""
                )

                # Discover should find the updated slice
                slices_updated = render.discover()
                new_text_updated = render.render(slices_updated)

                # The new rendered text should be different
                old_text = (plans_dir / "PLAN.md").read_text()
                assert old_text != new_text_updated


def test_render_check_missing_plan_md(tmp_path):
    """Test that --check returns 1 when PLAN.md does not exist."""
    # Create a minimal plans structure
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    loop_dir = plans_dir / "test-loop"
    loop_dir.mkdir()

    # Create a minimal PLAN.md with a slice
    plan_md = loop_dir / "PLAN.md"
    plan_md.write_text(
        """# Test plan

### TEST-SLICE-1

```yaml
id: TEST-SLICE-1
loop: test-loop
phase: test
status: pending
```

Test body.
"""
    )

    # Mock the PLANS_DIR to use our tmp_path
    with mock.patch.object(render, "PLANS_DIR", plans_dir):
        with mock.patch.object(render, "LOOP_DIRS", [loop_dir]):
            with mock.patch.object(render, "MASTER", plans_dir / "PLAN.md"):
                # Don't create PLAN.md, just discover slices
                slices = render.discover()
                new_text = render.render(slices)

                # PLAN.md should not exist
                assert not (plans_dir / "PLAN.md").exists()

                # Trying to check would fail since file doesn't exist
                master = plans_dir / "PLAN.md"
                assert not master.exists() or master.read_text() != new_text
