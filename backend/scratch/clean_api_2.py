import re

with open("../frontend/src/lib/api.ts", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
open_braces = 0

for i, line in enumerate(lines):
    if skip:
        open_braces += line.count('{') - line.count('}')
        if open_braces <= 0:
            skip = False
        continue

    # Look for the start of the mock fallback argument
    # Typically it looks like: , () => {
    # Or: , () => mockSomething
    # Or: , () => ({
    
    if ", () =>" in line:
        # If it's a one-liner
        if line.count('{') == line.count('}'):
            # Just remove everything from `, () =>` to the end, but we need to keep the closing `);`
            # Wait, there might be `);` at the end of the line
            if ");" in line:
                line = line[:line.find(", () =>")] + ");\n"
            else:
                line = line[:line.find(", () =>")] + "\n"
        else:
            # Multi-line mock object
            open_braces = line.count('{') - line.count('}')
            line = line[:line.find(", () =>")] + ");\n"
            if open_braces > 0:
                skip = True
    
    # Same for mock imports
    if "from './mock-data'" in line:
        continue
        
    new_lines.append(line)

# Handle apiFetch method signature change if not already done
content = "".join(new_lines)
with open("../frontend/src/lib/api.ts", "w", encoding="utf-8") as f:
    f.write(content)
