"""Python UsdValidation plugin; all rules share the CLI's driver-only checks."""
from pathlib import Path
import sys
from pxr import Sdf, UsdValidation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from usdaeco_plan.validation import findings
from . import validatorTokens as tokens


def task(rule):
    def validate(stage, time_range):
        return [UsdValidation.ValidationError(
            item["name"], getattr(UsdValidation.ValidationErrorType, item["severity"].title()),
            [UsdValidation.ValidationErrorSite(stage, Sdf.Path(p)) for p in item["paths"]],
            item["message"] + " Occurrences: " + str(item["occurrences"]))
            for item in findings(stage, rule)]
    return validate


_registry = UsdValidation.ValidationRegistry()
for _rule in tokens.ERROR_NAMES:
    _registry.RegisterPluginStageValidator("usdAecoPlanValidators:" + _rule + "Checker", task(_rule))
