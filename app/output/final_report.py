"""Final output report assembly."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


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


def write_final_report_json(sections: FinalReportSections, path: str | Path) -> Path:
    """Write machine-readable final report JSON output."""

    payload = {
        "recommendation_summary": sections.recommendation_summary,
        "ranked_options_matrix": sections.ranked_options_matrix,
        "implementation_summary": sections.implementation_summary,
        "testing_report": sections.testing_report,
        "video_output_summary": sections.video_output_summary,
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
