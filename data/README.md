# Data Directory

This directory contains sample datasets for testing and evaluation.

## Files

### sample_report.csv
Student profiles with:
- Student ID, name, email
- NBME score, UWorld percentile
- Weak and strong areas
- Study hours per day
- Target exam date

### sample_performance.csv
Session-level performance logs with:
- Student ID, timestamp
- Subject, topic
- Questions attempted/correct
- Time per question
- Confidence score

## Usage

These files are used for:
1. Testing agent pipeline execution
2. Validating database schema
3. Demonstrating system functionality
4. Bootstrapping development

## Loading Data

To load sample data into Supabase:

```python
import pandas as pd
from src.database.client import supabase

# Load students
students = pd.read_csv("data/sample_report.csv")
# Insert using Supabase client

# Load performance
performance = pd.read_csv("data/sample_performance.csv")
# Insert using Supabase client
```
