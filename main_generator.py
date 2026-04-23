# main_generator.py
import os
from prompt_generator import PromptBuilder

def main():
    print("=== 开始小说大纲设定生成 ===")
    pb = PromptBuilder("user_settings.json")
    prompt = pb.build_prompt()
    
    output_file = "generated_task.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(prompt)
        
    print(f"=== 生成完毕，已输出设定至 {output_file} ===")
    print("您可以直接查看生成的提示词，并调用大模型进行下一步的大纲创作。")

if __name__ == "__main__":
    main()
