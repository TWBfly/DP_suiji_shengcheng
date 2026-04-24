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
            print("检测到人工指定设定，启动覆盖模式。")
            target = self.config.get("gender_target") or self.config.get("main_category") or "未指定"
            genre = self.config.get("genre") or self.config.get("plot") or "未指定"
            bg_settings = self.config.get("background_settings", [])
            
            # 智能补全卡片机制（保证最少 10 个标签：target + genre + 8个背景）
            if len(bg_settings) < 8:
                print(f"人工指定的背景标签不足8个（当前{len(bg_settings)}个），正尝试随机补全...")
                
                db = None
                dimensions = []
                is_standard_pool = False
                
                # 寻找匹配的池子
                if target in SETTINGS_DB and "background_dimensions" in SETTINGS_DB[target]:
                    db = SETTINGS_DB[target]
                    dimensions = list(db["background_dimensions"].keys())
                    is_standard_pool = True
                else:
                     # 默认使用通用随机池进行补全
                     print(f"使用【通用随机池】补全背景卡片。")
                     db = SETTINGS_DB["通用随机池"]
                     dimensions = [k for k in db.keys() if k not in ["主分类", "情节"]]
                     is_standard_pool = False

                if db and dimensions:
                    random.shuffle(dimensions)
                    needed = 8 - len(bg_settings)
                    added = 0
                    for dim in dimensions:
                        if not any(dim in s for s in bg_settings):
                            if is_standard_pool:
                                val = random.choice(db["background_dimensions"][dim])
                            else:
                                val = random.choice(db[dim])
                            bg_settings.append(f"{dim}: {val}")
                            added += 1
                            if added >= needed:
                                break
            return target, genre, bg_settings

        print("未检测到人工指定设定，启动随机组合模式。")
        pool_key = random.choice(["男频", "女频", "通用随机池"])
        db = SETTINGS_DB[pool_key]

        if pool_key in ["男频", "女频"]:
            target = pool_key
            genre = random.choice(db["genres"])
            bg_settings = []
            dimensions = list(db["background_dimensions"].keys())
            
            selected_dims = []
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
            # 通用池逻辑
            categories = db["主分类"]
            # 强化逻辑：如果明确要求女频，则过滤掉男频分类
            if self.config.get("gender_target") == "女频":
                forbidden = ["男生生活", "男生情感", "男频衍生", "男频脑洞"]
                categories = [c for c in categories if c not in forbidden]
                print(f"检测到女频偏好，已过滤男频分类：{forbidden}")
            
            target = random.choice(categories)
            genre = random.choice(db["情节"])
            
            # 从通用池中随机抽取 8 个维度来凑够设定
            available_dims = [k for k in db.keys() if k not in ["主分类", "情节"]]
            random.shuffle(available_dims)
            # 尽可能取到 8 个，不足则全部取用
            selected_dims = available_dims[:8]
            
            bg_settings = []
            for dim in selected_dims:
                bg_settings.append(f"{dim}: {random.choice(db[dim])}")
            
        return target, genre, bg_settings

    def build_prompt(self):
        target, genre, bg_settings = self.generate_settings()
        settings_str = "\n".join([f"- {s}" for s in bg_settings])
        
        # 动态展开 1 到 9 章的骨架，并在每章加入三幕结构与更严密的逻辑约束状态流转
        chapters_cn = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        middle_chapters = ""
        for cn_num in chapters_cn:
            middle_chapters += f"### 第{cn_num}章：[章节名]\n- **因果承接**：[说明本章起因是如何由上一章结尾/前文事件直接推导而来的]\n- **出场人物**：\n- **核心目标**：\n- **主场景**：\n- **核心剧情（三幕式）**：\n  - 第一幕（起）：\n  - 第二幕（承/转）：\n  - 第三幕（合）：\n- **反派/暗线动态**：[反派/关键配角在本章的应对动作或阴谋推进]\n- **道具/伏笔状态**：[明确标注：新增埋伏 / 推进发酵 / 闭环回收。例如：新增-染血纽扣]\n- **主角心境/成长**：\n- **结尾钩子（Hook）**：[本章末尾制造的突发危机或悬念转折，引出下文]\n\n"
        
        prompt = f"""# 核心生成指令（多 Agent 协作工作流）

你现在不是一个普通的 AI，而是**一个由三位顶级专家组成的故事创作委员会**。你们将在内存中进行探讨协作，共同为一部短篇小说打造极致严密、充满张力的大纲。

**【委员会成员】**
1. **主编（Chief Editor）**：掌控整体节奏、题材底色（{target}）、商业卖点和悬念反转。
2. **逻辑审查员（Logic Auditor）**：确保因果连续性（上一章的果是下一章的因），严格追踪“道具流转”与“伏笔闭环”，一旦有不合理或未回收的线索立即驳回。
3. **人物设计专家（Character Expert）**：确保角色动机绝对自洽，建立“状态账本”。**绝对禁止降智反派与俗套桥段**，所有配角必须智商在线，主角必须有明显的心境变化弧光。

## 1. 故事核心设定卡 (必须严格遵守)
- **目标/分类**: {target}
- **核心题材/情节**: {genre}
- **精细化背景组合**:
{settings_str}

## 2. 创作纪律与逻辑铁律
1. **场景具体化**：严禁模糊描述。大纲中的场景必须具体且符合世界观（如：翰林院东庑、落梅池边的石凳、废弃的赛博工厂）。
2. **三幕式行动段落**：每章剧情必须拆解为起、承/转、合。必须写出具体的动作交锋，**严禁使用模板化词汇**（如“寻找借力点”、“展开交锋”）。
3. **道具与伏笔的因果闭环**：全书必须有贯穿的道具或关键线索流转（如：落在现场的手帕、一段被篡改的监控）。道具的出现和消失必须有因果，前面埋的雷后面必须爆。
4. **终章绝对收束**：第十章是结局，**严禁在结局新增续章钩子或新伏笔**。第十章必须：引爆终极冲突、揭示核心真相并清算主要反派、完成首尾呼应与主角命运定格。

## 3. 输出流程与格式要求

请按照以下两个阶段输出你们的协作成果：

### 阶段一：委员会专家探讨（思维链演绎）
*请以对话或纪要的形式，简短展现三位专家如何基于设定卡，构建出包含“核心道具流转链”、“主角反转弧光”和“反派智商在线的终极阴谋”的闭环因果结构。*

### 阶段二：正式大纲输出
*在探讨结束后，由主编进行汇总，必须先输出【核心资产清单】，然后再严格按以下 Markdown 格式输出全文章节：*

### 核心资产清单（全局约束，确保逻辑不崩盘）
- **核心人物表**：[主角及核心诉求]、[反派及核心底牌]
- **贯穿全书的核心道具/线索**：[写明核心悬念及最终真相]
- **全局核心冲突轴**：[一句话概括全书最大的悬念与因果]

### 楔子（第0章）：[一句话核心梗概]
- **出场人物**：
- **核心目标**：
- **主场景**：
- **核心剧情（三幕式）**：
  - 第一幕（起）：
  - 第二幕（承/转）：
  - 第三幕（合）：
- **开幕雷击点（强留人/强反转/强悬念）说明**：
- **道具与伏笔流转**：[抛出全书最核心的悬念/初始道具]
- **主角心境/状态变化**：

{middle_chapters}### 第十章（大结局）：[章节名]
- **出场人物**：
- **核心目标**：
- **主场景**：
- **结局高潮（三幕式）**：
  - 第一幕（起）：终极冲突全面爆发
  - 第二幕（承/转）：真相揭示与反派清算
  - 第三幕（合）：尘埃落定与首尾呼应
- **全书道具与伏笔终极收束**：[明确说明前文埋下的哪些雷在这里被引爆/回收]
- **人物最终结局**：

请专家委员会开始推演与创作：
"""
        return prompt

if __name__ == "__main__":
    pb = PromptBuilder()
    print(pb.build_prompt())
