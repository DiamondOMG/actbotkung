import { remote_api } from "../../actions/remote_api";

export async function GET(request: Request) {
  try {
    // Get parameters from URL if provided, otherwise use defaults for testing
    const { searchParams } = new URL(request.url);
    const sequence_id = searchParams.get("sequence_id") || "0200068F2535";
    const name = searchParams.get("name") || "monitor_tops_bangkhae_map";
    
    const data = await remote_api(sequence_id, name);
    
    return Response.json({
      success: true,
      message: "Remote API trigger test completed",
      input: { sequence_id, name },
      data: data
    });
  } catch (error: any) {
    console.error("Error testing remote API:", error);
    return Response.json({ 
      error: "Failed to trigger remote API",
      details: error?.response?.data || error.message
    }, { status: 500 });
  }
}
