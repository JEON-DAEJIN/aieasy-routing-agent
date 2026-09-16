"""분류 지침과 답변 규칙 프롬프트.

TODO:
- CATEGORIES: CONCEPT / PROMPT / APPLY / SERVICE / OUT_OF_SCOPE 5개 정의
- CLASSIFY_PROMPT: 질문 -> 카테고리 분류 지침 (few-shot 예시는 data/eval_set.csv와 절대 겹치지 않게)
- ANSWER_PROMPT: 카테고리별 근거만으로 답변 생성 지침
  ("근거에 없는 내용은 만들어내지 말고, 모르면 넘긴다"를 지시가 아니라 구조로 구현하는 것이 목표 —
   agent.py의 검증 노드가 이 지시를 실제로 지켰는지 사후 검사한다)
"""

CATEGORIES = ["CONCEPT", "PROMPT", "APPLY", "SERVICE", "OUT_OF_SCOPE"]
