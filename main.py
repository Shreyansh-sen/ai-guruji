from typing import TypedDict, List, Dict
import os
import json
import requests
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
# from langgraph.graph.graph import CompiledGraph
load_dotenv()

from prompts import(
    CLASSIFICATION_PROMPT,
    EMOTIONAL_USECASE_PROMPT,
    MANTRA_RESPONSE_PROMPT,
    CONVERSATIONAL_RESPONSE_PROMPT,
)

POCKETBASE_URL = "https://mantra-cms-sbox.a4bx.io"
MAPPING_COLLECTION = "mantra_god_usecase_mappings"
POCKETBASE_ADMIN_TOKEN =os.getenv('POCKETBASE_ADMIN_TOKEN')
PB_HEADERS = {
    "Authorization": f"Bearer {POCKETBASE_ADMIN_TOKEN}"
}
USECASE_COLLECTION = "usecases"
MAPPING_COLLECTION = os.getenv('MAPPING_COLLECTION')


llm = AzureChatOpenAI(
    azure_endpoint="https://a4b-srm-sbox-intern-resource.cognitiveservices.azure.com/",
    api_key=os.getenv('API_KEY'),  
    api_version=os.getenv('API_VERSION'),
    deployment_name=os.getenv('DEPLOYMENT_NAME'),
    # temperature=0
)

class GuruState(TypedDict):
    user_input: str
    category: str
    selected_usecases: List[str]
    mantra_records: List[Dict]
    final_response: str
    conversation_history:List[Dict]
    


def log(title: str, data):
    print(f"\n{title}")
    print(json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, (dict, list)) else data)


def format_history(history: List[Dict]) -> str:
    lines = []
    for h in history:
        role = "User" if h["role"] == "user" else "Guruji"
        lines.append(f"{role}: {h['content']}")
    return "\n".join(lines)

#match id with the name
def fetch_usecase_name_to_id() -> Dict[str, str]:
    url = f"{POCKETBASE_URL}/api/collections/{USECASE_COLLECTION}/records"
    params = {"perPage": 200}

    print(f"\nFetching usecases from PocketBase")
    print(f"URL: {url}")

    res = requests.get(url, headers=PB_HEADERS, params=params)
    print(f"Status Code: {res.status_code}")
    res.raise_for_status()

    items = res.json()["items"]

    log("Usecases returned", [
        {"name": i["name"], "id": i["id"]} for i in items
    ])

    return {item["name"]: item["id"] for item in items}

#by name
def fetch_available_usecases() -> List[str]:
    url = f"{POCKETBASE_URL}/api/collections/{USECASE_COLLECTION}/records"
    params = {"perPage": 200}

    res = requests.get(url, headers=PB_HEADERS, params=params)
    res.raise_for_status()

    return sorted([item["name"] for item in res.json()["items"]])

#fetch correct mantra feom selected usecase.

def input_node(state: GuruState) -> GuruState:
    return state

def classification_node(state:GuruState)->GuruState:
    query=state["user_input"]
    response=llm.invoke(CLASSIFICATION_PROMPT.format(query=query))

    return {
        **state,
        "category":response.content.strip()
    }



# select suitable usecases from PocketBase
def usecase_selector_node(state: GuruState) -> GuruState:
    query = state["user_input"]
    available = fetch_available_usecases()

    response = llm.invoke(
        EMOTIONAL_USECASE_PROMPT.format(
            query=query,
            available_usecases=", ".join(available)
        )
    )

    try:
        selected = json.loads(response.content.strip())
    except Exception:
        selected = ["Peace"]

    selected = [u for u in selected if u in available]

    if not selected:
        selected = ["Peace"]

    return {
        **state,
        "selected_usecases": selected
    }

#fetch mantras according to selected usecase
def mantra_tool_node(state: GuruState) -> GuruState:
    print("\n mantra_tool_node ENTERED")
    log("Selected usecases", state["selected_usecases"])

    mantras = fetch_mantras_by_usecase(state["selected_usecases"])

    log("Mantras after PocketBase fetch", mantras)

    return {
        **state,
        "mantra_records": mantras
    }


