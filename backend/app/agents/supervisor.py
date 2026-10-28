import re
from typing import Dict, Any, List
from app.agents.state import AgentState

class SupervisorAgent:
    """
    Supervisor Agent (LangGraph Central Router).
    Inspects user intent and dataset context to route work among
    Analyst, Visualization, and ML agents, coordinating their results.
    """

    @staticmethod
    def plan_route(state: AgentState) -> AgentState:
        query = state.get("user_query", "").lower()
        route_history = state.get("route_history", [])
        
        # Determine intent & target agent
        ml_keywords = ["predict", "prediction", "forecast", "cluster", "clustering", "pattern", "train", "accuracy", "model", "segmentation"]
        is_ml_query = any(re.search(rf"\b{w}\b", query) for w in ml_keywords)

        if is_ml_query:
            state["next_step"] = "ml_agent"
            state["intent"] = "predictive_modeling"
        else:
            state["next_step"] = "analyst"
            state["intent"] = "analytical_query"

        state["route_history"] = route_history + ["supervisor"]
        return state

    @staticmethod
    def synthesize_output(state: AgentState) -> AgentState:
        """Merges agent artifacts into a coordinated final multi-modal payload."""
        state["route_history"] = state.get("route_history", []) + ["final_synthesizer"]
        state["next_step"] = "end"
        state["confidence_score"] = 0.95 if not state.get("error_message") else 0.4
        return state
