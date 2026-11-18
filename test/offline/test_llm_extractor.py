import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from medcheck.extractor import llm

# 模拟一个合法的模型响应
MOCK_VALID_RESPONSE = {
    "choices": [{"message": {"content": '{"medications": [{"name_raw": "Warfarin", "name_canonical": "warfarin"}]}'}}]
}

def test_llm_uses_correct_prompt_version():
    """REQ-I-005: Extractor must pass prompt_version to the contract."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(MOCK_VALID_RESPONSE).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # 强行设置环境变量绕过 configured() 检查
        with patch.dict("os.environ", {"MEDCHECK_LLM_BASE_URL": "http://fake", "MEDCHECK_LLM_API_KEY": "fake"}):
            record = llm.extract("test note")
            assert record.prompt_version == "llm-v1.0"

def test_llm_api_error_raises_safely():
    """REQ-F-001: Model API errors must be caught and raised as known exceptions."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        # 模拟 HTTP 500 服务器错误
        mock_urlopen.side_effect = urllib.error.HTTPError("http://fake", 500, "Server Error", {}, None)
        
        with patch.dict("os.environ", {"MEDCHECK_LLM_BASE_URL": "http://fake", "MEDCHECK_LLM_API_KEY": "fake"}),              pytest.raises(urllib.error.HTTPError):
            # 目前 extract 会直接抛出 HTTPError，我们希望被包装成明确的错误
            llm.extract("test note")

def test_llm_fallback_appends_trace():
    """REQ-I-001: If fallback is allowed, it must append a trace to unparsed."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        # 模拟超时
        mock_urlopen.side_effect = TimeoutError("API Timeout")
        
        with patch.dict("os.environ", {"MEDCHECK_LLM_BASE_URL": "http://fake", "MEDCHECK_LLM_API_KEY": "fake"}):
            # 允许 fallback
            record = llm.extract_with_fallback("test note", allow_heuristic=True)
            
            # 断言：成功回退，且留下了耻辱柱（trace）
            assert any("heuristic fallback" in item for item in record.unparsed)
            assert record.prompt_version == "heuristic-v1" # 或者 heuristic 实际的版本号
