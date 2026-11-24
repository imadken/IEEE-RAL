"""Keep a calibrated recovery certificate separate from an identifying plan."""

from fractions import Fraction
from typing import Literal

from pydantic import model_validator

from .experiment_resolvability import minimum_resolving_experiments
from .experiment_schema import ExperimentPlan, ExperimentProblem
from .schema import Certificate, Frozen, Pair


class RecoveryEvidenceOutput(Frozen):
    status: Literal[
        "CERTIFIED_RECOVER",
        "UNRESOLVED",
        "NOT_RESOLVABLE_WITH_MENU",
        "REFUTED_WITHIN_CATALOGUE",
        "SOURCE_UNSUPPORTED",
    ]
    certificate: Certificate | None = None
    experiment_plan: ExperimentPlan | None = None
    recovery_authorized: bool = False
    reason: str
    interpretation: str

    @model_validator(mode="after")
    def authorization_requires_original_certificate(self):
        if self.recovery_authorized != (self.status == "CERTIFIED_RECOVER"):
            raise ValueError(
                "Only an original calibrated certificate authorizes recovery"
            )
        if self.recovery_authorized and (
            self.certificate is None or self.experiment_plan is not None
        ):
            raise ValueError("A plan is not a recovery certificate")
        if not self.recovery_authorized and self.certificate is not None:
            raise ValueError("Certificate must be returned explicitly as certified")
        if self.certificate is not None:
            c = self.certificate
            harm, gain, failure = (
                Fraction(str(v)) for v in (c.harm_upper, c.gain_lower, c.failure_upper)
            )
            qualified = (
                failure <= Fraction(1, 10)
                if c.obligation == "completion"
                else harm <= Fraction(1, 10)
                and (c.obligation == "harm_only" or gain >= Fraction(1, 20))
            )
            if (
                not qualified
                or not (0 <= harm <= 1 and 0 <= failure <= 1 and -1 <= gain <= 1)
                or not c.selected_leaf_scope
                or not c.assumptions
                or c.source_type == "uncontrolled_observational"
            ):
                raise ValueError(
                    "SOURCE_UNSUPPORTED: certificate fails the original obligation/source gate"
                )
        return self


class RepertoireInadequacy(Frozen):
    """An offline capability diagnostic, never an online future observation."""

    status: Literal["REPERTOIRE_INADEQUATE"] = "REPERTOIRE_INADEQUATE"
    witnessed_pair: Pair
    native_source_paths: tuple[str, str]
    native_source_sha256: tuple[str, str]
    source_qualified: Literal[True]
    offline_evidence_only: Literal[True] = True
    scope: Literal["THIS_RECORDED_CHECKPOINT_FIXED_MACROS_AND_HORIZON"] = (
        "THIS_RECORDED_CHECKPOINT_FIXED_MACROS_AND_HORIZON"
    )

    @model_validator(mode="after")
    def both_observed_macros_fail(self):
        if self.witnessed_pair.yc or self.witnessed_pair.yr:
            raise ValueError(
                "Repertoire failure needs two actually observed failed endpoints"
            )
        if not all(self.native_source_paths) or any(
            len(h) != 64 for h in self.native_source_sha256
        ):
            raise ValueError(
                "SOURCE_UNSUPPORTED: native paired provenance is incomplete"
            )
        return self


def resolve_evidence(
    *, certificate: Certificate | None = None, problem: ExperimentProblem | None = None
) -> RecoveryEvidenceOutput:
    """The certificate is the unchanged DSRE subroutine's validated output.

    This adapter neither creates a confidence set nor upgrades a finite catalogue
    to a physical confidence certificate. Physical actions remain the old gate.
    """
    if certificate is not None:
        return RecoveryEvidenceOutput(
            status="CERTIFIED_RECOVER",
            certificate=certificate,
            recovery_authorized=True,
            reason="ORIGINAL_SCOPE_VALID_DSRE_CERTIFICATE",
            interpretation="Original conditional calibration/source guarantees only",
        )
    if problem is None:
        return RecoveryEvidenceOutput(
            status="SOURCE_UNSUPPORTED",
            reason="SOURCE_OR_STATISTICAL_SUPPORT_MISSING",
            interpretation="No sound known-likelihood finite catalogue supplied; no invented worlds or outcomes",
        )
    plan = minimum_resolving_experiments(problem)
    context_note = (
        " Observation acquisition refines the target context; it does not resolve the old aggregate region's outcome law."
        if any(
            e.source.context_operation == "CONTEXT_REFINEMENT"
            for e in problem.experiments
        )
        else ""
    )
    if plan.status == "NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE":
        return RecoveryEvidenceOutput(
            status="NOT_RESOLVABLE_WITH_MENU",
            experiment_plan=plan,
            reason="OPPOSING_WORLDS_HAVE_IDENTICAL_ALL_MENU_LAWS",
            interpretation="Impossibility is conditional on this finite catalogue, declared sources and product-data model"
            + context_note,
        )
    if plan.unanimous_catalogue_verdict is False:
        return RecoveryEvidenceOutput(
            status="REFUTED_WITHIN_CATALOGUE",
            experiment_plan=plan,
            reason="ALL_DECLARED_FINITE_WORLDS_REJECT_OBLIGATION",
            interpretation="No actual robot repertoire failure or population refutation follows automatically",
        )
    return RecoveryEvidenceOutput(
        status="UNRESOLVED",
        experiment_plan=plan,
        reason="FINITE_CATALOGUE_ALREADY_POSITIVE_NOT_A_CALIBRATION_CERTIFICATE"
        if plan.unanimous_catalogue_verdict is True
        else "MINIMUM_CAPABLE_EXPERIMENT_TYPE_PLAN",
        interpretation="Different laws identify in principle; finite observations may remain inconclusive or refute recovery"
        + context_note,
    )
