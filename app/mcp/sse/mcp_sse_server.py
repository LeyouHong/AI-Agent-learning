from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math Tools")

@mcp.tool()
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y

@mcp.tool()
def multiply(x: int, y: int) -> int:
    """Multiply two numbers"""
    return x * y

if __name__ == "__main__":
    mcp.run(transport="streamable-http")