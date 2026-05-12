from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from app.common import llm, file_tools
import asyncio
import os

load_dotenv()


def create_google_map_mcp_client():
    api_key = os.environ["GOOGLE_MAPS_API_KEY"]

    return MultiServerMCPClient({
        "google-maps": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "google-maps-mcp-server"],
            "env": {
                "GOOGLE_MAPS_API_KEY": api_key,
            },
        }
    })


async def create_and_run_agent():
    client = create_google_map_mcp_client()

    tools = await client.get_tools()

    agent = create_react_agent(llm, tools + file_tools)

    question = """
    Target:
    - My starting location is 5265 Camden Ave, San Jose, CA 95124
    - My destination is Yellowstone National Park, USA
    - Trip duration: 4 days (self-driving road trip)
    - Travel season: based on current real weather conditions (must check forecast before planning)

    Requirements:
    - Design a 4-day Yellowstone National Park itinerary (road trip style)
    - Optimize route efficiency to minimize driving backtracking
    - Each day must include:
    - Morning / Afternoon / Evening plan
    - Driving route between spots
    - Estimated driving time
    - Weather considerations (temperature, rain/snow risk, road closures if any)
    - Wildlife / scenic highlights suggestions
    - Must consider seasonal weather and adjust itinerary accordingly

    Google Maps requirements:
    - Every driving segment must include a clickable Google Maps link
    - Include full route links (not just place links)
    - Example format:
    https://www.google.com/maps/dir/?api=1&origin=...&destination=...

    Weather requirements:
    - Provide daily weather summary for Yellowstone region
    - Suggest clothing and gear based on weather (layers, rain gear, etc.)
    - Warn about possible road closures or delays due to weather

    HTML output requirements:
    - Generate a complete standalone HTML file
    - The HTML must be saved to: app/temp/yellowstone_4day_trip.html
    - The HTML must include:
    - A clean itinerary layout (Day 1–Day 4 sections)
    - Embedded images for each major attraction (use online image URLs)
    - Weather section per day (with icons if possible)
    - Google Maps links for navigation
    - A summary table of the full route
    - A “Tips” section (wildlife safety, bear spray, parking, timing)
    - Must be mobile-friendly layout (responsive design preferred)

    Additional constraints:
    - Prioritize famous Yellowstone locations:
    - Old Faithful
    - Grand Prismatic Spring
    - Yellowstone Lake
    - Grand Canyon of the Yellowstone
    - Lamar Valley
    - Mammoth Hot Springs
    - Avoid unrealistic driving schedules
    - Include early start recommendation (to avoid traffic and wildlife jams)
    - Assume rental car road trip

    Output:
    - Save the itinerary plan to app/temp/yellowstone_4day_trip.html:
    """

    resp = await agent.ainvoke({
        "messages": [
            HumanMessage(content=question)
        ]
    })

    print("\n=== FINAL ANSWER ===")
    print(resp["messages"][-1].content)


asyncio.run(create_and_run_agent())