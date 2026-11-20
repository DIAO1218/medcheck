from medcheck.extractor import context


def test_extreme_overflow_triggers_compaction_and_keeps_l2():
    """REQ-C-001: Massive notes must be compacted, but never drop L2 constraints."""
    # 生成一篇超长垃圾病历，按 4 字符/token 估算，绝对超过 5000 token
    huge_note = "Patient is in severe pain. " * 1000
    
    assembled = context.assemble(note=huge_note)
    
    # 1. 断言确实触发了压实机制（否则这个测试就没意义了）
    assert len(assembled.layers_compacted) > 0, "Compaction did not trigger!"
    
    # 2. 断言 L2 约束的标志性语句依然出现在最终 payload 中
    assert "STANDING CONSTRAINTS" in assembled.payload
    
    # 3. 断言重注入成功
    assert assembled.constraint_reinjected is True
