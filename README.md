# Template-Engine-Bugs
## Jinja Syntax Error Detection and Repair Tool
### Folder Structure
**DetectionAndRepair/**
> - **fixer.py:** Core logic for error auto-repair (paired with detectors)
> - **detector.py:** Core module for syntax error detection (rule implementations)
> - **main.py:** Tool entry point (invokes detection/repair, handles input/output)
> - **models.py:** Data models (definitions for SyntaxError, State classes)
> - **template_test/:** Directory for test template files (place templates to be detected here)

## Jinja Template Element Extractor
### Folder Structure
**Extractor/**
> - **analyzer.py:** Core analysis entry (parses AST, invokes extractors)
> - **variable_extractor.py:** Extract variables model from Jinja2 AST
> - **tag_extractor.py:** Extract tags from Jinja2 AST
> - **filter_extractor.py:** Extract filters from Jinja2 AST
> - **test_templates/:** Test Jinja2 template files
> - **main.py:** Tool entry point (invokes analyzer, handles input/output)

