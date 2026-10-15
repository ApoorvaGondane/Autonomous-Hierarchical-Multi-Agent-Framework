from crewai import Agent, LLM
from src.tools import ComponentRAGTool, LogisticsRAGTool, ExactMathTool, MarketSearchTool
from langchain_ollama import ChatOllama
# Initialize the local Ollama LLM endpoint
# Ensures identical execution on both the 11th Gen i7 and your personal laptop
#local_llm = LLM(model="ollama/llama3:8b", base_url="http://localhost:11434")
# Replace the local_llm = LLM(...) block with this:
local_llm = LLM(
    model="ollama/llama3:8b",
    base_url="http://host.docker.internal:11434",
    temperature=0.0
)
# Instantiate customized tools
rag_tool = ComponentRAGTool()
logistics_tool = LogisticsRAGTool()
math_tool = ExactMathTool()
market_tool = MarketSearchTool()

# 1. The Manager (Boss) Agent
manager_agent = Agent(
    role="Chief Product Manager",
    goal="Coordinate cross-functional teams to design, price, and plan a viable physical product that strictly adheres to budget constraints.",
    backstory="You are an uncompromising project manager. You oversee R&D, Manufacturing, and Marketing. You break down requirements, assign sub-tasks, and relentlessly verify outputs. If a worker violates a budget or timeline constraint, you reject their work and demand revisions.",
    allow_delegation=True,
    llm=local_llm,
    max_retry_limit=10, # Add this to all agents
    catch_errors=True,
    verbose=True
)

# 2. R&D Engineer Agent
rnd_agent = Agent(
    role="Lead R&D Engineer",
    goal="Select technically feasible, real-world hardware components to build a draft Bill of Materials (BOM) based on product specs.",
    backstory="You are a pragmatic hardware engineer. You never guess component names or prices. You always query your catalog to find real parts, prioritizing technical feasibility.",
    tools=[rag_tool],
    allow_delegation=False,
    llm=local_llm,
    max_retry_limit=10, # Add this to all agents
    catch_errors=True,
    verbose=True
)

# 3. Manufacturing Lead Agent
mfg_agent = Agent(
    role="Director of Manufacturing",
    goal="Calculate exact unit costs, factory overhead, and project assembly timelines based on the R&D BOM.",
    backstory="You are a strict logistics director. You rely on historical shipping data to understand risks, and you ALWAYS use your calculator for arithmetic. You never estimate mathematical sums.",
    tools=[logistics_tool, math_tool],
    allow_delegation=False,
    llm=local_llm,
    max_retry_limit=10, # Add this to all agents
    catch_errors=True,
    verbose=True
)

# 4. Marketing Strategist Agent
mktg_agent = Agent(
    role="Go-To-Market Strategist",
    goal="Analyze live competitor pricing and define the target demographic and retail price.",
    backstory="You are a savvy market analyst. You search the live web to find current market trends and ensure the product's final retail price yields a healthy profit margin over the manufacturing costs.",
    tools=[market_tool],
    allow_delegation=False,
    llm=local_llm,
    max_retry_limit=10,
    catch_errors=True, # Add this to all agents
    verbose=True
)