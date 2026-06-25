import { change_monitor_screen } from "../../actions/change_monitor_screen";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Default values for testing
    const screens = searchParams.getAll("screens").length > 0 
      ? searchParams.getAll("screens") 
      : ["0200068F2535"];
    
    const sequenceId = searchParams.get("sequenceId") || "1329AE5711A9D4";
    const name = searchParams.get("name") || "monitor_tops_bangkhae_map";
    
    const result = await change_monitor_screen(screens, sequenceId, name);
    
    return Response.json({
      test_parameters: { screens, sequenceId, name },
      result: result
    });
  } catch (error: any) {
    console.error("Error testing change_monitor_screen:", error);
    return Response.json({ 
      error: "Critical error in test route",
      details: error.message
    }, { status: 500 });
  }
}
