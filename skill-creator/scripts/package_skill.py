#!/usr/bin/env python3
"""
Skill Packaging Script

Validates and packages a skill into a distributable zip file.

Usage:
    python package_skill.py <path/to/skill-folder> [output-directory]
    
Example:
    python package_skill.py ./my-skill
    python package_skill.py ./my-skill ./dist
"""

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path


def validate_skill(skill_path: Path) -> list[str]:
    """Validate a skill and return a list of errors."""
    errors = []
    
    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md not found")
        return errors
    
    content = skill_md.read_text()
    
    # Check YAML frontmatter
    if not content.startswith("---"):
        errors.append("SKILL.md must start with YAML frontmatter (---)")
        return errors
    
    # Extract frontmatter
    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("Invalid YAML frontmatter format")
        return errors
    
    frontmatter = parts[1]
    
    # Check required fields
    if "name:" not in frontmatter:
        errors.append("Missing 'name' field in frontmatter")
    if "description:" not in frontmatter:
        errors.append("Missing 'description' field in frontmatter")
    
    # Check description quality
    if "TODO" in frontmatter:
        errors.append("Frontmatter contains TODO placeholders - please complete the description")
    
    # Check name matches directory
    name_match = re.search(r"name:\s*(.+)", frontmatter)
    if name_match:
        skill_name = name_match.group(1).strip()
        if skill_name != skill_path.name:
            errors.append(f"Skill name '{skill_name}' doesn't match directory name '{skill_path.name}'")
    
    # Check body content
    body = parts[2]
    if "TODO" in body:
        errors.append("SKILL.md body contains TODO placeholders - please complete the content")
    
    return errors


def package_skill(skill_path: Path, output_dir: Path) -> Path | None:
    """Package a skill into a zip file."""
    
    # Validate first
    errors = validate_skill(skill_path)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return None
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create zip file
    zip_path = output_dir / f"{skill_path.name}.zip"
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_path.rglob("*"):
            if file_path.is_file():
                # Skip hidden files and __pycache__
                if any(part.startswith(".") or part == "__pycache__" 
                       for part in file_path.parts):
                    continue
                arcname = file_path.relative_to(skill_path.parent)
                zf.write(file_path, arcname)
    
    return zip_path


def main():
    parser = argparse.ArgumentParser(
        description="Validate and package a skill"
    )
    parser.add_argument(
        "skill_path",
        help="Path to the skill directory"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=".",
        help="Output directory for the zip file (default: current directory)"
    )
    
    args = parser.parse_args()
    
    skill_path = Path(args.skill_path).resolve()
    output_dir = Path(args.output_dir).resolve()
    
    if not skill_path.is_dir():
        print(f"Error: Not a directory: {skill_path}")
        sys.exit(1)
    
    print(f"Validating skill: {skill_path.name}")
    
    zip_path = package_skill(skill_path, output_dir)
    
    if zip_path:
        print(f"Successfully packaged: {zip_path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
