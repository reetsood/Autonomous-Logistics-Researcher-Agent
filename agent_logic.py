import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# --- CONFIG ---
os.environ["OPENAI_API_KEY"] = "NA"

# --- TOOLS ---
class CustomSearchTool(BaseTool):
    name: str = "DuckDuckGo Search"
    description: str = "Search the internet for facts, news, and trends. Returns results with Links."
    def _run(self, query: str) -> str:
        return DuckDuckGoSearchResults().run(query)

search_tool = CustomSearchTool()

# --- LLM CONFIG ---
crew_llm = LLM(model="ollama/llama3", base_url="http://localhost:11434")
chat_llm = ChatOllama(model="llama3", base_url="http://localhost:11434")

def get_logistics_research(topic):
    researcher = Agent(
        role='Senior Logistics Data Scout',
        goal=f'Gather comprehensive stats, exact numbers, and recent trends regarding: {topic}. Capture Source URLs.',
        backstory="You are a data collector who hates vague statements. You find exact numbers and the reasons behind them.",
        verbose=True,
        tools=[search_tool],
        llm=crew_llm
    )

    analyst = Agent(
        role='Logistics Educational Strategist',
        goal='Structure data into a professional report with valid Charts',
        backstory="""You are a top-tier analyst. You are a Mermaid.js EXPERT. 
        You know that Pie Charts FAIL if you don't use double quotes and colons correctly.""",
        verbose=True,
        llm=crew_llm
    )

    research_task = Task(
        description=f"Search for '{topic}'. Find exact stats and URLs.",
        expected_output="Raw findings with numbers and URLs.",
        agent=researcher
    )

    report_task = Task(
        description="""
        Create a detailed Markdown report. 
        
        STRICT RULES FOR THE VISUAL TREND (MERMAID):
        1. You MUST use 'pie' format.
        2. Every line MUST follow this EXACT pattern: "Label" : Value
        3. Note the SPACES: Quote-Label-Quote [SPACE] Colon [SPACE] Number.
        4. EXAMPLE:
           ```mermaid
           pie
               title "Correct Chart"
               "Category A" : 50
               "Category B" : 50
           ```
        5. DO NOT use symbols like % or $ in the value. Use pure numbers.

        Structure:
        1. Executive Summary
        2. Detailed Statistical View (Table)
        3. Deep Dive Contextual Analysis (3 paragraphs)
        4. Visual Trend (The Mermaid Pie Chart)
        5. Strategic Recommendations
        6. ## References (List of URLs)
        """,
        expected_output="A professional report with a valid mermaid pie chart and citations.",
        agent=analyst
    )

    crew = Crew(
        agents=[researcher, analyst],
        tasks=[research_task, report_task],
        process=Process.sequential
    )

    print(f"--- Starting Research on: {topic} ---")
    return str(crew.kickoff())

def ask_followup_question(context_text, user_question):
    template = """You are a helpful AI assistant. Answer based on this report: {context} \n\nQuestion: {question}"""
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | chat_llm
    return chain.invoke({"context": context_text, "question": user_question}).content