import json
import os
import random
from setting_config import SETTINGS_DB

class PromptBuilder:
    def __init__(self, config_file=None, seed=None, config=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = config_file or os.path.join(base_dir, "user_settings.json")
        self.rng = random.Random(seed)
        self.config = config
        self.load_config()

    def load_config(self):
        if self.config is not None:
            return
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"配置文件读取失败: {e}，将使用全随机模式。")
            self.config = {"use_override": False}

    def _raw_generate_settings(self):
        """
        【方案 C - 层级链式递进抽取】
        结合用户干预（优先级最高）以及上下文推导能力。
        波次一：定性（大类与题材）
        波次二：筑基（时代与地域）
        波次三：人设（职业、阶层、金手指、冲突等）
        """
        # 1. 提取用户已指定的设定，这具有绝对最高优先级
        user_bg = self.config.get("background_settings", [])
        user_dict = {}
        for item in user_bg:
            if ":" in item:
                k, v = item.split(":", 1)
                user_dict[k.strip()] = v.strip()
            elif "属性" in item: # 兼容 "属性: 爽文" 等
                user_dict["属性"] = item.replace("属性:", "").strip()

        # 读取大分类目标与题材
        target = self.config.get("gender_target") or self.config.get("main_category")
        genre = self.config.get("genre") or self.config.get("plot")

        # 波次一：确定性别分类和主题材
        if not target:
            target = self.rng.choice(["男频", "女频"])
        
        # 匹配池子
        if target in SETTINGS_DB and "genres" in SETTINGS_DB[target]:
            db = SETTINGS_DB[target]
            if not genre:
                genre = self.rng.choice(db["genres"])
        else:
            db = SETTINGS_DB["通用随机池"]
            if not genre:
                genre = self.rng.choice(db.get("情节", ["都市日常"]))

        # 最终输出的背景配置列表
        bg_settings = []
        
        # 用于冲突检测的当前状态池
        current_state_str = f"{target} {genre} " + " ".join(user_dict.values())

        # 标签匹配定义
        is_ancient = any(kw in current_state_str for kw in ["古代", "古言", "宅斗", "王朝", "宫闱", "民国", "旧影", "下乡"])
        is_modern = any(kw in current_state_str for kw in ["都市", "现代", "职场", "科技", "赛博", "未来"])
        is_sweet_爽 = any(kw in current_state_str for kw in ["甜宠", "爽文", "逆袭", "打脸", "无敌", "咸鱼", "爆笑"])
        is_sad_虐 = any(kw in current_state_str for kw in ["虐恋", "悲剧", "凄美", "痛点", "遗憾"])
        is_big_heroine_revenge = "大女主/爽文" in current_state_str

        # 收集该池子中的所有背景维度
        if "background_dimensions" in db:
            dimensions = list(db["background_dimensions"].keys())
        else:
            dimensions = [k for k in db.keys() if k not in ["主分类", "情节"]]

        # 确保几个核心要素（按波次顺序遍历）
        essentials = ["时代", "地域", "社会阶层", "职业", "角色原型", "能力机制", "金手指", "金手指/规则", "冲突引擎", "情绪引擎", "平台入口", "结局倾向"]
        ordered_dims = [d for d in essentials if d in dimensions]
        # 补充未包含在 essentials 中的其他维度
        for d in dimensions:
            if d not in ordered_dims:
                ordered_dims.append(d)

        # 链式推导与抽取
        for dim in ordered_dims:
            # 规则 1：人指定的背景设定优先级永远最高
            if dim in user_dict:
                bg_settings.append(f"{dim}: {user_dict[dim]}")
                continue
            
            # 规则 1.5：金手指/能力机制可以没有
            if dim in ["金手指/规则", "金手指", "能力机制"]:
                if self.rng.random() < 0.5:
                    bg_settings.append(f"{dim}: 无")
                    continue
            
            # 获取当前维度的备选池
            if "background_dimensions" in db:
                pool = db["background_dimensions"][dim]
            else:
                pool = db[dim]

            # 规则 2：方案 C 关联过滤逻辑
            filtered_pool = []
            for val in pool:
                modern_terms = [
                    "硬核科技", "赛博", "总裁", "白领", "科学家", "科研", "一线都市",
                    "职场", "公司", "娱乐圈", "主播", "演员", "法医", "刑警", "程序员", "豪门家族/别墅"
                ]
                ancient_terms = ["王妃", "女官", "嫡庶", "宗门", "朝堂", "出马仙", "书生", "侯府", "宫廷"]
                # 现代职业/背景不要混入古代
                if is_ancient and any(kw in val for kw in modern_terms):
                    # 允许部分特例，如系统、今穿古外挂
                    if "穿" not in val and "系统" not in val:
                        continue
                
                # 古代背景不要混入纯现代
                if is_modern and any(kw in val for kw in ancient_terms):
                    if "穿" not in val and "系统" not in val:
                        continue
                
                # 结局倾向与情感隔离
                if is_sweet_爽 and ("悲剧" in val or "BE" in val or "遗憾" in val):
                    continue
                if is_sad_虐 and ("无敌" in val or "沙雕" in val or "爆笑" in val):
                    continue
                if is_big_heroine_revenge and ("爆笑沙雕" in val or "咸鱼解压" in val):
                    continue

                filtered_pool.append(val)

            # 如果过滤后池子为空，回退到完整池
            if not filtered_pool:
                filtered_pool = pool

            # 抽取并加入背景设定
            chosen_val = self.rng.choice(filtered_pool)
            bg_settings.append(f"{dim}: {chosen_val}")

        # 兜底逻辑：如果人工设置里面有“属性”或者独立维度的“时代”被截断的写法，一并合入
        for k, v in user_dict.items():
            if not any(k in s for s in bg_settings):
                bg_settings.append(f"{k}: {v}")

        # 过滤掉可能重复的键（以防兜底导致冲突）
        seen_keys = set()
        unique_bg = []
        for item in bg_settings:
            if ":" in item:
                k = item.split(":")[0].strip()
                if k not in seen_keys:
                    seen_keys.add(k)
                    unique_bg.append(item)
            else:
                unique_bg.append(item)

        # 如果总数不足8个（可能用户设置维度很少且池子也小），自动把不够的部分填满（用通用池补充）
        if len(unique_bg) < 8 and target != "通用随机池":
            common_db = SETTINGS_DB.get("通用随机池", {})
            for k, v in common_db.items():
                if k not in ["主分类", "情节"] and k not in seen_keys:
                    unique_bg.append(f"{k}: {self.rng.choice(v)}")
                    seen_keys.add(k)
                    if len(unique_bg) >= 8:
                        break

        return target, genre, unique_bg

    def generate_settings(self):
        """
        核心去重封装：读取历史设定并拦截完全一致的组合（题材+时代+金手指）
        """
        history_fingerprints = set()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        work_dir = os.path.join(base_dir, "work")
        
        if os.path.exists(work_dir):
            for root, dirs, files in os.walk(work_dir):
                for file in files:
                    if file == "settings.json":
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                h_data = json.load(f)
                                h_tgt = h_data.get("target", "")
                                h_gnr = h_data.get("genre", "")
                                h_bg = h_data.get("background_settings", [])
                                
                                h_era = "未知时代"
                                h_cheat = "无"
                                for item in h_bg:
                                    if ":" in item:
                                        k, v = item.split(":", 1)
                                        k = k.strip()
                                        v = v.strip()
                                        if k == "时代":
                                            h_era = v
                                        elif k in ["金手指/规则", "金手指", "能力机制"]:
                                            h_cheat = v
                                history_fingerprints.add((h_tgt, h_gnr, h_era, h_cheat))
                        except:
                            pass

        max_retries = 50
        for attempt in range(max_retries):
            target, genre, unique_bg = self._raw_generate_settings()
            
            curr_era = "未知时代"
            curr_cheat = "无"
            for item in unique_bg:
                if ":" in item:
                    k, v = item.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    if k == "时代":
                        curr_era = v
                    elif k in ["金手指/规则", "金手指", "能力机制"]:
                        curr_cheat = v
            
            curr_fp = (target, genre, curr_era, curr_cheat)
            
            if curr_fp not in history_fingerprints:
                return target, genre, unique_bg
            
            print(f"检测到核心设定与历史完全一致 {curr_fp}，正在触发 Reroll 拦截机制（尝试 {attempt+1}/{max_retries}）...")
            
        print(f"Warning: 达到最大重试次数 {max_retries}，未能生成完全不重复的设定。")
        return target, genre, unique_bg

    def settings_to_dict(self, target, genre, bg_settings):
        return {
            "target": target,
            "genre": genre,
            "background_settings": bg_settings,
        }

    def format_settings_card(self, settings):
        settings_str = "\n".join([f"- {s}" for s in settings["background_settings"]])
        return (
            f"- **目标/分类**: {settings['target']}\n"
            f"- **核心题材/情节**: {settings['genre']}\n"
            f"- **精细化背景组合**:\n{settings_str}"
        )

    def build_prompt(self, settings=None):
        if settings is None:
            target, genre, bg_settings = self.generate_settings()
            settings = self.settings_to_dict(target, genre, bg_settings)
        target = settings["target"]
        genre = settings["genre"]
        bg_settings = settings["background_settings"]
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

