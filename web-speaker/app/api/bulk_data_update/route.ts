import { bulk_data_update_screen_with_sequence } from "../../actions/bulk_data_update";

export async function GET() {
  try {
    // Example data for testing
    const screens = ["0200068F2535"];
    const sequenceId = "1329AE5711A9D4";
    
    const data = await bulk_data_update_screen_with_sequence(screens, sequenceId);
    
    return Response.json({
      success: true,
      message: "Bulk data update test completed",
      data: data
    });
  } catch (error: any) {
    console.error("Error testing bulk data update:", error);
    return Response.json({ 
      error: "Failed to perform bulk data update",
      details: error?.response?.data || error.message
    }, { status: 500 });
  }
}
