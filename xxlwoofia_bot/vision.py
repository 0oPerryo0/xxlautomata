from __future__ import annotations

from pathlib import Path
import re


def find_template(
    screenshot_png: bytes,
    template_path: Path,
    threshold: float = 0.82,
) -> tuple[int, int, float] | None:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Image matching requires opencv-python and numpy. Run: pip install -r requirements-xxlwoofia-bot.txt"
        ) from exc

    if not template_path.exists():
        raise FileNotFoundError(f"Template image not found: {template_path}")

    screenshot_array = np.frombuffer(screenshot_png, dtype=np.uint8)
    screenshot = cv2.imdecode(screenshot_array, cv2.IMREAD_COLOR)
    template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if screenshot is None:
        raise RuntimeError("Could not decode ADB screenshot.")
    if template is None:
        raise RuntimeError(f"Could not read template image: {template_path}")

    match = _find_feature_match(cv2, np, screenshot, template)
    if match is None:
        match = _find_multiscale_template_match(cv2, screenshot, template)
    if match is None:
        return None

    center_x, center_y, score = match
    if score < threshold:
        return None
    return center_x, center_y, score


def _find_feature_match(cv2, np, screenshot, template) -> tuple[int, int, float] | None:
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(
        nfeatures=2500,
        scaleFactor=1.2,
        nlevels=8,
        edgeThreshold=15,
        patchSize=31,
        fastThreshold=7,
    )
    template_keypoints, template_descriptors = orb.detectAndCompute(template_gray, None)
    screenshot_keypoints, screenshot_descriptors = orb.detectAndCompute(screenshot_gray, None)

    if (
        template_descriptors is None
        or screenshot_descriptors is None
        or len(template_keypoints) < 6
        or len(screenshot_keypoints) < 6
    ):
        return None

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    raw_matches = matcher.knnMatch(template_descriptors, screenshot_descriptors, k=2)
    good_matches = []
    for pair in raw_matches:
        if len(pair) != 2:
            continue
        first, second = pair
        if first.distance < 0.75 * second.distance:
            good_matches.append(first)

    if len(good_matches) < 6:
        return None

    template_points = np.float32([template_keypoints[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    screenshot_points = np.float32([screenshot_keypoints[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    homography, mask = cv2.findHomography(template_points, screenshot_points, cv2.RANSAC, 5.0)
    if homography is None or mask is None:
        return None

    inliers = int(mask.ravel().sum())
    if inliers < 8:
        return None

    template_height, template_width = template.shape[:2]
    corners = np.float32(
        [
            [0, 0],
            [template_width - 1, 0],
            [template_width - 1, template_height - 1],
            [0, template_height - 1],
        ]
    ).reshape(-1, 1, 2)
    projected = cv2.perspectiveTransform(corners, homography).reshape(-1, 2)

    screen_height, screen_width = screenshot.shape[:2]
    if (
        projected[:, 0].min() < -template_width
        or projected[:, 1].min() < -template_height
        or projected[:, 0].max() > screen_width + template_width
        or projected[:, 1].max() > screen_height + template_height
    ):
        return None

    center = projected.mean(axis=0)
    inlier_ratio = inliers / max(len(good_matches), 1)
    inlier_count_score = min(1.0, inliers / 10)
    score = (inlier_ratio * 0.5) + (inlier_count_score * 0.5)
    return int(center[0]), int(center[1]), float(score)


def _find_multiscale_template_match(cv2, screenshot, template) -> tuple[int, int, float] | None:
    screen_height, screen_width = screenshot.shape[:2]
    template_height, template_width = template.shape[:2]
    best: tuple[int, int, float] | None = None

    for scale in (0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30, 1.40):
        width = max(8, int(template_width * scale))
        height = max(8, int(template_height * scale))
        if width >= screen_width or height >= screen_height:
            continue
        resized = cv2.resize(template, (width, height), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        result = cv2.matchTemplate(screenshot, resized, cv2.TM_CCOEFF_NORMED)
        _, max_value, _, max_location = cv2.minMaxLoc(result)
        if best is None or max_value > best[2]:
            best = (
                max_location[0] + width // 2,
                max_location[1] + height // 2,
                float(max_value),
            )

    return best


def find_text(
    screenshot_png: bytes,
    *,
    text: str | None = None,
    contains: str | None = None,
    regex: str | None = None,
    lang: str = "eng",
    confidence: int = 40,
    tesseract_cmd: str | None = None,
) -> tuple[int, int, str, int] | None:
    try:
        import cv2
        import numpy as np
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR requires opencv-python, numpy, Pillow, and pytesseract. Run: pip install -r requirements-xxlwoofia-bot.txt"
        ) from exc
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    screenshot_array = np.frombuffer(screenshot_png, dtype=np.uint8)
    screenshot = cv2.imdecode(screenshot_array, cv2.IMREAD_COLOR)
    if screenshot is None:
        raise RuntimeError("Could not decode ADB screenshot.")

    rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
    try:
        data = pytesseract.image_to_data(rgb, lang=lang, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or is not on PATH. Install Tesseract, then either add it to PATH or set daily_mission.tesseract_cmd in config.json."
        ) from exc
    pattern = re.compile(regex) if regex else None

    for index, raw in enumerate(data.get("text", [])):
        value = str(raw).strip()
        if not value:
            continue
        try:
            conf = int(float(data["conf"][index]))
        except (ValueError, TypeError):
            conf = -1
        if conf < confidence:
            continue
        if not _text_matches(value, text=text, contains=contains, pattern=pattern):
            continue

        x = int(data["left"][index]) + int(data["width"][index]) // 2
        y = int(data["top"][index]) + int(data["height"][index]) // 2
        return x, y, value, conf

    phrase_match = _find_phrase_match(data, text=text, contains=contains, pattern=pattern, confidence=confidence)
    if phrase_match is not None:
        return phrase_match

    return None


def _find_phrase_match(
    data: dict[str, object],
    *,
    text: str | None,
    contains: str | None,
    pattern: re.Pattern[str] | None,
    confidence: int,
) -> tuple[int, int, str, int] | None:
    words: list[tuple[str, int, int, int, int, int]] = []
    for index, raw in enumerate(data.get("text", [])):  # type: ignore[arg-type]
        value = str(raw).strip()
        if not value:
            continue
        try:
            conf = int(float(data["conf"][index]))  # type: ignore[index]
        except (ValueError, TypeError):
            conf = -1
        if conf < confidence:
            continue
        words.append(
            (
                value,
                int(data["left"][index]),  # type: ignore[index]
                int(data["top"][index]),  # type: ignore[index]
                int(data["width"][index]),  # type: ignore[index]
                int(data["height"][index]),  # type: ignore[index]
                conf,
            )
        )

    if not words:
        return None

    query_words = _query_words(text or contains)
    if query_words:
        phrase = _find_word_sequence(words, query_words)
        if phrase is not None:
            return phrase

    joined = " ".join(word[0] for word in words)
    normalized = re.sub(r"\s+", " ", joined).strip()
    if not _text_matches(normalized, text=text, contains=contains, pattern=pattern):
        return None

    left = min(word[1] for word in words)
    top = min(word[2] for word in words)
    right = max(word[1] + word[3] for word in words)
    bottom = max(word[2] + word[4] for word in words)
    avg_conf = sum(word[5] for word in words) // len(words)
    return (left + right) // 2, (top + bottom) // 2, normalized, avg_conf


def _query_words(value: str | None) -> list[str]:
    if value is None or " " not in value.strip():
        return []
    return [_normalize_word(word) for word in value.split() if _normalize_word(word)]


def _find_word_sequence(
    words: list[tuple[str, int, int, int, int, int]],
    query_words: list[str],
) -> tuple[int, int, str, int] | None:
    normalized_words = [_normalize_word(word[0]) for word in words]
    for start in range(0, len(normalized_words) - len(query_words) + 1):
        if normalized_words[start : start + len(query_words)] != query_words:
            continue
        matched = words[start : start + len(query_words)]
        left = min(word[1] for word in matched)
        top = min(word[2] for word in matched)
        right = max(word[1] + word[3] for word in matched)
        bottom = max(word[2] + word[4] for word in matched)
        avg_conf = sum(word[5] for word in matched) // len(matched)
        value = " ".join(word[0] for word in matched)
        return (left + right) // 2, (top + bottom) // 2, value, avg_conf
    return None


def _normalize_word(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def _text_matches(
    value: str,
    *,
    text: str | None,
    contains: str | None,
    pattern: re.Pattern[str] | None,
) -> bool:
    if text is not None and value != text:
        return False
    if contains is not None and contains.lower() not in value.lower():
        return False
    if pattern is not None and not pattern.search(value):
        return False
    return text is not None or contains is not None or pattern is not None
