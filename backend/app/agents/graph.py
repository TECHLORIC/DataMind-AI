from pathlib import Path
from typing import Dict, Any, Callable
from app.agents.state import AgentState
from app.agents.supervisor import SupervisorAgent
from app.agents.analyst import AnalystAgent
from app.agents.visualization import VisualizationAgent
from app.agents.ml_agent import MLAgent
from app.models.domain.ml import MLTrainRequest

# Check if official langgraph is importable without missing submodules
HAS_LANGGRAPH_PACKAGE = False
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH_PACKAGE = True
except Exception:
    HAS_LANGGRAPH_PACKAGE = False
    END = "__END__"

# Node Implementations
def supervisor_node(state: AgentState) -> AgentState:
    return SupervisorAgent.plan_route(state)

def analyst_node(state: AgentState) -> AgentState:
    parquet_path = Path(state["parquet_path"])
    schema_info = state.get("schema_info", {})
    query = state.get("user_query", "")

    result = AnalystAgent.analyze(parquet_path, schema_info, query, conversation_history=state.get("chat_history"))
    state["analyst_text"] = result.get("explanation")
    state["sql_executed"] = result.get("sql_query")
    state["table_data"] = result.get("table_data")
    state["intent"] = result.get("intent")
    state["route_history"] = state.get("route_history", []) + ["analyst"]
    state["next_step"] = "visualization"
    return state

def ml_node(state: AgentState) -> AgentState:
    parquet_path = Path(state["parquet_path"])
    query = state.get("user_query", "")
    dataset_id = state.get("dataset_id", "")

    req = MLTrainRequest(
        dataset_id=dataset_id,
        task_type="clustering" if "cluster" in query.lower() else "auto"
    )
    try:
        resp = MLAgent.train(parquet_path, req)
        state["ml_summary"] = resp.summary
        state["analyst_text"] = f"### 🤖 AutoML & Pattern Discovery\n\n{resp.summary}\n\n**Algorithm:** `{resp.algorithm_name}`\n**Confidence Score:** `{resp.confidence_score:.1%}`"
        state["model_metrics"] = resp.metrics
        state["feature_importance"] = resp.feature_importance
        state["cluster_profiles"] = resp.cluster_profiles
        state["plotly_spec"] = resp.plotly_spec
        state["route_history"] = state.get("route_history", []) + ["ml_agent"]
    except Exception as e:
        state["error_message"] = str(e)
        state["analyst_text"] = f"ML analysis could not be completed: {str(e)}"

    state["next_step"] = "visualization"
    return state

def visualization_node(state: AgentState) -> AgentState:
    # If ML node already generated a custom plotly spec (e.g. 2D cluster projection or actual-vs-predicted)
    if state.get("plotly_spec"):
        state["route_history"] = state.get("route_history", []) + ["visualization"]
        state["next_step"] = "synthesizer"
        return state

    table_data = state.get("table_data", [])
    intent = state.get("intent", "categorical_ranking")
    query = state.get("user_query", "")

    chart_spec = VisualizationAgent.generate_chart(
        data=table_data,
        intent=intent,
        title=f"Visual Analysis: {query[:36]}..."
    )

    if chart_spec:
        state["chart_spec"] = chart_spec.model_dump()
        state["plotly_spec"] = chart_spec.plotly_spec
        state["echarts_spec"] = chart_spec.echarts_option

    state["route_history"] = state.get("route_history", []) + ["visualization"]
    state["next_step"] = "synthesizer"
    return state

def synthesizer_node(state: AgentState) -> AgentState:
    return SupervisorAgent.synthesize_output(state)

# -------------------------------------------------------------------
# Resilient StateGraph Workflow Compiler
# -------------------------------------------------------------------
class NativeStateGraph:
    """Production-grade StateGraph coordinator with identical semantics to LangGraph."""
    def __init__(self, state_schema):
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable[[AgentState], AgentState]] = {}
        self.entry_point: str = "supervisor"

    def add_node(self, name: str, func: Callable[[AgentState], AgentState]):
        self.nodes[name] = func

    def set_entry_point(self, name: str):
        self.entry_point = name

    def compile(self):
        return CompiledStateWorkflow(self.nodes, self.entry_point)

class CompiledStateWorkflow:
    def __init__(self, nodes: Dict[str, Callable], entry_point: str):
        self.nodes = nodes
        self.entry_point = entry_point

    def invoke(self, initial_state: AgentState) -> AgentState:
        state = dict(initial_state)
        current_node_name = self.entry_point
        max_hops = 10
        hops = 0

        while current_node_name != "__END__" and current_node_name != "end" and hops < max_hops:
            hops += 1
            node_fn = self.nodes.get(current_node_name)
            if not node_fn:
                break

            state = node_fn(state)

            # Routing conditions
            if current_node_name == "supervisor":
                target = state.get("next_step", "analyst")
                current_node_name = "ml_agent" if target == "ml_agent" else "analyst"
            elif current_node_name in ["analyst", "ml_agent"]:
                current_node_name = "visualization"
            elif current_node_name == "visualization":
                current_node_name = "synthesizer"
            elif current_node_name == "synthesizer":
                current_node_name = "__END__"
            else:
                break

        return state

def build_analytics_graph():
    """Builds and compiles the multi-agent analytics state graph."""
    if HAS_LANGGRAPH_PACKAGE:
        try:
            workflow = StateGraph(AgentState)
            workflow.add_node("supervisor", supervisor_node)
            workflow.add_node("analyst", analyst_node)
            workflow.add_node("ml_agent", ml_node)
            workflow.add_node("visualization", visualization_node)
            workflow.add_node("synthesizer", synthesizer_node)

            workflow.set_entry_point("supervisor")

            def route_from_supervisor(state: AgentState):
                return state.get("next_step", "analyst")

            workflow.add_conditional_edges(
                "supervisor",
                route_from_supervisor,
                {
                    "ml_agent": "ml_agent",
                    "analyst": "analyst"
                }
            )
            workflow.add_edge("analyst", "visualization")
            workflow.add_edge("ml_agent", "visualization")
            workflow.add_edge("visualization", "synthesizer")
            workflow.add_edge("synthesizer", END)

            return workflow.compile()
        except Exception:
            pass

    # Native graph execution
    graph = NativeStateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("ml_agent", ml_node)
    graph.add_node("visualization", visualization_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.set_entry_point("supervisor")
    return graph.compile()

# Global compiled graph singleton
analytics_graph = build_analytics_graph()
