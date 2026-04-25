import argparse
import json
import os
from datetime import datetime
from prompt_generator import PromptBuilder


DEFAULT_CONFIG = {
    "use_override": True,
    "gender_target": "女频",
    "genre": "大女主/爽文 (复仇虐渣、恶毒女配翻身、独立觉醒、清醒打脸)",
    "background_settings": ["时代: 架空古代", "属性: 爽文"],
}


def write_text(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="生成同一批次的大纲、审查、优化提示词与固定背景卡。")
    parser.add_argument("--config", default=None, help="用户设定 JSON；默认读取项目内 user_settings.json")
    parser.add_argument("--seed", type=int, default=None, help="随机种子；用于复现背景设定")
    parser.add_argument("--output-root", default=os.path.join(os.path.dirname(__file__), "work"))
    parser.add_argument("--legacy-file", action="store_true", help="同时输出旧版单文件大纲 prompt")
    args = parser.parse_args()

    print("=== 开始定制化随机大纲设定生成 ===")

    if args.config:
        pb = PromptBuilder(config_file=args.config, seed=args.seed)
    else:
        pb = PromptBuilder(seed=args.seed, config=DEFAULT_CONFIG)

    target, actual_genre, bg_settings = pb.generate_settings()
    settings = pb.settings_to_dict(target, actual_genre, bg_settings)
    outline_prompt = pb.build_prompt(settings)
    audit_prompt = pb.build_audit_prompt_from_settings(settings)
    optimize_prompt = pb.build_optimize_prompt_from_settings(settings)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    batch_dir = os.path.join(args.output_root, timestamp)

    write_json(os.path.join(batch_dir, "settings.json"), settings)
    write_text(os.path.join(batch_dir, "00_大纲生成_prompt.md"), outline_prompt)
    write_text(os.path.join(batch_dir, "02_审核_prompt.md"), audit_prompt)
    write_text(os.path.join(batch_dir, "03_优化_prompt.md"), optimize_prompt)

    if args.legacy_file:
        write_text(os.path.join(args.output_root, f"{timestamp}.md"), outline_prompt)
        
    print(f"=== 生成完毕 ===")
    print(f"固定设定: {target}, {actual_genre}")
    print(f"推导设定: {', '.join(bg_settings)}")
    print(f"输出目录: {batch_dir}")
    print("下一步：把 00_大纲生成_prompt.md 交给模型生成 01_原始大纲.md，再用 02/03 prompt 完成审核和优化。")


if __name__ == "__main__":
    main()
