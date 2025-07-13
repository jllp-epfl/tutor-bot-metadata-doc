# Exercise Mapping File
A simple JSON-based system for mapping exercise numbers between different editions of courses.

## Overview

This system helps track how exercise numbering changes between course editions. It supports both:
- **Series-based courses**: Exercises organized in series (e.g., Series 1, Exercise 3)
- **Exercise-only courses**: Simple sequential numbering (e.g., Exercise 5)

## JSON Format

The mapping uses string keys for maximum flexibility:

```json
{
  "1-1": "1-4",
  "1-2": "1-2", 
  "1-3": null,
  "2-1": "2-2",
  "2-2": null,
  "5": "3",
  "6": null
}
```

### Key Format
- **Series-based**: (e.g., `"1-3"` for Series 1, Exercise 3)
- **Exercise-only**: (e.g., `"5"` for Exercise 5)

### Value Format
- **Mapped exercise**: String in same format as keys (e.g., `"1-4"` or `"3"`)
- **Removed exercise**: `null` for exercises that no longer exist


## File Naming Convention

Use the format `cousecode_{source_year}_to_{target_year}.json`:
- `2022_to_2024.json`
- `2023_to_2024.json`

