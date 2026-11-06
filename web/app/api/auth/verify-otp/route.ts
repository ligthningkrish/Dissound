import { NextRequest, NextResponse } from "next/server";
import { verifyOtp, signSessionToken } from "@/lib/auth";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const code = body.code;
    let userId = body.userId;

    // Check cookie fallback if userId not in body
    if (!userId) {
      userId = request.cookies.get("pending_userId")?.value;
    }

    if (!userId || !code) {
      return NextResponse.json(
        { success: false, error: "Missing user identification or verification code." },
        { status: 400 }
      );
    }

    const { valid, record, error } = verifyOtp(userId, code);
    if (!valid || !record) {
      return NextResponse.json(
        { success: false, error: error || "Invalid verification code." },
        { status: 400 }
      );
    }

    // Sign session JWT
    const sessionJwt = signSessionToken(record.userData, record.guilds);

    const response = NextResponse.json({
      success: true,
      message: "Authentication successful! Redirecting to dashboard...",
      redirect: "/dashboard",
      user: {
        id: record.userData.id,
        username: record.userData.username,
        email: record.userData.email,
      },
    });

    // Set 7-day secure HTTP-only cookie
    response.cookies.set("dissound_session", sessionJwt, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      maxAge: 7 * 24 * 60 * 60, // 7 days
      path: "/",
      sameSite: "lax",
    });

    // Clear pending cookie
    response.cookies.delete("pending_userId");

    return response;
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: `Internal server error: ${err.message}` },
      { status: 500 }
    );
  }
}
