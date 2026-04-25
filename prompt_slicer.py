import argparse
import json
import os
import re
from prompt_generator import PromptBuilder


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE_DIR = "/Users/tang/PycharmProjects/pythonProject/.agent/skills/novel_evolution_engine/scripts/dp_promet"
CHAPTER_ORDER = ["楔子", "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章", "第九章", "第十章"]


def read_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def write_text(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_outline(filepath):
    content = read_text(filepath)
    pattern = re.compile(r"^(#{2,4})\s+(楔子|第[一二三四五六七八九十百零0-9]+章|结局)(.*)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    chapters = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()

        ch_type = match.group(2).strip()
        if ch_type == "结局":
            ch_type = "第十章"
        ch_suffix = re.sub(r"^[：:\s（）()第0-9一二三四五六七八九十零百章大结局]+", "", match.group(3).strip())
        full_title = f"{ch_type}：{ch_suffix}" if ch_suffix else ch_type

        def extract_field(field_names):
            for name in field_names:
                m = re.search(fr"^\s*[-*]?\s*\*{{0,2}}{name}\*{{0,2}}[:：]\s*(.+)$", body, re.MULTILINE)
                if m:
                    return m.group(1).strip()
            return ""

        def extract_act(act_name):
            m = re.search(fr"^\s*[-*]?\s*\*{{0,2}}{act_name}.*?\*{{0,2}}[:：]\s*(.+)$", body, re.MULTILINE)
            return m.group(1).strip() if m else ""

        chapters.append({
            "type": ch_type,
            "title": full_title,
            "clean_title": ch_suffix,
            "scene": extract_field(["主场景", "场景"]),
            "chars": extract_field(["出场人物", "人物"]),
            "core": extract_field(["核心目标", "核心剧情"]),
            "act1": extract_act("第一幕"),
            "act2": extract_act("第二幕"),
            "act3": extract_act("第三幕"),
            "darkline": extract_field(["反派/暗线动态", "暗线动态"]),
            "foreshadow": extract_field(["道具/伏笔状态", "道具与伏笔流转", "全书道具与伏笔终极收束"]),
            "growth": extract_field(["主角心境/成长", "主角心境/状态变化", "人物最终结局"]),
            "hook": extract_field(["结尾钩子（Hook）", "结尾钩子", "开幕雷击点（强留人/强反转/强悬念）说明"]),
        })
    return chapters


def validate_outline(chapters):
    errors = []
    warnings = []
    seen = [ch["type"] for ch in chapters]

    if len(chapters) != 11:
        errors.append(f"章节数量应为 11（楔子+第一章到第十章），实际为 {len(chapters)}。")

    for expected in CHAPTER_ORDER:
        if expected not in seen:
            errors.append(f"缺少章节：{expected}。")

    required = {
        "scene": "主场景/场景",
        "chars": "出场人物/人物",
        "core": "核心目标/核心剧情",
        "act1": "第一幕",
        "act2": "第二幕",
        "act3": "第三幕",
    }
    for ch in chapters:
        for key, label in required.items():
            if ch["type"] == "第十章" and key == "core":
                continue
            if not ch.get(key):
                errors.append(f"{ch['type']} 缺少字段：{label}。")
        if ch["type"] != "第十章" and not ch.get("hook"):
            warnings.append(f"{ch['type']} 没有明确结尾钩子或承接点。")
        if ch["type"] != "楔子" and not ch.get("foreshadow"):
            warnings.append(f"{ch['type']} 没有明确道具/伏笔状态。")

    tenth = next((ch for ch in chapters if ch["type"] == "第十章"), None)
    if tenth:
        tenth_text = " ".join(str(v) for v in tenth.values())
        if any(word in tenth_text for word in ["新伏笔", "新的伏笔", "续章", "下一部", "未完待续"]):
            errors.append("第十章疑似新增续章钩子或新伏笔。")
        if not any(word in tenth_text for word in ["收束", "回收", "真相", "清算", "首尾呼应", "结局"]):
            warnings.append("第十章缺少明确的真相揭示、伏笔回收或首尾呼应表达。")

    return {
        "ok": not errors,
        "chapter_count": len(chapters),
        "errors": errors,
        "warnings": warnings,
    }


REQUIRED_SETTINGS_KEYS = {"target", "genre", "background_settings"}


def load_settings(settings_file=None, outline_file=None, output_dir=None):
    candidates = []
    if settings_file:
        candidates.append(settings_file)
    if output_dir:
        abs_output_dir = os.path.abspath(output_dir)
        candidates.append(os.path.join(abs_output_dir, "settings.json"))
        candidates.append(os.path.join(os.path.dirname(abs_output_dir), "settings.json"))
    if outline_file:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(outline_file)), "settings.json"))
    candidates.append(os.path.join(BASE_DIR, "settings.json"))

    seen_paths = set()
    for path in candidates:
        if not path:
            continue
        path = os.path.abspath(path)
        if path in seen_paths:
            continue
        seen_paths.add(path)
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if REQUIRED_SETTINGS_KEYS <= set(data):
            return data
        raise ValueError(f"设定文件格式不完整：{path}")

    print("Warning: 未找到 settings.json，使用全随机设定兜底；建议传入 --settings 或将 settings.json 放在输出/大纲目录。")
    pb = PromptBuilder(config={"use_override": False})
    target, genre, bg_settings = pb.generate_settings()
    return pb.settings_to_dict(target, genre, bg_settings)


