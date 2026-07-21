"""
Сгенерируем system prompt контекст для LLM на основе workshops.
Workshop-информация = "что умеет Техинком" — это важно для LLM чтобы
предлагать РЕАЛЬНЫЕ операции на РЕАЛЬНОМ оборудовании.
"""
import json

with open('/workspace/attachments/tehinkom_workshops.json', 'r', encoding='utf-8') as f:
    workshops = json.load(f)

# Группируем по section
by_section = {}
for w in workshops:
    sec = w['section']
    by_section.setdefault(sec, []).append(w)

lines = ["# УЧАСТКИ И ОПЕРАЦИИ ТЕХИНКОМ — РЕАЛЬНЫЕ ДАННЫЕ ПРОИЗВОДСТВА", ""]
lines.append("Используй ТОЛЬКО эти участки и операции при генерации маршрута.")
lines.append("НЕ придумывай операции, которых нет в этом списке.")
lines.append("Каждой операции соответствует реальное оборудование Техинкома.\n")

for sec, ws in by_section.items():
    lines.append(f"\n## {sec}")
    for w in ws:
        lines.append(f"\n### {w['name']} ({len(w['operations'])} операций)")
        for op in w['operations']:
            notes = f" — {op['notes']}" if op['notes'] else ""
            lines.append(f"- {op['name']}{notes}")

context = '\n'.join(lines)
with open('/workspace/attachments/workshop_context.md', 'w', encoding='utf-8') as f:
    f.write(context)

print(f"Context size: {len(context)} chars, {context.count(chr(10))} lines")
print("---")
print(context[:500])
