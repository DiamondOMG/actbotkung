import { playback_screen_by_id } from "../../actions/screen";

export async function GET() {
  try {
    const data = await playback_screen_by_id("06BC2025123E");
    return Response.json(data);
  } catch (error) {
    console.error("Error fetching screen:", error);
    return Response.json({ error: "Failed to fetch screen" }, { status: 500 });
  }
}
