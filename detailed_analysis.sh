#!/bin/bash

for service in app/services/*.py; do
  echo "### DETAILED ANALYSIS: $(basename $service)" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  echo "**Line-by-line Coverage Plan:**" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  # Count lines and functions
  lines=$(wc -l < "$service")
  functions=$(grep -c "def " "$service" || echo "0")
  classes=$(grep -c "^class " "$service" || echo "0")
  
  echo "- Total Lines: $lines" >> TODO_ANALYSIS.md
  echo "- Functions: $functions" >> TODO_ANALYSIS.md
  echo "- Classes: $classes" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  echo "**Functions to Test:**" >> TODO_ANALYSIS.md
  grep -n "def " "$service" | head -20 >> TODO_ANALYSIS.md || echo "No functions found" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  echo "**Dependencies:**" >> TODO_ANALYSIS.md
  grep -n "^from \|^import " "$service" | head -5 >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  echo "**TODO Items for Postman Collection:**" >> TODO_ANALYSIS.md
  echo "1. Create test requests for all public methods" >> TODO_ANALYSIS.md
  echo "2. Add comprehensive validation tests" >> TODO_ANALYSIS.md
  echo "3. Include error handling scenarios" >> TODO_ANALYSIS.md
  echo "4. Add performance tests for database operations" >> TODO_ANALYSIS.md
  echo "5. Create integration tests with related services" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
  
  echo "---" >> TODO_ANALYSIS.md
  echo "" >> TODO_ANALYSIS.md
done
