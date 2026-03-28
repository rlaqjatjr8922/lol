from dataclasses import dataclass, field
from typing import List


@dataclass
class CoachResult:
    title: str = ""
    summary: str = ""
    tips: List[str] = field(default_factory=list)
    danger: str = "normal"

    def to_multiline_text(self) -> str:
        lines = []
        if self.title:
            lines.append(self.title)
        if self.summary:
            lines.append(self.summary)
        if self.tips:
            lines.append("")
            lines.append("추천:")
            for tip in self.tips:
                lines.append(f"- {tip}")
        return "\n".join(lines).strip()