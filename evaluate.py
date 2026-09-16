"""도구 호출 적절성 · 답변 적절성 측정.

실행: python evaluate.py

두 지표(N039 8장):
- 도구 호출 적절성: agent가 실제로 판정한 카테고리(=조회한 문서 집합)가 기대 카테고리와
  정확히 일치하면 1점.
- 답변 적절성: 필수 사실을 모두 포함하고, 금지 사실을 하나도 어기지 않으면 1점.
  표현이 아니라 "사실이 담겼는가"로 채점하기 위해 별도 LLM 호출(judge)을 쓴다.

채점기 자체도 먼저 검증한다 — 모범 답안을 넣으면 통과, 의도적 오답을 넣으면
실패가 나오는지 스모크 테스트를 메인 평가보다 먼저 실행한다.
"""

import csv
import json
import os
import pathlib

from anthropic import Anthropic
from dotenv import load_dotenv

import agent

load_dotenv()

DATA_DIR = pathlib.Path(__file__).parent / "data"
_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def judge_answer(answer: str, must_include: list, must_forbid: list) -> dict:
    """답변이 필수 사실을 담고 금지 사실을 어기지 않았는지 사실 단위로 채점한다.

    표현이 아니라 사실 일치로 판단하도록 프롬프트에 명시한다 (N039 8장 원칙).
    """
    prompt = f"""아래 [답변]이 [필수 사실]을 모두 포함하는지, [금지 사실]을 하나라도
포함하는지 판단하세요. 문장 표현이 달라도 같은 사실이면 "포함"으로 판단하세요.

[답변]
{answer}

[필수 사실]
{json.dumps(must_include, ensure_ascii=False)}

[금지 사실]
{json.dumps(must_forbid, ensure_ascii=False)}

다음 JSON 형식으로만 답하세요.
{{"missing": ["답변에 빠진 필수 사실"], "violated": ["답변에 등장한 금지 사실"], "passed": true 또는 false}}
passed는 missing과 violated가 둘 다 비어 있을 때만 true입니다."""

    response = _get_client().messages.create(
        model=_MODEL, max_tokens=400, messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    start, end = raw.index("{"), raw.rindex("}") + 1
    return json.loads(raw[start:end])


def self_test_judge():
    """채점기 자체를 모범답안/오답으로 먼저 검증한다."""
    must_include = ["트랙1 레슨 6개와 퀴즈는 영구 무료"]
    must_forbid = ["결제해야만 레슨을 볼 수 있다"]

    gold = judge_answer("트랙1 레슨 6개와 퀴즈는 영구 무료로 제공됩니다.", must_include, must_forbid)
    bad = judge_answer("죄송하지만 트랙1 레슨을 보려면 결제해야만 합니다.", must_include, must_forbid)

    assert gold["passed"] is True, f"채점기 오류: 모범답안이 실패 처리됨 -> {gold}"
    assert bad["passed"] is False, f"채점기 오류: 오답이 통과 처리됨 -> {bad}"
    print("[채점기 자체 검증] 통과 — 모범답안=PASS, 오답=FAIL 정상 확인")


def classify_error(expected: str, predicted: str, judge_result: dict | None) -> str:
    if expected == "OUT_OF_SCOPE" and predicted != "OUT_OF_SCOPE":
        return "범위 밖 질문에 답변"
    if expected != "OUT_OF_SCOPE" and predicted == "OUT_OF_SCOPE":
        return "과잉 넘기기(답할 수 있는데 범위 밖으로 오분류)"
    if predicted != expected:
        return "잘못된 카테고리(문서) 선택"
    if judge_result and judge_result.get("violated"):
        return "문서에 없는 정보를 생성"
    if judge_result and judge_result.get("missing"):
        return "필수 사실 누락"
    return "-"


def main():
    self_test_judge()
    print()

    eval_rows = list(csv.DictReader(open(DATA_DIR / "eval_set.csv", encoding="utf-8")))
    gold = json.load(open(DATA_DIR / "answer_gold.json", encoding="utf-8"))

    results = []
    for row in eval_rows:
        qid, question, expected = row["id"], row["question"], row["expected_category"]
        gold_item = gold[qid]

        state = agent.run(question)
        predicted = state["category"]
        answer = state["answer"]

        tool_correct = predicted == expected

        judge_result = None
        if predicted != "OUT_OF_SCOPE":
            judge_result = judge_answer(answer, gold_item["must_include"], gold_item["must_forbid"])
            answer_correct = judge_result["passed"]
        else:
            # OUT_OF_SCOPE로 넘긴 경우: 실제로 범위 밖이 정답이면 통과, 아니면 실패
            answer_correct = expected == "OUT_OF_SCOPE"

        error_type = "-" if (tool_correct and answer_correct) else classify_error(
            expected, predicted, judge_result
        )

        results.append(
            {
                "id": qid,
                "question": question,
                "expected": expected,
                "predicted": predicted,
                "tool_correct": tool_correct,
                "answer_correct": answer_correct,
                "error_type": error_type,
                "answer": answer,
            }
        )
        status = "OK" if (tool_correct and answer_correct) else "FAIL"
        print(f"[{status}] {qid} expected={expected} predicted={predicted} error={error_type}")

    tool_acc = sum(r["tool_correct"] for r in results) / len(results)
    answer_acc = sum(r["answer_correct"] for r in results) / len(results)

    print()
    print(f"도구 호출 적절성: {tool_acc:.0%} ({sum(r['tool_correct'] for r in results)}/{len(results)})")
    print(f"답변 적절성:     {answer_acc:.0%} ({sum(r['answer_correct'] for r in results)}/{len(results)})")

    fails = [r for r in results if r["error_type"] != "-"]
    if fails:
        print("\n오류 원인 분류:")
        for r in fails:
            print(f"  {r['id']}: {r['error_type']}")

    out_path = DATA_DIR / "eval_results.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\n상세 결과 저장: {out_path}")


if __name__ == "__main__":
    main()