def fetch_mantras_by_usecase(usecase_names: List[str]) -> List[Dict]:
    print("\nfetch_mantras_by_usecase CALLED")
    log("Requested usecase names", usecase_names)

    if not usecase_names:
        print("No usecases passed")
        return []

    name_to_id = fetch_usecase_name_to_id()

    usecase_ids = [
        name_to_id[name]
        for name in usecase_names
        if name in name_to_id
    ]

    log("Resolved usecase IDs", usecase_ids)

    if not usecase_ids:
        print(" No matching usecase IDs found")
        return []

    filter_query = " || ".join(
        [f'usecase="{uid}"' for uid in usecase_ids]
    )

    url = f"{POCKETBASE_URL}/api/collections/{MAPPING_COLLECTION}/records"

    params = {
        "filter": filter_query,
        "expand": "mantra,god,usecase",
        "perPage": 5
    }

    print("\n🔵 Fetching mantras from PocketBase")
    print(f"URL: {url}")
    print(f"Filter: {filter_query}")

    res = requests.get(url, headers=PB_HEADERS, params=params)

    print(f"Status Code: {res.status_code}")
    res.raise_for_status()

    raw_items = res.json().get("items", [])
    log("Raw records count", len(raw_items))

    if not raw_items:
        print(" PocketBase returned ZERO records")
        return []

    results = []

    for r in raw_items:
        mantra = r["expand"]["mantra"]
        god = r["expand"]["god"]
        usecase = r["expand"]["usecase"]

        results.append({
            "title": mantra["title"],
            "text": mantra.get("text"),
            "god": god["name"],
            "usecase": usecase["name"]
        })

    log("Parsed mantra titles", [m["title"] for m in results])

    return results


def conversational_tool_node(state:GuruState)->GuruState:
    usecases_all=fetch_available_usecases()
    query=state["user_input"]
    history=state["conversation_history"]
    response=llm.invoke(
        CONVERSATIONAL_RESPONSE_PROMPT.format(
            query=query,
            history=format_history(history),
            available_usecases=", ".join(usecases_all)
        )
    )

    return {
        **state,
        "final_response": response.content.strip(),
        "conversation_history": history + [{"role":"user","content":query},{"role":"assistant","content":response.content.strip()}]
    }

def mantra_response_node(state: GuruState) -> GuruState:
    mantras = state["mantra_records"]
    history=state["conversation_history"]
    query=state["user_input"]
    if not mantras:
        return {
            **state,
            "final_response": "🙏 Is samay ke liye koi mantra uplabdh nahi hai."
        }

    m = mantras[0]

    response = llm.invoke(
        MANTRA_RESPONSE_PROMPT.format(
            mantra=m["title"],
            god=m["god"],
            usecase=m["usecase"]
        )
    )

    return {
        **state,
        "final_response": response.content.strip(),
        "conversation_history": history + [{"role":"user","content":query},{"role":"assistant","content":response.content.strip()}]
    }


graph = StateGraph(GuruState)

graph.add_node("input", input_node)
graph.add_node("classification", classification_node)
graph.add_node("usecase_selector", usecase_selector_node)
graph.add_node("mantra_tool", mantra_tool_node)
graph.add_node("conversational_tool", conversational_tool_node)
graph.add_node("mantra_response", mantra_response_node)

graph.set_entry_point("input")

graph.add_edge("input", "classification")

# Conditional edges from classification node
def route_based_on_category(state: GuruState) -> str:
    category = state.get("category", "").strip().lower()
    if "mantra" in category:
        return "usecase_selector"
    else:
        return "conversational_tool"

graph.add_conditional_edges(
    "classification",
    route_based_on_category,
    {
        "usecase_selector": "usecase_selector",
        "conversational_tool": "conversational_tool"
    }
)

graph.add_edge("usecase_selector", "mantra_tool")

graph.add_edge("mantra_tool", "mantra_response")
graph.add_edge("conversational_tool", END)
graph.add_edge("mantra_response", END)

app = graph.compile()

memory_history = []

def ask_guruji(user_input: str) -> str:
    global memory_history

    result = app.invoke({
        "user_input": user_input,
        "selected_usecases": [],
        "mantra_records": [],
        "final_response": "",
        "conversation_history": memory_history,
        "category": ""
    })

    # persist updated memory
    memory_history = result["conversation_history"]

    return result["final_response"]


if __name__ == "__main__":
    while True:
        q = input("\nYou: ")
        if q.lower() in {"exit", "quit"}:
            break
        print("\nGuruji:", ask_guruji(q))
