import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const response = NextResponse.json({ success: true, redirect: "/" });
  response.cookies.delete("dissound_session");
  response.cookies.delete("pending_userId");
  return response;
}
