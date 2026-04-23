# prompt_generator.py
import json
import random
from setting_config import SETTINGS_DB

class PromptBuilder:
    def __init__(self, config_file="user_settings.json"):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"配置文件读取失败: {e}，将使用全随机模式。")
            self.config = {"use_override": False}

    def generate_settings(self):
        if self.config.get("use_override", False):
            print("检测到人工指定设定，最高优先级覆盖生效。")
            # 兼容新旧配置字段
            target = self.config.get("gender_target") or self.config.get("main_category") or "未指定"
            genre = self.config.get("genre") or self.config.get("plot") or "未指定"
            bg_settings = self.config.get("background_settings", [])
            # 如果是旧字段形式，直接返回
            return target, genre, bg_settings

        print("未检测到人工指定设定，启动随机组合模式。")
        # 随机选择一个池子
        pool_key = random.choice(["男频", "女频", "通用随机池"])
        db = SETTINGS_DB[pool_key]

        if pool_key in ["男频", "女频"]:
            target = pool_key
            genre = random.choice(db["genres"])
            bg_settings = []
            dimensions = list(db["background_dimensions"].keys())
            
            selected_dims = []
            # 强制包含核心叙事维度
            essentials = ["角色原型", "冲突引擎", "平台入口", "结局倾向"]
            for essential in essentials:
                if essential in dimensions:
                    selected_dims.append(essential)
                    dimensions.remove(essential)
            
            random.shuffle(dimensions)
            remaining_count = 8 - len(selected_dims)
            selected_dims.extend(dimensions[:remaining_count])
            
            for dim in selected_dims:
                val = random.choice(db["background_dimensions"][dim])
                bg_settings.append(f"{dim}: {val}")
        else:
            # 通用随机池逻辑
            target = random.choice(db["主分类"])
            genre = random.choice(db["情节"])
            bg_settings = [
                f"核心角色: {random.choice(db['角色'])}",
                f"情感基调: {random.choice(db['情绪'])}",
                f"故事背景: {random.choice(db['背景'])}"
            ]
            
        return target, genre, bg_settings

    def build_prompt(self):
        target, genre, bg_settings = self.generate_settings()
        
        settings_str = "\n".join([f"- {s}" for s in bg_settings])
        
        prompt = f"""# 核心生成指令

你是一个顶级的中文短篇小说架构师与金牌编辑。请根据以下提取的题材与背景设定，生成一份逻辑严密、人物极具张力的短篇小说大纲。

## 1. 核心设定 (必须严格遵守)
- **目标/分类**: {target}
- **核心题材/情节**: {genre}
- **精细化背景组合**:
{settings_str}

## 2. 创作要求
1. **人物塑造优先**：核心角色的性格必须极致，动机明确（复仇、自救、搞钱、夺权等），必须呈现明显的人物成长或转变弧光。严禁降智反派。
2. **逻辑严密与伏笔**：剧情必须讲究逻辑。在楔子和前三章必须埋下深层伏笔（信息差、未解谜团、隐蔽的利益纠葛），并在最后两章进行完美回收。
3. **结构规范**：
   - 必须包含：【楔子】 + 【第一章 到 第十章】。
   - **楔子（开幕雷击）**：楔子必须具备“开幕雷击”的效果，通过**强留人、强反转或强悬念**的手段，在极短篇幅内抛出全书最大的矛盾或最极致的冲突画面，迫使读者无法移开视线。
   - 第一章到第九章：剧情需层层递进，节奏紧凑（打脸、反转、身份揭晓、关系拉扯等高潮迭起）。
   - 第十章（大结局）：必须是剧情的总爆发与收尾。严禁烂尾，**必须做到首尾呼应**（呼应楔子中的核心悬念或意象），完成主题升华。

## 3. 输出格式要求
请严格按以下 Markdown 格式输出：
### 楔子：[一句话核心梗概]
- **出场人物**：
- **核心冲突/悬念**：
- **剧情概要**：
- **开幕雷击点（强留人/强反转/强悬念）说明**：

### 第一章：[章节名]
- **出场人物**：
- **核心剧情**：
- **伏笔埋设/回收**：
- **情绪/爽点锚点**：
...
(依此类推至第十章)

### 第十章（大结局）：[章节名]
- **出场人物**：
- **结局高潮**：
- **全书伏笔终极回收与首尾呼应**：
- **人物最终结局**：

请开始你的创作：
"""
        return prompt

if __name__ == "__main__":
    pb = PromptBuilder()
    print(pb.build_prompt())
