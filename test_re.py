import re
text = "**场景**：相府落梅池畔\n- **第一幕（起）**：寒冬..."
print(re.search(r'\*\*场景\*\*[:：]\s*(.*)', text).group(1))
