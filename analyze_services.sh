#!/bin/bash

for file in app/services/*.py; do
  echo "### $(basename $file)" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  echo "**File Path:** $file" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  # Extract class definitions
  echo "**Classes:**" >> TODO_ANALYSIS.md
  grep -n "^class " "$file" >> TODO_ANALYSIS.md || echo "No classes found" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  # Extract function definitions
  echo "**Functions:**" >> TODO_ANALYSIS.md
  grep -n "^def \|^    def " "$file" >> TODO_ANALYSIS.md || echo "No functions found" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  # Extract async functions
  echo "**Async Functions:**" >> TODO_ANALYSIS.md
  grep -n "^async def \|^    async def " "$file" >> TODO_ANALYSIS.md || echo "No async functions found" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  # Extract imports
  echo "**Imports:**" >> TODO_ANALYSIS.md
  grep -n "^from \|^import " "$file" | head -10 >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  echo "---" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
done
