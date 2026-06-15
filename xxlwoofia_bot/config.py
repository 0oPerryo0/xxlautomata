from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DailyMissionConfig:
    hard_mode_stage: str = "1-1"
    use_stamina_items: bool = False
    use_small_stamina_items: bool = False
    use_big_stamina_items: bool = False
    max_stamina_restore: int = 60
    stamina_item_order: tuple[int, ...] = (10, 60)
    ocr_language: str = "eng+chi_tra+chi_sim"
    tesseract_cmd: str = ""


@dataclass(frozen=True)
class Config:
    package: str = ""
    device_serial: str = ""
    launch_wait_seconds: float = 0.0
    package_keywords: tuple[str, ...] = ("xxlwoofia", "woofia", "xxl")
    daily_mission: DailyMissionConfig = DailyMissionConfig()

    def flow_vars(self) -> dict[str, object]:
        chapter, level = parse_stage(self.daily_mission.hard_mode_stage)
        return {
            "hard_mode_stage": self.daily_mission.hard_mode_stage,
            "hard_mode_chapter": f"{chapter:02d}",
            "hard_mode_level": f"{chapter}-{level}",
            "hard_mode_level_regex": rf"\u56f0\u96e3\s*{chapter}-{level}",
            "use_stamina_items": self.daily_mission.use_stamina_items,
            "use_small_stamina_items": self.daily_mission.use_small_stamina_items,
            "use_big_stamina_items": self.daily_mission.use_big_stamina_items,
            "max_stamina_restore": self.daily_mission.max_stamina_restore,
            "hard_mode_skip_ready": True,
            "ocr_language": self.daily_mission.ocr_language,
            "tesseract_cmd": self.daily_mission.tesseract_cmd,
        }


def load_config(path: Path) -> Config:
    if not path.exists():
        return Config()

    data = json.loads(path.read_text(encoding="utf-8-sig"))
    daily_data = data.get("daily_mission", {})
    return Config(
        package=str(data.get("package", "")).strip(),
        device_serial=str(data.get("device_serial", "")).strip(),
        launch_wait_seconds=float(data.get("launch_wait_seconds", 0.0)),
        package_keywords=tuple(data.get("package_keywords", ["xxlwoofia", "woofia", "xxl"])),
        daily_mission=DailyMissionConfig(
            hard_mode_stage=str(daily_data.get("hard_mode_stage", "1-1")).strip(),
            use_stamina_items=bool(daily_data.get("use_stamina_items", False)),
            use_small_stamina_items=bool(daily_data.get("use_small_stamina_items", False)),
            use_big_stamina_items=bool(daily_data.get("use_big_stamina_items", False)),
            max_stamina_restore=int(daily_data.get("max_stamina_restore", 60)),
            stamina_item_order=tuple(int(value) for value in daily_data.get("stamina_item_order", [10, 60])),
            ocr_language=str(daily_data.get("ocr_language", "eng+chi_tra+chi_sim")).strip(),
            tesseract_cmd=str(daily_data.get("tesseract_cmd", "")).strip(),
        ),
    )


def parse_stage(stage: str) -> tuple[int, int]:
    try:
        chapter, level = stage.split("-", 1)
        return int(chapter), int(level)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Invalid hard_mode_stage {stage!r}. Use a value like '1-1'.") from exc
