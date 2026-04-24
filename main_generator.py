# main_generator.py
import os
import random
from datetime import datetime
from prompt_generator import PromptBuilder
from setting_config import SETTINGS_DB

def main():
    print("=== 开始定制化随机大纲设定生成 ===")
    
    # 1. 强制设定核心背景
    gender = "女频"
    genre = "大女主/爽文 (复仇虐渣、恶毒女配翻身、独立觉醒、清醒打脸)"
    fixed_bg = ["时代: 架空古代", "属性: 爽文"]
    
    # 2. 随机抽取至少 8 个其他维度
    db = SETTINGS_DB[gender]
    dimensions = list(db["background_dimensions"].keys())
    
    # 排除掉已经固定的“时代”维度
    if "时代" in dimensions:
        dimensions.remove("时代")
        
    random.shuffle(dimensions)
    selected_dims = dimensions[:8] # 随机抽取 8 个维度
    
    bg_settings = fixed_bg.copy()
    for dim in selected_dims:
        val = random.choice(db["background_dimensions"][dim])
        bg_settings.append(f"{dim}: {val}")
    
    # 3. 使用 PromptBuilder 构建提示词
    pb = PromptBuilder()
    # 强制覆盖配置
    pb.config = {
        "use_override": True,
        "gender_target": gender,
        "genre": genre,
        "background_settings": bg_settings
    }
    
    prompt = pb.build_prompt()
    
    # 4. 生成符合 [月-日-时-分].md 格式的文件名
    timestamp = datetime.now().strftime("%m-%d-%H-%M")
    filename = f"{timestamp}.md"
    output_file = os.path.join(os.path.dirname(__file__), "work", filename)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(prompt)
        
    print(f"=== 生成完毕 ===")
    print(f"固定设定: 架空古代, 女频, 爽文")
    print(f"随机维度: {', '.join(selected_dims)}")
    print(f"输出文件: {output_file}")

if __name__ == "__main__":
    main()
