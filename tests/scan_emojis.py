import os
import unicodedata

src_dir = r"C:\BOT\agy-session-manager\src"
found = 0
for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.endswith(".py"):
            fp = os.path.join(root, f)
            with open(fp, "r", encoding="utf-8") as fh:
                for line_idx, line in enumerate(fh):
                    for char in line:
                        cat = unicodedata.category(char)
                        cp = ord(char)
                        if cp > 0x2000 and (cat in ("So", "Sk") or cp in range(0x1F300, 0x1F9FF) or cp in range(0x2600, 0x27BF)):
                            print(f"{f}:{line_idx+1} -> U+{cp:04X} ({unicodedata.name(char, 'UNKNOWN')}): {line.strip()[:60]}")
                            found += 1

if found == 0:
    print("ALL CLEAR: Zero emojis found in src/")
else:
    print(f"Total emojis found: {found}")
