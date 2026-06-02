# Technical Choices

## Object Tracking: YOLOv8
We chose YOLOv8 because it automatically tracks people across video frames using built-in ID assignment, making zone detection accurate without extra configuration.

## Database: SQLite
We chose SQLite because it requires zero setup, runs entirely as a local file, and is stable enough for evaluation without risk of crashes or connection issues.