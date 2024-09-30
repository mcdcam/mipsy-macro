# Get mips.yaml here: https://github.com/insou22/mipsy/blob/main/mips.yaml

import yaml
import json

registers = ["$zero", "$at", "$gp", "$sp", "$fp", "$ra"]
registers += [f"$v{n}" for n in range(2)]
registers += [f"$a{n}" for n in range(4)]
registers += [f"$t{n}" for n in range(10)]
registers += [f"$s{n}" for n in range(8)]
registers += [f"$k{n}" for n in range(2)]

directives = [
    ".text", ".data", ".ktext", ".kdata", ".align", ".ascii", ".asciiz",
    ".space", ".byte", ".half", ".word", ".float", ".double", ".globl"
]

with open("mips.yaml") as stream:
    try:
        mips = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

all_instructions_names = []
for _, instructions in mips.items():
    for instruction in instructions:
        all_instructions_names.append(instruction["name"].lower())

reserved_words = {
    "registers": registers,
    "directives": directives,
    "instructions": all_instructions_names
}
print(reserved_words)
with open("../reserved_words.json", "w") as f:
    json.dump(reserved_words, f, indent=2)
