import os
import re
import argparse

def parse_outline(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all chapter blocks. We assume they start with ### or ##
    pattern = re.compile(r'^(#{2,4})\s+(楔子|第[一二三四五六七八九十百零0-9]+章|结局)(.*)$', re.MULTILINE)
    matches = list(pattern.finditer(content))

    chapters = []
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()

        ch_type = matches[i].group(2).strip()
        ch_suffix = matches[i].group(3).strip()
        
        # Clean title suffix
        clean_suffix = re.sub(r'^[：:\s]+', '', ch_suffix)
        if clean_suffix:
            full_title = f"{ch_type}：{clean_suffix}"
        else:
            full_title = ch_type

        def extract_field(field_names):
            for name in field_names:
                m = re.search(fr'\*{{0,2}}{name}\*{{0,2}}[:：]\s*(.*)', body)
                if m:
                    return m.group(1).strip()
            return ""
        
        def extract_act(act_names):
            for name in act_names:
                m = re.search(fr'-\s*\*{{0,2}}{name}.*?\*{{0,2}}[:：]\s*(.*)', body)
                if m:
                    return m.group(1).strip()
            return ""

        scene = extract_field(['场景', '主场景'])
        chars = extract_field(['人物', '出场人物'])
        core = extract_field(['核心剧情', '核心目标'])
        if not core:
            # Fallback
            m = re.search(r'\*\*核心剧情\*\*：(.*)', body)
            if m: core = m.group(1)
            
        act1 = extract_act(['第一幕'])
        act2 = extract_act(['第二幕'])
        act3 = extract_act(['第三幕'])
        
        chapters.append({
            'type': ch_type,
            'title': full_title,
            'clean_title': clean_suffix, # Just the name without '第X章：'
            'scene': scene,
            'chars': chars,
            'core': core,
            'act1': act1,
            'act2': act2,
            'act3': act3
        })
    return chapters

def fill_template(template, prefix, chapter):
    if not chapter:
        return template
    t = template
    
    # We replace both {这里填本章标题} and {这里填你的第一章标题} types of placeholders
    clean_title = chapter['clean_title']
    full_title = chapter['title']

    # Replace non-prefixed placeholders for current chapter
    if prefix in ["本章", "你的楔子", "你的第一章", "你的结局"]:
        t = t.replace('{这里填场景}', chapter['scene'])
        t = t.replace('{这里填人物}', chapter['chars'])
        t = t.replace('{这里填核心剧情}', chapter['core'])
        t = t.replace('{这里填第一幕}', chapter['act1'])
        t = t.replace('{这里填第二幕}', chapter['act2'])
        t = t.replace('{这里填第三幕}', chapter['act3'])
        
        # specific template placeholders expecting the clean title
        t = t.replace('{这里填你的第一章标题}', clean_title if clean_title else full_title)
        t = t.replace('{这里填你的楔子标题}', clean_title if clean_title else full_title)
        t = t.replace('{这里填你的结局标题}', clean_title if clean_title else full_title)
        t = t.replace('{这里填本章标题}', full_title)
        
    # Normal prefixed placeholders
    t = t.replace(f'{{这里填{prefix}标题}}', full_title if prefix in ["本章", "上一章", "下一章"] else (clean_title if clean_title else full_title))
    t = t.replace(f'{{这里填{prefix}场景}}', chapter['scene'])
    t = t.replace(f'{{这里填{prefix}人物}}', chapter['chars'])
    t = t.replace(f'{{这里填{prefix}核心剧情}}', chapter['core'])
    t = t.replace(f'{{这里填{prefix}第一幕}}', chapter['act1'])
    t = t.replace(f'{{这里填{prefix}第二幕}}', chapter['act2'])
    t = t.replace(f'{{这里填{prefix}第三幕}}', chapter['act3'])

    return t

def slice_and_generate_prompts(outline_file, output_dir, template_dir):
    with open(os.path.join(template_dir, '00_楔子提示词模板.md'), 'r', encoding='utf-8') as f:
        tpl_0 = f.read()
    with open(os.path.join(template_dir, '01_第一章提示词模板.md'), 'r', encoding='utf-8') as f:
        tpl_1 = f.read()
    with open(os.path.join(template_dir, '02_第二章-第九章提示词模板.md'), 'r', encoding='utf-8') as f:
        tpl_2_9 = f.read()
    with open(os.path.join(template_dir, '03_结局提示词模板.md'), 'r', encoding='utf-8') as f:
        tpl_end = f.read()

    chapters = parse_outline(outline_file)
    print(f"Parsed {len(chapters)} chapters from outline.")

    os.makedirs(output_dir, exist_ok=True)
    
    # Clean previous prompts
    for filename in os.listdir(output_dir):
        if filename.endswith(".md"):
            os.remove(os.path.join(output_dir, filename))

    for i, ch in enumerate(chapters):
        if '楔子' in ch['type']:
            t = fill_template(tpl_0, "你的楔子", ch)
            if i + 1 < len(chapters):
                t = fill_template(t, "第一章", chapters[i+1])
            filename = "00_楔子_prompt.md"
        elif '第一章' in ch['type']:
            t = fill_template(tpl_1, "你的第一章", ch)
            if i + 1 < len(chapters):
                t = fill_template(t, "第二章", chapters[i+1])
            filename = "01_第一章_prompt.md"
        elif '结局' in ch['type'] or '第十章' in ch['type']:
            t = fill_template(tpl_end, "本章", ch)
            if i - 1 >= 0:
                t = fill_template(t, "上一章", chapters[i-1])
            # Save safe filename
            safe_title = ch['title'].replace('：', '_').replace(' ', '_').replace('（', '').replace('）', '')
            filename = f"{i:02d}_{safe_title}_prompt.md"
        else:
            t = fill_template(tpl_2_9, "本章", ch)
            if i - 1 >= 0:
                t = fill_template(t, "上一章", chapters[i-1])
            if i + 1 < len(chapters):
                t = fill_template(t, "下一章", chapters[i+1])
            safe_title = ch['title'].replace('：', '_').replace(' ', '_').replace('（', '').replace('）', '')
            filename = f"{i:02d}_{safe_title}_prompt.md"
            
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            f.write(t)
        print(f"Generated {filename}")
        
    print("Done generating prompts.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outline", type=str, required=True, help="优化后的完整大纲文件")
    parser.add_argument("--output", type=str, required=True, help="输出 prompt 文件夹路径")
    parser.add_argument("--template-dir", type=str, default="/Users/tang/PycharmProjects/pythonProject/.agent/skills/novel_evolution_engine/scripts/dp_promet")
    args = parser.parse_args()
    
    slice_and_generate_prompts(args.outline, args.output, args.template_dir)