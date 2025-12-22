#!/usr/bin/env python3
"""
Schema definitions for validating AI feedback system configuration files.
"""

from typing import Any, Dict, List, Optional, Tuple


# Known valid model names (as of December 2025)
KNOWN_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-5",
    "gpt-5.2",
    "o1",
    "o1-mini",
    "o1-preview",
    "o3",
    "o4-mini",
    "llama-3.1-405b-instruct",
    "llama-3.2-11b",
    "llama-3.2-90b",
    "phi-4",
    "phi-3.5-vision",
    "mistral-large",
    "mistral-large-2",
    "mistral-medium-2505",
    "deepseek-r1",
    "deepseek-r1-0528",
    "grok-2",
    "grok-3",
    "grok-3-mini",
]

# Known report formats
KNOWN_FORMATS = ["quarto", "markdown", "jupyter", "latex", "html"]

# Known truncation strategies
KNOWN_TRUNCATION_STRATEGIES = ["smart", "head", "tail"]


class ValidationError:
    """Represents a validation error with severity level."""

    ERROR = "error"
    WARNING = "warning"

    def __init__(self, severity: str, file: str, message: str, line: Optional[int] = None):
        self.severity = severity
        self.file = file
        self.message = message
        self.line = line

    def __str__(self):
        line_info = f"Line {self.line}: " if self.line else ""
        return f"{line_info}{self.message}"

    def __repr__(self):
        return f"ValidationError({self.severity}, {self.file}, {self.message}, {self.line})"


class ConfigSchema:
    """Schema for config.yml validation."""

    REQUIRED_FIELDS = [
        "report_file OR report.filename",
        "model.primary",
    ]

    @staticmethod
    def validate(config: Dict[str, Any]) -> List[ValidationError]:
        """Validate config.yml structure and values."""
        errors = []

        # Check required fields - support both old and new format
        # Old format: report_file
        # New format: report.filename
        has_report_file = "report_file" in config
        has_report_nested = "report" in config and isinstance(config.get("report"), dict) and "filename" in config["report"]

        if not has_report_file and not has_report_nested:
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    "config.yml",
                    "'report_file' or 'report.filename' is required but missing",
                )
            )

        if "model" not in config or not isinstance(config.get("model"), dict):
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    "config.yml",
                    "'model' section is required and must be a dictionary",
                )
            )
        else:
            model = config["model"]
            if "primary" not in model:
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "config.yml",
                        "'model.primary' is required but missing",
                    )
                )
            else:
                # Validate model name
                primary = model["primary"]
                if primary not in KNOWN_MODELS:
                    errors.append(
                        ValidationError(
                            ValidationError.WARNING,
                            "config.yml",
                            f"'model.primary' uses unknown model '{primary}'. "
                            f"Known models: {', '.join(KNOWN_MODELS[:5])}... "
                            f"(This may be fine if GitHub Models added new models)",
                        )
                    )

            if "fallback" in model:
                fallback = model["fallback"]
                if fallback not in KNOWN_MODELS:
                    errors.append(
                        ValidationError(
                            ValidationError.WARNING,
                            "config.yml",
                            f"'model.fallback' uses unknown model '{fallback}'",
                        )
                    )

        # Validate token limits (optional but recommended)
        if "max_input_tokens" in config:
            max_input = config["max_input_tokens"]
            if not isinstance(max_input, int) or max_input <= 0:
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "config.yml",
                        f"'max_input_tokens' must be a positive integer, got: {max_input}",
                    )
                )
        else:
            errors.append(
                ValidationError(
                    ValidationError.WARNING,
                    "config.yml",
                    "'max_input_tokens' is not set. Consider adding it for better control over token usage.",
                )
            )

        if "max_output_tokens" in config:
            max_output = config["max_output_tokens"]
            if not isinstance(max_output, int) or max_output <= 0:
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "config.yml",
                        f"'max_output_tokens' must be a positive integer, got: {max_output}",
                    )
                )
        else:
            errors.append(
                ValidationError(
                    ValidationError.WARNING,
                    "config.yml",
                    "'max_output_tokens' is not set. Consider adding it for better control over token usage.",
                )
            )

        # Validate report format (if present)
        if "report_format" in config:
            report_format = config["report_format"]
            if report_format not in KNOWN_FORMATS:
                errors.append(
                    ValidationError(
                        ValidationError.WARNING,
                        "config.yml",
                        f"'report_format' uses unknown format '{report_format}'. "
                        f"Known formats: {', '.join(KNOWN_FORMATS)}",
                    )
                )

        # Validate truncation strategy (if present)
        if "truncation_strategy" in config:
            strategy = config["truncation_strategy"]
            if strategy not in KNOWN_TRUNCATION_STRATEGIES:
                errors.append(
                    ValidationError(
                        ValidationError.WARNING,
                        "config.yml",
                        f"'truncation_strategy' uses unknown strategy '{strategy}'. "
                        f"Known strategies: {', '.join(KNOWN_TRUNCATION_STRATEGIES)}",
                    )
                )

        # Validate timeout settings (if present)
        if "request_timeout" in config:
            timeout = config["request_timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "config.yml",
                        f"'request_timeout' must be a positive number, got: {timeout}",
                    )
                )

        if "workflow_timeout" in config:
            timeout = config["workflow_timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "config.yml",
                        f"'workflow_timeout' must be a positive number, got: {timeout}",
                    )
                )

        # Validate feature flags (if present)
        feature_flags = [
            "enable_code_analysis",
            "enable_figure_checking",
            "enable_citation_checking",
            "enable_section_checking",
        ]
        for flag in feature_flags:
            if flag in config and not isinstance(config[flag], bool):
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "config.yml",
                        f"'{flag}' must be a boolean (true/false), got: {config[flag]}",
                    )
                )

        # Validate debug_mode section (if present)
        if "debug_mode" in config:
            debug = config["debug_mode"]
            if not isinstance(debug, dict):
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "config.yml",
                        "'debug_mode' must be a dictionary",
                    )
                )
            else:
                debug_flags = [
                    "enabled",
                    "save_prompts",
                    "save_responses",
                    "save_context",
                    "save_api_metadata",
                    "prettify_json",
                    "upload_artifacts",
                ]
                for flag in debug_flags:
                    if flag in debug and not isinstance(debug[flag], bool):
                        errors.append(
                            ValidationError(
                                ValidationError.ERROR,
                                "config.yml",
                                f"'debug_mode.{flag}' must be a boolean, got: {debug[flag]}",
                            )
                        )

                # Security warning if upload_artifacts is enabled
                if debug.get("upload_artifacts", False):
                    errors.append(
                        ValidationError(
                            ValidationError.WARNING,
                            "config.yml",
                            "'debug_mode.upload_artifacts' is enabled. Artifacts will contain student "
                            "report content and grading prompts. Only use in instructor-controlled repos.",
                        )
                    )

        return errors


