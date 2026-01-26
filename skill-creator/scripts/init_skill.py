#!/usr/bin/env python3
"""
Skill Initialization Script

Creates a new skill directory with the proper structure and template files.

Usage:
    python init_skill.py <skill-name> --path <output-directory>
    
Example:
    python init_skill.py my-awesome-skill --path ~/.opencode/skills/
"""

import argparse
import os
from pathlib import Path


SKILL_TEMPLATE = '''---
name: {skill_name}
description: TODO: Add a clear description of what this skill does and when it should be used. Use third-person (e.g., "This skill should be used when...")
---

# {skill_title}

TODO: Add the main content of your skill here.

## When to Use This Skill

TODO: Describe the scenarios when this skill should be triggered.

## How to Use

TODO: Provide instructions on how to use this skill effectively.

## References

TODO: List any reference files in the `references/` directory that Claude should load when needed.

## Scripts

TODO: List any scripts in the `scripts/` directory that can be executed.

## Assets

TODO: List any assets in the `assets/` directory that are used in output.
'''


def create_skill(skill_name: str, output_path: str) -> None:
    """Create a new skill directory with template files."""
    
    skill_dir = Path(output_path) / skill_name
    
    if skill_dir.exists():
        print(f"Error: Directory already exists: {skill_dir}")
        return
    
    # Create directory structure
    skill_dir.mkdir(parents=True)
    (skill_dir / "scripts").mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "assets").mkdir()
    
    # Create SKILL.md
    skill_title = skill_name.replace("-", " ").title()
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title
    )
    (skill_dir / "SKILL.md").write_text(skill_content)
    
    # Create example files
    (skill_dir / "scripts" / "example.py").write_text(
        '#!/usr/bin/env python3\n"""Example script - delete if not needed."""\n\nprint("Hello from skill!")\n'
    )
    (skill_dir / "references" / "example.md").write_text(
        "# Example Reference\n\nThis is an example reference file. Delete if not needed.\n"
    )
    (skill_dir / "assets" / ".gitkeep").write_text("")
    
    print(f"Created skill: {skill_dir}")
    print(f"  - SKILL.md (edit this file)")
    print(f"  - scripts/ (add executable scripts)")
    print(f"  - references/ (add reference documentation)")
    print(f"  - assets/ (add templates, images, etc.)")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new skill directory"
    )
    parser.add_argument(
        "skill_name",
        help="Name of the skill (use kebab-case, e.g., my-awesome-skill)"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Output directory for the skill (default: current directory)"
    )
    
    args = parser.parse_args()
    create_skill(args.skill_name, args.path)


if __name__ == "__main__":
    main()
