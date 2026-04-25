import glob
import os
from prompt_slicer import DEFAULT_TEMPLATE_DIR, slice_and_generate_prompts


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, "work")


def find_latest_outline_dir():
    patterns = [
        os.path.join(WORK_DIR, "*"),
        os.path.join(WORK_DIR, "【*】"),
    ]
    candidates = []
    for pattern in patterns:
        for path in glob.glob(pattern):
            if not os.path.isdir(path):
                continue
            outline = os.path.join(path, "2_优化大纲.md")
            if not os.path.exists(outline):
                outline = os.path.join(path, "03_优化大纲.md")
            if os.path.exists(outline):
                candidates.append((os.path.getmtime(outline), path, outline))
    if not candidates:
        raise FileNotFoundError("未找到包含 2_优化大纲.md 或 03_优化大纲.md 的批次目录。")
    candidates.sort(reverse=True)
    return candidates[0][1], candidates[0][2]


def main():
    batch_dir, outline_file = find_latest_outline_dir()
    output_dir = os.path.join(batch_dir, "prompt")
    settings_file = os.path.join(batch_dir, "settings.json")
    if not os.path.exists(settings_file):
        settings_file = None
    slice_and_generate_prompts(
        outline_file,
        output_dir,
        template_dir=DEFAULT_TEMPLATE_DIR,
        settings_file=settings_file,
        strict=True,
    )


if __name__ == "__main__":
    main()
