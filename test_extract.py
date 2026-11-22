from medcheck.extractor import heuristic

note = "Warfarin 6 mg mane. Warfarin 6 mg nocte."
record = heuristic.extract(note, ())

print("\n====== 抽取结果 ======")
print(f"抽出了 {len(record.medications)} 条记录")
for m in record.medications:
    print(f"- 药名: {m.name_raw}, 剂量: {m.dose_value} {m.dose_unit}, 频次: {m.frequency_text}")
print("======================\n")
