@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowRequest,
    settings: Settings = Depends(get_settings),
    registry: ToolRegistry = Depends(get_tool_registry),
    memory: MemoryStore = Depends(get_memory_store),
):
    """Create and execute a multi-step workflow."""
    model_gateway = ModelGateway(
        provider=request.model_provider or settings.DEFAULT_MODEL_PROVIDER,
        settings=settings
    )
    
    from app.planner.workflows import WorkflowEngine
    engine = WorkflowEngine(model_gateway=model_gateway, memory=memory)
    
    result = await engine.execute(
        name=request.name,
        description=request.description,
        inputs=request.inputs
    )
    
    return WorkflowResponse(**result)