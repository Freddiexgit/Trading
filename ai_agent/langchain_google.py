from typing import Annotated
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END, MessagesState



class AgentState(MessagesState):
    company_of_interest: str
    trade_date: str
    messages: Annotated[list[tuple[str, str]], "Conversation history"]

def llm_node(state: AgentState):
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    user_message = state.get("messages") # last message content
    response = llm.invoke(user_message)
    state.get("messages").append(("ai", response.content))
    return state

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("llm_node", llm_node)
    workflow.add_edge(START, "llm_node")
    workflow.add_edge("llm_node", END)
    return workflow.compile()

if __name__ == "__main__":
    os.environ["GOOGLE_API_KEY"] = "AIzaSyCH5ud2FnsklQ-c95YJPDJrIHWJiCxHFDw"
    graph = build_graph()
    init_agent_state = AgentState(
        messages=[
            ("system", "You are a helpful financial analyst..."),  # your system prompt
            ("human", "should hold or sell RBLX?"),
        ],
        company_of_interest="RBLX",
        trade_date="2025-08-011",
    )
    result = graph.invoke(init_agent_state)
    print(result["messages"])


('ai', "As a helpful financial analyst, I can provide you with a balanced overview of factors to consider when deciding whether to hold or sell RBLX (Roblox) stock."
       "\n\n**IMPORTANT DISCLAIMER:** I am an AI and cannot provide personalized financial advice. This information is for educational purposes only and "
       "does not constitute a recommendation to buy, sell, or hold any security. Your investment decisions should always align with your personal "
       "financial goals, risk tolerance, and time horizon. It is highly recommended to consult with a qualified financial advisor before making any"
       " investment decisions.\n\n"
       "---\n\n**Understanding Roblox (RBLX):"
       "**\nRoblox is an online entertainment platform where users can interact with experiences created by other "
       "users and developers. It's known for its user-generated content (UGC) model and its strong appeal to a younger demographic."
       "\n\n**Arguments for HOLDING RBLX:**"
       "\n\n1.  **Strong User Engagement & Network Effects:** Roblox boasts a massive and highly "
       "engaged user base, particularly among younger demographics. The UGC model creates strong network effects: more users attract "
       "more creators, and more creators attract more users."
       "\n2.  **Long-Term Metaverse Potential:** Many view Roblox as a leading contender in "
       "the development of the metaverse. Its existing platform, virtual economy (Robux), and developer ecosystem position it well for future "
       "growth in this evolving space."
       "\n3.  **Diversification Efforts:** Roblox is actively working to diversify its user base by attracting older "
       "users and expanding internationally. They are also exploring new monetization avenues, such as advertising, which could boost future revenue."
       "\n4.  **Healthy Balance Sheet:** Roblox generally maintains a strong cash position, which provides flexibility for investments in technology, "
       "talent, and strategic acquisitions."
       "\n5.  **Innovation and Platform Development:** The company continues to invest heavily in platform technology,"
       " developer tools, and user experience, aiming to keep its platform competitive and cutting-edge.\n6.  **Potential for Profitability Improvement:** "
       "While not consistently profitable yet, as the company scales and potentially moderates its spending on growth initiatives, there's a path towards "
       "improved operating leverage and profitability."
       "\n\n**Arguments for SELLING RBLX:**"
       "\n\n1.  **Slowing Growth Post-Pandemic:** The hyper-growth"
       " seen during the pandemic (when people were stuck at home) has normalized. While still growing, the pace has slowed, leading to investor "
       "concerns about future revenue trajectory."
       "\n2.  **Profitability Challenges:** Despite significant revenue, Roblox has struggled to achieve "
       "consistent GAAP profitability due to high operating costs, investments in R&D, and substantial payouts to developers."
       "n3.  **Demographic Concentration:** While expanding, Roblox still heavily relies on a younger user base, which can have lower average revenue per user"
       " (ARPU) compared to platforms targeting older, more affluent demographics. This also raises concerns about parental spending limits and safety regulations."
       "\n4.  **Intense Competition:** The online gaming and entertainment space is highly competitive. Roblox faces competition from other gaming platforms"
       " (Fortnite, Minecraft), social media companies, and emerging metaverse platforms."
       "\n5.  **Valuation Concerns:** Despite the stock price fluctuations,"
       " some investors still view Roblox's valuation as demanding, especially given its current profitability challenges and slowing growth. It's priced more"
       " like a high-growth tech company than a mature, profitable one."
       "\n6.  **Macroeconomic Headwinds:** Discretionary consumer spending"
       " (on things like in-game purchases) can be impacted by broader economic slowdowns, inflation, and reduced consumer confidence."
       "\n\n**Key Questions to Ask Yourself Before Deciding:**"
       "\n\n*   **What are your original reasons for investing in RBLX?** Have those reasons changed?"
       "\n*   **What is your investment horizon?** Are you looking for short-term gains or long-term growth?\n*   **What is your risk tolerance?**"
       " RBLX is a growth stock with inherent volatility."
       "\n*   **How much conviction do you have in the metaverse and Roblox's ability to capitalize on it?**"
       "\n*   **Have you reviewed their latest earnings report and future guidance?** Look at metrics like bookings, DAU (Daily Active Users), "
       "and ARPU (Average Revenue Per User)."
       "\n*   **How does RBLX fit into your overall portfolio diversification strategy?**\n\n**Conclusion:**\n\n"
       "The decision to hold or sell RBLX depends entirely on your personal investment strategy and outlook.\n\n*   **Consider holding** if you are a "
       "long-term investor who believes strongly in the future of the metaverse, Roblox's platform, its ability to diversify its user base, and its potential "
       "to achieve profitability down the line."
       "\n*   **Consider selling** if you are concerned about slowing growth, persistent unprofitability, competitive pressures,"
       " or if you believe there are better investment opportunities elsewhere that align more closely with your current risk/reward profile."
       "\n\nBefore making any move, conduct thorough due diligence, review the company's latest financial reports, and consider "
       "consulting with a professional financial advisor.")