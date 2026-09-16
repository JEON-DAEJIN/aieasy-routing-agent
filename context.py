"""카테고리 -> 근거 조립.

문서 "전체"가 아니라 그 카테고리에 매핑된 문서만 읽어 근거로 넣는다 (N039 2·5장 원칙).
매핑은 README.md의 카테고리-문서 매핑표와 반드시 일치시킨다.
"""

import pathlib

DOCS_DIR = pathlib.Path(__file__).parent / "docs"

CATEGORY_DOCS = {
    "CONCEPT": ["레슨1_AI는_도대체_뭘까.md", "레슨3_AI가_잘하는것_못하는것.md"],
    "PROMPT": ["레슨2_프롬프트란_무엇인가.md", "레슨4_나만의_첫_프롬프트_써보기.md"],
    "APPLY": ["레슨5_AI로_일상문제_해결하기.md", "레슨6_AI를_계속_배우는법.md"],
    "SERVICE": ["서비스이용_안내.md"],
    "OUT_OF_SCOPE": [],
}


def load_evidence(category: str) -> str:
    """카테고리에 매핑된 문서를 읽어 하나의 근거 문자열로 합쳐 반환한다.

    OUT_OF_SCOPE는 매핑된 문서가 없으므로 빈 문자열을 반환한다 — 호출부(agent.py)는
    이 경우 답변 생성 없이 바로 넘기기 응답으로 분기해야 한다.
    """
    filenames = CATEGORY_DOCS.get(category)
    if filenames is None:
        raise ValueError(f"알 수 없는 카테고리: {category}")

    chunks = []
    for filename in filenames:
        text = (DOCS_DIR / filename).read_text(encoding="utf-8")
        chunks.append(f"### 출처: {filename}\n{text}")

    return "\n\n".join(chunks)