class RubricSchema:
    """Schema for rubric.yml validation."""

    @staticmethod
    def validate(rubric: Dict[str, Any]) -> List[ValidationError]:
        """Validate rubric.yml structure and values."""
        errors = []

        # Check assignment section
        if "assignment" not in rubric:
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    "rubric.yml",
                    "'assignment' section is required but missing",
                )
            )
        else:
            assignment = rubric["assignment"]
            if not isinstance(assignment, dict):
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "rubric.yml",
                        "'assignment' must be a dictionary",
                    )
                )
            else:
                # Required assignment fields
                if "name" not in assignment:
                    errors.append(
                        ValidationError(
                            ValidationError.ERROR,
                            "rubric.yml",
                            "'assignment.name' is required but missing",
                        )
                    )
                if "course" not in assignment:
                    errors.append(
                        ValidationError(
                            ValidationError.ERROR,
                            "rubric.yml",
                            "'assignment.course' is required but missing",
                        )
                    )
                if "total_points" not in assignment:
                    errors.append(
                        ValidationError(
                            ValidationError.ERROR,
                            "rubric.yml",
                            "'assignment.total_points' is required but missing",
                        )
                    )
                else:
                    total = assignment["total_points"]
                    if not isinstance(total, (int, float)) or total <= 0:
                        errors.append(
                            ValidationError(
                                ValidationError.ERROR,
                                "rubric.yml",
                                f"'assignment.total_points' must be a positive number, got: {total}",
                            )
                        )

        # Check criteria
        if "criteria" not in rubric:
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    "rubric.yml",
                    "'criteria' list is required but missing",
                )
            )
        else:
            criteria = rubric["criteria"]
            if not isinstance(criteria, list):
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "rubric.yml",
                        "'criteria' must be a list",
                    )
                )
            elif len(criteria) == 0:
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        "rubric.yml",
                        "'criteria' list is empty - at least one criterion is required",
                    )
                )
            else:
                # Validate each criterion
                total_weight = 0
                seen_ids = set()

                for i, criterion in enumerate(criteria):
                    if not isinstance(criterion, dict):
                        errors.append(
                            ValidationError(
                                ValidationError.ERROR,
                                "rubric.yml",
                                f"Criterion {i+1} must be a dictionary",
                            )
                        )
                        continue

                    # Required fields
                    required = ["id", "name", "weight", "description"]
                    for field in required:
                        if field not in criterion:
                            errors.append(
                                ValidationError(
                                    ValidationError.ERROR,
                                    "rubric.yml",
                                    f"Criterion {i+1}: '{field}' is required but missing",
                                )
                            )

                    # Validate ID uniqueness
                    if "id" in criterion:
                        criterion_id = criterion["id"]
                        if criterion_id in seen_ids:
                            errors.append(
                                ValidationError(
                                    ValidationError.ERROR,
                                    "rubric.yml",
                                    f"Criterion {i+1}: duplicate id '{criterion_id}'",
                                )
                            )
                        seen_ids.add(criterion_id)

                    # Validate weight
                    if "weight" in criterion:
                        weight = criterion["weight"]
                        if not isinstance(weight, (int, float)) or weight <= 0:
                            errors.append(
                                ValidationError(
                                    ValidationError.ERROR,
                                    "rubric.yml",
                                    f"Criterion {i+1} ({criterion.get('name', '?')}): "
                                    f"'weight' must be a positive number, got: {weight}",
                                )
                            )
                        else:
                            total_weight += weight

                    # Validate levels
                    if "levels" not in criterion:
                        errors.append(
                            ValidationError(
                                ValidationError.WARNING,
                                "rubric.yml",
                                f"Criterion {i+1} ({criterion.get('name', '?')}): "
                                f"'levels' section is missing (recommended)",
                            )
                        )
                    else:
                        levels = criterion["levels"]
                        if not isinstance(levels, dict):
                            errors.append(
                                ValidationError(
                                    ValidationError.ERROR,
                                    "rubric.yml",
                                    f"Criterion {i+1} ({criterion.get('name', '?')}): "
                                    f"'levels' must be a dictionary",
                                )
                            )
                        else:
                            # Validate each level
                            for level_name, level_info in levels.items():
                                if not isinstance(level_info, dict):
                                    errors.append(
                                        ValidationError(
                                            ValidationError.ERROR,
                                            "rubric.yml",
                                            f"Criterion {i+1} ({criterion.get('name', '?')}), "
                                            f"level '{level_name}': must be a dictionary",
                                        )
                                    )
                                    continue

                                # Check point_range
                                if "point_range" in level_info:
                                    point_range = level_info["point_range"]
                                    if not isinstance(point_range, list) or len(point_range) != 2:
                                        errors.append(
                                            ValidationError(
                                                ValidationError.ERROR,
                                                "rubric.yml",
                                                f"Criterion {i+1} ({criterion.get('name', '?')}), "
                                                f"level '{level_name}': 'point_range' must be a list of 2 numbers [min, max]",
                                            )
                                        )
                                    else:
                                        min_points, max_points = point_range
                                        if min_points > max_points:
                                            errors.append(
                                                ValidationError(
                                                    ValidationError.ERROR,
                                                    "rubric.yml",
                                                    f"Criterion {i+1} ({criterion.get('name', '?')}), "
                                                    f"level '{level_name}': point_range min ({min_points}) > max ({max_points})",
                                                )
                                            )

                # Check total weight
                expected_weight = 100
                if "assignment" in rubric and "total_points" in rubric["assignment"]:
                    # If total_points is specified, we could use that, but 100% is conventional
                    pass

                if abs(total_weight - expected_weight) > 0.01:  # Allow for floating point
                    errors.append(
                        ValidationError(
                            ValidationError.WARNING,
                            "rubric.yml",
                            f"Criterion weights sum to {total_weight}, expected {expected_weight}. "
                            f"This may be intentional, but typically weights should sum to 100%.",
                        )
                    )

        return errors


class GuidanceSchema:
    """Schema for guidance.md validation."""

    @staticmethod
    def validate(guidance_path: str) -> List[ValidationError]:
        """Validate guidance.md exists and is not empty."""
        errors = []

        try:
            with open(guidance_path, "r") as f:
                content = f.read().strip()
                if not content:
                    errors.append(
                        ValidationError(
                            ValidationError.ERROR,
                            "guidance.md",
                            "File is empty - guidance content is required",
                        )
                    )
                elif len(content) < 100:
                    errors.append(
                        ValidationError(
                            ValidationError.WARNING,
                            "guidance.md",
                            f"File is very short ({len(content)} characters). "
                            f"Consider providing more detailed guidance for the AI.",
                        )
                    )
        except FileNotFoundError:
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    "guidance.md",
                    "File not found - guidance.md is required",
                )
            )
        except Exception as e:
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    "guidance.md",
                    f"Error reading file: {e}",
                )
            )

        return errors
