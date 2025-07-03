@dataclass
class MCPAgentConfig:
    """Configuration for the MCP agent."""
    server_url: str = "ws://localhost:3000"
    tools_enabled: List[str] = field(default_factory=lambda: ["all"])
    vault_path: Optional[Path] = None
    model: str = "llama2:7b"
    max_tokens: int = 4000

class ArrowheadMCPAgent:
    """MCP agent that can interact with Obsidian through MCP server."""
    
    def __init__(self, config: MCPAgentConfig):
        self.config = config
        self.server = MCPServer(config.server_url)
        self.tools = ObsidianTools(config.vault_path)
        self.summarizer = LLMSummarizer(config.model)
        
    async def start(self):
        """Start the MCP agent and connect to server."""
        
    async def handle_message(self, message: MCPMessage):
        """Handle incoming MCP messages."""
        
    async def execute_tool(self, tool_name: str, params: dict):
        """Execute a specific tool."""