def format_bg_card(settings):
    settings_str = "\n".join([f"  - {s}" for s in settings["background_settings"]])
    return f"【核心故事设定卡】\n- 主分类: {settings['target']}\n- 核心题材: {settings['genre']}\n- 设定细节:\n{settings_str}\n"


def load_templates(template_dir):
    return {
        "prologue": read_text(os.path.join(template_dir, "00_楔子提示词模板.md")),
        "first": read_text(os.path.join(template_dir, "01_第一章提示词模板.md")),
        "middle": read_text(os.path.join(template_dir, "02_第二章-第九章提示词模板.md")),
        "end": read_text(os.path.join(template_dir, "03_结局提示词模板.md")),
    }


def fill_template(template, prefix, chapter, bg_card=""):
    if not chapter:
        return template
    text = template
    clean_title = chapter.get("clean_title") or chapter["title"]
    full_title = chapter["title"]

    if prefix in ["本章", "你的楔子", "你的第一章", "你的结局"]:
        replacements = {
            "{这里填场景}": chapter["scene"],
            "{这里填人物}": chapter["chars"],
            "{这里填核心剧情}": chapter["core"],
            "{这里填第一幕}": chapter["act1"],
            "{这里填第二幕}": chapter["act2"],
            "{这里填第三幕}": chapter["act3"],
            "{这里填你的第一章标题}": clean_title,
            "{这里填你的楔子标题}": clean_title,
            "{这里填你的结局标题}": clean_title,
            "{这里填本章标题}": full_title,
        }
        for key, value in replacements.items():
            text = text.replace(key, value)
        if bg_card:
            text = bg_card + "\n" + text

    title_value = full_title if prefix in ["本章", "上一章", "下一章"] else clean_title
    prefixed = {
        f"{{这里填{prefix}标题}}": title_value,
        f"{{这里填{prefix}场景}}": chapter["scene"],
        f"{{这里填{prefix}人物}}": chapter["chars"],
        f"{{这里填{prefix}核心剧情}}": chapter["core"],
        f"{{这里填{prefix}第一幕}}": chapter["act1"],
        f"{{这里填{prefix}第二幕}}": chapter["act2"],
        f"{{这里填{prefix}第三幕}}": chapter["act3"],
    }
    for key, value in prefixed.items():
        text = text.replace(key, value)

    return text


def safe_filename(name):
    name = name.replace("：", "_").replace(":", "_").replace(" ", "_")
    return re.sub(r"[\\/（）()]+", "", name)


def slice_and_generate_prompts(outline_file, output_dir, template_dir=DEFAULT_TEMPLATE_DIR, settings_file=None, strict=True):
    settings = load_settings(settings_file=settings_file, outline_file=outline_file, output_dir=output_dir)
    bg_card = format_bg_card(settings)
    templates = load_templates(template_dir)
    chapters = parse_outline(outline_file)
    validation = validate_outline(chapters)
    write_json(os.path.join(os.path.dirname(os.path.abspath(outline_file)), "04_validation.json"), validation)

    if strict and not validation["ok"]:
        raise ValueError("大纲结构校验失败：\n" + "\n".join(validation["errors"]))

    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(output_dir):
        if filename.endswith(".md"):
            os.remove(os.path.join(output_dir, filename))

    for i, ch in enumerate(chapters):
        if ch["type"] == "楔子":
            text = fill_template(templates["prologue"], "你的楔子", ch, bg_card)
            if i + 1 < len(chapters):
                text = fill_template(text, "第一章", chapters[i + 1])
            filename = "00_楔子_prompt.md"
        elif ch["type"] == "第一章":
            text = fill_template(templates["first"], "你的第一章", ch, bg_card)
            if i + 1 < len(chapters):
                text = fill_template(text, "第二章", chapters[i + 1])
            filename = "01_第一章_prompt.md"
        elif ch["type"] == "第十章":
            text = fill_template(templates["end"], "本章", ch, bg_card)
            if i - 1 >= 0:
                text = fill_template(text, "上一章", chapters[i - 1])
            filename = f"{i:02d}_{safe_filename(ch['title'])}_prompt.md"
        else:
            text = fill_template(templates["middle"], "本章", ch, bg_card)
            if i - 1 >= 0:
                text = fill_template(text, "上一章", chapters[i - 1])
            if i + 1 < len(chapters):
                text = fill_template(text, "下一章", chapters[i + 1])
            filename = f"{i:02d}_{safe_filename(ch['title'])}_prompt.md"

        write_text(os.path.join(output_dir, filename), text)
        print(f"Generated {filename}")

    print(f"Parsed {len(chapters)} chapters from outline.")
    print(f"Validation: {'ok' if validation['ok'] else 'failed'}")
    if validation["errors"]:
        print("Errors:")
        for error in validation["errors"]:
            print(f"- {error}")
    if validation["warnings"]:
        print("Warnings:")
        for warning in validation["warnings"]:
            print(f"- {warning}")
    return validation


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outline", type=str, required=True, help="优化后的完整大纲文件")
    parser.add_argument("--output", type=str, required=True, help="输出 prompt 文件夹路径")
    parser.add_argument("--settings", type=str, default=None, help="同批次 settings.json；默认使用大纲同目录 settings.json")
    parser.add_argument("--template-dir", type=str, default=DEFAULT_TEMPLATE_DIR)
    parser.add_argument("--no-strict", action="store_true", help="校验失败也继续生成 prompt")
    args = parser.parse_args()

    slice_and_generate_prompts(
        args.outline,
        args.output,
        template_dir=args.template_dir,
        settings_file=args.settings,
        strict=not args.no_strict,
    )