### 阶段一：委员会审稿纪要
*请以简短纪要形式输出三位专家的关键决策，只写结论、取舍与约束；不要展开完整思考过程。纪要必须明确“核心道具流转链”、“主角反转弧光”和“反派智商在线的终极阴谋”。*

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

    def build_audit_prompt(self, raw_outline_placeholder="[在这里粘贴模型生成的原始大纲]"):
        target, genre, bg_settings = self.generate_settings()
        settings = self.settings_to_dict(target, genre, bg_settings)
        return self.build_audit_prompt_from_settings(settings, raw_outline_placeholder)

    def build_audit_prompt_from_settings(self, settings, raw_outline_placeholder="[在这里粘贴模型生成的原始大纲]"):
        return f"""# 小说大纲审查指令

你是严苛的网文大纲审稿委员会。请基于同一张设定卡，审查楔子、第1章到第10章的大纲。

## 设定卡
{self.format_settings_card(settings)}

## 审查维度
1. 章节完整性：必须有楔子、第1章至第10章，共11个章节块。
2. 因果连续性：每章结尾必须自然推出下一章起因。
3. 人物动机：主角、反派、关键配角的目标、代价、选择必须自洽，禁止降智。
4. 剧情张力：每章必须有明确目标、阻力、转折、结果。
5. 道具与伏笔：列出所有核心道具/线索的出现、推进、回收状态，指出未闭环项。
6. 世界观一致性：时代、职业、制度、语言口吻不得与设定卡冲突。
7. 终章收束：第十章必须清算主冲突、揭示核心真相、回收主要伏笔，禁止新增续章钩子。

## 输出格式
### 总体评分
- 结构完整性：
- 人物自洽：
- 因果逻辑：
- 道具伏笔：
- 爽点/情绪：

### 必须修复的问题
- 按严重程度列出。

### 分章审查
- 楔子：
- 第一章：
- 第二章：
- 第三章：
- 第四章：
- 第五章：
- 第六章：
- 第七章：
- 第八章：
- 第九章：
- 第十章：

### 优化指令清单
- 给后续优化大纲使用，必须具体到章节、人物、道具或伏笔。

## 待审查大纲
{raw_outline_placeholder}
"""

    def build_optimize_prompt_from_settings(
        self,
        settings,
        raw_outline_placeholder="[在这里粘贴原始大纲]",
        audit_placeholder="[在这里粘贴审核意见]",
    ):
        return f"""# 小说大纲优化指令

你是执行型主编。请严格基于设定卡、原始大纲和审核意见，重写出最终优化版大纲。

## 设定卡
{self.format_settings_card(settings)}

## 优化硬约束
1. 保留楔子、第1章到第10章，共11个章节块。
2. 每章必须包含：主场景、出场人物、核心目标、三幕式剧情、反派/暗线动态、道具/伏笔状态、主角心境变化、结尾承接。
3. 第十章必须完成终极冲突、真相揭示、反派清算、伏笔回收和首尾呼应。
4. 所有改动必须响应审核意见，不得另起炉灶。
5. 背景设定不得漂移，不得加入与设定卡冲突的新职业、制度、时代元素。

## 原始大纲
{raw_outline_placeholder}

## 审核意见
{audit_placeholder}

## 输出格式
先输出“核心资产清单”，再按 Markdown 输出：
### 楔子：...
### 第一章：...
...
### 第十章：...
"""

if __name__ == "__main__":
    pb = PromptBuilder()
    print(pb.build_prompt())
