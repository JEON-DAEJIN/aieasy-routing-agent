"""LangGraph 파이프라인: 카테고리 판정 -> 근거 조립 -> 답변 -> 검증.

TODO:
- State: {"question", "category", "evidence", "answer", "validation"} (N039 부록 A 참고)
- 노드 4개를 분리해서 구현:
  1) classify_node   — 카테고리 판정 (prompts.CLASSIFY_PROMPT)
  2) assemble_node   — context.load_evidence(category)
  3) answer_node     — 근거만으로 답변 생성 (prompts.ANSWER_PROMPT)
  4) verify_node     — 답변 속 주장을 근거와 대조, 근거 밖 내용이면 실패 처리
- OUT_OF_SCOPE로 판정되면 근거 조립/답변 생성 없이 바로 넘기기 응답으로 분기
- 실제 배포 챗봇(ai-easy/04_개발/챗봇-서버리스/src/index.js)의 handleChat()과
  같은 입력(user_id, lesson_id, question)을 받도록 인터페이스를 맞춰 두면
  나중에 이 로직을 그 Worker에 이식하기 쉽다.
"""
