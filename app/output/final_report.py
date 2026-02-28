"""Final output report assembly."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FinalReportSections:
    """Structured sections for final output."""

    recommendation_summary: str
    ranked_options_matrix: str
    implementation_summary: str
    testing_report: str
    video_output_summary: str


def assemble_final_report(sections: FinalReportSections) -> str:
    """Assemble final human-readable report in required section order."""

    return "\n\n".join(
        [
            "## Recommendation Summary\n" + sections.recommendation_summary,
            "## Ranked Options Matrix\n" + sections.ranked_options_matrix,
            "## Implementation Summary\n" + sections.implementation_summary,
            "## Testing Report\n" + sections.testing_report,
            "## Demo Video Output Summary\n" + sections.video_output_summary,
        ]
    )
