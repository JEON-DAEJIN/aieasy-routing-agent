"""분류 지침과 답변 규칙 프롬프트.

few-shot 예시는 반드시 data/fewshot_examples.json에서만 가져온다 — data/eval_set.csv
문항을 예시로 쓰면 평가가 암기력 측정이 되어버리기 때문이다 (N039 6장 원칙).
"""

import json
import pathlib

CATEGORIES = ["CONCEPT", "PROMPT", "APPLY", "SERVICE", "OUT_OF_SCOPE"]

_DATA_DIR = pathlib.Path(__file__).parent / "data"

CATEGORY_DESCRIPTIONS = {
    "CONCEPT": "AI가 무엇인지, 어떻게 학습하는지, 환각이 무엇인지처럼 AI 자체의 개념/한계를 정의하는 질문. "
    "'AI가 왜 틀리는가'를 묻는 것이지, '내 질문/요청을 어떻게 고치면 좋을지'를 묻는 것이 아니다.",
    "PROMPT": "프롬프트(질문/지시문) 자체를 어떻게 잘 쓰는지(역할·과업·형식·제약)에 대한 질문. "
    "'같은 AI인데 답변 품질/결과가 왜 다른가'를 묻는 질문도 여기 포함된다 — "
    "원인이 AI의 한계가 아니라 사용자가 준 지시(프롬프트)의 구체성이기 때문이다.",
    "APPLY": "레슨에서 배운 개념/프롬프트 작성법을 실제 상황(사진 검색, 문서·계약서 요약, 이메일 초안 등)에 "
    "어떻게 적용할지 묻는 구체적 활용 질문, 그리고 'AI가 발전해도 사람이 최종적으로 해야 할 일이 무엇인가'처럼 "
    "AI 활용 시의 태도에 대한 질문. 개념 자체의 정의를 묻는 게 아니라 '어떻게 하면 좋을까'를 묻는다.",
    "SERVICE": "AI Easy 앱 자체 이용 방법(요금, 무료 질문 횟수, 진도, 다른 트랙 출시 여부 등)에 대한 질문",
    "OUT_OF_SCOPE": "위 네 카테고리 어디에도 속하지 않는 질문 (트랙1과 무관한 일반 질문, 또는 실질적으로 다른 트랙의 내용을 대신 수행해달라는 요청)",
}


def _load_fewshot_examples():
    path = _DATA_DIR / "fewshot_examples.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["examples"]


def build_classify_prompt(question: str) -> str:
    """카테고리 분류용 프롬프트를 조립한다."""
    examples = _load_fewshot_examples()
    example_lines = "\n".join(
        f'- "{ex["question"]}" -> {ex["category"]}' for ex in examples
    )
    category_lines = "\n".join(
        f"- {cat}: {desc}" for cat, desc in CATEGORY_DESCRIPTIONS.items()
    )

    return f"""당신은 AI 초보자용 학습 앱 "AI Easy"의 레슨 챗봇 라우터입니다.
사용자 질문을 아래 5개 카테고리 중 정확히 하나로만 분류하세요.

[카테고리]
{category_lines}

[분류 예시]
{example_lines}

[판단 기준]
- 질문이 "이 앱에 어떤 트랙/기능이 있는가"를 묻는 것이면 문서로 답할 수 있으므로 SERVICE입니다.
- 질문이 "다른 트랙(영어/수학 등)의 실제 내용을 대신 수행"해달라는 요청(번역, 문제 풀이 등)이면
  이 앱이 답할 근거가 없으므로 OUT_OF_SCOPE입니다.
- 애매하면 OUT_OF_SCOPE로 판단하세요. 근거 없이 답하는 것보다 넘기는 것이 안전합니다.

카테고리 이름 하나만 출력하세요. 다른 설명은 쓰지 마세요.

질문: {question}
카테고리:"""


def build_answer_prompt(question: str, evidence: str) -> str:
    """근거만으로 답변을 생성하는 프롬프트."""
    return f"""당신은 AI Easy의 레슨 챗봇입니다. 아래 [근거]에 있는 내용만 사용해서 사용자 질문에 답하세요.

규칙:
1. [근거]에 있는 사실만 답변에 포함하세요. 근거에 없는 내용은 절대 지어내지 마세요.
2. [근거]로 답할 수 없는 세부사항을 물으면, 모른다고 솔직히 말하세요.
3. 200자 내외로 간결하게, 초보자가 이해하기 쉬운 한국어로 답하세요.
4. 제목, 굵게(**), 목록 기호 같은 마크다운 서식은 쓰지 마세요.

[근거]
{evidence}

[질문]
{question}

[답변]"""


OUT_OF_SCOPE_MESSAGE = (
    "이 질문은 지금 배우고 계신 'AI로 AI 공부하는 법' 트랙 범위 밖이라, "
    "정확한 답을 드리기 어려워요. 트랙 내용으로 다시 질문해 주시겠어요?"
)


def build_verify_prompt(answer: str, evidence: str) -> str:
    """답변의 각 주장이 근거에 있는지 대조하는 검증 프롬프트."""
    return f"""아래 [답변]에 등장하는 사실 주장을 모두 나열하고, 각 주장이 [근거]에 실제로 있는지 대조하세요.

[근거]
{evidence}

[답변]
{answer}

다음 JSON 형식으로만 답하세요. 다른 설명은 쓰지 마세요.
{{"unsupported_claims": ["근거에 없는 주장1", "..."], "passed": true 또는 false}}

근거에 없는 주장이 하나도 없으면 unsupported_claims는 빈 배열이고 passed는 true입니다."""
