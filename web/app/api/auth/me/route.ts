import { NextRequest, NextResponse } from "next/server";
import { verifySessionToken } from "@/lib/auth";

export async function GET(request: NextRequest) {
  const token = request.cookies.get("dissound_session")?.value;
  if (!token) {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }

  const payload = verifySessionToken(token);
  if (!payload) {
    return NextResponse.json({ authenticated: false, error: "Invalid session" }, { status: 401 });
  }

  return NextResponse.json({
    authenticated: true,
    user: payload.user,
    guilds: payload.guilds || [],
  });
}
