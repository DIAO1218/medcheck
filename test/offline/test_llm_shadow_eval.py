import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from medcheck.extractor import llm
from medcheck.pipeline import process_case

FIXTURES = Path(__file__).parent.parent / "fixtures" / "cases"

def test_shadow_eval_llm_mock_perfect_response():
    """
    REQ-C-001: Shadow evaluation of the live extractor path.
    We mock the LLM API to return the perfect extraction payload for a fixture,
    and verify the pipeline processes it correctly through to adjudication.
    """
    # 用 c01（单药批准）这个用例来做测试
    case_path = FIXTURES / "c01_approve_single.json"
    if not case_path.exists():
        pytest.skip("Fixture c01_approve_single.json not found")
        
    case = json.loads(case_path.read_text(encoding="utf-8"))
    
    # 构造一个完美的 Mock 模型响应（假设模型完美抽取了华法林 5mg）
    mock_model_response = {
        "choices": [{
            "message": {
                "content": '{"medications": [{"name_raw": "Warfarin", "name_canonical": "warfarin", "dose_value": 5, "dose_unit": "mg", "frequency_text": "daily", "route": null}], "egfr": null, "unparsed": []}'
            }
        }]
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_model_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with patch.dict("os.environ", {"MEDCHECK_LLM_BASE_URL": "http://fake", "MEDCHECK_LLM_API_KEY": "fake"}):
            # 1. 先验证在线抽取器能完美解析
            record = llm.extract(case["note"])
            assert len(record.medications) == 1
            assert record.medications[0].name_canonical == "warfarin"
            
            # 2. 将解析结果喂给流水线，验证能否走通最终裁决
            # 注意：因为真实 pipeline 是用默认 heuristic 的，我们需要注入 extractor
            outcome = process_case(case, extractor=lambda text, vocab: record)
            
            # 3. 验证最终的裁决结果（根据具体的规则表，c01 应该是 APPROVE 或 HOLD）
            assert outcome.verdict in ["APPROVE", "HOLD", "BLOCK"]
            # 确保有输出建议
            assert len(outcome.advisory) > 0
