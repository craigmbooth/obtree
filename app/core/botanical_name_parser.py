"""Botanical name parser for parsing scientific names into structured components.

This module provides functionality to parse botanical scientific names into their
constituent parts: genus, species, subspecies, variety, and cultivar.
"""

import re
from typing import Optional, Dict


def parse_botanical_name(name: str) -> Dict[str, Optional[str]]:
    """Parse a botanical scientific name into structured components.

    Handles various formats including:
    - Genus species
    - Genus species var. variety
    - Genus species subsp. subspecies
    - Genus species 'Cultivar'
    - Combinations of the above

    Args:
        name: The full botanical name to parse

    Returns:
        Dict with keys: genus, species_name, subspecies, variety, cultivar

    Examples:
        >>> parse_botanical_name("Acer rubrum")
        {'genus': 'Acer', 'species_name': 'rubrum', ...}

        >>> parse_botanical_name("Acer rubrum var. trilobum")
        {'genus': 'Acer', 'species_name': 'rubrum', 'variety': 'trilobum', ...}

        >>> parse_botanical_name("Rosa 'Peace'")
        {'genus': 'Rosa', 'species_name': None, 'cultivar': 'Peace', ...}
    """
    result = {
        'genus': None,
        'species_name': None,
        'subspecies': None,
        'variety': None,
        'cultivar': None
    }

    if not name or not name.strip():
        return result

    # Clean up the input
    name = name.strip()

    # Extract cultivar first (enclosed in single quotes)
    cultivar_match = re.search(r"'([^']+)'", name)
    if cultivar_match:
        result['cultivar'] = cultivar_match.group(1)
        # Remove cultivar from the name for further parsing
        name = re.sub(r"'[^']+'", '', name).strip()

    # Split the remaining name into parts
    parts = name.split()

    if len(parts) == 0:
        return result

    # First part is always the genus (capitalized)
    result['genus'] = parts[0].capitalize()

    if len(parts) == 1:
        return result

    # Second part is the species (lowercase)
    result['species_name'] = parts[1].lower()

    if len(parts) == 2:
        return result

    # Look for subspecies or variety markers
    i = 2
    while i < len(parts):
        part = parts[i].lower()

        # Check for subspecies marker
        if part in ['subsp.', 'ssp.', 'subsp', 'ssp', 'subspecies']:
            if i + 1 < len(parts):
                result['subspecies'] = parts[i + 1].lower()
                i += 2
            else:
                i += 1

        # Check for variety marker
        elif part in ['var.', 'var', 'variety', 'v.']:
            if i + 1 < len(parts):
                result['variety'] = parts[i + 1].lower()
                i += 2
            else:
                i += 1

        # Check for forma marker (treat as variety)
        elif part in ['f.', 'forma', 'form']:
            if i + 1 < len(parts):
                result['variety'] = parts[i + 1].lower()
                i += 2
            else:
                i += 1

        else:
            # If no marker, might be a variety without the marker
            # This is a bit ambiguous, but we'll treat it as variety
            if not result['variety'] and not result['subspecies']:
                result['variety'] = part
            i += 1

    return result
