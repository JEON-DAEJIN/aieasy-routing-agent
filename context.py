"""카테고리 -> 근거 조립.

TODO:
- CATEGORY_DOCS: 카테고리별로 읽어들일 docs/ 파일 목록 매핑 (README.md 매핑표와 반드시 일치시킬 것)
- load_evidence(category: str) -> str: 매핑된 문서를 읽어 하나의 근거 문자열로 합쳐 반환
  (문서 "전체"가 아니라 그 카테고리에 필요한 부분만 넣는다는 N039 원칙을 지킬 것)
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
