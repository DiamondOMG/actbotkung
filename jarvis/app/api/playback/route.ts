import { playback } from "../../actions/playback";

export async function GET() {
  try {
    const data = await playback("06BC2025123E");
    return Response.json(data);
  } catch (error) {
    console.error("Error fetching playback:", error);
    return Response.json({ error: "Failed to fetch playback" }, { status: 500 });
  }
}
