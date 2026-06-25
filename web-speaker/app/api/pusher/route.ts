// app/api/pusher/route.ts
import Pusher from "pusher";

const pusher = new Pusher({
  appId: process.env.PUSHER_APP_ID!,
  key: process.env.PUSHER_KEY!,
  secret: process.env.PUSHER_SECRET!,
  cluster: process.env.PUSHER_CLUSTER!,
  useTLS: true,
});

export async function POST(req: Request) {
  const body = await req.json();

  await pusher.trigger(
    "monitor_screen",
    "player-event",
    body
  );
  console.log(body);
  return Response.json({ success: true });
}
