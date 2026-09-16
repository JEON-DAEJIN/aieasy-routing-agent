"""LangGraph 파이프라인: 카테고리 판정 -> 근거 조립 -> 답변 -> 검증.

State는 에이전트가 단계마다 채워 넣는 "작업 가방"이다 (N039 9장 비유):
    question   -> 사용자 질문
    category   -> classify_node가 채움
    evidence   -> assemble_node가 채움
    answer     -> answer_node가 채움
    validation -> verify_node가 채움

실제 배포 챗봇(ai-easy/04_개발/챗봇-서버리스/src/index.js)의 handleChat()과 같은
입력(question)을 받는 run() 함수를 최상위에 노출해 두어, 검증된 로직을 그 Worker에
이식할 때 이 함수 시그니처를 그대로 참고할 수 있게 했다.
"""

import json
import os
from typing import TypedDict

from anthropic import Anthropic
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

import context
import prompts

load_dotenv()

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _call_claude(user_prompt: str, max_tokens: int = 400) -> str:
    model = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    response = _get_client().messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()


class AgentState(TypedDict, total=False):
    question: str
    category: str
    evidence: str
    answer: str
    validation: dict


def classify_node(state: AgentState) -> AgentState:
    raw = _call_claude(prompts.build_classify_prompt(state["question"]), max_tokens=20)
    # 모델이 카테고리 이름 외의 군더더기를 붙일 때를 대비해, 알려진 카테고리 중
    # 응답 안에 실제로 등장하는 것을 찾는다. 하나도 못 찾으면 안전하게 넘긴다.
    category = next((c for c in prompts.CATEGORIES if c in raw), "OUT_OF_SCOPE")
    return {"category": category}


def route_after_classify(state: AgentState) -> str:
    return "out_of_scope" if state["category"] == "OUT_OF_SCOPE" else "assemble"


def assemble_node(state: AgentState) -> AgentState:
    evidence = context.load_evidence(state["category"])
    return {"evidence": evidence}


def answer_node(state: AgentState) -> AgentState:
    answer = _call_claude(
        prompts.build_answer_prompt(state["question"], state["evidence"]),
        max_tokens=300,
    )
    return {"answer": answer}


def verify_node(state: AgentState) -> AgentState:
    raw = _call_claude(
        prompts.build_verify_prompt(state["answer"], state["evidence"]),
        max_tokens=400,
    )
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        validation = json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        # 검증 모델 응답 자체가 깨졌을 때는 "미확인"으로 안전하게 실패 처리한다.
        validation = {"unsupported_claims": ["검증 응답 파싱 실패"], "passed": False}
    return {"validation": validation}


def out_of_scope_node(state: AgentState) -> AgentState:
    return {
        "evidence": "",
        "answer": prompts.OUT_OF_SCOPE_MESSAGE,
        "validation": {"unsupported_claims": [], "passed": True},
    }


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node)
    graph.add_node("assemble", assemble_node)
    graph.add_node("answer", answer_node)
    graph.add_node("verify", verify_node)
    graph.add_node("out_of_scope", out_of_scope_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {"assemble": "assemble", "out_of_scope": "out_of_scope"},
    )
    graph.add_edge("assemble", "answer")
    graph.add_edge("answer", "verify")
    graph.add_edge("verify", END)
    graph.add_edge("out_of_scope", END)

    return graph.compile()


_graph = None


def run(question: str) -> AgentState:
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph.invoke({"question": question})


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "챗봇 질문은 하루에 몇 번까지 무료인가요?"
    result = run(q)
    print(json.dumps(result, ensure_ascii=False, indent=2))
